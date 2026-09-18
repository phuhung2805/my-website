from django.core.management.base import BaseCommand
from core.models import Vocabulary, Flashcard

class Command(BaseCommand):
    help = 'Tự động tạo Flashcard cho các từ vựng chưa có thẻ'

    def handle(self, *args, **kwargs):
        vocabs = Vocabulary.objects.all()
        count = 0
        
        for v in vocabs:
            # Tạo thẻ flashcard, nếu đã có rồi thì bỏ qua để tránh lỗi trùng lặp
            obj, created = Flashcard.objects.get_or_create(vocabulary=v)
            if created:
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Tuyệt vời! Đã biến {count} từ vựng thành thẻ Flashcard sẵn sàng để học.'))