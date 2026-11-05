"""
models.py – Core data models cho English Pro.

Cấu trúc quan hệ:
  Category ──< Vocabulary ──< Flashcard >── User
  User ──1 UserProfile
  User ──< UserSubmission, PlacementTestResult, LevelUpExamResult
  ReadingPassage ──< ReadingQuestion; ListeningTrack ──< ListeningQuestion
  PlacementQuestion ──< PlacementChoice
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

LEVEL_CHOICES = [
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
    ("B2", "B2"),
]
LEVELS = [code for code, _ in LEVEL_CHOICES]

SCORE_SCALE_MAX = 10.0
DEFAULT_SKILL_TARGET = 6.5


class Category(models.Model):
    """Chủ đề từ vựng (ví dụ: Giao tiếp hàng ngày, Du lịch,…)."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
        blank=True,
        verbose_name="Người sở hữu",
    )
    name = models.CharField(max_length=100, verbose_name="Tên chủ đề")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )

    class Meta:
        verbose_name = "Chủ đề"
        verbose_name_plural = "Chủ đề"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Vocabulary(models.Model):
    """Từ vựng tiếng Anh với đầy đủ thông tin ngữ pháp."""

    WORD_TYPE_CHOICES = [
        ("noun", "Danh từ"),
        ("verb", "Động từ"),
        ("adjective", "Tính từ"),
        ("adverb", "Trạng từ"),
        ("preposition", "Giới từ"),
        ("conjunction", "Liên từ"),
        ("other", "Khác"),
    ]

    TOPIC_CHOICES = [
        ("people", "People & Family"),
        ("school", "School & Work"),
        ("home", "Home & Surroundings"),
        ("food", "Food & Drink"),
        ("verbs", "Verbs & Actions"),
        ("adjectives", "Adjectives & Description"),
        ("travel", "Travel & Places"),
        ("weather", "Weather & Seasons"),
        ("nature", "Nature & Environment"),
        ("health", "Health & Sports"),
        ("arts", "Leisure & Arts"),
        ("tech", "Technology & Media"),
        ("communication", "Communication & Info"),
        ("professional", "Professional & Abstract"),
        ("other", "Other topics"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="vocabularies",
        null=True,
        blank=True,
        verbose_name="Người sở hữu",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="vocabularies",
        verbose_name="Giáo trình",
    )
    word = models.CharField(max_length=100, verbose_name="Từ vựng")
    ipa = models.CharField(
        max_length=100, blank=True, verbose_name="Phiên âm IPA"
    )
    meaning = models.CharField(max_length=255, verbose_name="Nghĩa tiếng Việt")
    word_type = models.CharField(
        max_length=20,
        choices=WORD_TYPE_CHOICES,
        default="other",
        verbose_name="Từ loại",
    )
    example = models.TextField(blank=True, verbose_name="Câu ví dụ")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )
    topic = models.CharField(
        max_length=50,
        choices=TOPIC_CHOICES,
        default="other",
        verbose_name="Nhóm từ theo nội dung",
    )

    class Meta:
        verbose_name = "Từ vựng"
        verbose_name_plural = "Từ vựng"
        ordering = ["word"]

    def __str__(self):
        return self.word


class Flashcard(models.Model):
    """Thẻ ghi nhớ liên kết với một từ vựng của một người dùng cụ thể."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="flashcards",
        verbose_name="Người sở hữu",
    )
    vocabulary = models.ForeignKey(
        Vocabulary,
        on_delete=models.CASCADE,
        related_name="flashcards",
        verbose_name="Từ vựng",
    )
    is_mastered = models.BooleanField(default=False, verbose_name="Đã thuộc")
    review_count = models.PositiveIntegerField(
        default=0, verbose_name="Số lần ôn tập"
    )
    repetition_count = models.IntegerField(default=0, verbose_name="Số lần lặp lại liên tiếp")
    easiness_factor = models.FloatField(default=2.5, verbose_name="Hệ số dễ (EF)")
    interval = models.IntegerField(default=0, verbose_name="Khoảng thời gian (ngày)")
    next_review_date = models.DateField(default=timezone.localdate, verbose_name="Ngày ôn tập tiếp theo")

    class Meta:
        verbose_name = "Flashcard"
        verbose_name_plural = "Flashcard"
        unique_together = ("user", "vocabulary")

    def __str__(self):
        return f"Flashcard: {self.vocabulary.word}"


# ===========================================================================
# 4-SKILLS PLATFORM & USER DASHBOARD MODELS
# ===========================================================================

class UserProfile(models.Model):
    """Thông tin cá nhân hóa của học viên, lưu trữ mục tiêu học tập."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    target_listening = models.FloatField(default=DEFAULT_SKILL_TARGET, verbose_name="Mục tiêu Nghe (Listening)")
    target_speaking = models.FloatField(default=DEFAULT_SKILL_TARGET, verbose_name="Mục tiêu Nói (Speaking)")
    target_reading = models.FloatField(default=DEFAULT_SKILL_TARGET, verbose_name="Mục tiêu Đọc (Reading)")
    target_writing = models.FloatField(default=DEFAULT_SKILL_TARGET, verbose_name="Mục tiêu Viết (Writing)")
    exam_date = models.DateField(null=True, blank=True, verbose_name="Ngày thi dự kiến")
    assigned_level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        blank=True,
        verbose_name="Trình độ đầu vào",
    )
    has_taken_placement_test = models.BooleanField(
        default=False,
        verbose_name="Đã làm bài test đầu vào",
    )

    class Meta:
        verbose_name = "Thông tin học viên"
        verbose_name_plural = "Thông tin học viên"

    def __str__(self):
        return f"Profile của {self.user.username}"


class ReadingPassage(models.Model):
    """Bài đọc hiểu."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reading_passages",
        null=True,
        blank=True,
        verbose_name="Người tạo",
    )
    title = models.CharField(max_length=200, verbose_name="Tiêu đề bài đọc")
    text_content = models.TextField(verbose_name="Nội dung văn bản")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )

    class Meta:
        verbose_name = "Bài đọc (Reading)"
        verbose_name_plural = "Bài đọc (Reading)"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ListeningTrack(models.Model):
    """Bài nghe hiểu."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listening_tracks",
        null=True,
        blank=True,
        verbose_name="Người tạo",
    )
    title = models.CharField(max_length=200, verbose_name="Tiêu đề bài nghe")
    audio_file = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Đường dẫn file âm thanh",
    )
    transcript = models.TextField(blank=True, verbose_name="Bản ghi lời thoại (Transcript)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )

    class Meta:
        verbose_name = "Bài nghe (Listening)"
        verbose_name_plural = "Bài nghe (Listening)"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class WritingTask(models.Model):
    """Bài viết luận."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="writing_tasks",
        null=True,
        blank=True,
        verbose_name="Người tạo",
    )
    title = models.CharField(max_length=200, verbose_name="Tiêu đề bài viết")
    prompt_text = models.TextField(verbose_name="Đề bài luận")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )

    class Meta:
        verbose_name = "Bài viết (Writing)"
        verbose_name_plural = "Bài viết (Writing)"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SpeakingPrompt(models.Model):
    """Bài nói/phản xạ."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="speaking_prompts",
        null=True,
        blank=True,
        verbose_name="Người tạo",
    )
    title = models.CharField(max_length=200, verbose_name="Tiêu đề bài nói")
    prompt_text = models.TextField(verbose_name="Câu hỏi phản xạ/chủ đề nói")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )

    class Meta:
        verbose_name = "Bài nói (Speaking)"
        verbose_name_plural = "Bài nói (Speaking)"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class UserSubmission(models.Model):
    """Bản ghi hoạt động nộp bài/hoàn thành bài tập của học viên."""

    SKILL_CHOICES = [
        ("listening", "Listening"),
        ("speaking", "Speaking"),
        ("reading", "Reading"),
        ("writing", "Writing"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Học viên",
    )
    skill_type = models.CharField(
        max_length=20,
        choices=SKILL_CHOICES,
        verbose_name="Kỹ năng",
    )
    task_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Mã đề (theo kỹ năng)",
    )
    task_title = models.CharField(max_length=255, verbose_name="Tiêu đề bài tập")
    score_achieved = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Điểm thang 10 (trống nếu chưa được chấm)",
    )
    essay_text = models.TextField(blank=True, verbose_name="Bài viết")
    audio_path = models.CharField(max_length=255, blank=True, verbose_name="File ghi âm")
    feedback = models.TextField(blank=True, verbose_name="Nhận xét")
    completed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Thời gian hoàn thành",
    )

    class Meta:
        verbose_name = "Lịch sử nộp bài"
        verbose_name_plural = "Lịch sử nộp bài"
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.get_skill_type_display()} - {self.task_title}"


class SkillQuestion(models.Model):
    """Phần chung của câu hỏi kỹ năng Đọc và Nghe."""

    question_text = models.TextField(verbose_name="Nội dung câu hỏi")
    options = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Danh sách lựa chọn (dạng mảng JSON)",
    )
    correct_answer = models.CharField(max_length=255, verbose_name="Đáp án đúng")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )

    class Meta:
        abstract = True

    def is_correct(self, user_answer: str) -> bool:
        """Lớp câu hỏi giữ đáp án nên tự kiểm tra câu trả lời (mẫu Expert)."""
        return self.normalize_answer(user_answer) == self.normalize_answer(self.correct_answer)

    def normalize_answer(self, answer: str) -> str:
        """Quy đáp án dạng chữ cái (A, B, C...) về nội dung lựa chọn rồi so sánh không phân biệt hoa thường."""
        value = (answer or "").strip()
        if len(value) == 1 and value.isalpha() and self.options:
            index = ord(value.upper()) - ord("A")
            if 0 <= index < len(self.options):
                value = str(self.options[index])
        return value.lower()


class ReadingQuestion(SkillQuestion):
    """Câu hỏi thuộc bài đọc hiểu."""

    QUESTION_TYPE_CHOICES = [
        ("multiple_choice", "Trắc nghiệm chọn một (Multiple Choice)"),
        ("tfng", "Đúng / Sai / Không nhắc tới (True / False / Not Given)"),
    ]

    passage = models.ForeignKey(
        ReadingPassage,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Bài đọc",
    )
    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPE_CHOICES,
        default="multiple_choice",
        verbose_name="Loại câu hỏi",
    )

    class Meta:
        verbose_name = "Câu hỏi đọc hiểu"
        verbose_name_plural = "Câu hỏi đọc hiểu"

    def __str__(self):
        return f"{self.passage.title} - Q: {self.question_text[:50]}"


class ListeningQuestion(SkillQuestion):
    """Câu hỏi thuộc bài nghe hiểu."""

    QUESTION_TYPE_CHOICES = [
        ("multiple_choice", "Trắc nghiệm chọn một (Multiple Choice)"),
        ("fill_blank", "Điền vào chỗ trống (Fill in the Blank)"),
    ]

    track = models.ForeignKey(
        ListeningTrack,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Bài nghe",
    )
    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPE_CHOICES,
        default="multiple_choice",
        verbose_name="Loại câu hỏi",
    )

    class Meta:
        verbose_name = "Câu hỏi nghe hiểu"
        verbose_name_plural = "Câu hỏi nghe hiểu"

    def __str__(self):
        return f"{self.track.title} - Q: {self.question_text[:50]}"


# ===========================================================================
# PLACEMENT TEST (BÀI KIỂM TRA ĐẦU VÀO) MODELS
# ===========================================================================

class PlacementQuestion(models.Model):
    """Câu hỏi trắc nghiệm của bài đầu vào hoặc bài thi nâng band (hai ngân hàng đề tách biệt)."""

    EXAM_PLACEMENT = "placement"
    EXAM_LEVEL_UP = "level_up"
    EXAM_TYPE_CHOICES = [
        (EXAM_PLACEMENT, "Bài kiểm tra đầu vào"),
        (EXAM_LEVEL_UP, "Bài thi nâng band"),
    ]

    question_text = models.CharField(max_length=500, verbose_name="Nội dung câu hỏi")
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        default=EXAM_PLACEMENT,
        verbose_name="Thuộc bài thi",
    )
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Độ khó",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự sắp xếp")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Câu hỏi test đầu vào"
        verbose_name_plural = "Câu hỏi test đầu vào"
        ordering = ["order", "id"]

    def __str__(self):
        return f"[{self.level}] #{self.order}: {self.question_text[:50]}"


class PlacementChoice(models.Model):
    """Lựa chọn đáp án cho câu hỏi Placement Test."""

    question = models.ForeignKey(
        PlacementQuestion,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Câu hỏi",
    )
    choice_text = models.CharField(max_length=255, verbose_name="Nội dung lựa chọn")
    is_correct = models.BooleanField(default=False, verbose_name="Đáp án đúng")

    class Meta:
        verbose_name = "Lựa chọn đáp án"
        verbose_name_plural = "Lựa chọn đáp án"

    def __str__(self):
        return f"{self.choice_text} {'(Đúng)' if self.is_correct else ''}"


class PlacementTestResult(models.Model):
    """Kết quả bài kiểm tra đầu vào của học viên."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="placement_results",
        null=True,
        blank=True,
        verbose_name="Học viên",
    )
    score = models.IntegerField(default=0, verbose_name="Số câu đúng")
    total_questions = models.IntegerField(default=0, verbose_name="Tổng số câu")
    assigned_level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ xếp hạng",
    )
    answers_detail = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Chi tiết câu trả lời",
    )
    ai_feedback = models.JSONField(default=dict, blank=True, verbose_name="Nhận xét đã lưu")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian hoàn thành")

    class Meta:
        verbose_name = "Kết quả kiểm tra đầu vào"
        verbose_name_plural = "Kết quả kiểm tra đầu vào"
        ordering = ["-completed_at"]

    def __str__(self):
        username = self.user.username if self.user else "Khách"
        return f"{username} - {self.score}/{self.total_questions} ({self.assigned_level}) - {self.completed_at.strftime('%d/%m/%Y')}"

    @property
    def percentage(self):
        if self.total_questions > 0:
            return round((self.score / self.total_questions) * 100, 1)
        return 0.0


# ===========================================================================
# LEVEL-UP EXAM (BÀI THI NÂNG BAND) MODELS
# ===========================================================================

NEXT_LEVEL_MAP = {
    "A1": "A2",
    "A2": "B1",
    "B1": "B2",
}


def get_next_level(current_level: str):
    """
    Xác định cấp độ tiếp theo theo quy tắc CEFR:
    A1 -> A2, A2 -> B1, B1 -> B2.
    Nếu đang ở B2 hoặc không hợp lệ, trả về None.
    """
    return NEXT_LEVEL_MAP.get(current_level)


class LevelUpExamResult(models.Model):
    """Lịch sử kết quả bài thi nâng band (Level-Up Exam) của học viên."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="levelup_results",
        verbose_name="Học viên",
    )
    from_level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        verbose_name="Cấp độ ban đầu",
    )
    target_level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        verbose_name="Cấp độ mục tiêu",
    )
    score = models.IntegerField(default=0, verbose_name="Số câu đúng")
    total_questions = models.IntegerField(default=0, verbose_name="Tổng số câu")
    is_passed = models.BooleanField(default=False, verbose_name="Kết quả Đạt")
    submitted_late = models.BooleanField(default=False, verbose_name="Nộp quá giờ")
    answers_detail = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Chi tiết câu trả lời",
    )
    ai_feedback = models.JSONField(default=dict, blank=True, verbose_name="Nhận xét đã lưu")
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời gian hoàn thành",
    )

    class Meta:
        verbose_name = "Kết quả thi nâng band"
        verbose_name_plural = "Kết quả thi nâng band"
        ordering = ["-completed_at"]

    def __str__(self):
        status = "Đạt" if self.is_passed else "Không đạt"
        return f"{self.user.username} - {self.from_level} -> {self.target_level}: {self.score}/{self.total_questions} ({status}) - {self.completed_at.strftime('%d/%m/%Y')}"

    @property
    def percentage(self):
        if self.total_questions > 0:
            return round((self.score / self.total_questions) * 100, 1)
        return 0.0
