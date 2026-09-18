import os
from gtts import gTTS
from django.core.management.base import BaseCommand
from core.models import Vocabulary

class Command(BaseCommand):
    help = 'Tạo file âm thanh tự động cho từ vựng'

    def handle(self, *args, **kwargs):
        # Tạo thư mục chứa audio nếu chưa có
        audio_path = os.path.join('static', 'audio')
        if not os.path.exists(audio_path):
            os.makedirs(audio_path)

        vocabs = Vocabulary.objects.all()
        self.stdout.write(f"Đang tạo âm thanh cho {vocabs.count()} từ...")

        for v in vocabs:
            file_name = f"{v.word.lower()}.mp3"
            full_path = os.path.join(audio_path, file_name)
            
            # Chỉ tạo nếu file chưa tồn tại
            if not os.path.exists(full_path):
                tts = gTTS(text=v.word, lang='en')
                tts.save(full_path)
                self.stdout.write(self.style.SUCCESS(f"Đã xong: {v.word}"))
        
        self.stdout.write(self.style.SUCCESS("Hoàn thành tạo kho âm thanh!"))