"""
services.py – Tầng nghiệp vụ của English Pro.

View chỉ nhận yêu cầu và trả phản hồi (mẫu Controller); các quy tắc về trình độ,
chấm điểm, lịch ôn tập và lưu bài nằm tại đây để dễ kiểm thử và tái sử dụng.
"""
import datetime
import math
import os
import random
from dataclasses import dataclass, field

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import (
    DEFAULT_SKILL_TARGET,
    LEVELS,
    SCORE_SCALE_MAX,
    Flashcard,
    LevelUpExamResult,
    PlacementQuestion,
    PlacementTestResult,
    UserProfile,
    UserSubmission,
    Vocabulary,
)

SKILLS = ["listening", "reading", "writing", "speaking"]

# Số từ tối thiểu đề xuất cho bài viết theo trình độ
WRITING_WORD_TARGETS = {"A1": 50, "A2": 80, "B1": 120, "B2": 180}
WRITING_MIN_WORDS = 20

AUDIO_EXTENSIONS = {
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
}


# ---------------------------------------------------------------------------
# Hồ sơ và trình độ
# ---------------------------------------------------------------------------

def get_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def is_level_unlocked(level: str, assigned_level: str) -> bool:
    return LEVELS.index(level) <= LEVELS.index(assigned_level or "A1")


def resolve_active_level(request, requested=None):
    """
    Trả về (trình độ đang học, có bị từ chối hay không).
    Học viên chỉ được chọn trình độ không vượt quá trình độ đã đạt.
    """
    assigned = get_profile(request.user).assigned_level or "A1"
    candidate = (requested or request.session.get("active_level") or assigned).upper()
    if candidate not in LEVELS:
        candidate = assigned
    denied = not is_level_unlocked(candidate, assigned)
    level = assigned if denied else candidate
    request.session["active_level"] = level
    return level, denied


# ---------------------------------------------------------------------------
# Flashcard
# ---------------------------------------------------------------------------

def sync_flashcards(user, level: str) -> None:
    """Tạo thẻ còn thiếu cho đúng trình độ đang học."""
    existing = Flashcard.objects.filter(user=user).values_list("vocabulary_id", flat=True)
    missing = Vocabulary.objects.filter(
        Q(user=user) | Q(user__isnull=True),
        level=level,
    ).exclude(id__in=existing)
    Flashcard.objects.bulk_create(
        [Flashcard(user=user, vocabulary=vocabulary) for vocabulary in missing],
        ignore_conflicts=True,
    )


def due_flashcards(user, level: str):
    return Flashcard.objects.filter(
        user=user,
        vocabulary__level=level,
        is_mastered=False,
        next_review_date__lte=timezone.localdate(),
    ).select_related("vocabulary")


MASTERED_INTERVAL_DAYS = 21


def apply_sm2(card: Flashcard, quality: int) -> Flashcard:
    """Cập nhật thẻ theo thuật toán SM-2; quality phải nằm trong khoảng 0–5."""
    if not 0 <= quality <= 5:
        raise ValueError("quality phải từ 0 đến 5")

    if quality >= 3:
        if card.repetition_count == 0:
            card.interval = 1
        elif card.repetition_count == 1:
            card.interval = 6
        else:
            card.interval = round(card.interval * card.easiness_factor)
        card.repetition_count += 1
    else:
        card.repetition_count = 0
        card.interval = 1

    delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    card.easiness_factor = max(1.3, card.easiness_factor + delta)
    card.review_count += 1
    card.next_review_date = timezone.localdate() + datetime.timedelta(days=card.interval)
    card.is_mastered = card.interval >= MASTERED_INTERVAL_DAYS
    card.save(update_fields=[
        "repetition_count", "easiness_factor", "interval",
        "next_review_date", "review_count", "is_mastered",
    ])
    return card


# ---------------------------------------------------------------------------
# Chấm điểm
# ---------------------------------------------------------------------------

@dataclass
class SkillGrade:
    score: int
    total: int
    percentage: float
    score_10: float
    results: dict = field(default_factory=dict)


def grade_skill_questions(questions, post_data) -> SkillGrade:
    """Chấm bài Đọc/Nghe và quy đổi tuyến tính sang thang 10."""
    questions = list(questions)
    results = {}
    score = 0
    for question in questions:
        raw_answer = post_data.get(f"q_{question.id}", "").strip()
        is_correct = bool(raw_answer) and question.is_correct(raw_answer)
        score += is_correct
        results[question.id] = {
            "raw_answer": raw_answer,
            "user_answer": _display_answer(question, raw_answer),
            "is_correct": is_correct,
            "correct_answer": _display_answer(question, question.correct_answer),
        }
    total = len(questions)
    percentage = round(score / total * 100, 2) if total else 0.0
    return SkillGrade(score, total, percentage, round(score / total * SCORE_SCALE_MAX, 1) if total else 0.0, results)


def _display_answer(question, answer: str) -> str:
    """Hiển thị nội dung lựa chọn thay vì chữ cái A, B, C."""
    value = (answer or "").strip()
    if len(value) == 1 and value.isalpha() and question.options:
        index = ord(value.upper()) - ord("A")
        if 0 <= index < len(question.options):
            return str(question.options[index])
    return value


def skill_feedback(score_10: float) -> str:
    if score_10 >= 8:
        return "Rất tốt! Bạn đã nắm chắc nội dung của bài này."
    if score_10 >= 5:
        return "Khá ổn. Hãy xem lại các câu sai để củng cố thêm."
    return "Bạn cần luyện thêm. Hãy xem lại đáp án và làm lại bài sau khi ôn tập."


def grade_multiple_choice_exam(questions, post_data):
    """Chấm bài đầu vào hoặc bài nâng band; trả về (số câu đúng, chi tiết từng câu)."""
    score = 0
    answers_detail = []
    for question in questions:
        choices = list(question.choices.all())
        correct = next((c for c in choices if c.is_correct), None)
        selected = None
        raw_choice = post_data.get(f"question_{question.id}", "")
        if str(raw_choice).isdigit():
            selected = next((c for c in choices if c.id == int(raw_choice)), None)
        is_correct = bool(selected and selected.is_correct)
        score += is_correct
        answers_detail.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "level": question.level,
            "selected_choice_id": selected.id if selected else None,
            "selected_choice_text": selected.choice_text if selected else "Chưa chọn",
            "correct_choice_id": correct.id if correct else None,
            "correct_choice_text": correct.choice_text if correct else "",
            "is_correct": is_correct,
        })
    return score, answers_detail


def calculate_placement_level(score, total):
    """
    Quy đổi tỷ lệ đúng sang CEFR: dưới 45% là A1, 45–64.9% là A2,
    65–84.9% là B1, từ 85% là B2.
    """
    if total <= 0:
        return "A1", 0.0
    percentage = round(score / total * 100, 1)
    if percentage >= 85.0:
        return "B2", percentage
    if percentage >= 65.0:
        return "B1", percentage
    if percentage >= 45.0:
        return "A2", percentage
    return "A1", percentage


def placement_questions():
    return (
        PlacementQuestion.objects.filter(exam_type=PlacementQuestion.EXAM_PLACEMENT)
        .prefetch_related("choices")
        .order_by("order", "id")
    )


def claim_anonymous_placement(request, user) -> bool:
    """Gán kết quả bài đầu vào đã làm khi chưa đăng nhập cho tài khoản vừa đăng nhập/đăng ký."""
    result_id = request.session.get("last_placement_result_id")
    if not result_id:
        return False
    profile = get_profile(user)
    if profile.has_taken_placement_test:
        return False
    result = PlacementTestResult.objects.filter(id=result_id, user__isnull=True).first()
    if result is None:
        return False
    result.user = user
    result.save(update_fields=["user"])
    profile.assigned_level = result.assigned_level
    profile.has_taken_placement_test = True
    profile.save(update_fields=["assigned_level", "has_taken_placement_test"])
    request.session["active_level"] = result.assigned_level
    return True


# ---------------------------------------------------------------------------
# Thi nâng band
# ---------------------------------------------------------------------------

EXAM_SESSION_KEY = "level_up_exam"


def level_up_cooldown_until(user):
    """Thời điểm được thi lại sau lần trượt gần nhất, hoặc None nếu được thi ngay."""
    hours = settings.LEVEL_UP_RETRY_COOLDOWN_HOURS
    if hours <= 0:
        return None
    last_fail = LevelUpExamResult.objects.filter(user=user, is_passed=False).order_by("-completed_at").first()
    if last_fail is None:
        return None
    available_at = last_fail.completed_at + datetime.timedelta(hours=hours)
    return available_at if available_at > timezone.now() else None


def start_or_resume_exam(request, target_level: str):
    """Giữ đề và giờ bắt đầu ở server, nên tải lại trang không đổi đề hay đặt lại đồng hồ."""
    exam = request.session.get(EXAM_SESSION_KEY)
    now = timezone.now().timestamp()
    limit = settings.LEVEL_UP_TIME_LIMIT_SECONDS
    if exam and exam["target"] == target_level and now - exam["started_at"] < limit:
        return exam

    bank = list(
        PlacementQuestion.objects.filter(
            exam_type=PlacementQuestion.EXAM_LEVEL_UP,
            level=target_level,
        ).values_list("id", flat=True)
    )
    count = min(settings.LEVEL_UP_QUESTION_COUNT, len(bank))
    exam = {
        "target": target_level,
        "question_ids": random.sample(bank, count),
        "started_at": now,
    }
    request.session[EXAM_SESSION_KEY] = exam
    return exam


def exam_questions(exam):
    by_id = PlacementQuestion.objects.prefetch_related("choices").in_bulk(exam["question_ids"])
    return [by_id[qid] for qid in exam["question_ids"] if qid in by_id]


def exam_seconds_remaining(exam) -> int:
    elapsed = timezone.now().timestamp() - exam["started_at"]
    return max(0, math.ceil(settings.LEVEL_UP_TIME_LIMIT_SECONDS - elapsed))


def is_exam_late(exam) -> bool:
    elapsed = timezone.now().timestamp() - exam["started_at"]
    return elapsed > settings.LEVEL_UP_TIME_LIMIT_SECONDS + settings.LEVEL_UP_GRACE_SECONDS


# ---------------------------------------------------------------------------
# Bài nộp và tiến độ
# ---------------------------------------------------------------------------

def record_submission(user, skill, task, title_prefix, score=None, **extra) -> UserSubmission:
    return UserSubmission.objects.create(
        user=user,
        skill_type=skill,
        task_id=task.id,
        task_title=f"{title_prefix}: {task.title}",
        score_achieved=score,
        **extra,
    )


def save_speaking_audio(user, prompt, audio_file) -> str:
    """Kiểm tra và lưu file ghi âm; trả về đường dẫn tương đối trong MEDIA_ROOT."""
    if audio_file.size == 0:
        raise ValueError("File ghi âm rỗng.")
    if audio_file.size > settings.SPEAKING_MAX_UPLOAD_BYTES:
        raise ValueError("File ghi âm vượt quá dung lượng cho phép (10 MB).")
    content_type = (audio_file.content_type or "").split(";")[0].strip().lower()
    extension = AUDIO_EXTENSIONS.get(content_type)
    if extension is None:
        raise ValueError("Định dạng file không phải âm thanh được hỗ trợ.")

    filename = f"user_{user.id}_prompt_{prompt.id}_{int(timezone.now().timestamp())}.{extension}"
    relative_path = f"speaking_uploads/{filename}"
    full_path = os.path.join(settings.MEDIA_ROOT, "speaking_uploads", filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as destination:
        for chunk in audio_file.chunks():
            destination.write(chunk)
    return relative_path


def skill_progress(user, profile):
    """Tiến độ thật của từng kỹ năng: điểm trung bình 5 bài gần nhất so với mục tiêu."""
    progress = []
    for skill in SKILLS:
        scores = list(
            UserSubmission.objects.filter(user=user, skill_type=skill, score_achieved__isnull=False)
            .order_by("-completed_at")
            .values_list("score_achieved", flat=True)[:5]
        )
        target = getattr(profile, f"target_{skill}") or DEFAULT_SKILL_TARGET
        average = round(sum(scores) / len(scores), 1) if scores else None
        percent = min(100, round(average / target * 100)) if average is not None and target > 0 else 0
        progress.append({"skill": skill, "average": average, "percent": percent, "target": target})
    return progress
