import json
import os
from django.core.management.base import BaseCommand
from core.models import Category, Vocabulary

class Command(BaseCommand):
    help = 'Tự động import từ vựng từ file vocab.json vào Database'

    def handle(self, *args, **kwargs):
        # 1. Tạo một Danh mục mặc định nếu chưa có
        category, created = Category.objects.get_or_create(
            name='Giao tiếp hàng ngày',
            defaults={'description': '50 từ vựng tiếng Anh cơ bản trình độ A1'}
        )

        # 2. Tìm và đọc file vocab.json
        file_path = os.path.join('core', 'vocab.json')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = 0
                
                # 3. Lặp qua từng từ và đưa vào Database
                for item in data:
                    # Dùng get_or_create để tránh bị trùng lặp nếu lỡ chạy lệnh 2 lần
                    obj, created_vocab = Vocabulary.objects.get_or_create(
                        word=item['word'],
                        category=category,
                        defaults={
                            'meaning': item['meaning'],
                            'example': item['example']
                        }
                    )
                    if created_vocab:
                        count += 1
                        
            self.stdout.write(self.style.SUCCESS(f'Tuyệt vời! Đã bơm thành công {count} từ vựng vào hệ thống.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Không tìm thấy file vocab.json. Bạn kiểm tra lại xem đã để file trong thư mục core chưa nhé!'))