"""
seed_database.py – Management command để khởi tạo và seed cơ sở dữ liệu.

Sử dụng:
    python manage.py seed_database           # Seed dữ liệu mặc định
    python manage.py seed_database --reset   # Xóa toàn bộ và seed lại từ đầu

Tuân thủ PEP8, sử dụng bulk_create để tối ưu hiệu năng.
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Category, Flashcard, VocabSet, Vocabulary


# ---------------------------------------------------------------------------
# Dữ liệu mẫu
# ---------------------------------------------------------------------------

SAMPLE_CATEGORIES = [
    {
        "name": "Giao Tiếp Hàng Ngày",
        "description": (
            "Các từ vựng cơ bản và thiết yếu nhất cho cuộc sống"
            " và giao tiếp hàng ngày."
        ),
    },
    {
        "name": "Học Thuật & Khoa Học",
        "description": (
            "Từ vựng học thuật dùng trong môi trường giáo dục,"
            " nghiên cứu và khoa học."
        ),
    },
    {
        "name": "Kinh Doanh & Công Nghệ",
        "description": (
            "Thuật ngữ chuyên ngành dùng trong kinh doanh,"
            " công nghệ thông tin và khởi nghiệp."
        ),
    },
]

# Dữ liệu từ vựng học thuật bổ sung (ngoài vocab.json)
EXTRA_VOCAB_DATA = [
    {
        "category": "Học Thuật & Khoa Học",
        "words": [
            {
                "word": "Analyze",
                "ipa": "/ˈænəlaɪz/",
                "meaning": "Phân tích",
                "word_type": "verb",
                "example": "Scientists analyze data to find patterns.",
            },
            {
                "word": "Hypothesis",
                "ipa": "/haɪˈpɒθɪsɪs/",
                "meaning": "Giả thuyết",
                "word_type": "noun",
                "example": "The researcher tested her hypothesis.",
            },
            {
                "word": "Significant",
                "ipa": "/sɪɡˈnɪfɪkənt/",
                "meaning": "Đáng kể, quan trọng",
                "word_type": "adjective",
                "example": "There was a significant increase in results.",
            },
            {
                "word": "Conclude",
                "ipa": "/kənˈkluːd/",
                "meaning": "Kết luận",
                "word_type": "verb",
                "example": "We can conclude that the experiment succeeded.",
            },
            {
                "word": "Evidence",
                "ipa": "/ˈevɪdəns/",
                "meaning": "Bằng chứng",
                "word_type": "noun",
                "example": "There is strong evidence for climate change.",
            },
        ],
    },
    {
        "category": "Kinh Doanh & Công Nghệ",
        "words": [
            {
                "word": "Innovation",
                "ipa": "/ˌɪnəˈveɪʃn/",
                "meaning": "Đổi mới sáng tạo",
                "word_type": "noun",
                "example": "Innovation drives business growth.",
            },
            {
                "word": "Strategy",
                "ipa": "/ˈstrætədʒi/",
                "meaning": "Chiến lược",
                "word_type": "noun",
                "example": "The company developed a new marketing strategy.",
            },
            {
                "word": "Implement",
                "ipa": "/ˈɪmplɪment/",
                "meaning": "Thực hiện, triển khai",
                "word_type": "verb",
                "example": "We will implement the new system next month.",
            },
            {
                "word": "Algorithm",
                "ipa": "/ˈælɡərɪðəm/",
                "meaning": "Thuật toán",
                "word_type": "noun",
                "example": "The search algorithm finds results quickly.",
            },
            {
                "word": "Optimize",
                "ipa": "/ˈɒptɪmaɪz/",
                "meaning": "Tối ưu hóa",
                "word_type": "verb",
                "example": "We need to optimize the code for speed.",
            },
        ],
    },
]


class Command(BaseCommand):
    """Khởi tạo cơ sở dữ liệu với các categories và dữ liệu từ vựng mẫu."""

    help = "Seed cơ sở dữ liệu với dữ liệu từ vựng tiếng Anh mẫu."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xóa toàn bộ dữ liệu hiện có trước khi seed lại.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset_database()

        with transaction.atomic():
            categories = self._seed_categories()
            vocab_count = self._seed_vocabulary_from_json(categories)
            extra_count = self._seed_extra_vocabulary(categories)
            massive_count = self._seed_massive_vocab()
            flashcard_count = self._create_flashcards()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeed hoan tat!\n"
                f"   - {len(categories)} chu de\n"
                f"   - {vocab_count} tu tu vocab.json\n"
                f"   - {extra_count} tu bo sung\n"
                f"   - {massive_count} tu tu massive_vocab.json\n"
                f"   - {flashcard_count} flashcard da tao\n"
            )
        )

    def _reset_database(self):
        """Xóa toàn bộ dữ liệu từ vựng và flashcard."""
        self.stdout.write("[RESET] Dang xoa du lieu cu...")
        Flashcard.objects.all().delete()
        Vocabulary.objects.all().delete()
        VocabSet.objects.all().delete()
        Category.objects.all().delete()
        self.stdout.write(self.style.WARNING("   Da xoa xong."))

    def _seed_categories(self):
        """Tạo các category mẫu nếu chưa tồn tại."""
        categories = {}
        for cat_data in SAMPLE_CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={"description": cat_data["description"]},
            )
            categories[cat_data["name"]] = cat
            status = "[NEW]  " if created else "[SKIP] (da co)"
            self.stdout.write(f"   {status}: Category '{cat.name}'")
        return categories

    def _seed_vocabulary_from_json(self, categories):
        """Đọc vocab.json và chèn vào category đầu tiên."""
        default_cat = categories.get("Giao Tiếp Hàng Ngày")
        if not default_cat:
            raise CommandError("Không tìm thấy category 'Giao Tiếp Hàng Ngày'.")

        json_path = Path(__file__).resolve().parent.parent.parent / "vocab.json"
        if not json_path.exists():
            self.stdout.write(self.style.WARNING(f"   [WARN] Khong tim thay {json_path}, bo qua."))
            return 0

        with open(json_path, encoding="utf-8") as f:
            raw_words = json.load(f)

        count = 0
        for item in raw_words:
            _, created = Vocabulary.objects.get_or_create(
                word=item["word"],
                defaults={
                    "category": default_cat,
                    "ipa": item.get("ipa", ""),
                    "meaning": item.get("meaning", ""),
                    "word_type": "other",
                    "example": item.get("example", ""),
                },
            )
            if created:
                count += 1

        self.stdout.write(f"   [JSON] Da seed {count} tu tu vocab.json")
        return count

    def _seed_extra_vocabulary(self, categories):
        """Chèn từ vựng học thuật và kinh doanh bổ sung."""
        count = 0
        for group in EXTRA_VOCAB_DATA:
            cat = categories.get(group["category"])
            if not cat:
                continue
            for item in group["words"]:
                _, created = Vocabulary.objects.get_or_create(
                    word=item["word"],
                    defaults={
                        "category": cat,
                        "ipa": item.get("ipa", ""),
                        "meaning": item["meaning"],
                        "word_type": item.get("word_type", "other"),
                        "example": item.get("example", ""),
                    },
                )
                if created:
                    count += 1
        self.stdout.write(f"   [EXTRA] Da seed {count} tu bo sung")
        return count

    def _seed_massive_vocab(self):
        """Đọc massive_vocab.json và tạo Category & Vocabulary tương ứng."""
        json_path = Path(settings.BASE_DIR) / "massive_vocab.json"
        if not json_path.exists():
            self.stdout.write(self.style.WARNING(f"   [WARN] Khong tim thay {json_path}, bo qua massive vocab."))
            return 0

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for cat_name, words in data.items():
            cat, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={"description": f"Bộ từ vựng {cat_name}"}
            )
            
            for item in words:
                _, v_created = Vocabulary.objects.get_or_create(
                    word=item["word"],
                    defaults={
                        "category": cat,
                        "ipa": item.get("ipa", ""),
                        "meaning": item.get("meaning", ""),
                        "word_type": item.get("word_type", "other"),
                        "example": item.get("example", ""),
                    },
                )
                if v_created:
                    count += 1
                    
        self.stdout.write(f"   [MASSIVE JSON] Da seed {count} tu tu massive_vocab.json")
        return count

    def _create_flashcards(self):
        """Tạo Flashcard cho tất cả Vocabulary chưa có flashcard."""
        vocabs_without_card = Vocabulary.objects.filter(flashcards__isnull=True)
        flashcards = [
            Flashcard(vocabulary=v, is_mastered=False)
            for v in vocabs_without_card
        ]
        Flashcard.objects.bulk_create(flashcards, ignore_conflicts=True)
        self.stdout.write(f"   [FLASH] Da tao {len(flashcards)} flashcard moi")
        return len(flashcards)
