"""
tests.py – Unit tests và integration tests cho English Pro.

Chạy tests:
    pytest --cov=core --cov-report=term-missing
    python manage.py test core

Coverage target: ≥ 80% cho tất cả module core.
"""
import json
from unittest.mock import patch, MagicMock

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import (
    Category, Flashcard, Vocabulary, ReadingPassage, UserProfile,
    PlacementQuestion, PlacementChoice, PlacementTestResult,
    LevelUpExamResult, get_next_level
)
from .views import calculate_placement_level
from .ai_service import get_ai_explanation, get_ai_roadmap_feedback, call_gemini_api


# ===========================================================================

# 3. INTEGRATION TESTS – Django Views (Route Testing)
# ===========================================================================

class ViewsIntegrationTest(TestCase):
    """Test các route bằng Django test client."""

    @classmethod
    def setUpTestData(cls):
        """Tạo dữ liệu dùng chung cho tất cả test trong class."""
        cls.user = User.objects.create_user(username="testuser", password="password")
        cls.cat = Category.objects.create(
            name="Test Category",
            description="Category dùng để test.",
            user=cls.user,
        )
        cls.vocabs = []
        sample_words = [
            ("Apple", "Táo"),
            ("Book", "Quyển sách"),
            ("Car", "Xe hơi"),
            ("Dog", "Con chó"),
            ("Eat", "Ăn"),
        ]
        for word, meaning in sample_words:
            v = Vocabulary.objects.create(
                category=cls.cat,
                user=cls.user,
                word=word,
                meaning=meaning,
                ipa=f"/{word.lower()}/",
                word_type="noun",
                example=f"I see a {word.lower()}.",
            )
            cls.vocabs.append(v)
            Flashcard.objects.create(user=cls.user, vocabulary=v, is_mastered=False)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    # --- index view ---

    def test_index_returns_200(self):
        """GET / → HTTP 200."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_index_uses_correct_template(self):
        """Trang chủ dùng template core/index.html."""
        response = self.client.get(reverse("index"))
        self.assertTemplateUsed(response, "core/index.html")

    def test_index_contains_flashcards_in_context(self):
        """Context của trang chủ phải chứa 'flashcards'."""
        response = self.client.get(reverse("index"))
        self.assertIn("flashcards", response.context)

    # --- mark_mastered view ---

    def test_mark_mastered_redirects_to_index(self):
        """GET /mark-mastered/<id>/ → redirect về trang chủ."""
        card = Flashcard.objects.first()
        response = self.client.get(
            reverse("mark_mastered", kwargs={"card_id": card.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))

    def test_mark_mastered_updates_database(self):
        """Sau khi gọi mark_mastered, is_mastered phải là True."""
        # Tạo card mới chắc chắn is_mastered=False
        v = Vocabulary.objects.create(
            category=self.cat,
            user=self.user,
            word="TestWord",
            meaning="Từ kiểm tra",
            word_type="noun",
        )
        card = Flashcard.objects.create(user=self.user, vocabulary=v, is_mastered=False)
        self.client.get(
            reverse("mark_mastered", kwargs={"card_id": card.id})
        )
        card.refresh_from_db()
        self.assertTrue(card.is_mastered)
        self.assertEqual(card.review_count, 1)

    def test_mark_mastered_404_for_invalid_id(self):
        """mark_mastered với ID không tồn tại → 404."""
        response = self.client.get(
            reverse("mark_mastered", kwargs={"card_id": 99999})
        )
        self.assertEqual(response.status_code, 404)


# ===========================================================================
# 4. TESTS CHO MODELS – Validation và Integrity
# ===========================================================================

class ModelValidationTest(TestCase):
    """Kiểm tra tính toàn vẹn của models."""

    def setUp(self):
        self.cat = Category.objects.create(name="Test", description="")

    def test_vocabulary_str_returns_word(self):
        """__str__ của Vocabulary trả về từ."""
        v = Vocabulary.objects.create(
            category=self.cat, word="Hello", meaning="Xin chào", word_type="other"
        )
        self.assertEqual(str(v), "Hello")

    def test_flashcard_str_format(self):
        """__str__ của Flashcard có định dạng 'Flashcard: <word>'."""
        v = Vocabulary.objects.create(
            category=self.cat, word="World", meaning="Thế giới", word_type="noun"
        )
        card = Flashcard.objects.create(vocabulary=v)
        self.assertEqual(str(card), "Flashcard: World")

    def test_flashcard_default_not_mastered(self):
        """Flashcard mới mặc định is_mastered=False."""
        v = Vocabulary.objects.create(
            category=self.cat, word="New", meaning="Mới", word_type="adjective"
        )
        card = Flashcard.objects.create(vocabulary=v)
        self.assertFalse(card.is_mastered)
        self.assertEqual(card.review_count, 0)

    def test_category_cascade_deletes_vocabulary(self):
        """Xóa Category → xóa tất cả Vocabulary liên quan (CASCADE)."""
        cat2 = Category.objects.create(name="To Delete", description="")
        Vocabulary.objects.create(
            category=cat2, word="Temp", meaning="Tạm", word_type="other"
        )
        vocab_id = Vocabulary.objects.filter(category=cat2).first().id
        cat2.delete()
        self.assertFalse(Vocabulary.objects.filter(id=vocab_id).exists())

    def test_vocabulary_word_type_choices(self):
        """word_type phải là một trong các giá trị hợp lệ."""
        valid_types = ["noun", "verb", "adjective", "adverb",
                       "preposition", "conjunction", "other"]
        for wt in valid_types:
            v = Vocabulary(
                category=self.cat,
                word=f"Word_{wt}",
                meaning="Test",
                word_type=wt,
            )
            # Không raise exception khi tạo với word_type hợp lệ
            v.full_clean()  # Validate Django field choices


class MultiLevelTests(TestCase):
    """Kiểm tra tính năng hỗ trợ đa cấp độ (A1, A2, B1)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser2", password="password")
        cls.cat_a1 = Category.objects.create(name="Cat A1", level="A1", user=cls.user)
        cls.cat_a2 = Category.objects.create(name="Cat A2", level="A2", user=cls.user)

        cls.v_a1 = Vocabulary.objects.create(
            category=cls.cat_a1, word="A1Word", meaning="A1 Meaning", level="A1", user=cls.user
        )
        cls.v_a2 = Vocabulary.objects.create(
            category=cls.cat_a2, word="A2Word", meaning="A2 Meaning", level="A2", user=cls.user
        )

        Flashcard.objects.create(user=cls.user, vocabulary=cls.v_a1, is_mastered=False)
        Flashcard.objects.create(user=cls.user, vocabulary=cls.v_a2, is_mastered=False)

        cls.passage_a1 = ReadingPassage.objects.create(title="Passage A1", text_content="A1 text", level="A1")
        cls.passage_a2 = ReadingPassage.objects.create(title="Passage A2", text_content="A2 text", level="A2")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_dashboard_filters_by_level(self):
        """Dashboard lọc bài học theo level."""
        # Test A1 dashboard (default)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.passage_a1, response.context["reading_passages"])
        self.assertNotIn(self.passage_a2, response.context["reading_passages"])

        # Test A2 dashboard via dynamic route
        response = self.client.get(reverse("dashboard_level", kwargs={"level_code": "a2"}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.passage_a2, response.context["reading_passages"])
        self.assertNotIn(self.passage_a1, response.context["reading_passages"])

    def test_index_filters_flashcards_by_level(self):
        """Trang flashcard lọc từ vựng theo level."""
        response = self.client.get(reverse("index") + "?level=a2")
        self.assertEqual(response.status_code, 200)
        flashcards = response.context["flashcards"]
        self.assertTrue(all(f.vocabulary.level == "A2" for f in flashcards))

    def test_api_lessons_endpoint(self):
        """API /api/lessons trả về dữ liệu đúng trình độ."""
        response = self.client.get(reverse("api_lessons") + "?level=a2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["level"], "A2")
        reading_titles = [r["title"] for r in data["data"]["reading"]]
        self.assertIn("Passage A2", reading_titles)
        self.assertNotIn("Passage A1", reading_titles)

    def test_api_flashcards_endpoint(self):
        """API /api/flashcards/ trả về danh sách flashcards có phân trang, tìm kiếm và lọc."""
        # 1. Gán topic cho từ vựng để test lọc theo chủ đề
        self.v_a1.topic = "home"
        self.v_a1.save()
        self.v_a2.topic = "food"
        self.v_a2.save()

        # 2. Test API mặc định (level A1)
        response = self.client.get(reverse("api_flashcards"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["current_page"], 1)
        self.assertEqual(data["total_count"], 1)
        self.assertEqual(data["flashcards"][0]["vocabulary"]["word"], "A1Word")

        # 3. Test API level A2
        response = self.client.get(reverse("api_flashcards") + "?level=a2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["flashcards"][0]["vocabulary"]["word"], "A2Word")

        # 4. Test lọc theo topic
        response = self.client.get(reverse("api_flashcards") + "?level=a1&topic=home")
        self.assertEqual(response.json()["total_count"], 1)
        response = self.client.get(reverse("api_flashcards") + "?level=a1&topic=food")
        self.assertEqual(response.json()["total_count"], 0)

        # 5. Test tìm kiếm (search)
        response = self.client.get(reverse("api_flashcards") + "?level=a1&search=a1")
        self.assertEqual(response.json()["total_count"], 1)
        response = self.client.get(reverse("api_flashcards") + "?level=a1&search=meaning")
        self.assertEqual(response.json()["total_count"], 1)
        response = self.client.get(reverse("api_flashcards") + "?level=a1&search=xyz")
        self.assertEqual(response.json()["total_count"], 0)

    def test_update_goals_endpoint(self):
        """API /api/user/goals/ cập nhật mục tiêu của UserProfile thành công."""
        payload = {
            "target_listening": 7.5,
            "target_speaking": 8.0,
            "target_reading": 6.5,
            "target_writing": 7.0,
        }
        response = self.client.post(
            reverse("update_goals"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["target_listening"], 7.5)
        self.assertEqual(data["data"]["target_speaking"], 8.0)

        # Kiểm tra UserProfile trong Database đã được cập nhật đúng chưa
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.target_listening, 7.5)
        self.assertEqual(profile.target_speaking, 8.0)
        self.assertEqual(profile.target_reading, 6.5)
        self.assertEqual(profile.target_writing, 7.0)


# ===========================================================================
# 4. PLACEMENT TEST UNIT & INTEGRATION TESTS
# ===========================================================================

class PlacementTestTests(TestCase):
    """Test suite cho tính năng Bài kiểm tra đầu vào (Placement Test)."""

    def setUp(self):
        self.user = User.objects.create_user(username="student1", password="password123")
        self.client = Client()
        self.client.force_login(self.user)

        # Tạo câu hỏi mẫu
        self.q1 = PlacementQuestion.objects.create(
            order=1,
            level="A1",
            question_text="She _______ from Vietnam.",
        )
        self.c1_wrong = PlacementChoice.objects.create(question=self.q1, choice_text="am", is_correct=False)
        self.c1_correct = PlacementChoice.objects.create(question=self.q1, choice_text="is", is_correct=True)

        self.q2 = PlacementQuestion.objects.create(
            order=2,
            level="B1",
            question_text="If I _______ rich, I would travel the world.",
        )
        self.c2_correct = PlacementChoice.objects.create(question=self.q2, choice_text="were", is_correct=True)
        self.c2_wrong = PlacementChoice.objects.create(question=self.q2, choice_text="will be", is_correct=False)

    def test_level_calculation_logic(self):
        """Kiểm tra logic quy đổi % sang CEFR: <45% A1, 45-64% A2, 65-84% B1, >=85% B2."""
        level, pct = calculate_placement_level(0, 10)
        self.assertEqual(level, "A1")
        self.assertEqual(pct, 0.0)

        level, pct = calculate_placement_level(4, 10)
        self.assertEqual(level, "A1")
        self.assertEqual(pct, 40.0)

        level, pct = calculate_placement_level(5, 10)
        self.assertEqual(level, "A2")
        self.assertEqual(pct, 50.0)

        level, pct = calculate_placement_level(7, 10)
        self.assertEqual(level, "B1")
        self.assertEqual(pct, 70.0)

        level, pct = calculate_placement_level(9, 10)
        self.assertEqual(level, "B2")
        self.assertEqual(pct, 90.0)

    def test_placement_test_get_view(self):
        """GET /placement-test/ trả về HTTP 200 và render template đúng."""
        response = self.client.get(reverse("placement_test"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/placement_test.html")
        self.assertIn("questions", response.context)
        self.assertEqual(response.context["total_questions"], 2)

    def test_placement_test_post_and_scoring(self):
        """POST /placement-test/ chấm điểm đúng, lưu kết quả và cập nhật profile."""
        post_data = {
            f"question_{self.q1.id}": self.c1_correct.id,
            f"question_{self.q2.id}": self.c2_wrong.id,
        }
        response = self.client.post(reverse("placement_test"), data=post_data)
        
        # 1/2 câu đúng = 50% -> Level A2
        self.assertEqual(response.status_code, 302)
        
        result = PlacementTestResult.objects.filter(user=self.user).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.score, 1)
        self.assertEqual(result.total_questions, 2)
        self.assertEqual(result.assigned_level, "A2")
        self.assertEqual(result.percentage, 50.0)

        # Kiểm tra cập nhật UserProfile
        profile = UserProfile.objects.get(user=self.user)
        self.assertTrue(profile.has_taken_placement_test)
        self.assertEqual(profile.assigned_level, "A2")

        # Kiểm tra session active_level
        self.assertEqual(self.client.session.get("active_level"), "A2")

    def test_placement_result_view(self):
        """GET /placement-test/result/<id>/ hiển thị đúng kết quả bài test."""
        result = PlacementTestResult.objects.create(
            user=self.user,
            score=2,
            total_questions=2,
            assigned_level="B2",
            answers_detail=[],
        )
        response = self.client.get(reverse("placement_result", kwargs={"result_id": result.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/placement_result.html")
        self.assertEqual(response.context["result"].id, result.id)
        self.assertEqual(response.context["percentage"], 100.0)
        self.assertContains(response, "B2")


# ===========================================================================
# 5. LEVEL-UP EXAM UNIT & INTEGRATION TESTS
# ===========================================================================

class LevelUpExamTests(TestCase):
    """Test suite cho tính năng Bài thi nâng band (Level-Up Exam)."""

    def setUp(self):
        self.user = User.objects.create_user(username="candidate1", password="password123")
        self.profile = UserProfile.objects.create(user=self.user, assigned_level="A1")
        self.client = Client()
        self.client.force_login(self.user)

        # Tạo câu hỏi level A1
        self.q_a1 = PlacementQuestion.objects.create(order=1, level="A1", question_text="A1 Question?")
        PlacementChoice.objects.create(question=self.q_a1, choice_text="Opt A", is_correct=True)
        PlacementChoice.objects.create(question=self.q_a1, choice_text="Opt B", is_correct=False)

        # Tạo 5 câu hỏi level A2 để test target_level A2
        self.a2_questions = []
        for i in range(1, 6):
            q = PlacementQuestion.objects.create(
                order=10 + i,
                level="A2",
                question_text=f"A2 Question {i}?",
            )
            c_correct = PlacementChoice.objects.create(question=q, choice_text="Correct", is_correct=True)
            c_wrong = PlacementChoice.objects.create(question=q, choice_text="Wrong", is_correct=False)
            self.a2_questions.append((q, c_correct, c_wrong))

    def test_get_next_level_logic(self):
        """Kiểm tra quy tắc nâng band: A1 -> A2, A2 -> B1, B1 -> B2, B2 -> None."""
        self.assertEqual(get_next_level("A1"), "A2")
        self.assertEqual(get_next_level("A2"), "B1")
        self.assertEqual(get_next_level("B1"), "B2")
        self.assertIsNone(get_next_level("B2"))
        self.assertIsNone(get_next_level("C1"))

    def test_levelup_requires_login(self):
        """Anonymous user truy cập /level-up-exam/ bị redirect về login."""
        anonymous_client = Client()
        response = anonymous_client.get(reverse("level_up_exam"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_levelup_get_for_a1_user(self):
        """User A1 làm bài thi nâng band target_level A2, chỉ query câu hỏi level A2."""
        response = self.client.get(reverse("level_up_exam"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/level_up_exam.html")
        self.assertEqual(response.context["current_level"], "A1")
        self.assertEqual(response.context["target_level"], "A2")
        self.assertFalse(response.context["is_max_level"])

        # Chỉ có các câu hỏi level A2 trong danh sách questions
        questions = response.context["questions"]
        self.assertEqual(len(questions), 5)
        for q in questions:
            self.assertEqual(q.level, "A2")

    def test_levelup_get_when_already_b2(self):
        """User B2 khi vào trang thi nâng band nhận được thông báo đã đạt cấp độ cao nhất."""
        self.profile.assigned_level = "B2"
        self.profile.save()

        response = self.client.get(reverse("level_up_exam"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_max_level"])
        self.assertEqual(response.context["current_level"], "B2")
        self.assertContains(response, "Bạn Đã Đạt Cấp Độ B2")

    def test_levelup_post_pass_updates_profile_and_session(self):
        """User làm bài đúng 4/5 câu (80%) -> Đậu -> nâng lên A2, cập nhật profile và session."""
        post_data = {}
        # Đúng 4 câu đầu, sai câu thứ 5 -> 4/5 = 80% (Pass)
        for idx, (q, c_correct, c_wrong) in enumerate(self.a2_questions):
            if idx < 4:
                post_data[f"question_{q.id}"] = c_correct.id
            else:
                post_data[f"question_{q.id}"] = c_wrong.id

        response = self.client.post(reverse("level_up_exam"), data=post_data)
        
        # PRG redirect sang trang result
        self.assertEqual(response.status_code, 302)
        
        result = LevelUpExamResult.objects.filter(user=self.user).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.score, 4)
        self.assertEqual(result.total_questions, 5)
        self.assertEqual(result.percentage, 80.0)
        self.assertTrue(result.is_passed)
        self.assertEqual(result.from_level, "A1")
        self.assertEqual(result.target_level, "A2")

        # UserProfile được nâng lên A2
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.assigned_level, "A2")

        # Session active_level được cập nhật
        self.assertEqual(self.client.session.get("active_level"), "A2")

    def test_levelup_post_fail_keeps_original_level(self):
        """User làm bài đúng 2/5 câu (40% < 80%) -> Trượt -> giữ nguyên cấp độ A1."""
        post_data = {}
        for idx, (q, c_correct, c_wrong) in enumerate(self.a2_questions):
            if idx < 2:
                post_data[f"question_{q.id}"] = c_correct.id
            else:
                post_data[f"question_{q.id}"] = c_wrong.id

        response = self.client.post(reverse("level_up_exam"), data=post_data)
        self.assertEqual(response.status_code, 302)

        result = LevelUpExamResult.objects.filter(user=self.user).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.score, 2)
        self.assertFalse(result.is_passed)
        self.assertEqual(result.percentage, 40.0)

        # UserProfile giữ nguyên A1
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.assigned_level, "A1")

    def test_levelup_result_view_access(self):
        """Trang kết quả hiển thị thông tin bài thi của học viên."""
        result = LevelUpExamResult.objects.create(
            user=self.user,
            from_level="A1",
            target_level="A2",
            score=5,
            total_questions=5,
            is_passed=True,
            answers_detail=[],
        )
        response = self.client.get(reverse("level_up_result", kwargs={"result_id": result.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/level_up_result.html")
        self.assertTrue(response.context["is_passed"])
        self.assertEqual(response.context["percentage"], 100.0)
        self.assertContains(response, "Thăng Hạng Thành Công")

    def test_levelup_result_unauthorized_user_redirect(self):
        """User khác không được xem kết quả của candidate1 -> redirect dashboard."""
        other_user = User.objects.create_user(username="other_student", password="password123")
        self.client.force_login(other_user)

        result = LevelUpExamResult.objects.create(
            user=self.user,
            from_level="A1",
            target_level="A2",
            score=5,
            total_questions=5,
            is_passed=True,
            answers_detail=[],
        )
        response = self.client.get(reverse("level_up_result", kwargs={"result_id": result.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))


# ===========================================================================
# 6. AI TUTOR & EXPLANATION UNIT TESTS
# ===========================================================================

class AITutorTests(TestCase):
    """Test suite cho tính năng AI Gia Sư giải thích câu sai & tư vấn lộ trình."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="aitestuser", password="password123")
        self.client.force_login(self.user)

        self.q = PlacementQuestion.objects.create(
            order=1,
            level="A1",
            question_text="She _______ from Vietnam. She is twenty years old.",
        )
        self.c_wrong = PlacementChoice.objects.create(question=self.q, choice_text="am", is_correct=False)
        self.c_correct = PlacementChoice.objects.create(question=self.q, choice_text="is", is_correct=True)

    def test_ai_service_rule_based_fallback_explanation(self):
        """Hàm get_ai_explanation hoạt động trơn tru với fallback khi không có API call."""
        with patch("core.ai_service.call_gemini_api", return_value=None):
            result = get_ai_explanation(
                question_text=self.q.question_text,
                correct_answer="is",
                user_answer="am",
                level="A1",
                choices=["am", "is", "are", "be"],
            )
            self.assertTrue(result["success"])
            self.assertIn("explanation", result)
            self.assertEqual(result["source"], "fallback")
            self.assertTrue(len(result["explanation"]) > 20)
            self.assertIn("is", result["explanation"])

    def test_ai_service_rule_based_fallback_roadmap(self):
        """Hàm get_ai_roadmap_feedback trả về nhận xét lộ trình đúng chuẩn."""
        with patch("core.ai_service.call_gemini_api", return_value=None):
            fb_placement = get_ai_roadmap_feedback(score=8, total=10, level="B1", exam_type="placement")
            self.assertTrue(fb_placement["success"])
            self.assertIn("B1", fb_placement["feedback"])

            fb_passed = get_ai_roadmap_feedback(score=9, total=10, level="B2", exam_type="level_up", is_passed=True)
            self.assertTrue(fb_passed["success"])
            self.assertIn("B2", fb_passed["feedback"])

            fb_failed = get_ai_roadmap_feedback(score=3, total=10, level="A2", exam_type="level_up", is_passed=False)
            self.assertTrue(fb_failed["success"])

    def test_api_ai_explain_endpoint_json_request(self):
        """POST /api/ai-explain/ với JSON body trả về 200 OK và lời giải thích."""
        with patch("core.ai_service.call_gemini_api", return_value=None):
            payload = {
                "question_id": self.q.id,
                "user_choice_id": self.c_wrong.id,
            }
            response = self.client.post(
                reverse("api_ai_explain"),
                data=json.dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertIn("explanation", data)
            self.assertEqual(data["source"], "fallback")

    def test_api_ai_explain_endpoint_form_data_request(self):
        """POST /api/ai-explain/ với form-data và câu hỏi tùy biến trả về 200 OK."""
        with patch("core.ai_service.call_gemini_api", return_value=None):
            response = self.client.post(
                reverse("api_ai_explain"),
                data={
                    "question_text": "If I had known, I _______ you.",
                    "correct_answer": "would have told",
                    "user_answer": "will tell",
                    "level": "B2",
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertIn("explanation", data)

    def test_api_ai_explain_endpoint_handles_missing_params_gracefully(self):
        """POST /api/ai-explain/ với dữ liệu rỗng không bao giờ báo lỗi 500 (Zero-crash)."""
        with patch("core.ai_service.call_gemini_api", return_value=None):
            response = self.client.post(reverse("api_ai_explain"), data={})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertIn("explanation", data)

    @patch("core.ai_service.call_gemini_api")
    def test_gemini_api_integration_mock_success(self, mock_gemini):
        """Khi Gemini API phản hồi thành công, source trả về 'gemini'."""
        mock_gemini.return_value = "Phân tích từ Gemini: Đáp án đúng là 'is' vì chủ ngữ 'She' là ngôi thứ ba số ít."
        result = get_ai_explanation(
            question_text="She _______ a student.",
            correct_answer="is",
            user_answer="am",
            level="A1",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["source"], "gemini")
        self.assertIn("Gemini", result["explanation"])




