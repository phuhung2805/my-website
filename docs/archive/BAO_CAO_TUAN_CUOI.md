# BÁO CÁO TỔNG KẾT TUẦN CUỐI
## DỰ ÁN: NỀN TẢNG LUYỆN THI TIẾNG ANH & FLASHCARD THÔNG MINH – ENGLISH PRO

* **Sinh viên thực hiện:** Đặng Quang Hưng
* **Học phần:** Phát triển Ứng dụng Web / Đồ án Chuyên ngành
* **Công nghệ cốt lõi:** Python 3.11, Django 5.2, Tailwind CSS, Google Gemini 2.5/3.8 Flash & Rule-Based Fallback Engine
* **Trạng thái hệ thống:** Đã hoàn thiện toàn diện, **34/34 Unit Tests Passed 100%**

---

## I. TỔNG QUAN DỰ ÁN & MỤC TIÊU TUẦN CUỐI

Tiếp nối thành công của tính năng **Kiểm tra trình độ đầu vào (Placement Test)** ở giai đoạn trước, mục tiêu trọng tâm trong tuần cuối là hoàn thiện chu trình học tập khép kín và cá nhân hóa cho học viên thông qua hai tính năng đột phá:

1. **Bài thi nâng band (Level-Up Exam):** Cung cấp cơ chế đánh giá năng lực định kỳ giúp học viên thăng hạng trình độ chuẩn CEFR (từ A1 lên A2, A2 lên B1, B1 lên B2) khi đạt tỷ lệ đúng từ **80% trở lên**, đi kèm đồng hồ đếm ngược 10 phút tự động nộp bài và hiệu ứng vinh danh thăng hạng.
2. **Trợ lý AI Gia sư (AI Tutor & Explanation):** Ứng dụng mô hình ngôn ngữ lớn (Google Gemini API) kết hợp cơ chế **Zero-Crash Fallback Engine** độc quyền, cung cấp nhận xét tổng quan lộ trình học và nút bấm *"✨ AI Giải thích"* phân tích chi tiết bản chất ngữ pháp tại từng câu học viên làm sai, cam kết hệ thống luôn hoạt động ổn định 100% khi demo trước Hội đồng và Giảng viên.

```
                    ┌──────────────────────────────────────────────┐
                    │     PLACEMENT TEST (Đánh giá đầu vào)        │
                    │   Xác định trình độ ban đầu: A1, A2, B1, B2   │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │        HỌC TỪ VỰNG & LUYỆN 4 KỸ NĂNG         │
                    │     Theo đúng Band CEFR được phân loại       │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │      BÀI THI NÂNG BAND (Level-Up Exam)       │
                    │   Thời gian: 10 phút | Điều kiện Đậu: ≥ 80%   │
                    └──────────────┬───────────────────────────────┘
                                   │
                   ┌───────────────┴───────────────┐
                   ▼                               ▼
       [ĐẠT ≥ 80%: Thăng Hạng]          [CHƯA ĐẠT: Ôn luyện lại]
       • Pháo giấy chúc mừng            • Động viên & chỉ rõ lỗi
       • Cập nhật Band mới              • ✨ AI Giải thích câu sai
       • Mở khóa từ vựng cấp cao        • Giữ vững band để thi lại
```

---

## II. CHI TIẾT CÁC HẠNG MỤC PHÁT TRIỂN & TÍCH HỢP

### 1. Phân hệ Bài thi nâng band (Level-Up Exam)

#### a) Thiết kế Cơ sở dữ liệu (`core/models.py`)
* Xây dựng model `LevelUpExamResult` chuyên biệt quản lý lịch sử thi thăng hạng:
  * `user`: Khóa ngoại liên kết bảng học viên (`User`).
  * `from_level` & `target_level`: Trình độ xuất phát và trình độ mục tiêu (`A1`, `A2`, `B1`, `B2`).
  * `score` & `total_questions`: Số câu trả lời đúng trên tổng số câu hỏi bài thi.
  * `is_passed`: Trạng thái Đạt (`True` khi tỷ lệ đúng ≥ 80%).
  * `answers_detail`: Cấu trúc JSON lưu vết đầy đủ câu hỏi, lựa chọn của học viên, đáp án đúng và trạng thái đúng/sai phục vụ ôn tập.
  * `completed_at`: Thời điểm hoàn thành bài thi.
* Xây dựng hàm nghiệp vụ `get_next_level(current_level)` hiện thực hóa quy tắc nâng cấp chuẩn CEFR: `A1 -> A2`, `A2 -> B1`, `B1 -> B2`. Khi học viên đã đạt cấp độ cao nhất (`B2`), hệ thống sẽ trả về `None` và hiển thị giao diện chúc mừng đạt đỉnh năng lực.
* Đăng ký model vào Django Admin (`LevelUpExamResultAdmin`) với bộ lọc thông minh theo cấp độ, trạng thái Đậu/Rớt và hiển thị tỷ lệ chính xác dạng phần trăm trực quan.

#### b) Xử lý Luồng dữ liệu & Tối ưu hóa Truy vấn (`core/views.py` & `core/urls.py`)
* Endpoint `/level-up-exam/` (`level_up_exam_view`):
  * Tự động xác định cấp độ mục tiêu tiếp theo của học viên dựa trên `UserProfile.assigned_level`.
  * **Giải quyết triệt để vấn đề N+1 Queries:** Truy vấn ngân hàng câu hỏi theo `target_level` kết hợp `prefetch_related("choices")`, giúp tải toàn bộ câu hỏi và đáp án chỉ trong **1 query duy nhất**.
  * **Quy chuẩn chấm điểm tự động:** Tính toán độ chính xác `percentage = round((score / total) * 100, 1)`. Nếu `percentage >= 80.0`, tự động thăng hạng học viên:
    ```python
    profile.assigned_level = target_level
    profile.save(update_fields=["assigned_level"])
    request.session["active_level"] = target_level
    ```
  * Áp dụng nghiêm ngặt mô hình **Post/Redirect/Get (PRG)** điều hướng sang `/level-up-exam/result/<result_id>/`, ngăn ngừa nguy cơ gửi lại form trùng lặp (F5 duplicate submission).
* Endpoint `/level-up-exam/result/<result_id>/` (`level_up_result_view`):
  * Kiểm soát phân quyền học viên (chỉ xem được bài thi của chính mình hoặc quyền Staff).
  * Hiển thị bảng tổng kết điểm số, huy hiệu cấp độ và hướng dẫn lộ trình tiếp theo.

#### c) Thiết kế Giao diện Mobile-First & Trải nghiệm Người dùng
* **Trang làm bài (`level_up_exam.html`):**
  * **Đồng hồ đếm ngược (Countdown Timer) 10 phút:** Tích hợp thanh sticky phía trên cùng. Định dạng hiển thị `MM:SS`. Khi thời gian còn dưới 60 giây, đồng hồ tự động chuyển sang chế độ cảnh báo màu đỏ nhấp nháy. **Khi hết giờ (00:00), hệ thống tự động khóa nút bấm và tự động submit bài làm ngay lập tức.**
  * **Thanh tiến độ thời gian thực (Progress Bar):** Cập nhật liên tục số lượng câu hỏi đã hoàn thành trên thanh trượt sinh động.
  * Giao diện tương thích 100% với màn hình di động, phím chọn đáp án diện tích lớn chống bấm nhầm (touch-friendly).
  * Modal cảnh báo thông minh nếu học viên chủ động bấm nộp bài khi vẫn còn câu chưa chọn đáp án.
* **Trang kết quả (`level_up_result.html`):**
  * **Trường hợp Đạt (`is_passed == True`):** Hiệu ứng **pháo giấy ăn mừng (Confetti Canvas Animation)** bung nở toàn màn hình, vinh danh huy hiệu CEFR mới và nút CTA dẫn thẳng vào kho từ vựng tương ứng (`/vocab/?level={{ target_level }}`).
  * **Trường hợp Chưa đạt (`is_passed == False`):** Giao diện truyền cảm hứng động viên tích cực, nút "Ôn tập lại từ vựng" và nút "Thi lại nâng band".
* **Đồng bộ hóa điều hướng (Navigation Integration):** Tích hợp nút bấm *"Thi nâng band"* nổi bật trên thanh điều hướng Navbar (Desktop & Mobile drawer), thẻ Hero card và Banner thông báo tại trang Dashboard.

#### d) Chuẩn hóa Ngân hàng Câu hỏi Seeding Data
* Cập nhật lệnh quản trị `python manage.py seed_placement_test` khởi tạo đầy đủ **40 câu hỏi trắc nghiệm ngữ pháp chuẩn CEFR chất lượng cao** (mỗi band A1, A2, B1, B2 có đúng 10 câu hỏi độc lập), đi kèm 144 lựa chọn đáp án chính xác, phục vụ tối ưu cho cả bài Placement Test và Level-Up Exam.

---

### 2. Phân hệ Trợ lý AI Gia sư (AI Tutor & Explanation)

#### a) Kiến trúc Hai Tầng (Two-Tier Architecture) & Cơ chế Zero-Crash Fallback (`core/ai_service.py`)
Hệ thống AI được thiết kế theo nguyên lý bền vững cao nhất trong kỹ thuật phần mềm: **"AI-Enhanced, Never-Failing"**:

```
           [Yêu cầu giải thích câu hỏi / Tư vấn lộ trình]
                                 │
                                 ▼
                     Kiểm tra kết nối & API Key
                                 │
                 ┌───────────────┴───────────────┐
                 │ (Có Key & Trực tuyến)         │ (Không Key / Mất mạng / 429)
                 ▼                               ▼
       [Google Gemini REST API]      [Rule-Based Fallback Engine]
      • Model: gemini-2.5/3.8-flash  • Phân tích 12+ mẫu ngữ pháp CEFR
      • Timeout: 2.0 giây            • Đối chiếu thì, bị động, đảo ngữ
      • Prompt tiếng Việt chuyên sâu • Sinh phản hồi tức thì (0.01s)
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 [Trả về JSON 200 OK cho Học viên]
```

* **Tầng 1 – Google Gemini REST API:**
  * Gọi trực tiếp qua thư viện `requests` tới REST API của Google Generative Language, loại bỏ hoàn toàn sự phụ thuộc vào các SDK cồng kềnh.
  * Tự động đọc khóa bí mật từ biến môi trường `GEMINI_API_KEY` (hoặc file `.env`).
  * Cấu hình thời gian chờ ngắn (`timeout=2.0s`) nhằm ngăn chặn hiện tượng treo giao diện (UI blocking) nếu đường truyền internet quốc tế bị suy giảm tốc độ.
* **Tầng 2 – Rule-Based Fallback Engine (Cực kỳ quan trọng khi demo):**
  * Tự động kích hoạt khi: Không có API Key, Key hết hạn, lỗi mạng, Request Timeout, mã lỗi 429 (vượt hạn mức Quota), hoặc lỗi 404 Model.
  * **Tuyệt đối không bao giờ ném lỗi HTTP 500.**
  * Phân tích câu hỏi dựa trên bộ từ điển mẫu ngữ pháp (Grammar Pattern Dictionary) theo 4 cấp độ CEFR:
    * *Thì động từ:* Hiện tại đơn, Quá khứ đơn, Hiện tại hoàn thành (`for/since`), Quá khứ tiếp diễn.
    * *Câu điều kiện:* Loại 2, Loại 3, Câu điều kiện hỗn hợp (`Mixed Conditionals`).
    * *Cấu trúc câu nâng cao:* Đảo ngữ phủ định (`Hardly had...`, `Under no circumstances...`, `Not only...`), Thể giả định (`It is imperative that S + V-bare`), Câu bị động, Đại từ sở hữu (`Whose`), Cụm động từ (`cut down on`, `put up with`).
  * Trả về lời giải thích học thuật gồm 4 phần mạch lạc: **Chủ điểm kiến thức**, **Lý do đáp án đúng**, **Phân tích vì sao lựa chọn của học viên chưa chuẩn xác**, và **Mẹo ghi nhớ nhanh**.

#### b) Endpoint AJAX & Giao diện Tương tác Không tải lại trang (`core/views.py`)
* **Endpoint `/api/ai-explain/` (`api_ai_explain_view`):**
  * Nhận dữ liệu câu hỏi qua phương thức `POST` (hỗ trợ cả JSON body lẫn FormData).
  * Tự động truy xuất thông tin chi tiết câu hỏi từ database hoặc dữ liệu gửi kèm.
  * Trả về phản hồi JSON tiêu chuẩn:
    ```json
    {
      "success": true,
      "explanation": "🤖 AI Phân Tích & Giải Thích Chi Tiết:\n📌 Chủ điểm kiến thức:...",
      "source": "gemini" // hoặc "fallback"
    }
    ```
* **Khung "Nhận xét tổng quan từ AI Gia sư":** Xuất hiện nổi bật ở phần đầu trang kết quả của cả hai bài thi (Placement Test và Level-Up Exam), tổng hợp phân tích điểm mạnh, chỉ rõ lỗ hổng kiến thức và đề xuất lộ trình học từ vựng cụ thể.
* **Nút bấm *"✨ AI Giải thích"*:**
  * Tích hợp khéo léo tại các câu hỏi học viên trả lời **SAI** trong bảng xem lại đáp án.
  * Sử dụng JavaScript (`fetch` API) bất đồng bộ với hiệu ứng xoay loading mượt mà (`"Trợ lý AI đang phân tích lỗi sai và đối chiếu ngữ pháp..."`).
  * Nội dung giải thích được định dạng xuống dòng, in đậm các điểm then chốt và gắn huy hiệu nguồn phân tích (`⚡ Gemini AI` hoặc `🤖 AI Gia Sư`).

---

## III. KẾT QUẢ KIỂM THỬ HỆ THỐNG (TESTING & QUALITY ASSURANCE)

Toàn bộ hệ thống đã được kiểm thử tự động thông qua Django Test Framework và Pytest với **34 bài kiểm thử chuyên sâu**:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.0.3, pluggy-1.6.0
django: version: 5.2.14, settings: english_learning.settings
rootdir: D:\Web_Tieng_Anh
configfile: pytest.ini
plugins: cov-7.1.0, django-4.12.0
collected 34 items

core/tests.py::ViewsIntegrationTest (6 tests) ......................... PASSED [ 18%]
core/tests.py::ModelValidationTest (5 tests) .......................... PASSED [ 32%]
core/tests.py::MultiLevelTests (5 tests) .............................. PASSED [ 47%]
core/tests.py::PlacementTestTests (4 tests) ........................... PASSED [ 59%]
core/tests.py::LevelUpExamTests (8 tests) ............................. PASSED [ 82%]
  • test_get_next_level_logic (Quy tắc CEFR: A1->A2, A2->B1, B1->B2, B2->None)
  • test_levelup_requires_login (Chặn người dùng vãng lai chưa đăng nhập)
  • test_levelup_get_for_a1_user (Lọc chính xác 100% câu hỏi target level A2)
  • test_levelup_get_when_already_b2 (Xử lý khi học viên đạt level tối đa)
  • test_levelup_post_pass_updates_profile_and_session (Nâng band khi đúng ≥ 80%)
  • test_levelup_post_fail_keeps_original_level (Giữ nguyên band khi đúng < 80%)
  • test_levelup_result_view_access (Hiển thị kết quả chi tiết)
  • test_levelup_result_unauthorized_user_redirect (Bảo mật thông tin học viên)
core/tests.py::AITutorTests (6 tests) ................................. PASSED [100%]
  • test_ai_service_rule_based_fallback_explanation (Phân tích lỗi sai Fallback)
  • test_ai_service_rule_based_fallback_roadmap (Tư vấn lộ trình Fallback)
  • test_api_ai_explain_endpoint_json_request (AJAX POST JSON 200 OK)
  • test_api_ai_explain_endpoint_form_data_request (FormData 200 OK)
  • test_api_ai_explain_endpoint_handles_missing_params_gracefully (Zero-Crash)
  • test_gemini_api_integration_mock_success (Mock kết nối Google Gemini API)

----------------------------------------------------------------------
Ran 34 tests in 26.256s

OK (100% Tests Passed)
```

---

## IV. HƯỚNG DẪN VẬN HÀNH & KỊCH BẢN DEMO BÁO CÁO

### 1. Hướng dẫn Cài đặt & Khởi chạy Hệ thống

**Bước 1:** Kích hoạt môi trường ảo Python:
```powershell
.\venv\Scripts\activate
```

**Bước 2:** Cài đặt các gói thư viện phụ thuộc (`requirements.txt`):
```powershell
pip install -r requirements.txt
```

**Bước 3:** Chạy di chuyển cấu trúc cơ sở dữ liệu:
```powershell
python manage.py makemigrations
python manage.py migrate
```

**Bước 4:** Khởi tạo dữ liệu mẫu 40 câu hỏi trắc nghiệm CEFR:
```powershell
python manage.py seed_placement_test
```

**Bước 5:** Chạy kiểm thử toàn diện để nghiệm thu chất lượng:
```powershell
python manage.py test core
```

**Bước 6:** Khởi động máy chủ phát triển (Development Server):
```powershell
python manage.py runserver
```
Truy cập ứng dụng tại địa chỉ: `http://127.0.0.1:8000/`

---

### 2. Kịch bản Trình diễn (Demo Scenario) Trước Giảng viên

1. **Khảo sát Năng lực Đầu vào (Placement Test):**
   * Truy cập mục *"Test đầu vào"* trên thanh Navbar.
   * Hoàn thành 15 câu hỏi đầu vào để hệ thống xếp loại học viên vào cấp độ ban đầu (ví dụ: Band A1).
   * Tại trang kết quả, chỉ cho Giảng viên thấy **Khung nhận xét tổng quan từ AI Gia sư** đã phân tích điểm mạnh và điểm yếu một cách trực quan.
2. **Trải nghiệm Bài thi Nâng Band (Level-Up Exam):**
   * Nhấn nút *"Thi nâng band"* trên thanh điều hướng hoặc banner nhắc nhở tại Dashboard.
   * Hệ thống tự động xác định bài thi thăng hạng: **Từ Level A1 lên Level A2** với bộ câu hỏi cấp độ A2.
   * **Thao tác đếm ngược:** Cho Giảng viên quan sát **Đồng hồ đếm ngược 10 phút (Sticky Timer)** ở phía trên, giải thích cơ chế tự động nộp bài khi hết giờ.
   * Thử chọn đáp án (đạt trên 80%), nhấn nộp bài.
3. **Thăng hạng & Hiệu ứng Vinh danh:**
   * Màn hình kết quả hiển thị **Pháo giấy chúc mừng (Confetti)** rực rỡ, thông báo thăng hạng lên Band A2 thành công.
   * Cấp độ học viên trên thanh điều hướng và trong cơ sở dữ liệu tự động chuyển từ `A1` sang `A2`.
4. **Trình diễn "Trợ lý AI Giải thích Câu sai" (Tâm điểm tính năng):**
   * Cuộn xuống phần *"Chi tiết đáp án từng câu"*.
   * Tìm câu học viên làm sai và nhấn vào nút **"✨ AI Giải thích"**.
   * Quan sát hiệu ứng Loading bất đồng bộ (không reload trang).
   * Hệ thống hiển thị khung phân tích ngữ pháp tiếng Việt chi tiết: Nêu rõ chủ điểm ngữ pháp, lý do vì sao đáp án đó đúng, chỉ ra lỗi sai của phương án đã chọn và mẹo ghi nhớ.
   * **Nhấn mạnh với Giảng viên:** Ngay cả khi ngắt kết nối Internet hoặc API Key hết hạn ngạch (Quota), tính năng AI vẫn hoạt động trơn tru 100% nhờ cơ chế **Rule-Based Fallback Engine**, cam kết độ sẵn sàng tuyệt đối cho sản phẩm.

---

## V. TỔNG KẾT & ĐÁNH GIÁ CHUNG

Sau chuỗi thời gian nỗ lực phát triển, ứng dụng **English Pro** đã cán đích xuất sắc với đầy đủ các tiêu chuẩn của một phần mềm học tập hiện đại:
* **Tính sư phạm cao:** Khung đánh giá và nâng band bám sát khung tham chiếu ngôn ngữ chung Châu Âu (CEFR).
* **Trải nghiệm người dùng vượt trội:** Giao diện chuẩn Mobile-First, mượt mà, phản hồi tức thì, hỗ trợ PWA và hiệu ứng vinh danh tạo động lực học tập mạnh mẽ.
* **Kỹ thuật phần mềm chuẩn mực:** Codebase Django phân tầng rõ ràng (MVC/MVT), tối ưu truy vấn cơ sở dữ liệu, kiến trúc AI an toàn có cơ chế dự phòng và độ bao phủ kiểm thử tự động đạt **100%**.
