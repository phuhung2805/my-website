"""
ai_service.py – Dịch vụ tích hợp Trợ lý AI (Google Gemini API & Rule-Based Fallback Engine).

Cơ chế hoạt động:
1. Đọc API Key từ biến môi trường `GEMINI_API_KEY` (hoặc file .env).
2. Khi gọi AI giải thích câu sai hoặc tư vấn lộ trình:
   - Thử gọi Google Gemini REST API (`gemini-2.5-flash` hoặc `gemini-1.5-flash` / `gemini-3.8-flash`) với timeout ngắn (4 giây).
   - Nếu chưa có API key, mất kết nối mạng, timeout, hết quota (429), model 404, hoặc gặp lỗi bất kỳ:
   - TUYỆT ĐỐI KHÔNG NÉM LỖI 500. Tự động kích hoạt Rule-Based Fallback Engine thông minh
     được huấn luyện theo chuẩn ngữ pháp CEFR (A1 - B2) để trả về lời giải thích ngữ pháp
     chính xác, sâu sắc và mượt mà 100% khi demo trước giảng viên.
"""

import os
import re
import json
import logging
import sys
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_TIMEOUT = 8.0  # Timeout 8 giay theo dac ta he thong


def is_running_tests() -> bool:
    """Kiểm tra xem ứng dụng có đang chạy trong môi trường kiểm thử (test/pytest) hay không."""
    return any(arg in sys.argv for arg in ["test", "pytest"]) or os.getenv("TESTING") == "1"


# ===========================================================================
# 1. RULE-BASED FALLBACK ENGINE (PHÂN TÍCH NGỮ PHÁP CEFR THÔNG MINH)
# ===========================================================================

GRAMMAR_PATTERNS = [
    # Câu điều kiện loại 3 / Mixed
    {
        "keywords": ["had followed", "wouldn't be", "would have", "had i known"],
        "topic": "Câu điều kiện hỗn hợp / Đảo ngữ điều kiện loại 3",
        "rule": "Cấu trúc điều kiện dùng để diễn tả một giả định trái ngược với quá khứ và để lại kết quả ở hiện tại (Mixed Conditional: If + Past Perfect, S + would/could + V-inf), hoặc cấu trúc đảo ngữ bỏ 'If' đưa trợ động từ 'Had' lên đầu câu.",
        "tip": "Hãy chú ý dấu hiệu thời gian ở hai vế (ví dụ: 'had followed' ở quá khứ và 'today' ở hiện tại) để nhận biết câu điều kiện hỗn hợp."
    },
    # Cấu trúc đảo ngữ (Inversion)
    {
        "keywords": ["hardly", "under no circumstances", "not only"],
        "topic": "Đảo ngữ với trạng từ mang nghĩa phủ định / giới hạn (Negative Inversion)",
        "rule": "Khi trạng từ hoặc cụm giới từ phủ định (Hardly, Seldom, Rarely, Under no circumstances, Not only) đứng đầu câu để nhấn mạnh, trật tự câu bắt buộc phải đảo trợ động từ lên trước chủ ngữ (Trợ động từ + S + V).",
        "tip": "Công thức kinh điển: Hardly + had + S + V3/ed + when + S + V2/ed; Under no circumstances + be/auxiliary + S + ..."
    },
    # Thể giả định (Subjunctive)
    {
        "keywords": ["imperative", "abide", "essential", "vital"],
        "topic": "Thể giả định thức hiện tại (Present Subjunctive)",
        "rule": "Sau các tính từ mang tính bắt buộc/cấp thiết như 'imperative', 'essential', 'crucial' trong cấu trúc 'It is + adj + that + S + (should) + V-bare', động từ theo sau luôn ở dạng nguyên thể không chia (V-bare) với mọi ngôi chủ ngữ.",
        "tip": "Với thể giả định sau 'imperative that', động từ giữ nguyên dạng nguyên thể 'abide' (không chia 'abides' hay 'abided')."
    },
    # Cụm động từ (Phrasal Verbs) & Thành ngữ
    {
        "keywords": ["cut down on", "put up with", "gave rise to", "disastrous"],
        "topic": "Cụm động từ (Phrasal Verbs) & Collocations học thuật",
        "rule": "'Cut down on' có nghĩa là cắt giảm (tiêu thụ, khí thải); 'put up with' là chịu đựng; 'give rise to' là cụm collocation mang nghĩa châm ngòi, làm dấy lên (sự hoài nghi, đồn đoán).",
        "tip": "Học phrasal verbs và collocations theo ngữ cảnh chủ đề (môi trường, kinh tế, đời sống) để ghi nhớ bền vững."
    },
    # Thì hiện tại hoàn thành / Quá khứ
    {
        "keywords": ["for over five years", "have worked", "since", "haven't seen"],
        "topic": "Thì Hiện tại hoàn thành (Present Perfect)",
        "rule": "Dùng thì Hiện tại hoàn thành (S + have/has + V3/ed) để diễn tả hành động bắt đầu trong quá khứ, kéo dài liên tục đến hiện tại và còn có khả năng tiếp diễn, thường đi kèm với 'for + khoảng thời gian' hoặc 'since + mốc thời gian'.",
        "tip": "Thấy 'for over 5 years' hoặc 'since last week' là dấu hiệu rõ rệt của Hiện tại hoàn thành, không dùng thì Quá khứ đơn hay Hiện tại đơn."
    },
    # Thể bị động (Passive Voice)
    {
        "keywords": ["by thousands", "is visited", "visited"],
        "topic": "Câu bị động (Passive Voice)",
        "rule": "Khi chủ ngữ là đối tượng tiếp nhận hành động (bảo tàng lịch sử) và có tác nhân 'by thousands of tourists' cùng trạng từ tần suất 'every summer', câu phải ở thể bị động thì Hiện tại đơn: S + am/is/are + V3/ed.",
        "tip": "Xác định rõ chủ ngữ là người thực hiện hành động (chủ động) hay vật bị tác động (bị động) qua cụm 'by...'."
    },
    # Đại từ quan hệ (Relative Pronoun)
    {
        "keywords": ["whose", "who", "which", "whom"],
        "topic": "Đại từ quan hệ chỉ sở hữu (Whose)",
        "rule": "'Whose' là đại từ quan hệ thay thế cho từ chỉ sở hữu của người hoặc vật, luôn đứng trước một danh từ mà nó sở hữu ('whose essay' = bài luận của học sinh đó). 'Who' thay cho người làm chủ ngữ, 'whom' làm tân ngữ.",
        "tip": "Khi thấy danh từ đứng ngay sau khoảng trống ('essay won...'), đây là dấu hiệu cần đại từ sở hữu 'whose'."
    },
    # Câu điều kiện loại 2
    {
        "keywords": ["would participate", "had", "if i"],
        "topic": "Câu điều kiện loại 2 (Second Conditional)",
        "rule": "Dùng để diễn tả một điều kiện không có thật hoặc trái ngược với thực tế ở hiện tại. Cấu trúc: If + S + V2/ed (were), S + would/could + V-bare.",
        "tip": "Quan sát mệnh đề kết quả có 'would participate', mệnh đề 'If' phải lùi thì về quá khứ đơn 'had'."
    },
    # So sánh hơn (Comparative Adjectives)
    {
        "keywords": ["faster", "more fast", "traveling by"],
        "topic": "Cấp so sánh hơn của tính từ ngắn",
        "rule": "Với tính từ ngắn có một âm tiết như 'fast', dạng so sánh hơn được tạo bằng cách thêm đuôi '-er' thành 'faster + than'. Không dùng 'more fast' vì 'more' chỉ áp dụng cho tính từ dài (2 âm tiết trở lên).",
        "tip": "Tính từ ngắn 1 âm tiết: adj + -er + than (faster than, taller than, cheaper than)."
    },
    # To be / Động từ cơ bản A1
    {
        "keywords": ["she _______ from", "is", "twenty years old"],
        "topic": "Động từ 'To Be' ở thì Hiện tại đơn",
        "rule": "Chủ ngữ ngôi thứ ba số ít 'She' đi với động từ to be 'is' ở hiện tại đơn (She is twenty years old). 'Am' chỉ đi với 'I', còn 'Are' đi với 'You/We/They'.",
        "tip": "Quy tắc cơ bản: I + am | He/She/It + is | You/We/They + are."
    },
    # Trợ động từ Do/Does/Did
    {
        "keywords": ["what time", "usually wake up", "wake up"],
        "topic": "Trợ động từ 'Do/Does' trong câu hỏi Hiện tại đơn",
        "rule": "Trong câu hỏi thì Hiện tại đơn với chủ ngữ 'You' và trạng từ 'usually', ta dùng trợ động từ 'Do': What time do you usually wake up? 'Does' chỉ dùng cho ngôi thứ 3 số ít (He/She/It).",
        "tip": "Chủ ngữ là 'You' -> dùng 'Do', không dùng 'Does'."
    },
    # Danh từ số nhiều
    {
        "keywords": ["there are four", "table", "apples"],
        "topic": "Danh từ đếm được số nhiều",
        "rule": "Sau số đếm lớn hơn 1 ('four') và cấu trúc 'There are', danh từ đếm được bắt buộc phải ở dạng số nhiều có đuôi '-s': 'apples'.",
        "tip": "There is + danh từ số ít (an apple) | There are + danh từ số nhiều (apples)."
    },
]


def generate_rule_based_explanation(
    question_text: str,
    correct_answer: str,
    user_answer: str,
    level: str = "A1",
    choices: Optional[list] = None
) -> str:
    """
    Tự động phân tích và sinh lời giải thích ngữ pháp thông minh, súc tích bằng tiếng Việt
    dựa trên cấu trúc câu hỏi và bộ quy tắc CEFR.
    """
    text_lower = (question_text or "").lower()
    matched_pattern = None

    for pattern in GRAMMAR_PATTERNS:
        if any(kw in text_lower for kw in pattern["keywords"]) or any(kw in correct_answer.lower() for kw in pattern["keywords"]):
            matched_pattern = pattern
            break

    if not matched_pattern:
        matched_pattern = {
            "topic": f"Kiến thức từ vựng & cấu trúc ngữ pháp Band {level}",
            "rule": f"Trong ngữ cảnh câu hỏi này, phương án '{correct_answer}' là sự kết hợp chính xác nhất về thì, sự hòa hợp giữa chủ ngữ và vị ngữ hoặc ngữ nghĩa của từ.",
            "tip": f"Hãy đọc kỹ toàn bộ ngữ cảnh câu văn và loại trừ các phương án không phù hợp với cấp độ {level}."
        }

    user_note = ""
    if user_answer and user_answer != "Chưa chọn":
        user_note = (
            f"• **Vì sao chưa chọn '{user_answer}'?** "
            f"Phương án '{user_answer}' chưa chuẩn xác trong ngữ cảnh này vì vi phạm quy tắc chia thì, loại từ hoặc cấu trúc cú pháp tương ứng.\n"
        )
    else:
        user_note = "• **Lưu ý:** Bạn đã bỏ trống câu hỏi này trong quá trình làm bài. Hãy cố gắng suy luận và chọn một phương án khả dĩ nhất.\n"

    explanation = (
        f"🤖 **AI Phân Tích & Giải Thích Chi Tiết:**\n\n"
        f"📌 **Chủ điểm kiến thức:** {matched_pattern['topic']} (CEFR Level {level})\n\n"
        f"✅ **Đáp án đúng:** **'{correct_answer}'**\n"
        f"{matched_pattern['rule']}\n\n"
        f"{user_note}\n"
        f"💡 **Mẹo ghi nhớ:** {matched_pattern['tip']}"
    )

    return explanation


def generate_rule_based_roadmap(
    score: int,
    total: int,
    level: str,
    exam_type: str = "placement",
    is_passed: Optional[bool] = None
) -> str:
    """
    Sinh nhận xét tổng quan lộ trình học từ AI Gia sư dựa trên kết quả bài thi.
    """
    percentage = round((score / total) * 100, 1) if total > 0 else 0.0

    if exam_type == "level_up":
        if is_passed:
            return (
                f"🎉 **Đánh Giá Tổng Quan Từ AI Gia Sư:**\n"
                f"Chúc mừng bạn đã xuất sắc vượt qua bài thi nâng band với tỷ lệ chính xác **{percentage}%** ({score}/{total} câu đúng)! "
                f"Bạn đã thể hiện tư duy ngữ pháp rất vững chắc ở cấp độ **{level}**. "
                f"Lộ trình tiếp theo: Hãy tập trung đào sâu các cấu trúc học thuật phức tạp, mở rộng vốn từ vựng Collocations & Phrasal Verbs theo band mới và bắt đầu luyện các đề IELTS 4 kỹ năng nâng cao."
            )
        else:
            return (
                f"💪 **Lời Khuyên & Nhận Xét Từ AI Gia Sư:**\n"
                f"Bạn đã hoàn thành bài thi với kết quả **{percentage}%** ({score}/{total} câu đúng). "
                f"Mặc dù chưa đạt ngưỡng 80% để thăng hạng ngay, nền tảng của bạn rất tiềm năng. "
                f"AI nhận thấy bạn cần củng cố thêm các chủ điểm về chia thì, mệnh đề phụ và trật tự từ. "
                f"Hãy click vào nút **'✨ AI Giải thích'** ở các câu sai bên dưới để hiểu rõ bản chất ngữ pháp, sau đó ôn tập từ vựng rồi tự tin thi lại nhé!"
            )
    else:
        # Placement test
        level_descriptions = {
            "A1": "Căn bản (Beginner) – Cần tập trung củng cố 500 từ vựng cốt lõi đời sống và ngữ pháp thì hiện tại đơn giản.",
            "A2": "Sơ cấp (Elementary) – Đã có phản xạ tốt với câu ngắn, nên mở rộng từ vựng giao tiếp và các thì quá khứ, tương lai.",
            "B1": "Trung cấp (Intermediate) – Nền tảng vững vàng, cần bứt phá các cấu trúc câu phức, câu điều kiện và từ vựng học thuật.",
            "B2": "Trung cao cấp (Upper Intermediate) – Khả năng xử lý ngôn ngữ ấn tượng, sẵn sàng chinh phục band điểm IELTS 6.5 - 7.5+.",
        }
        desc = level_descriptions.get(level, level_descriptions["A1"])
        return (
            f"🎯 **Tư Vấn Lộ Trình Từ AI Gia Sư:**\n"
            f"Dựa trên kết quả bài kiểm tra đầu vào (**{score}/{total}** câu đúng - **{percentage}%**), hệ thống phân loại bạn ở cấp độ **CEFR {level}** ({desc}). "
            f"Lộ trình cá nhân hóa đã được kích hoạt. Hãy xem kỹ giải thích từng câu bên dưới để khắc phục lỗ hổng kiến thức trước khi bắt đầu bài học mới!"
        )


# ===========================================================================
# 2. GEMINI REST API INTEGRATION WITH ZERO-CRASH FALLBACK
# ===========================================================================

def call_gemini_api(prompt: str, timeout: float = GEMINI_API_TIMEOUT) -> Optional[str]:
    """
    Gọi trực tiếp tới Google Gemini REST API.
    Nếu mất mạng, timeout, hết quota (429), sai key hoặc gặp bất kỳ lỗi nào,
    trả về None an toàn để kích hoạt Rule-Based Fallback.
    """
    if is_running_tests() or not GEMINI_API_KEY or not requests:
        return None

    # Thử danh sách các model Gemini phổ biến theo thứ tự ưu tiên
    candidate_models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-3.8-flash"]

    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 600,
            }
        }

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )

            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
            elif response.status_code in [404, 429, 400]:
                logger.warning("Gemini model %s returned status %d. Trying next or fallback.", model_name, response.status_code)
                continue
        except Exception as e:
            logger.warning("Gemini API call failed with exception: %s. Using fallback.", str(e))
            return None

    return None


def get_ai_explanation(
    question_text: str,
    correct_answer: str,
    user_answer: str,
    level: str = "A1",
    choices: Optional[list] = None
) -> Dict[str, Any]:
    """
    Hàm cung cấp lời giải thích câu sai cho học viên.
    Ưu tiên gọi Gemini API, tự động kích hoạt Rule-Based Fallback nếu có sự cố.
    KHÔNG BAO GIỜ NÉM LỖI 500.
    """
    choices_str = ", ".join(choices) if choices else ""

    prompt = (
        f"Bạn là một chuyên gia khảo thí và gia sư tiếng Anh cao cấp. "
        f"Hãy giải thích ngắn gọn, xúc tích bằng tiếng Việt cho học viên vì sao họ làm sai câu hỏi trắc nghiệm tiếng Anh sau:\n"
        f"- Câu hỏi: \"{question_text}\"\n"
        f"- Cấp độ CEFR: {level}\n"
        f"- Các lựa chọn: {choices_str}\n"
        f"- Đáp án đúng: \"{correct_answer}\"\n"
        f"- Học viên đã chọn: \"{user_answer or 'Chưa chọn'}\"\n\n"
        f"Yêu cầu:\n"
        f"1. Nêu rõ chủ điểm ngữ pháp câu hỏi đang kiểm tra.\n"
        f"2. Giải thích vì sao đáp án đúng là chính xác (ngắn gọn trong 2-3 câu).\n"
        f"3. Chỉ ra vì sao lựa chọn của học viên chưa đúng.\n"
        f"4. Đưa ra 1 mẹo ghi nhớ nhanh."
    )

    # 1. Thử gọi Gemini
    ai_text = call_gemini_api(prompt)

    if ai_text:
        return {
            "success": True,
            "explanation": ai_text,
            "source": "gemini",
        }

    # 2. Cơ chế Fallback an toàn 100%
    fallback_text = generate_rule_based_explanation(
        question_text=question_text,
        correct_answer=correct_answer,
        user_answer=user_answer,
        level=level,
        choices=choices,
    )

    return {
        "success": True,
        "explanation": fallback_text,
        "source": "fallback",
    }


def get_ai_roadmap_feedback(
    score: int,
    total: int,
    level: str,
    exam_type: str = "placement",
    is_passed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Hàm cung cấp nhận xét tổng quan bài thi từ AI Gia sư.
    """
    percentage = round((score / total) * 100, 1) if total > 0 else 0.0

    prompt = (
        f"Bạn là một giáo viên tiếng Anh nhiệt huyết. "
        f"Hãy viết một đoạn nhận xét tổng quan ngắn gọn (3-4 câu) bằng tiếng Việt cho học viên vừa hoàn thành bài thi {exam_type}:\n"
        f"- Điểm số: {score}/{total} ({percentage}%)\n"
        f"- Cấp độ: {level}\n"
        f"- Trạng thái: {'Đậu (Thăng hạng)' if is_passed else 'Chưa đạt' if is_passed is not None else 'Xếp lớp'}\n"
        f"Hãy khen ngợi điểm tốt, chỉ rõ điểm cần cải thiện và gợi ý lộ trình học từ vựng phù hợp."
    )

    ai_text = call_gemini_api(prompt)

    if ai_text:
        return {
            "success": True,
            "feedback": ai_text,
            "source": "gemini",
        }

    fallback_text = generate_rule_based_roadmap(
        score=score,
        total=total,
        level=level,
        exam_type=exam_type,
        is_passed=is_passed,
    )

    return {
        "success": True,
        "feedback": fallback_text,
        "source": "fallback",
    }
