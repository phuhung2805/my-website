"""
models.py – Core data models cho English Pro.

Cấu trúc quan hệ:
  User (built-in) ──< VocabSet ──< Vocabulary ──1 Flashcard
  Category ──< Vocabulary
  User ──< QuizResult >── Category
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

LEVEL_CHOICES = [
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
]


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


class VocabSet(models.Model):
    """Bộ từ vựng do người dùng tạo ra từ tính năng AI Generator."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="vocab_sets",
        null=True,
        blank=True,
        verbose_name="Người tạo",
    )
    title = models.CharField(max_length=200, verbose_name="Tiêu đề bộ từ vựng")
    source_text = models.TextField(blank=True, verbose_name="Đoạn văn nguồn")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Bộ từ vựng"
        verbose_name_plural = "Bộ từ vựng"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


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
        verbose_name="Chủ đề",
    )
    vocab_set = models.ForeignKey(
        VocabSet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="words",
        verbose_name="Bộ từ vựng",
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
        verbose_name="Chủ đề",
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
        null=True,
        blank=True,
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
    next_review_date = models.DateField(default=timezone.now, verbose_name="Ngày ôn tập tiếp theo")

    class Meta:
        verbose_name = "Flashcard"
        verbose_name_plural = "Flashcard"
        unique_together = ("user", "vocabulary")

    def __str__(self):
        return f"Flashcard: {self.vocabulary.word}"


class QuizResult(models.Model):
    """Kết quả bài kiểm tra – thay thế và mở rộng UserProgress."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quiz_results",
        null=True,
        blank=True,
        verbose_name="Người dùng",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Chủ đề",
    )
    score = models.IntegerField(default=0, verbose_name="Số câu đúng")
    total = models.IntegerField(default=5, verbose_name="Tổng số câu")
    percentage = models.FloatField(default=0.0, verbose_name="Phần trăm đúng")
    answers_detail = models.JSONField(
        default=dict, blank=True, verbose_name="Chi tiết đáp án"
    )
    completed_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Thời gian hoàn thành"
    )

    class Meta:
        verbose_name = "Kết quả kiểm tra"
        verbose_name_plural = "Kết quả kiểm tra"
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.user or 'Khách'} – {self.category} – {self.score}/{self.total}"


# Giữ alias để không phá vỡ code cũ tham chiếu UserProgress
UserProgress = QuizResult


# ===========================================================================
# 4-SKILLS PLATFORM & USER DASHBOARD MODELS
# ===========================================================================

class UserProfile(models.Model):
    """Thông tin cá nhân hóa của học viên, lưu trữ mục tiêu học tập."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    target_listening = models.FloatField(default=0.0, verbose_name="Mục tiêu Nghe (Listening)")
    target_speaking = models.FloatField(default=0.0, verbose_name="Mục tiêu Nói (Speaking)")
    target_reading = models.FloatField(default=0.0, verbose_name="Mục tiêu Đọc (Reading)")
    target_writing = models.FloatField(default=0.0, verbose_name="Mục tiêu Viết (Writing)")
    exam_date = models.DateField(null=True, blank=True, verbose_name="Ngày thi dự kiến")

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
    task_title = models.CharField(max_length=255, verbose_name="Tiêu đề bài tập")
    score_achieved = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Điểm số đạt được",
    )
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


class ReadingQuestion(models.Model):
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
    question_text = models.TextField(verbose_name="Nội dung câu hỏi")
    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPE_CHOICES,
        default="multiple_choice",
        verbose_name="Loại câu hỏi",
    )
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
        verbose_name = "Câu hỏi đọc hiểu"
        verbose_name_plural = "Câu hỏi đọc hiểu"

    def __str__(self):
        return f"{self.passage.title} - Q: {self.question_text[:50]}"


class ListeningQuestion(models.Model):
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
    question_text = models.TextField(verbose_name="Nội dung câu hỏi")
    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPE_CHOICES,
        default="multiple_choice",
        verbose_name="Loại câu hỏi",
    )
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
        verbose_name = "Câu hỏi nghe hiểu"
        verbose_name_plural = "Câu hỏi nghe hiểu"

    def __str__(self):
        return f"{self.track.title} - Q: {self.question_text[:50]}"


class VocabularyQuestion(models.Model):
    """Câu hỏi trắc nghiệm kiểm tra từ vựng."""
    question_text = models.TextField(verbose_name="Câu hỏi")
    options = models.JSONField(default=list, verbose_name="Danh sách lựa chọn (dạng mảng JSON)")
    correct_answer = models.CharField(max_length=255, verbose_name="Đáp án đúng")
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Trình độ",
    )

    class Meta:
        verbose_name = "Câu hỏi từ vựng"
        verbose_name_plural = "Câu hỏi từ vựng"

    def __str__(self):
        return f"Q: {self.question_text[:50]} ({self.level})"