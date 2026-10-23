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
    PlacementQuestion,
    PlacementChoice,
    PlacementTestResult,
    LevelUpExamResult,
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
    list_display = (
        "user",
        "assigned_level",
        "has_taken_placement_test",
        "target_listening",
        "target_speaking",
        "target_reading",
        "target_writing",
        "exam_date",
    )
    list_filter = ("assigned_level", "has_taken_placement_test", "exam_date")
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


class PlacementChoiceInline(admin.TabularInline):
    model = PlacementChoice
    extra = 4
    min_num = 2


@admin.register(PlacementQuestion)
class PlacementQuestionAdmin(admin.ModelAdmin):
    list_display = ("order", "question_text", "level", "get_choices_count", "get_correct_choice")
    list_filter = ("level",)
    search_fields = ("question_text",)
    ordering = ("order", "id")
    inlines = [PlacementChoiceInline]

    @admin.display(description="Số lựa chọn")
    def get_choices_count(self, obj):
        return obj.choices.count()

    @admin.display(description="Đáp án đúng")
    def get_correct_choice(self, obj):
        correct = obj.choices.filter(is_correct=True).first()
        return correct.choice_text if correct else "—"


@admin.register(PlacementTestResult)
class PlacementTestResultAdmin(admin.ModelAdmin):
    list_display = ("user", "score", "total_questions", "percentage_display", "assigned_level", "completed_at")
    list_filter = ("assigned_level", "completed_at")
    search_fields = ("user__username",)
    readonly_fields = ("completed_at",)

    @admin.display(description="Tỷ lệ đúng")
    def percentage_display(self, obj):
        return f"{obj.percentage}%"


@admin.register(LevelUpExamResult)
class LevelUpExamResultAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "from_level",
        "target_level",
        "score",
        "total_questions",
        "percentage_display",
        "is_passed",
        "completed_at",
    )
    list_filter = ("is_passed", "from_level", "target_level", "completed_at")
    search_fields = ("user__username",)
    readonly_fields = ("completed_at",)

    @admin.display(description="Tỷ lệ đúng")
    def percentage_display(self, obj):
        return f"{obj.percentage}%"
