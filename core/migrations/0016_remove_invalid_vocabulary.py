"""Xóa các từ sinh tự động không tồn tại hoặc sai nghĩa; flashcard của các từ này bị xóa theo."""
from pathlib import Path

from django.db import migrations

REJECTED_FILE = Path(__file__).resolve().parent.parent / "data" / "rejected_vocabulary.txt"
BATCH_SIZE = 500


def remove_invalid_vocabulary(apps, schema_editor):
    Vocabulary = apps.get_model("core", "Vocabulary")
    words = REJECTED_FILE.read_text(encoding="utf-8").split()
    for start in range(0, len(words), BATCH_SIZE):
        Vocabulary.objects.filter(
            user__isnull=True,
            word__in=words[start:start + BATCH_SIZE],
        ).exclude(level="B2").delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0015_schema_cleanup")]

    operations = [migrations.RunPython(remove_invalid_vocabulary, migrations.RunPython.noop)]
