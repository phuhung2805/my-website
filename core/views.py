"""
views.py – Controller của English Pro.

View chỉ đọc yêu cầu, gọi tầng nghiệp vụ (services.py, ai_service.py) và trả phản hồi.

Routes chính:
    /                       → dashboard_view (bảng điều khiển)
    /course/<level>/        → dashboard_view (chọn trình độ đã mở khóa)
    /vocab/                 → index (flashcard đến hạn ôn)
    /login/, /register/     → xác thực (logout chỉ nhận POST)
    /reading|listening|writing|speaking/test/<id>/ → làm bài 4 kỹ năng
    /placement-test/        → bài đầu vào
    /level-up-exam/         → bài thi nâng band
    /api/...                → các API JSON
"""
import collections
import datetime
import json
import math

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone, translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .ai_service import (
    generate_rule_based_explanation,
    get_ai_explanation,
    get_ai_roadmap_feedback,
    grade_writing,
)
from .models import (
    LEVELS,
    SCORE_SCALE_MAX,
    Category,
    Flashcard,
    LevelUpExamResult,
    ListeningTrack,
    PlacementQuestion,
    PlacementTestResult,
    ReadingPassage,
    SpeakingPrompt,
    UserSubmission,
    WritingTask,
    get_next_level,
)
from .services import (
    EXAM_SESSION_KEY,
    WRITING_MIN_WORDS,
    WRITING_WORD_TARGETS,
    apply_sm2,
    calculate_placement_level,
    claim_anonymous_placement,
    due_flashcards,
    exam_questions,
    exam_seconds_remaining,
    get_profile,
    grade_multiple_choice_exam,
    grade_skill_questions,
    is_exam_late,
    is_level_unlocked,
    level_up_cooldown_until,
    placement_questions,
    record_submission,
    resolve_active_level,
    save_speaking_audio,
    skill_feedback,
    skill_progress,
    start_or_resume_exam,
    sync_flashcards,
)

LOCKED_LEVEL_MESSAGE = "Trình độ này chưa mở khóa. Hãy vượt qua bài thi nâng band để học tiếp."


# ---------------------------------------------------------------------------
# Xác thực
# ---------------------------------------------------------------------------

def _safe_next_url(request):
    """Chỉ chuyển hướng tới địa chỉ nội bộ để tránh open redirect."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


def login_view(request):
    """Đăng nhập; tên đăng nhập không phân biệt hoa thường."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        data = request.POST.copy()
        typed = data.get("username", "").strip()
        stored = User.objects.filter(username__iexact=typed).values_list("username", flat=True).first()
        data["username"] = stored or typed
        form = AuthenticationForm(request, data=data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            claim_anonymous_placement(request, user)
            return redirect(_safe_next_url(request) or "dashboard")
        error = "Tên đăng nhập hoặc mật khẩu không chính xác."
    else:
        form = AuthenticationForm()

    return render(request, "core/login.html", {"form": form, "error": error})


def _registration_error(username, password, password_confirm):
    if not username or not password:
        return "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."
    if len(username) > 150:
        return "Tên đăng nhập quá dài."
    try:
        UnicodeUsernameValidator()(username)
    except ValidationError:
        return "Tên đăng nhập chỉ gồm chữ, số và các ký tự @ . + - _"
    if password != password_confirm:
        return "Mật khẩu xác nhận không trùng khớp."
    if User.objects.filter(username__iexact=username).exists():
        return "Tên đăng nhập đã tồn tại trên hệ thống."
    try:
        with translation.override("vi"):
            validate_password(password, user=User(username=username))
    except ValidationError as exc:
        return " ".join(exc.messages)
    return None


def register_view(request):
    """Đăng ký tài khoản rồi đưa học viên đến bài kiểm tra đầu vào."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "")
        error = _registration_error(username, password, request.POST.get("password_confirm", ""))
        if error is None:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                claimed = claim_anonymous_placement(request, user)
            return redirect("dashboard" if claimed else "placement_test")

    return render(request, "core/register.html", {"error": error})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


# ---------------------------------------------------------------------------
# Flashcard
# ---------------------------------------------------------------------------

@login_required
def index(request):
    """Trang flashcard theo trình độ đang học."""
    level, denied = resolve_active_level(request, request.GET.get("level"))
    if denied:
        messages.warning(request, LOCKED_LEVEL_MESSAGE)

    sync_flashcards(request.user, level)
    category = Category.objects.filter(
        Q(user=request.user) | Q(user__isnull=True),
        level=level,
    ).first()

    return render(
        request,
        "core/index.html",
        {"category": category, "flashcards": due_flashcards(request.user, level), "active_level": level},
    )


@login_required
@require_POST
def mark_mastered(request, card_id):
    card = get_object_or_404(Flashcard, id=card_id, user=request.user)
    card.is_mastered = True
    card.review_count += 1
    card.save(update_fields=["is_mastered", "review_count"])
    return redirect("index")


@login_required
@require_POST
def review_flashcard(request, card_id):
    """Nhận đánh giá của học viên và tính lịch ôn tiếp theo theo SM-2."""
    card = get_object_or_404(Flashcard, id=card_id, user=request.user)
    try:
        quality = int(json.loads(request.body).get("quality"))
        apply_sm2(card, quality)
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({"error": "Đánh giá phải là số nguyên từ 0 đến 5."}, status=400)

    return JsonResponse({
        "status": "success",
        "next_review_date": card.next_review_date.strftime("%Y-%m-%d"),
        "interval": card.interval,
        "is_mastered": card.is_mastered,
    })


# ---------------------------------------------------------------------------
# Bảng điều khiển
# ---------------------------------------------------------------------------

def _heatmap_class(count):
    if count == 0:
        return "bg-slate-100 hover:bg-slate-200"
    if count <= 1:
        return "bg-emerald-100 hover:bg-emerald-200"
    if count <= 2:
        return "bg-emerald-300 hover:bg-emerald-400"
    if count <= 4:
        return "bg-emerald-500 hover:bg-emerald-600"
    return "bg-emerald-700 hover:bg-emerald-800"


def _build_heatmap(user, days=126):
    end_date = timezone.localdate()
    start_date = end_date - datetime.timedelta(days=days - 1)
    counts = collections.Counter(
        UserSubmission.objects.filter(
            user=user,
            completed_at__date__range=[start_date, end_date],
        ).values_list("completed_at__date", flat=True)
    )
    return [
        {
            "date_str": day.strftime("%Y-%m-%d"),
            "formatted_date": day.strftime("%d/%m/%Y"),
            "count": counts.get(day, 0),
            "bg_class": _heatmap_class(counts.get(day, 0)),
        }
        for day in (start_date + datetime.timedelta(days=offset) for offset in range(days))
    ]


@login_required
def dashboard_view(request, level_code=None):
    level, denied = resolve_active_level(request, level_code or request.GET.get("level"))
    if denied:
        messages.warning(request, LOCKED_LEVEL_MESSAGE)
        return redirect("dashboard")

    profile = get_profile(request.user)
    days_remaining = None
    if profile.exam_date:
        days_remaining = max(0, (profile.exam_date - timezone.localdate()).days)

    context = {
        "profile": profile,
        "days_remaining": days_remaining,
        "progress": {item["skill"]: item for item in skill_progress(request.user, profile)},
        "recent_submissions": UserSubmission.objects.filter(user=request.user).order_by("-completed_at")[:5],
        "heatmap_data": _build_heatmap(request.user),
        "reading_passages": ReadingPassage.objects.filter(level=level)[:5],
        "listening_tracks": ListeningTrack.objects.filter(level=level)[:5],
        "writing_tasks": WritingTask.objects.filter(level=level)[:5],
        "speaking_prompts": SpeakingPrompt.objects.filter(level=level)[:5],
        "active_level": level,
    }
    return render(request, "core/dashboard.html", context)


def _parse_target(value):
    target = float(value)
    if not math.isfinite(target) or not 0 <= target <= SCORE_SCALE_MAX:
        raise ValueError("Mục tiêu ngoài khoảng cho phép")
    return target


@login_required
@require_POST
def update_goals_view(request):
    """Cập nhật mục tiêu thang 10 và ngày thi của học viên."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Dữ liệu JSON không hợp lệ."}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "Dữ liệu JSON không hợp lệ."}, status=400)

    profile = get_profile(request.user)
    fields = ["target_listening", "target_speaking", "target_reading", "target_writing"]
    try:
        for name in fields:
            setattr(profile, name, _parse_target(data.get(name, getattr(profile, name))))
    except (ValueError, TypeError):
        return JsonResponse({"error": f"Mục tiêu phải là số từ 0 đến {SCORE_SCALE_MAX:g}."}, status=400)

    if "exam_date" in data:
        raw_date = data["exam_date"]
        try:
            profile.exam_date = datetime.date.fromisoformat(raw_date) if raw_date else None
        except (ValueError, TypeError):
            return JsonResponse({"error": "Ngày thi không hợp lệ."}, status=400)
        if profile.exam_date and profile.exam_date < timezone.localdate():
            return JsonResponse({"error": "Ngày thi không được ở trong quá khứ."}, status=400)

    profile.save(update_fields=[*fields, "exam_date"])
    return JsonResponse({
        "status": "success",
        "message": "Cập nhật mục tiêu thành công!",
        "data": {
            **{name: getattr(profile, name) for name in fields},
            "exam_date": profile.exam_date.isoformat() if profile.exam_date else None,
        },
    })


# ---------------------------------------------------------------------------
# Làm bài 4 kỹ năng
# ---------------------------------------------------------------------------

def _level_locked(request, task):
    """Chặn mở đề của trình độ chưa mở khóa, kể cả khi nhập trực tiếp URL."""
    if is_level_unlocked(task.level, get_profile(request.user).assigned_level):
        return False
    messages.warning(request, LOCKED_LEVEL_MESSAGE)
    return True


def _objective_test(request, task, skill, title_prefix, template, context_name):
    """Luồng chung của bài Đọc và Nghe."""
    if _level_locked(request, task):
        return redirect("dashboard")
    questions = task.questions.all()
    if not questions.exists():
        return redirect("dashboard")

    context = {context_name: task, "questions": questions, "mode": "test"}
    if request.method == "POST":
        grade = grade_skill_questions(questions, request.POST)
        feedback = skill_feedback(grade.score_10)
        record_submission(request.user, skill, task, title_prefix, score=grade.score_10, feedback=feedback)
        context.update({
            "mode": "result",
            "score": grade.score,
            "total_questions": grade.total,
            "percentage": grade.percentage,
            "skill_score": grade.score_10,
            "feedback": feedback,
            "results": grade.results,
        })
    return render(request, template, context)


@login_required
def reading_test_view(request, passage_id):
    passage = get_object_or_404(ReadingPassage, id=passage_id)
    return _objective_test(request, passage, "reading", "Reading", "core/reading_test.html", "passage")


@login_required
def listening_test_view(request, track_id):
    track = get_object_or_404(ListeningTrack, id=track_id)
    return _objective_test(request, track, "listening", "Listening", "core/listening_test.html", "track")


@login_required
def writing_test_view(request, task_id):
    """Bài viết được Gemini chấm; khi không có AI thì lưu bài và ghi rõ là chưa chấm."""
    task = get_object_or_404(WritingTask, id=task_id)
    if _level_locked(request, task):
        return redirect("dashboard")

    word_target = WRITING_WORD_TARGETS.get(task.level, WRITING_WORD_TARGETS["B1"])
    context = {"task": task, "mode": "test", "word_target": word_target, "min_words": WRITING_MIN_WORDS}

    if request.method == "POST":
        essay_text = request.POST.get("essay_text", "").strip()
        word_count = len(essay_text.split())
        if word_count < WRITING_MIN_WORDS:
            context.update({
                "essay_text": essay_text,
                "error": f"Bài viết cần ít nhất {WRITING_MIN_WORDS} từ để được ghi nhận.",
            })
            return render(request, "core/writing_test.html", context)

        grade = grade_writing(task.prompt_text, essay_text, task.level, word_count, word_target)
        record_submission(
            request.user, "writing", task, "Writing",
            score=grade["score"], essay_text=essay_text, feedback=grade["feedback"],
        )
        context.update({
            "mode": "result",
            "essay_text": essay_text,
            "word_count": word_count,
            "skill_score": grade["score"],
            "feedback": grade["feedback"],
            "graded_by_ai": grade["source"] == "gemini",
        })
    return render(request, "core/writing_test.html", context)


@login_required
def speaking_test_view(request, prompt_id):
    """Lưu bài ghi âm của học viên. Bài nói chưa được chấm tự động nên không có điểm."""
    prompt = get_object_or_404(SpeakingPrompt, id=prompt_id)
    if _level_locked(request, prompt):
        if request.method == "POST":
            return JsonResponse({"error": LOCKED_LEVEL_MESSAGE}, status=403)
        return redirect("dashboard")

    if request.method == "POST":
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return JsonResponse({"error": "Không tìm thấy dữ liệu âm thanh."}, status=400)
        try:
            audio_path = save_speaking_audio(request.user, prompt, audio_file)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except OSError:
            return JsonResponse({"error": "Không thể lưu file ghi âm. Vui lòng thử lại."}, status=500)

        record_submission(request.user, "speaking", prompt, "Speaking", score=None, audio_path=audio_path)
        return JsonResponse({
            "status": "success",
            "message": "Bài nói của bạn đã được lưu. Hệ thống chưa chấm điểm tự động kỹ năng Nói.",
        })

    return render(request, "core/speaking_test.html", {"prompt": prompt})


# ---------------------------------------------------------------------------
# API dữ liệu
# ---------------------------------------------------------------------------

@login_required
def api_lessons(request):
    """Danh sách bài học theo trình độ đã mở khóa. GET /api/lessons?level=A2"""
    level = request.GET.get("level", "A1").upper()
    if level not in LEVELS:
        return JsonResponse({"error": "Trình độ không hợp lệ. Vui lòng chọn A1, A2, B1 hoặc B2."}, status=400)
    if not is_level_unlocked(level, get_profile(request.user).assigned_level):
        return JsonResponse({"error": LOCKED_LEVEL_MESSAGE}, status=403)

    fields = ("id", "title", "created_at")
    return JsonResponse({
        "status": "success",
        "level": level,
        "data": {
            "reading": list(ReadingPassage.objects.filter(level=level).values(*fields)),
            "listening": list(ListeningTrack.objects.filter(level=level).values(*fields)),
            "writing": list(WritingTask.objects.filter(level=level).values(*fields)),
            "speaking": list(SpeakingPrompt.objects.filter(level=level).values(*fields)),
        },
    })


@login_required
def api_flashcards(request):
    """Danh sách flashcard đến hạn, hỗ trợ tìm kiếm, lọc nhóm từ và phân trang."""
    level, _ = resolve_active_level(request, request.GET.get("level"))
    sync_flashcards(request.user, level)
    queryset = due_flashcards(request.user, level)

    search_query = request.GET.get("search", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(vocabulary__word__icontains=search_query) |
            Q(vocabulary__meaning__icontains=search_query)
        )
    topic_query = request.GET.get("topic", "").strip()
    if topic_query:
        queryset = queryset.filter(vocabulary__topic=topic_query)
    queryset = queryset.order_by("id")

    try:
        page = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page = 1
    limit = 20
    offset = (page - 1) * limit
    total_count = queryset.count()

    return JsonResponse({
        "status": "success",
        "level": level,
        "flashcards": [_flashcard_json(card) for card in queryset[offset:offset + limit]],
        "total_pages": math.ceil(total_count / limit) if total_count else 1,
        "current_page": page,
        "total_count": total_count,
    })


def _flashcard_json(card):
    vocabulary = card.vocabulary
    return {
        "id": card.id,
        "is_mastered": card.is_mastered,
        "review_count": card.review_count,
        "repetition_count": card.repetition_count,
        "easiness_factor": card.easiness_factor,
        "interval": card.interval,
        "next_review_date": card.next_review_date.strftime("%Y-%m-%d") if card.next_review_date else None,
        "vocabulary": {
            "id": vocabulary.id,
            "word": vocabulary.word,
            "ipa": vocabulary.ipa,
            "meaning": vocabulary.meaning,
            "word_type": vocabulary.word_type,
            "word_type_display": vocabulary.get_word_type_display(),
            "example": vocabulary.example,
            "level": vocabulary.level,
            "topic": vocabulary.topic,
        },
    }


# ---------------------------------------------------------------------------
# Bài kiểm tra đầu vào
# ---------------------------------------------------------------------------

def _stored_feedback(result, use_ai, **kwargs):
    """Nhận xét chỉ tạo một lần rồi lưu lại, tải lại trang không gọi AI thêm."""
    if result.ai_feedback:
        return result.ai_feedback
    result.ai_feedback = get_ai_roadmap_feedback(
        score=result.score,
        total=result.total_questions,
        use_ai=use_ai,
        **kwargs,
    )
    result.save(update_fields=["ai_feedback"])
    return result.ai_feedback


def placement_test_view(request):
    """Mỗi tài khoản chỉ làm bài đầu vào một lần; lên trình độ qua bài thi nâng band."""
    if request.user.is_authenticated:
        profile = get_profile(request.user)
        if profile.has_taken_placement_test:
            messages.info(request, "Bạn đã làm bài đầu vào. Hãy dùng bài thi nâng band để lên trình độ tiếp theo.")
            has_result = PlacementTestResult.objects.filter(user=request.user).exists()
            return redirect("placement_result_latest" if has_result else "dashboard")

    questions = placement_questions()

    if request.method == "POST":
        total_questions = questions.count()
        if total_questions == 0:
            return redirect("placement_test")

        score, answers_detail = grade_multiple_choice_exam(questions, request.POST)
        assigned_level, _ = calculate_placement_level(score, total_questions)

        with transaction.atomic():
            result = PlacementTestResult.objects.create(
                user=request.user if request.user.is_authenticated else None,
                score=score,
                total_questions=total_questions,
                assigned_level=assigned_level,
                answers_detail=answers_detail,
            )
            if request.user.is_authenticated:
                profile.assigned_level = assigned_level
                profile.has_taken_placement_test = True
                profile.save(update_fields=["assigned_level", "has_taken_placement_test"])
                request.session["active_level"] = assigned_level

        request.session["last_placement_result_id"] = result.id
        return redirect("placement_result", result_id=result.id)

    return render(
        request,
        "core/placement_test.html",
        {"questions": questions, "total_questions": questions.count()},
    )


PLACEMENT_LEVEL_META = {
    "A1": {
        "title": "A1 - Căn bản (Beginner)",
        "subtitle": "Khởi đầu vững vàng trên con đường chinh phục tiếng Anh",
        "badge_color": "emerald",
        "desc": "Bạn đã bước đầu nhận biết được các từ vựng và câu ngắn cơ bản nhất.",
        "guidance": "Ở trình độ A1, bạn nên tập trung củng cố vốn từ vựng nền tảng về cuộc sống thường ngày (gia đình, đồ vật, số đếm, thời gian) kết hợp cấu trúc thì hiện tại đơn giản.",
        "action_text": "Học từ vựng trình độ A1",
    },
    "A2": {
        "title": "A2 - Sơ cấp (Elementary)",
        "subtitle": "Tự tin giao tiếp và diễn đạt nhu cầu thiết yếu hàng ngày",
        "badge_color": "sky",
        "desc": "Bạn đã nắm khá tốt các câu hỏi thông dụng và giao tiếp cơ bản.",
        "guidance": "Ở trình độ A2, bạn có thể diễn đạt các chủ đề quen thuộc. Hãy mở rộng vốn từ miêu tả, du lịch, mua sắm và làm quen thêm các thì quá khứ đơn, tương lai.",
        "action_text": "Học từ vựng trình độ A2",
    },
    "B1": {
        "title": "B1 - Trung cấp (Intermediate)",
        "subtitle": "Nền tảng vững chắc để bứt phá học thuật",
        "badge_color": "indigo",
        "desc": "Rất tốt! Bạn hiểu ý chính trong ngữ cảnh quen thuộc và xử lý tốt các tình huống giao tiếp.",
        "guidance": "Ở trình độ B1, bạn đã có thể diễn đạt quan điểm, kế hoạch và trải nghiệm cá nhân. Hãy trau dồi thêm collocations, phrasal verbs và rèn 4 kỹ năng chuyên sâu.",
        "action_text": "Học từ vựng trình độ B1",
    },
    "B2": {
        "title": "B2 - Trung cao cấp (Upper Intermediate)",
        "subtitle": "Sử dụng tiếng Anh linh hoạt, tự nhiên với độ chính xác cao",
        "badge_color": "amber",
        "desc": "Xuất sắc! Khả năng nắm bắt ngôn ngữ học thuật và giao tiếp trôi chảy của bạn rất ấn tượng.",
        "guidance": "Ở trình độ B2, bạn đã có thể hiểu các văn bản phức tạp và tương tác trôi chảy. Hãy tiếp tục với các bài đọc học thuật và luyện viết luận chuyên sâu.",
        "action_text": "Học từ vựng trình độ B2",
    },
}


def placement_result_view(request, result_id=None):
    """Chỉ chủ bài làm, quản trị viên hoặc phiên vừa làm bài mới xem được kết quả."""
    session_result_id = request.session.get("last_placement_result_id")
    if result_id:
        result = get_object_or_404(PlacementTestResult, id=result_id)
    elif request.user.is_authenticated:
        result = PlacementTestResult.objects.filter(user=request.user).order_by("-completed_at").first()
        if result is None:
            return redirect("placement_test")
    elif session_result_id:
        result = get_object_or_404(PlacementTestResult, id=session_result_id)
    else:
        return redirect("placement_test")

    is_owner = request.user.is_authenticated and (result.user_id == request.user.id or request.user.is_staff)
    is_session_guest = result.user_id is None and session_result_id == result.id
    if not (is_owner or is_session_guest):
        raise Http404("Không tìm thấy kết quả.")

    ai_feedback = _stored_feedback(
        result,
        use_ai=request.user.is_authenticated,
        level=result.assigned_level,
        exam_type="placement",
    )

    return render(
        request,
        "core/placement_result.html",
        {
            "result": result,
            "percentage": result.percentage,
            "meta": PLACEMENT_LEVEL_META.get(result.assigned_level, PLACEMENT_LEVEL_META["A1"]),
            "ai_feedback": ai_feedback,
            "answers_detail": result.answers_detail or [],
        },
    )


# ---------------------------------------------------------------------------
# Bài thi nâng band
# ---------------------------------------------------------------------------

@login_required
def level_up_exam_view(request):
    """
    Thi từ trình độ hiện tại lên trình độ kế tiếp, đạt khi đúng từ 80%.
    Đề được rút ngẫu nhiên từ ngân hàng riêng; đề và giờ bắt đầu được giữ ở server.
    """
    profile = get_profile(request.user)
    current_level = profile.assigned_level or "A1"
    target_level = get_next_level(current_level)

    if not target_level:
        return render(request, "core/level_up_exam.html", {"is_max_level": True, "current_level": current_level})

    if request.method == "POST":
        exam = request.session.get(EXAM_SESSION_KEY)
        if not exam or exam.get("target") != target_level:
            messages.warning(request, "Phiên làm bài không còn hiệu lực. Vui lòng bắt đầu lại.")
            return redirect("level_up_exam")

        questions = exam_questions(exam)
        if not questions:
            return redirect("dashboard")

        submitted_late = is_exam_late(exam)
        score, answers_detail = grade_multiple_choice_exam(questions, request.POST)
        total_questions = len(questions)
        percentage = round(score / total_questions * 100, 1)
        is_passed = percentage >= settings.LEVEL_UP_PASS_PERCENT and not submitted_late

        with transaction.atomic():
            result = LevelUpExamResult.objects.create(
                user=request.user,
                from_level=current_level,
                target_level=target_level,
                score=score,
                total_questions=total_questions,
                is_passed=is_passed,
                submitted_late=submitted_late,
                answers_detail=answers_detail,
            )
            if is_passed:
                profile.assigned_level = target_level
                profile.save(update_fields=["assigned_level"])
                request.session["active_level"] = target_level

        request.session.pop(EXAM_SESSION_KEY, None)
        request.session["last_levelup_result_id"] = result.id
        return redirect("level_up_result", result_id=result.id)

    cooldown_until = level_up_cooldown_until(request.user)
    if cooldown_until and not request.session.get(EXAM_SESSION_KEY):
        return render(
            request,
            "core/level_up_exam.html",
            {
                "is_cooldown": True,
                "cooldown_until": cooldown_until,
                "current_level": current_level,
                "target_level": target_level,
            },
        )

    exam = start_or_resume_exam(request, target_level)
    questions = exam_questions(exam)
    return render(
        request,
        "core/level_up_exam.html",
        {
            "is_max_level": False,
            "current_level": current_level,
            "target_level": target_level,
            "questions": questions,
            "total_questions": len(questions),
            "seconds_remaining": exam_seconds_remaining(exam),
            "pass_percent": settings.LEVEL_UP_PASS_PERCENT,
        },
    )


LEVEL_UP_LEVEL_META = {
    "A1": {
        "title": "A1 - Căn bản (Beginner)",
        "subtitle": "Khởi đầu nền móng vững chắc",
        "badge_color": "emerald",
    },
    "A2": {
        "title": "A2 - Sơ cấp (Elementary)",
        "subtitle": "Giao tiếp cơ bản và diễn đạt nhu cầu thiết yếu",
        "badge_color": "sky",
    },
    "B1": {
        "title": "B1 - Trung cấp (Intermediate)",
        "subtitle": "Sử dụng tiếng Anh tự tin trong công việc & học thuật",
        "badge_color": "indigo",
    },
    "B2": {
        "title": "B2 - Trung cao cấp (Upper Intermediate)",
        "subtitle": "Làm chủ ngôn ngữ trong môi trường học thuật và công việc",
        "badge_color": "amber",
    },
}


@login_required
def level_up_result_view(request, result_id=None):
    if result_id:
        result = get_object_or_404(LevelUpExamResult, id=result_id)
        if result.user != request.user and not request.user.is_staff:
            return redirect("dashboard")
    else:
        result = LevelUpExamResult.objects.filter(user=request.user).order_by("-completed_at").first()
        if result is None:
            return redirect("level_up_exam")

    ai_feedback = _stored_feedback(
        result,
        use_ai=True,
        level=result.target_level if result.is_passed else result.from_level,
        exam_type="level_up",
        is_passed=result.is_passed,
    )

    return render(
        request,
        "core/level_up_result.html",
        {
            "result": result,
            "percentage": result.percentage,
            "is_passed": result.is_passed,
            "from_level": result.from_level,
            "target_level": result.target_level,
            "target_meta": LEVEL_UP_LEVEL_META.get(result.target_level, LEVEL_UP_LEVEL_META["A2"]),
            "from_meta": LEVEL_UP_LEVEL_META.get(result.from_level, LEVEL_UP_LEVEL_META["A1"]),
            "ai_feedback": ai_feedback,
            "answers_detail": result.answers_detail or [],
            "retry_available_at": level_up_cooldown_until(request.user),
        },
    )


# ---------------------------------------------------------------------------
# Giải thích câu sai
# ---------------------------------------------------------------------------

def _ai_quota_available(user):
    """Gemini chỉ dành cho tài khoản đã đăng nhập và giới hạn số lần mỗi phút."""
    if not user.is_authenticated:
        return False
    key = f"ai-explain:{user.id}:{timezone.now():%Y%m%d%H%M}"
    cache.add(key, 0, timeout=120)
    return cache.incr(key) <= settings.AI_RATE_LIMIT_PER_MINUTE


@require_POST
def api_ai_explain_view(request):
    """
    Trả về lời giải thích câu sai. Gemini chỉ được gọi với câu hỏi có trong CSDL;
    các trường hợp còn lại dùng bộ giải thích theo quy tắc nên không tốn hạn mức.
    """
    data = {}
    if request.content_type == "application/json":
        try:
            parsed = json.loads(request.body.decode("utf-8"))
            data = parsed if isinstance(parsed, dict) else {}
        except (ValueError, UnicodeDecodeError):
            data = {}
    else:
        data = request.POST

    user_answer = str(data.get("user_answer") or "").strip()
    correct_answer = str(data.get("correct_answer") or "").strip() or "Đáp án chuẩn theo ngữ pháp"
    question_text = str(data.get("question_text") or "").strip() or "Câu hỏi trắc nghiệm tiếng Anh"
    level = str(data.get("level") or "A1").strip()
    choices = []
    question = None

    question_id = str(data.get("question_id") or "")
    if question_id.isdigit():
        question = PlacementQuestion.objects.prefetch_related("choices").filter(id=int(question_id)).first()

    if question:
        question_text = question.question_text
        level = question.level
        all_choices = list(question.choices.all())
        choices = [choice.choice_text for choice in all_choices]
        correct = next((choice for choice in all_choices if choice.is_correct), None)
        if correct:
            correct_answer = correct.choice_text
        selected = next((c for c in all_choices if str(c.id) == str(data.get("user_choice_id"))), None)
        if selected:
            user_answer = selected.choice_text

    if question and _ai_quota_available(request.user):
        return JsonResponse(get_ai_explanation(question_text, correct_answer, user_answer, level, choices))

    return JsonResponse({
        "success": True,
        "explanation": generate_rule_based_explanation(question_text, correct_answer, user_answer, level, choices),
        "source": "fallback",
    })


def offline_view(request):
    """Trang hiển thị khi thiết bị mất mạng (được Service Worker lưu sẵn)."""
    return render(request, "offline.html")
