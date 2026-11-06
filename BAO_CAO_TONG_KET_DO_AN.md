# BÁO CÁO TỔNG KẾT ĐỒ ÁN
## ĐỀ TÀI: XÂY DỰNG NỀN TẢNG HỌC TIẾNG ANH THEO KHUNG THAM CHIẾU CEFR (ENGLISH PRO)

* **Học phần:** Phân tích thiết kế hệ thống
* **Sinh viên thực hiện:** Đặng Quang Hưng
* **Công nghệ:** Python 3.11, Django 5.2, SQLite, Tailwind CSS, Google Gemini REST API
* **Kết quả kiểm thử:** 89/89 test đạt; độ phủ `views.py` 90%, `services.py` 96%, `models.py` 93%, `ai_service.py` 79%
* **Tài liệu thiết kế UML:** [docs/THIET_KE_UML.md](docs/THIET_KE_UML.md)

---

## 1. Tổng quan

English Pro giúp người học xác định trình độ theo khung CEFR (A1, A2, B1, B2), học từ vựng bằng flashcard lặp lại ngắt quãng, luyện 4 kỹ năng và lên trình độ qua bài thi. Hệ thống dùng kiến trúc MVT của Django, tách riêng tầng nghiệp vụ trong `core/services.py` và dịch vụ AI trong `core/ai_service.py`.

Thang đo thống nhất trong toàn hệ thống:
* **Trình độ:** CEFR A1–B2. Hệ thống không phải là công cụ luyện hay quy đổi điểm IELTS.
* **Điểm bài luyện:** thang 10, tính tuyến tính theo số câu đúng ở cả Nghe và Đọc.

## 2. Các phân hệ

### 2.1. Xác thực
Đăng ký dùng bộ kiểm tra mật khẩu của Django (tối thiểu 8 ký tự, không quá phổ biến). Tên đăng nhập không phân biệt hoa thường. Đăng xuất chỉ nhận POST. Sau đăng nhập chỉ chuyển hướng tới địa chỉ nội bộ.

### 2.2. Bài kiểm tra đầu vào
* 40 câu trắc nghiệm, 10 câu cho mỗi trình độ, khoảng 20–30 phút, không tính giờ.
* Thứ tự đáp án được trộn khi hiển thị.
* Mỗi tài khoản làm một lần. Khách vẫn làm được và kết quả được gán khi đăng ký hoặc đăng nhập.
* Chỉ chủ bài làm, quản trị viên hoặc phiên vừa làm bài mới xem được kết quả.

| Tỷ lệ đúng | Trình độ |
| :--- | :---: |
| Dưới 45% | A1 |
| 45% – 64.9% | A2 |
| 65% – 84.9% | B1 |
| Từ 85% | B2 |

### 2.3. Bài thi nâng band
* Rút ngẫu nhiên 10 câu từ ngân hàng riêng (15 câu cho mỗi trình độ A2, B1, B2), không trùng với bài đầu vào.
* Đạt khi đúng từ 80%. Đề và giờ bắt đầu lưu ở server, tải lại trang không đổi đề hay đặt lại đồng hồ.
* Giới hạn 10 phút, cho phép trễ 30 giây để tính độ trễ mạng. Nộp muộn hơn thì bài được lưu nhưng không tính đạt.
* Sau khi trượt phải chờ 24 giờ mới thi lại (đổi bằng biến `LEVEL_UP_RETRY_COOLDOWN_HOURS`; đặt 0 để tắt khi demo).
* Học viên chỉ học được trình độ không vượt quá trình độ đã đạt, kể cả khi nhập trực tiếp URL.

### 2.4. Flashcard
Thuật toán SM-2 nhận mức đánh giá 0–5. Thẻ được đánh dấu đã thuộc khi khoảng cách ôn đạt từ 21 ngày. Thẻ chỉ được tạo cho trình độ học viên đang học.

### 2.5. Luyện 4 kỹ năng

| Kỹ năng | Cách hoạt động | Chấm điểm |
| :--- | :--- | :--- |
| Đọc | Trắc nghiệm theo bài đọc | Tự động, thang 10 |
| Nghe | Trình duyệt đọc transcript (Web Speech API); hiện lời thoại sau khi nộp | Tự động, thang 10 |
| Viết | Soạn bài, tối thiểu 20 từ, bài được lưu lại | Do Gemini chấm; nếu AI không khả dụng thì ghi "Chưa chấm", không tự đặt điểm |
| Nói | Ghi âm và lưu file, kiểm tra định dạng và giới hạn 10 MB | **Chưa chấm tự động**, không có điểm |

### 2.6. Giải thích câu sai
* **Gemini:** chỉ dành cho tài khoản đã đăng nhập, chỉ với câu hỏi có trong CSDL, tối đa 10 lần mỗi phút, timeout 8 giây.
* **Bộ quy tắc dự phòng:** khớp mẫu ngữ pháp theo trọn từ. Đây là luật viết sẵn, không phải AI, nên giao diện ghi nguồn là "Theo quy tắc". Câu chưa có quy tắc riêng sẽ nhận lời giải thích chung.
* Nhận xét tổng quan chỉ tạo một lần rồi lưu lại, tải lại trang không gọi AI thêm.

### 2.7. Bảng điều khiển
Hiển thị trình độ, mục tiêu thang 10 và ngày thi do học viên tự đặt, tiến độ thật (điểm trung bình 5 bài gần nhất so với mục tiêu), heatmap hoạt động và lịch sử bài nộp.

### 2.8. PWA
Có manifest và Service Worker. Trang có dữ liệu cá nhân không được lưu cache; khi mất mạng người dùng thấy trang thông báo ngoại tuyến. Hệ thống **không** hỗ trợ học offline.

## 3. Kiểm thử

Chạy bằng `pytest core/tests.py` hoặc `python manage.py test core`. Bộ test gồm 89 ca, trong đó các nhóm mới bao phủ:
* Bảo mật: mật khẩu yếu, open redirect, quyền xem kết quả, đổi dữ liệu phải dùng POST.
* Quy tắc trình độ: khóa cấp độ, làm bài đầu vào một lần, gán kết quả của khách.
* Thi nâng band: ngân hàng đề riêng, giữ đề khi tải lại, nộp quá giờ, thời gian chờ thi lại.
* Chấm điểm: đối chiếu đáp án trắc nghiệm, bài viết khi có và không có AI, kiểm tra file ghi âm.
* Dữ liệu đầu vào: mức đánh giá SM-2, mục tiêu ngoài khoảng, ngày thi không hợp lệ.
* Dịch vụ AI: không gọi API thật khi test, giới hạn tần suất, bộ quy tắc dự phòng.

Việc gọi Gemini thật chỉ được kiểm thử bằng mock, nên cần chạy thử một lần với khóa API hợp lệ trước khi báo cáo.

## 4. Hướng dẫn cài đặt

```bash
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_large_data
python manage.py seed_b2_content
python manage.py seed_placement_test
python manage.py createsuperuser
python manage.py runserver
```

Điền khóa của bạn vào `GEMINI_API_KEY` trong `.env`. Không commit file này và không ghi khóa vào tài liệu.

**Triển khai trên Render:** đặt biến môi trường `DJANGO_SECRET_KEY` và `GEMINI_API_KEY`; `build.sh` tự chạy migrate và tạo dữ liệu.

## 5. Kịch bản demo

1. Đăng ký tài khoản mới, hệ thống chuyển tới bài đầu vào. Làm bài và xem trình độ được xếp.
2. Mở thử một trình độ cao hơn để thấy biểu tượng khóa và thông báo chưa mở khóa.
3. Học flashcard, đánh giá vài thẻ để thấy thẻ rời khỏi danh sách đến hạn.
4. Làm một bài Đọc hoặc Nghe, xem điểm thang 10; ở bài Nghe bấm phát để nghe và xem lời thoại sau khi nộp.
5. Thi nâng band: chỉ đồng hồ, tải lại trang để thấy đề và thời gian không đổi, rồi nộp bài.
6. Ở trang kết quả, bấm "Giải thích câu này" tại một câu sai và chỉ ra nhãn nguồn của lời giải thích.

Khi trình bày, nên chuẩn bị trước một tài khoản chưa thi và đặt `LEVEL_UP_RETRY_COOLDOWN_HOURS=0` nếu cần thi lại nhiều lần.

## 6. Giới hạn hiện tại

* **Chất lượng từ vựng A1–B1:** kho từ đã được lọc: từ ghép tự động chỉ được giữ nếu tần suất sử dụng đủ cao theo dữ liệu wordfreq (Zipf từ 3.0) và nghĩa ghép đúng theo rà soát thủ công. Danh sách từ bị loại nằm ở `core/data/rejected_vocabulary.txt`. Phiên âm và câu ví dụ của từ ghép vẫn sinh theo quy tắc nên chưa được kiểm tra từng từ.
* **Nội dung B2 ít hơn:** 60 từ và 3 bài mỗi kỹ năng, so với khoảng 470–550 từ và 7 bài ở các trình độ khác.
* **Kỹ năng Nói** chưa được chấm tự động.
* **Dữ liệu trên Render:** SQLite và file ghi âm có thể mất khi triển khai lại; vận hành thật cần PostgreSQL và dịch vụ lưu file.
* **Bộ quy tắc giải thích** chỉ phủ các chủ điểm phổ biến.
* **Giao diện** dùng Tailwind Play CDN, phù hợp để demo nhưng cần chuyển sang bản biên dịch khi vận hành thật.

## 7. Hướng phát triển

* Mở rộng nội dung B2 và rà soát phiên âm, câu ví dụ của từ ghép.
* Chấm bài Nói bằng nhận diện giọng nói.
* Chuyển sang PostgreSQL và lưu trữ file bên ngoài.
* Bài kiểm tra thích ứng theo năng lực.
