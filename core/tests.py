"""
tests.py – Unit tests và integration tests cho English Pro.

Chạy tests:
    pytest --cov=core --cov-report=term-missing
    python manage.py test core

Coverage target: ≥ 80% cho tất cả module core.
"""
import json

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Category, Flashcard, Vocabulary, ReadingPassage, UserProfile


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

