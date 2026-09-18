def calculate_quiz_results(user_answers: list, correct_answers: list):
    """
    Tính toán kết quả bài kiểm tra.
    
    :param user_answers: List các đáp án người dùng chọn (ví dụ: ['A', 'B', 'C'])
    :param correct_answers: List các đáp án đúng từ DB (ví dụ: ['A', 'C', 'C'])
    :return: dict chứa kết quả và lời khuyên
    """
    total_questions = len(correct_answers)
    if total_questions == 0:
        return {"error": "Không có câu hỏi nào."}

    # Tính số câu đúng
    score = sum(1 for u, c in zip(user_answers, correct_answers) if u == c)
    
    # Tính phần trăm
    percentage = (score / total_questions) * 100
    
    # Logic đưa ra lời khuyên
    if percentage >= 80:
        feedback = "Xuất sắc! Bạn đã nắm vững kiến thức chủ đề này."
    elif percentage >= 50:
        feedback = "Khá tốt, nhưng hãy xem lại các câu sai để cải thiện nhé."
    else:
        feedback = "Bạn cần luyện tập thêm chủ đề này. Đừng nản lòng nhé!"

    return {
        "score": score,
        "total": total_questions,
        "percentage": round(percentage, 2),
        "feedback": feedback
    }