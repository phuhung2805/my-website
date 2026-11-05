from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("course/<str:level_code>/", views.dashboard_view, name="dashboard_level"),
    path("api/lessons", views.api_lessons, name="api_lessons"),
    path("api/flashcards/", views.api_flashcards, name="api_flashcards"),
    path("api/user/goals/", views.update_goals_view, name="update_goals"),
    path("vocab/", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("reading/test/<int:passage_id>/", views.reading_test_view, name="reading_test"),
    path("listening/test/<int:track_id>/", views.listening_test_view, name="listening_test"),
    path("writing/test/<int:task_id>/", views.writing_test_view, name="writing_test"),
    path("speaking/test/<int:prompt_id>/", views.speaking_test_view, name="speaking_test"),
    path("mark-mastered/<int:card_id>/", views.mark_mastered, name="mark_mastered"),
    path("review-flashcard/<int:card_id>/", views.review_flashcard, name="review_flashcard"),

    # Placement Test Routes
    path("placement-test/", views.placement_test_view, name="placement_test"),
    path("placement-test/result/", views.placement_result_view, name="placement_result_latest"),
    path("placement-test/result/<int:result_id>/", views.placement_result_view, name="placement_result"),

    # Level-Up Exam Routes
    path("level-up-exam/", views.level_up_exam_view, name="level_up_exam"),
    path("level-up-exam/result/", views.level_up_result_view, name="level_up_result_latest"),
    path("level-up-exam/result/<int:result_id>/", views.level_up_result_view, name="level_up_result"),

    # AI Tutor Routes
    path("api/ai-explain/", views.api_ai_explain_view, name="api_ai_explain"),

    path("offline/", views.offline_view, name="offline"),
]
