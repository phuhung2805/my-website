"""admin.py – Đăng ký tất cả models với Django Admin."""
from django.contrib import admin

from .models import (
    Category,
    Flashcard,
    QuizResult,
    Vocabulary,
    VocabSet,
    UserProfile,
    ReadingPassage,
    ReadingQuestion,
    ListeningTrack,
    ListeningQuestion,
    WritingTask,
    SpeakingPrompt,
    UserSubmission,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "description")
    list_filter = ("user",)
    search_fields = ("name",)


@admin.register(VocabSet)
class VocabSetAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    list_filter = ("user",)
    search_fields = ("title",)
    readonly_fields = ("created_at",)


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ("word", "ipa", "word_type", "meaning", "category", "user")
    list_filter = ("category", "word_type", "user")
    search_fields = ("word", "meaning")


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ("vocabulary", "user", "is_mastered", "review_count")
    list_filter = ("is_mastered", "user")


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "score", "total", "percentage", "completed_at")
    list_filter = ("user", "category")
    readonly_fields = ("completed_at",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "target_listening", "target_speaking", "target_reading", "target_writing", "exam_date")
    list_filter = ("exam_date",)
    search_fields = ("user__username",)


@admin.register(ReadingPassage)
class ReadingPassageAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title", "text_content")


@admin.register(ListeningTrack)
class ListeningTrackAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title", "transcript")


@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title", "prompt_text")


@admin.register(SpeakingPrompt)
class SpeakingPromptAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title", "prompt_text")


@admin.register(UserSubmission)
class UserSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "skill_type", "task_title", "score_achieved", "completed_at")
    list_filter = ("skill_type", "completed_at", "user")
    search_fields = ("task_title", "user__username")


@admin.register(ReadingQuestion)
class ReadingQuestionAdmin(admin.ModelAdmin):
    list_display = ("passage", "question_text", "question_type", "correct_answer")
    list_filter = ("passage", "question_type")
    search_fields = ("question_text", "correct_answer")


@admin.register(ListeningQuestion)
class ListeningQuestionAdmin(admin.ModelAdmin):
    list_display = ("track", "question_text", "question_type", "correct_answer")
    list_filter = ("track", "question_type")
    search_fields = ("question_text", "correct_answer")