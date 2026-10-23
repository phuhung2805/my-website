# BÁO CÁO TỔNG KẾT ĐỒ ÁN CHUYÊN NGÀNH
## ĐỀ TÀI: XÂY DỰNG NỀN TẢNG HỌC TIẾNG ANH VÀ ĐÁNH GIÁ NĂNG LỰC TRỰC TUYẾN THEO CHUẨN KHUNG THAM CHIẾU CEFR (ENGLISH PRO)

* **Học phần:** Đồ án Chuyên ngành Công nghệ Thông tin / Phát triển Ứng dụng Web
* **Sinh viên thực hiện:** Đặng Quang Hưng
* **Giảng viên hướng dẫn:** Bộ môn Công nghệ Phần mềm
* **Công nghệ phát triển:** Python 3.11, Django Framework 5.2, SQLite Database, Tailwind CSS, Google Gemini 2.5 Flash REST API & Rule-Based Fallback Engine
* **Thời gian thực hiện:** 06 Tuần
* **Tình trạng nghiệm thu:** Hoàn thành 100% các mục tiêu kỹ thuật, 34/34 Unit Tests đạt chuẩn (Pass 100%)

---

## MỤC LỤC BÁO CÁO

1. **Phần I: Tổng quan Đề tài và Mục tiêu Nghiên cứu**
   * 1.1. Bối cảnh và Tính cấp thiết của Đề tài
   * 1.2. Mục tiêu Tổng quát và Phạm vi Ứng dụng
   * 1.3. Kiến trúc Công nghệ Cốt lõi
2. **Phần II: Bảng Tổng kết Tiến độ Dự án (Từ Tuần 1 đến Tuần 6)**
3. **Phần III: Hiện thực Hóa Chi tiết 3 Phân hệ Nòng cốt**
   * 3.1. Phân hệ 1: Bài kiểm tra Đánh giá Trình độ Đầu vào (Placement Test)
   * 3.2. Phân hệ 2: Bài thi Nâng Band Định kỳ (Level-Up Exam)
   * 3.3. Phân hệ 3: Trợ lý AI Gia sư Phân tích Ngữ pháp và Tư vấn Lộ trình (AI Tutor)
4. **Phần IV: Công tác Kiểm thử và Đảm bảo Chất lượng (Quality Assurance)**
   * 4.1. Chiến lược Kiểm thử Tự động
   * 4.2. Bảng Thống kê 34/34 Test Cases
5. **Phần V: Hướng dẫn Triển khai và Kịch bản Vận hành Hệ thống**
   * 5.1. Yêu cầu Môi trường và Cài đặt Thư viện
   * 5.2. Cấu hình Biến Môi trường và Quản trị Cơ sở Dữ liệu
   * 5.3. Khởi tạo Tài khoản Quản trị và Dữ liệu Mẫu
   * 5.4. Kịch bản Báo cáo Trực tiếp trước Hội đồng
6. **Phần VI: Kết luận và Định hướng Phát triển**

---

## PHẦN I: TỔNG QUAN ĐỀ TÀI VÀ MỤC TIÊU NGHIÊN CỨU

### 1.1. Bối cảnh và Tính cấp thiết của Đề tài
Trong kỷ nguyên chuyển đổi số trong giáo dục, việc tự học ngoại ngữ đòi hỏi một nền tảng không chỉ cung cấp tài liệu đơn thuần mà phải có khả năng:
* Đánh giá chính xác trình độ khởi điểm của người học theo khung tham chiếu ngôn ngữ chuẩn quốc tế.
* Cá nhân hóa kho ngữ liệu từ vựng theo đúng năng lực thực tế, tránh gây quá tải hoặc nhàm chán.
* Cung cấp cơ chế kiểm tra định kỳ để thăng hạng trình độ một cách minh bạch, tạo động lực liên tục.
* Đưa công nghệ Trí tuệ Nhân tạo (AI) vào việc giải thích tường tận nguyên nhân sai sót ngữ pháp thay vì chỉ đưa ra đáp án đúng/sai khô khan.

Dự án **English Pro** được nghiên cứu và hiện thực hóa nhằm giải quyết trọn vẹn các bài toán nêu trên, tạo nên một chu trình học tập khép kín và tự động hóa.

### 1.2. Mục tiêu Tổng quát và Phạm vi Ứng dụng
* **Mục tiêu sư phạm:** Xây dựng lộ trình học tập bám sát Khung tham chiếu trình độ ngôn ngữ chung Châu Âu (CEFR) gồm 4 cấp độ nền tảng: A1 (Căn bản), A2 (Sơ cấp), B1 (Trung cấp) và B2 (Trung cao cấp).
* **Mục tiêu kỹ thuật:** Xây dựng hệ thống web chuẩn kiến trúc MVT (Model - View - Template) trên nền tảng Django, thiết kế giao diện ưu tiên thiết bị di động (Mobile-First Design), tối ưu hóa hiệu năng truy vấn cơ sở dữ liệu và tích hợp API Trí tuệ Nhân tạo với cơ chế dự phòng an toàn tuyệt đối.

### 1.3. Kiến trúc Công nghệ Cốt lõi
* **Ngôn ngữ lập trình:** Python phiên bản 3.11.
* **Framework phụ trách Backend:** Django Framework 5.2.
* **Cơ sở dữ liệu:** SQLite Database (hỗ trợ toàn vẹn ràng buộc quan hệ và dữ liệu JSONField).
* **Giao diện người dùng (Frontend):** HTML5, Tailwind CSS, Font Awesome 6.4, Canvas Confetti.
* **Tích hợp Trí tuệ nhân tạo:** Google Gemini 2.5 Flash REST API kết hợp Rule-Based Fallback Engine.
* **Hỗ trợ PWA:** Service Worker và Manifest cho phép cài đặt ứng dụng trên thiết bị di động.

---

## PHẦN II: BẢNG TỔNG KẾT TIẾN ĐỘ DỰ ÁN (TỪ TUẦN 1 ĐẾN TUẦN 6)

| Giai đoạn | Nội dung Công việc Trọng tâm | Kết quả Đạt được | Tình trạng |
| :--- | :--- | :--- | :--- |
| **Tuần 1** | Khảo sát yêu cầu, thiết kế kiến trúc tổng thể cơ sở dữ liệu, khởi tạo dự án Django, xây dựng phân hệ xác thực người dùng (Đăng ký, Đăng nhập, Phân quyền). | Hoàn thành bộ khung User, Category, Vocabulary, UserProfile; thiết lập giao diện Base và Dashboard ban đầu. | Đạt 100% |
| **Tuần 2** | Xây dựng thuật toán Flashcard ghi nhớ ngắt quãng (Spaced Repetition), xây dựng các bài tập thực hành 4 kỹ năng cơ bản (Nghe, Nói, Đọc, Viết) và thiết lập mục tiêu Band điểm IELTS. | Hoàn thiện luồng học Flashcard, lưu vết lịch sử nộp bài của học viên, bộ đếm ngày thi dự kiến. | Đạt 100% |
| **Tuần 3** | Hiện thực hóa phân hệ Đánh giá Trình độ Đầu vào (Placement Test): Thiết kế 15 câu hỏi trắc nghiệm CEFR, thuật toán quy đổi điểm số sang Band điểm A1-B2. | Hoàn thành luồng thi đầu vào, cập nhật tự động trình độ học viên, xây dựng trang hiển thị kết quả và báo cáo tiến độ tuần 3. | Đạt 100% |
| **Tuần 4** | Mở rộng ngân hàng câu hỏi lên 40 câu chuẩn hóa; tối ưu hóa truy vấn cơ sở dữ liệu chống lỗi N+1 Queries; xây dựng cấu trúc bài thi nâng band. | Tạo lệnh quản trị seed_placement_test; kiểm thử truy vấn prefetch_related đạt hiệu năng tối ưu. | Đạt 100% |
| **Tuần 5** | Hoàn thiện Phân hệ Bài thi nâng band (Level-Up Exam): Ngưỡng đậu 80%, đồng hồ đếm ngược 10 phút tự động submit bài, hiệu ứng Confetti chúc mừng thăng hạng. | Triển khai mô hình PRG (Post/Redirect/Get), đồng bộ session active_level, tích hợp nút thi nâng band trên toàn hệ thống. | Đạt 100% |
| **Tuần 6** | Tích hợp Trợ lý AI Gia sư (AI Tutor) qua Google Gemini REST API và Rule-Based Fallback Engine; viết bổ sung Unit Tests đạt 34/34 bài; nghiệm thu tổng thể đồ án. | Đạt 34/34 Tests Passed 100%; endpoint AJAX /api/ai-explain/ hoạt động bền vững; hoàn thiện báo cáo tổng kết đồ án. | Đạt 100% |

---

## PHẦN III: HIỆN THỰC HÓA CHI TIẾT 3 PHÂN HỆ NÒNG CỐT

### 3.1. Phân hệ 1: Bài kiểm tra Đánh giá Trình độ Đầu vào (Placement Test)

#### a) Mục đích và Cơ chế Phân loại
Phân hệ Placement Test đóng vai trò là "cổng vào" của học viên. Khi bắt đầu sử dụng hệ thống, học viên được yêu cầu thực hiện một bài đánh giá toàn diện gồm 15 câu hỏi trắc nghiệm phân bổ đều theo độ khó tăng dần từ A1 đến B2 nhằm xác định chính xác trình độ khởi điểm.

#### b) Thang điểm và Thuật toán Quy đổi CEFR
Thuật toán phân loại cấp độ được xây dựng độc lập trong hàm `calculate_placement_level(score, total)` dựa trên tỷ lệ phần trăm câu đúng:

| Tỷ lệ Đúng (%) | Trình độ Xếp hạng | Tên gọi Chuẩn CEFR | Hướng dẫn Học tập Tương ứng |
| :--- | :---: | :--- | :--- |
| **Dưới 45.0%** | **A1** | Beginner (Căn bản) | Tập trung vào 500 từ vựng cơ bản về đời sống và cấu trúc câu thì hiện tại đơn giản. |
| **45.0% - 64.9%** | **A2** | Elementary (Sơ cấp) | Mở rộng vốn từ vựng miêu tả, du lịch, mua sắm và làm quen thì quá khứ đơn, tương lai. |
| **65.0% - 84.9%** | **B1** | Intermediate (Trung cấp) | Trau dồi câu phức, câu điều kiện, collocations và bắt đầu rèn 4 kỹ năng chuyên sâu. |
| **Từ 85.0% trở lên** | **B2** | Upper Intermediate (Trung cao cấp) | Rèn luyện văn bản học thuật phức tạp, sẵn sàng bước vào luyện thi IELTS 6.5 - 7.5+. |

#### c) Lưu vết và Cá nhân hóa Trải nghiệm
Sau khi bài làm được chấm điểm tự động:
* Bản ghi chi tiết được lưu vào bảng `PlacementTestResult`.
* Trường `UserProfile.assigned_level` và `UserProfile.has_taken_placement_test` được cập nhật trong một giao dịch cơ sở dữ liệu (`transaction.atomic`).
* Biến phiên làm việc `request.session["active_level"]` được gán bằng cấp độ xếp hạng, từ đó toàn bộ kho từ vựng và bài đọc tại Dashboard được tự động lọc theo cấp độ này.

---

### 3.2. Phân hệ 2: Bài thi Nâng Band Định kỳ (Level-Up Exam)

#### a) Quy tắc Thăng hạng và Điều kiện Đạt (Pass Threshold)
Sau thời gian tích lũy từ vựng ở cấp độ hiện tại, học viên có thể chủ động tham gia bài thi nâng band tại endpoint `/level-up-exam/`. Quy tắc nâng band tuân theo trật tự tịnh tiến một chiều:
* Học viên đang ở cấp độ **A1** thi bài thi nâng band lên **A2**.
* Học viên đang ở cấp độ **A2** thi bài thi nâng band lên **B1**.
* Học viên đang ở cấp độ **B1** thi bài thi nâng band lên **B2**.
* Nếu học viên đã ở cấp độ **B2** (cấp độ cao nhất hiện tại), hệ thống hiển thị thông báo danh dự đạt chuẩn tối đa và không bắt buộc thi nâng band.

**Điều kiện Đạt chuẩn:** Học viên bắt buộc phải đạt độ chính xác từ **80.0% trở lên** (tối thiểu 8/10 câu hỏi thuộc trình độ mục tiêu) để được hệ thống công nhận thăng hạng.

#### b) Thiết kế Mô hình Cơ sở Dữ liệu (`LevelUpExamResult`)
Mô hình `LevelUpExamResult` trong tệp `core/models.py` lưu trữ chi tiết:
* `user`: Khóa ngoại trỏ đến tài khoản người dùng (`models.ForeignKey(User, on_delete=models.CASCADE)`).
* `from_level`: Cấp độ xuất phát của học viên tại thời điểm thi.
* `target_level`: Cấp độ mục tiêu mà học viên đang thử sức.
* `score`: Số câu trả lời chính xác.
* `total_questions`: Tổng số câu hỏi của đề thi.
* `is_passed`: Giá trị kiểu Boolean ghi nhận kết quả Đậu (`True`) hay Chưa đạt (`False`).
* `answers_detail`: Trường kiểu JSON (`models.JSONField`) lưu vết chi tiết từng câu hỏi, mã lựa chọn, văn bản lựa chọn của học viên và đáp án đúng.
* `completed_at`: Thời gian hoàn thành bài thi (`auto_now_add=True`).

#### c) Tối ưu hóa Truy vấn và Xử lý Luồng Dữ liệu
* **Triệt tiêu lỗi N+1 Queries:** Đề thi chỉ lấy các câu hỏi thuộc cấp độ mục tiêu `target_level` thông qua câu lệnh:
  `PlacementQuestion.objects.filter(level=target_level).prefetch_related("choices").order_by("order", "id")`.
  Kỹ thuật `prefetch_related` tải trước toàn bộ các lựa chọn đáp án tương ứng vào bộ nhớ đệm, giảm thiểu số lượng truy vấn cơ sở dữ liệu xuống mức tối đa.
* **Mô hình Post/Redirect/Get (PRG):** Khi học viên nộp bài qua phương thức HTTP POST, hệ thống xử lý chấm điểm, cập nhật `UserProfile.assigned_level = target_level` nếu đậu, sau đó chuyển hướng bằng mã trạng thái HTTP 302 sang `/level-up-exam/result/<result_id>/`. Việc này loại bỏ hoàn toàn hiện tượng học viên bấm F5 dẫn đến việc ghi đè kết quả bài thi nhiều lần.

#### d) Trải nghiệm Giao diện và Bộ đếm Thời gian Tự động Submit
* **Đồng hồ đếm ngược 10 phút (Sticky Countdown Timer):** Được thiết lập trên thanh điều hướng cố định phía trên màn hình bằng JavaScript thuần. Khi thời gian còn dưới 60 giây, bộ đếm chuyển sang chế độ cảnh báo màu đỏ. **Khi đồng hồ chạm mốc 00:00, kịch bản JavaScript tự động vô hiệu hóa nút bấm và thực thi lệnh gửi form nộp bài ngay lập tức.**
* **Hiệu ứng Vinh danh Thăng hạng:** Tại trang kết quả, nếu `is_passed == True`, hệ thống kích hoạt hiệu ứng pháo giấy toàn màn hình (Canvas Confetti), hiển thị huy hiệu CEFR mới và cung cấp nút hành động dẫn thẳng tới kho từ vựng của cấp độ vừa mở khóa (`/vocab/?level={{ target_level }}`).

---

### 3.3. Phân hệ 3: Trợ lý AI Gia sư Phân tích Ngữ pháp và Tư vấn Lộ trình (AI Tutor)

#### a) Kiến trúc Hai Tầng và Cơ chế Dự phòng An toàn Tuyệt đối (Zero-Crash Fallback)
Một trong những yêu cầu nghiêm ngặt nhất của đồ án là ứng dụng AI không bao giờ được phép làm gián đoạn trải nghiệm người dùng hoặc phát sinh lỗi máy chủ 500 khi mất kết nối mạng hay hết hạn ngạch API. Dịch vụ AI tại tệp `core/ai_service.py` được thiết kế theo cấu trúc hai tầng độc lập:

* **Tầng 1 – Google Gemini 2.5 Flash REST API:**
  * Kết nối trực tiếp qua thư viện `requests` tới endpoint của Google Generative Language: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`.
  * Khóa xác thực được nạp tự động từ biến môi trường `GEMINI_API_KEY`.
  * **Cấu hình Timeout nghiêm ngặt:** Đặt ngưỡng thời gian chờ là **8.0 giây**. Nếu quá 8 giây mà máy chủ Google chưa phản hồi, tiến trình gọi API sẽ tự động ngắt kết nối an toàn để chuyển sang Tầng 2.
* **Tầng 2 – Rule-Based Fallback Engine (Đảm bảo sẵn sàng 100%):**
  * Tự động kích hoạt khi: Chưa cấu hình API Key, thiết bị mất mạng, gặp lỗi HTTP 404/429 (Quota Exceeded), hoặc vượt quá thời gian chờ 8 giây.
  * Động cơ phân tích hoạt động dựa trên cơ sở tri thức 12+ nhóm quy tắc ngữ pháp CEFR trọng tâm, đối chiếu trực tiếp giữa câu hỏi, phương án học viên chọn và đáp án đúng.
  * Phản hồi trả về trong thời gian dưới **0.05 giây** mà không phụ thuộc vào bất kỳ dịch vụ bên ngoài nào.

#### b) Cấu trúc Bốn Thành phần của Phản hồi Giải thích Ngữ pháp
Bất kể phản hồi được sinh ra từ Gemini API hay Fallback Engine, nội dung giải thích gửi đến học viên luôn đảm bảo cấu trúc sư phạm 4 phần chuẩn mực:
1. **Chủ điểm kiến thức:** Nêu rõ dạng ngữ pháp câu hỏi đang kiểm tra và cấp độ CEFR tương ứng (ví dụ: Câu điều kiện hỗn hợp, Đảo ngữ phủ định, Thể giả định, Thì Hiện tại hoàn thành).
2. **Lý do đáp án đúng:** Phân tích nguyên tắc ngữ pháp và ngữ nghĩa giải thích tại sao đáp án chính xác phải được chọn.
3. **Phân tích lựa chọn của học viên:** Chỉ rõ phương án học viên đã chọn vi phạm quy tắc ngữ pháp nào (sai thì, sai vị trí trạng từ, sai dạng động từ hay nhầm lẫn loại từ).
4. **Mẹo ghi nhớ nhanh:** Đúc kết quy tắc ngắn gọn giúp học viên không tái phạm lỗi sai tương tự.

#### c) Endpoint AJAX `/api/ai-explain/` và Tương tác Không Tải lại Trang
* Endpoint tiếp nhận yêu cầu qua phương thức HTTP POST, tiếp nhận các tham số: `question_id`, `user_choice_id`, `user_answer`, `correct_answer`, `question_text`, `level`.
* Tại bảng xem lại câu hỏi trong trang kết quả bài thi, nút bấm *"AI Giải thích"* được bố trí trực quan tại các câu học viên trả lời sai.
* Khi học viên nhấn nút, JavaScript thực hiện lệnh `fetch` bất đồng bộ kèm mã bảo mật CSRF Token. Giao diện hiển thị biểu tượng tải dữ liệu mượt mà và in lời giải thích chi tiết ngay bên dưới câu hỏi mà không cần làm mới lại trang web.

---

## PHẦN IV: CÔNG TÁC KIỂM THỬ VÀ ĐẢM BẢO CHẤT LƯỢNG (QUALITY ASSURANCE)

### 4.1. Chiến lược Kiểm thử Tự động
Dự án áp dụng phương pháp kiểm thử tự động toàn diện thông qua Django Test Framework và Pytest. Toàn bộ các luồng nghiệp vụ từ tầng cơ sở dữ liệu, xử lý logic views, xác thực bảo mật, đến các tình huống ngoại lệ của dịch vụ AI đều được xây dựng các kịch bản kiểm thử độc lập.

### 4.2. Bảng Thống kê 34/34 Test Cases Đạt Chuẩn (100% Passed)

| Nhóm Kiểm thử | Tên Test Case | Mục đích Kiểm tra | Kết quả |
| :--- | :--- | :--- | :---: |
| **Views Integration** | `test_index_returns_200` | Kiểm tra trang chủ trả về HTTP 200 | Đạt (Pass) |
| | `test_index_uses_correct_template` | Kiểm tra render đúng template `core/index.html` | Đạt (Pass) |
| | `test_index_contains_flashcards` | Kiểm tra context chứa danh sách thẻ Flashcard | Đạt (Pass) |
| | `test_mark_mastered_redirects` | Kiểm tra chuyển hướng sau khi thuộc từ vựng | Đạt (Pass) |
| | `test_mark_mastered_updates_db` | Kiểm tra cập nhật trạng thái `is_mastered` trong DB | Đạt (Pass) |
| | `test_mark_mastered_404_invalid` | Kiểm tra xử lý lỗi 404 khi ID không tồn tại | Đạt (Pass) |
| **Model Validation** | `test_category_cascade_delete` | Kiểm tra xóa Category kéo theo Vocabulary liên quan | Đạt (Pass) |
| | `test_flashcard_default_status` | Kiểm tra thẻ Flashcard mới mặc định chưa thuộc | Đạt (Pass) |
| | `test_flashcard_str_format` | Kiểm tra định dạng chuỗi đại diện của Flashcard | Đạt (Pass) |
| | `test_vocabulary_str_returns_word` | Kiểm tra `__str__` của Vocabulary trả về đúng từ vựng | Đạt (Pass) |
| | `test_vocabulary_word_type` | Kiểm tra tính hợp lệ của danh sách từ loại | Đạt (Pass) |
| **Multi-Level Logic** | `test_api_flashcards_endpoint` | Kiểm tra API danh sách Flashcard theo cấp độ | Đạt (Pass) |
| | `test_api_lessons_endpoint` | Kiểm tra API dữ liệu bài học | Đạt (Pass) |
| | `test_dashboard_filters_by_level` | Kiểm tra Dashboard lọc đúng dữ liệu theo Band điểm | Đạt (Pass) |
| | `test_index_filters_by_level` | Kiểm tra Flashcard tại trang chủ lọc đúng cấp độ | Đạt (Pass) |
| | `test_update_goals_endpoint` | Kiểm tra cập nhật mục tiêu Band điểm 4 kỹ năng | Đạt (Pass) |
| **Placement Test** | `test_level_calculation_logic` | Kiểm tra thuật toán quy đổi điểm: A1, A2, B1, B2 | Đạt (Pass) |
| | `test_placement_test_get_view` | Kiểm tra hiển thị form thi đầu vào HTTP 200 | Đạt (Pass) |
| | `test_placement_test_post_scoring` | Kiểm tra chấm điểm, lưu DB và cập nhật UserProfile | Đạt (Pass) |
| | `test_placement_result_view` | Kiểm tra hiển thị đúng trang kết quả bài test đầu vào | Đạt (Pass) |
| **Level-Up Exam** | `test_get_next_level_logic` | Kiểm tra quy tắc: A1->A2, A2->B1, B1->B2, B2->None | Đạt (Pass) |
| | `test_levelup_requires_login` | Chặn học viên chưa đăng nhập (Redirect login) | Đạt (Pass) |
| | `test_levelup_get_for_a1_user` | Kiểm tra đề thi nâng band A1->A2 chỉ chứa câu hỏi A2 | Đạt (Pass) |
| | `test_levelup_get_when_already_b2` | Kiểm tra thông báo khi học viên đã đạt cấp độ tối đa | Đạt (Pass) |
| | `test_levelup_post_pass_logic` | Đạt >= 80%: Thăng hạng, cập nhật profile và session | Đạt (Pass) |
| | `test_levelup_post_fail_logic` | Đạt < 80%: Giữ nguyên cấp độ ban đầu | Đạt (Pass) |
| | `test_levelup_result_view_access` | Hiển thị chi tiết điểm số và đáp án bài thi nâng band | Đạt (Pass) |
| | `test_levelup_unauthorized_user` | Chặn học viên khác truy cập kết quả của người khác | Đạt (Pass) |
| **AI Tutor & Service** | `test_ai_fallback_explanation` | Kiểm tra Fallback Engine giải thích câu sai chuẩn xác | Đạt (Pass) |
| | `test_ai_fallback_roadmap` | Kiểm tra Fallback Engine sinh nhận xét lộ trình học | Đạt (Pass) |
| | `test_api_ai_explain_json` | Kiểm tra endpoint AJAX nhận JSON body trả về 200 OK | Đạt (Pass) |
| | `test_api_ai_explain_form_data` | Kiểm tra endpoint AJAX nhận FormData trả về 200 OK | Đạt (Pass) |
| | `test_api_ai_explain_zero_crash` | Dữ liệu thiếu/rỗng không gây lỗi 500 (Zero-Crash) | Đạt (Pass) |
| | `test_gemini_mock_integration` | Kiểm tra kết nối Gemini thành công trả về `gemini` | Đạt (Pass) |

---

## PHẦN V: HƯỚNG DẪN TRIỂN KHAI VÀ KỊCH BẢN VẬN HÀNH HỆ THỐNG

### 5.1. Yêu cầu Môi trường và Cài đặt Thư viện
* Hệ điều hành: Windows 10/11, macOS hoặc Linux.
* Phiên bản Python: Python 3.10 trở lên (khuyến nghị Python 3.11).
* Quản lý gói phụ thuộc qua tệp `requirements.txt`:
  ```text
  Django>=5.0,<6.0
  gunicorn
  requests>=2.28.0
  python-dotenv>=1.0.0
  ```

**Các bước cài đặt môi trường:**
1. Khởi tạo và kích hoạt môi trường ảo (Virtual Environment):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Cài đặt các thư viện phụ thuộc:
   ```powershell
   pip install -r requirements.txt
   ```

### 5.2. Cấu hình Biến Môi trường và Cơ sở Dữ liệu
1. Tạo tệp `.env` tại thư mục gốc của dự án với nội dung cấu hình API:
   ```env
   GEMINI_API_KEY=AIzaSyA8v2vHKX0qVBnm8bjeYbg_bofzLRv1h2o
   GEMINI_MODEL=gemini-2.5-flash
   ```
   *(Lưu ý: Nếu không cấu hình khóa `GEMINI_API_KEY`, hệ thống vẫn tự động chuyển đổi sang Rule-Based Fallback Engine an toàn 100%).*
2. Thực thi di chuyển lược đồ cơ sở dữ liệu (Database Migrations):
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

### 5.3. Khởi tạo Tài khoản Quản trị và Dữ liệu Mẫu
1. Khởi tạo tài khoản Quản trị viên (Superuser / Admin):
   ```powershell
   python manage.py createsuperuser
   ```
   *(Nhập các thông tin: username, email và password theo yêu cầu của hệ thống).*
2. Nạp ngân hàng dữ liệu mẫu gồm 40 câu hỏi trắc nghiệm chuẩn CEFR:
   ```powershell
   python manage.py seed_placement_test
   ```
3. Chạy toàn bộ kiểm thử hệ thống để nghiệm thu:
   ```powershell
   python manage.py test core
   ```
4. Khởi động máy chủ phát triển (Development Server):
   ```powershell
   python manage.py runserver
   ```
   Truy cập nền tảng tại địa chỉ cục bộ: `http://127.0.0.1:8000/`.

### 5.4. Kịch bản Báo cáo Trực tiếp trước Hội đồng và Giảng viên
Để buổi bảo vệ đồ án diễn ra thuyết phục và mạch lạc nhất, sinh viên thực hiện thao tác demo theo 4 bước tuần tự sau:

* **Bước 1: Trình diễn Đánh giá Đầu vào (Placement Test):**
  * Đăng nhập tài khoản học viên mới, chọn mục *"Test đầu vào"* trên thanh điều hướng.
  * Hoàn thành bài trắc nghiệm 15 câu, nhấn nộp bài.
  * Tại trang kết quả, chỉ rõ khung *"Nhận xét tổng quan từ AI Gia sư"* phân tích điểm mạnh, điểm yếu và xếp học viên vào trình độ tương ứng (ví dụ: Band A1).
* **Bước 2: Trình diễn Bài thi Nâng Band (Level-Up Exam):**
  * Nhấn nút *"Thi nâng band"* tại thanh Navbar hoặc banner trên trang Dashboard.
  * Giới thiệu bộ câu hỏi mục tiêu thuộc cấp độ A2 và chỉ rõ **Đồng hồ đếm ngược 10 phút** ở thanh sticky phía trên.
  * Trình bày cơ chế bảo vệ: Khi hết thời gian làm bài, hệ thống sẽ tự động khóa bài và nộp dữ liệu.
* **Bước 3: Trình diễn Hiệu ứng Vinh danh và Thăng hạng Tự động:**
  * Chọn các đáp án đạt tỷ lệ trên 80% (Pass), nhấn hoàn thành.
  * Quan sát hiệu ứng pháo giấy Confetti chúc mừng thăng hạng thành công lên Band A2.
  * Cho Giảng viên quan sát cấp độ trên thanh điều hướng và trong cơ sở dữ liệu đã tự động chuyển đổi từ A1 sang A2.
* **Bước 4: Trình diễn Trợ lý AI Phân tích Ngữ pháp Câu sai (Điểm nhấn đồ án):**
  * Mở phần chi tiết bài làm tại một câu hỏi học viên làm sai, nhấn nút *"AI Giải thích"*.
  * Quan sát hiệu ứng xoay bất đồng bộ (không tải lại trang).
  * Khung phân tích hiện ra với 4 phần rõ ràng: Chủ điểm kiến thức, Vì sao đáp án đúng là chính xác, Vì sao lựa chọn của học viên sai và Mẹo ghi nhớ.
  * **Giải thích với Giảng viên về cơ chế Fallback:** Chứng minh rằng ngay cả khi máy tính bị ngắt kết nối mạng hoặc API key bị nghẽn, tính năng AI vẫn giải thích mượt mà 100% nhờ động cơ dự phòng, không bao giờ xảy ra lỗi gián đoạn 500.

---

## PHẦN VI: KẾT LUẬN VÀ ĐỊNH HƯỚNG PHÁT TRIỂN

### 6.1. Kết luận Đồ án
Sau 06 tuần triển khai nghiêm túc, dự án **English Pro** đã hoàn thành xuất sắc toàn bộ các mục tiêu đặt ra:
* Xây dựng thành công nền tảng học tiếng Anh cá nhân hóa theo chuẩn CEFR quốc tế.
* Hoàn thiện chu trình khép kín: Đánh giá đầu vào -> Lộ trình từ vựng -> Thi nâng band định kỳ.
* Ứng dụng thành công Trí tuệ Nhân tạo vào công tác sư phạm với cơ chế bền vững, an toàn tuyệt đối.
* Đạt độ bao phủ kiểm thử cao với 34/34 bài test vượt qua, mã nguồn tuân thủ nguyên lý thiết kế phần mềm sạch (Clean Architecture).

### 6.2. Hướng Phát triển Tương lai
* **Mở rộng Đánh giá Thích ứng (Computerized Adaptive Testing - CAT):** Ứng dụng lý thuyết khảo thí hiện đại (Item Response Theory) để tự động điều chỉnh độ khó câu hỏi tiếp theo dựa trên câu trả lời trước đó của học viên.
* **Tích hợp Nhận diện Phát âm AI cho Kỹ năng Nói (Speaking AI Tutor):** Ứng dụng công nghệ Speech-to-Text để chấm điểm phát âm, trọng âm và độ lưu loát theo thang điểm IELTS.
* **Cấp Chứng chỉ Điện tử (Digital Certificate):** Tự động khởi tạo và cấp chứng chỉ trực tuyến có mã QR xác thực khi học viên hoàn thành xuất sắc bài thi nâng band cấp độ B2.
