"""Dọn dữ liệu sai trước khi siết lược đồ."""
from django.db import migrations

DEFAULT_TARGET = 6.5
TARGET_FIELDS = ["target_listening", "target_speaking", "target_reading", "target_writing"]


def clean_data(apps, schema_editor):
    # Thẻ không có chủ sinh ra từ các lệnh seed cũ, không học viên nào dùng được.
    apps.get_model("core", "Flashcard").objects.filter(user__isnull=True).delete()

    # Mục tiêu cũ lẫn lộn 0, 75, 80; đưa về thang 10.
    UserProfile = apps.get_model("core", "UserProfile")
    for profile in UserProfile.objects.all():
        for name in TARGET_FIELDS:
            value = getattr(profile, name)
            if not 0 < value <= 10:
                setattr(profile, name, DEFAULT_TARGET)
        profile.save(update_fields=TARGET_FIELDS)

    # Điểm cũ không có giá trị: Nói ngẫu nhiên, Viết đếm số từ, Đọc/Nghe chấm sai đáp án trắc nghiệm.
    apps.get_model("core", "UserSubmission").objects.update(score_achieved=None)


class Migration(migrations.Migration):
    dependencies = [("core", "0013_levelupexamresult")]

    operations = [migrations.RunPython(clean_data, migrations.RunPython.noop)]
