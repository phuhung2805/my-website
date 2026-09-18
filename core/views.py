"""
views.py – Xử lý các route chính của ứng dụng English Pro với kiến trúc đa người dùng.

Routes:
    /login/           → login_view (đăng nhập)
    /register/        → register_view (đăng ký tài khoản mới)
    /logout/          → logout_view (đăng xuất)
    /                 → index (hiển thị flashcard chưa thuộc của user)
    /quiz/            → quiz_view (trắc nghiệm từ vựng của user)
    /ai-flashcard/    → ai_flashcard_view (tạo flashcard bằng AI cho user)
    /mark-mastered/<id>/ → mark_mastered (đánh dấu đã thuộc)
"""
import json
import random
import datetime

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Category, Flashcard, QuizResult, Vocabulary, VocabSet,
    UserProfile, ReadingPassage, ListeningTrack, WritingTask,
    SpeakingPrompt, UserSubmission
)


# ---------------------------------------------------------------------------
# Authentication Views
# ---------------------------------------------------------------------------

def login_view(request):
    """Xử lý đăng nhập người dùng."""
    if request.user.is_authenticated:
        return redirect("index")

    error = None
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next", "index")
            return redirect(next_url)
        else:
            error = "Tên đăng nhập hoặc mật khẩu không chính xác."
    else:
        form = AuthenticationForm()

    return render(request, "core/login.html", {"form": form, "error": error})


def register_view(request):
    """Xử lý đăng ký tài khoản mới."""
    if request.user.is_authenticated:
        return redirect("index")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        if not username or not password:
            error = "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."
        elif len(password) < 6:
            error = "Mật khẩu phải chứa ít nhất 6 ký tự."
        elif password != password_confirm:
            error = "Mật khẩu xác nhận không trùng khớp."
        elif User.objects.filter(username=username).exists():
            error = "Tên đăng nhập đã tồn tại trên hệ thống."
        else:
            with transaction.atomic():
                # Tạo user mới
                user = User.objects.create_user(username=username, password=password)
                login(request, user)

                # Tự động đồng bộ các từ vựng global mặc định làm bộ Flashcard ban đầu cho user
                global_vocabs = Vocabulary.objects.filter(user__isnull=True)
                if global_vocabs.exists():
                    new_cards = [
                        Flashcard(user=user, vocabulary=v, is_mastered=False)
                        for v in global_vocabs
                    ]
                    Flashcard.objects.bulk_create(new_cards, ignore_conflicts=True)

                return redirect("index")
    
    return render(request, "core/register.html", {"error": error})


def logout_view(request):
    """Xử lý đăng xuất tài khoản."""
    logout(request)
    return redirect("login")


# ---------------------------------------------------------------------------
# Trang chủ – Flashcard học từ vựng (Yêu cầu Login)
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def index(request):
    """Hiển thị tất cả flashcard chưa thuộc của người dùng hiện tại theo trình độ."""
    level = request.GET.get('level', request.session.get('active_level', 'A1')).upper()
    if level not in ['A1', 'A2', 'B1']:
        level = 'A1'
    request.session['active_level'] = level

    # 1. Đồng bộ hóa các từ vựng mới thuộc level đã chọn
    user_flashcard_vocab_ids = Flashcard.objects.filter(user=request.user).values_list("vocabulary_id", flat=True)
    missing_vocabs = Vocabulary.objects.filter(
        Q(user=request.user) | Q(user__isnull=True),
        level=level
    ).exclude(id__in=user_flashcard_vocab_ids)

    if missing_vocabs.exists():
        new_cards = [
            Flashcard(user=request.user, vocabulary=v, is_mastered=False)
            for v in missing_vocabs
        ]
        Flashcard.objects.bulk_create(new_cards, ignore_conflicts=True)

    # 2. Lấy chủ đề đầu tiên để làm nhãn mặc định
    category = Category.objects.filter(
        Q(user=request.user) | Q(user__isnull=True),
        level=level
    ).first()
    
    # 3. Lấy flashcards chưa thuộc và đến hạn ôn tập
    flashcards = Flashcard.objects.filter(
        user=request.user,
        vocabulary__level=level,
        is_mastered=False,
        next_review_date__lte=timezone.now().date()
    ).select_related("vocabulary")

    return render(
        request,
        "core/index.html",
        {"category": category, "flashcards": flashcards, "active_level": level},
    )


# ---------------------------------------------------------------------------
# Đánh dấu flashcard đã thuộc
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def mark_mastered(request, card_id):
    """Đánh dấu một flashcard là đã thuộc và quay lại trang chủ."""
    card = get_object_or_404(Flashcard, id=card_id, user=request.user)
    card.is_mastered = True
    card.review_count += 1
    card.save(update_fields=["is_mastered", "review_count"])
    return redirect("index")


# ---------------------------------------------------------------------------
# Đánh giá Flashcard (SM-2)
# ---------------------------------------------------------------------------

@login_required(login_url="login")
@require_POST
def review_flashcard(request, card_id):
    """Xử lý thuật toán SM-2 khi người dùng ôn tập Flashcard."""
    card = get_object_or_404(Flashcard, id=card_id, user=request.user)
    try:
        data = json.loads(request.body)
        quality = int(data.get("quality", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Dữ liệu không hợp lệ."}, status=400)

    # SM-2 logic
    if quality >= 3:
        if card.repetition_count == 0:
            card.interval = 1
        elif card.repetition_count == 1:
            card.interval = 6
        else:
            card.interval = round(card.interval * card.easiness_factor)
        card.repetition_count += 1
    else:
        card.repetition_count = 0
        card.interval = 1
    
    card.easiness_factor = card.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if card.easiness_factor < 1.3:
        card.easiness_factor = 1.3
        
    card.next_review_date = timezone.now().date() + datetime.timedelta(days=card.interval)
    card.save(update_fields=["repetition_count", "easiness_factor", "interval", "next_review_date"])

    return JsonResponse({
        "status": "success", 
        "next_review_date": card.next_review_date.strftime("%Y-%m-%d"),
        "interval": card.interval
    })





# ---------------------------------------------------------------------------
# 4-Skills Personal Dashboard View
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def dashboard_view(request, level_code=None):
    """
    Hiển thị bảng điều khiển cá nhân hóa của học viên (Dashboard).
    Tính toán ngày đếm ngược thi, mục tiêu điểm số và lịch sử hoạt động hàng ngày.
    """
    if level_code:
        level = level_code.upper()
        if level in ['A1', 'A2', 'B1']:
            request.session['active_level'] = level
        else:
            return redirect("dashboard")
    else:
        level = request.GET.get('level', request.session.get('active_level', 'A1')).upper()
        if level not in ['A1', 'A2', 'B1']:
            level = 'A1'
        request.session['active_level'] = level

    # 1. Tự động tìm hoặc khởi tạo UserProfile cho học viên
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "target_listening": 75,
            "target_speaking": 75,
            "target_reading": 75,
            "target_writing": 75,
            "exam_date": datetime.date.today() + datetime.timedelta(days=90)
        }
    )

    # 2. Tính toán ngày đếm ngược tới ngày thi
    days_remaining = None
    if profile.exam_date:
        today = timezone.now().date()
        delta = profile.exam_date - today
        days_remaining = max(0, delta.days)

    # 3. Lấy ra lịch sử hoạt động nộp bài gần đây của học viên (tối đa 5 hoạt động)
    recent_submissions = UserSubmission.objects.filter(user=request.user).order_by("-completed_at")[:5]

    # 4. Sinh dữ liệu thực tế cho Biểu đồ nhiệt đóng góp học tập (Heatmap Grid - 126 ngày = 18 tuần)
    import collections
    end_date = timezone.now().date()
    start_date = end_date - datetime.timedelta(days=125)

    # Lấy số lượng nộp bài theo từng ngày từ Database
    submission_counts = collections.Counter(
        UserSubmission.objects.filter(
            user=request.user,
            completed_at__date__range=[start_date, end_date]
        ).values_list("completed_at__date", flat=True)
    )

    # Xây dựng danh sách ô đóng góp cho heatmap
    heatmap_data = []
    current_date = start_date
    while current_date <= end_date:
        count = submission_counts.get(current_date, 0)
        
        # Quyết định độ đậm của màu ngọc lục bảo (Emerald Green) dựa trên số bài tập
        if count == 0:
            bg_class = "bg-slate-100 hover:bg-slate-200"
        elif count <= 1:
            bg_class = "bg-emerald-100 hover:bg-emerald-200"
        elif count <= 2:
            bg_class = "bg-emerald-300 hover:bg-emerald-400"
        elif count <= 4:
            bg_class = "bg-emerald-500 hover:bg-emerald-600"
        else:
            bg_class = "bg-emerald-700 hover:bg-emerald-800"

        heatmap_data.append({
            "date_str": current_date.strftime("%Y-%m-%d"),
            "formatted_date": current_date.strftime("%d/%m/%Y"),
            "count": count,
            "bg_class": bg_class
        })
        current_date += datetime.timedelta(days=1)

    # Lấy danh sách các đề luyện tập có sẵn cho 4 kỹ năng theo cấp độ đã chọn
    reading_passages = ReadingPassage.objects.filter(level=level)[:5]
    listening_tracks = ListeningTrack.objects.filter(level=level)[:5]
    writing_tasks = WritingTask.objects.filter(level=level)[:5]
    speaking_prompts = SpeakingPrompt.objects.filter(level=level)[:5]

    context = {
        "profile": profile,
        "days_remaining": days_remaining,
        "recent_submissions": recent_submissions,
        "heatmap_data": heatmap_data,
        "reading_passages": reading_passages,
        "listening_tracks": listening_tracks,
        "writing_tasks": writing_tasks,
        "speaking_prompts": speaking_prompts,
        "active_level": level,
    }
    return render(request, "core/dashboard.html", context)


@login_required(login_url="login")
@require_POST
def update_goals_view(request):
    """Cập nhật mục tiêu điểm số của học viên qua API."""
    try:
        data = json.loads(request.body)
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Get and validate targets (ensure they are floats)
        try:
            listening = float(data.get('target_listening', profile.target_listening))
            speaking = float(data.get('target_speaking', profile.target_speaking))
            reading = float(data.get('target_reading', profile.target_reading))
            writing = float(data.get('target_writing', profile.target_writing))
        except (ValueError, TypeError):
            return JsonResponse({"error": "Dữ liệu không hợp lệ, mục tiêu phải là số."}, status=400)
            
        profile.target_listening = listening
        profile.target_speaking = speaking
        profile.target_reading = reading
        profile.target_writing = writing
        
        profile.save(update_fields=['target_listening', 'target_speaking', 'target_reading', 'target_writing'])
        
        return JsonResponse({
            "status": "success", 
            "message": "Cập nhật mục tiêu thành công!",
            "data": {
                "target_listening": profile.target_listening,
                "target_speaking": profile.target_speaking,
                "target_reading": profile.target_reading,
                "target_writing": profile.target_writing
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({"error": "Dữ liệu JSON không hợp lệ."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Có lỗi xảy ra: {str(e)}"}, status=500)


# ---------------------------------------------------------------------------
# Giao diện thi Đọc hiểu hai màn hình (Split-Screen Reading Test)
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def reading_test_view(request, passage_id):
    """
    Xử lý giao diện làm bài thi Đọc hiểu hai màn hình (Split-Screen Reading Test).
    GET: Hiển thị bài đọc và câu hỏi ở chế độ làm bài ("test").
    POST: Thu thập câu trả lời, tính toán số câu đúng, quy đổi thang điểm IELTS,
          lưu vào lịch sử đóng góp (UserSubmission), và render chế độ kết quả ("result").
    """
    # 1. Lấy bài đọc hoặc trả về 404
    from .models import ReadingPassage, ReadingQuestion, UserSubmission
    passage = get_object_or_404(ReadingPassage, id=passage_id)
    questions = passage.questions.all()

    # Nếu không có câu hỏi nào, quay lại trang chủ
    if not questions.exists():
        return redirect("dashboard")

    # 2. Xử lý khi nộp bài thi (POST)
    if request.method == "POST":
        score = 0
        total_questions = questions.count()
        results = {}  # Lưu chi tiết: {question_id: {'user_ans': ..., 'is_correct': ..., 'correct_ans': ...}}

        for q in questions:
            user_answer = request.POST.get(f"q_{q.id}", "").strip()
            is_correct = (user_answer.lower() == q.correct_answer.lower())
            
            if is_correct:
                score += 1
                
            results[q.id] = {
                "user_answer": user_answer,
                "is_correct": is_correct,
                "correct_answer": q.correct_answer
            }

        # Tính tỷ lệ đúng & quy đổi band điểm IELTS (0 - 9)
        percentage = round((score / total_questions) * 100, 2)
        
        # IELTS Band Score mapping logic (quy đổi tương đối dựa trên % câu đúng)
        if percentage >= 95:
            band = 9.0
        elif percentage >= 88:
            band = 8.5
        elif percentage >= 80:
            band = 8.0
        elif percentage >= 72:
            band = 7.5
        elif percentage >= 65:
            band = 7.0
        elif percentage >= 58:
            band = 6.5
        elif percentage >= 50:
            band = 6.0
        elif percentage >= 40:
            band = 5.5
        elif percentage >= 30:
            band = 5.0
        else:
            band = 4.0

        # Lời khuyên cá nhân hóa
        if band >= 7.5:
            feedback = "Xuất sắc! Kỹ năng đọc hiểu của bạn đang ở mức rất cao chuẩn học thuật."
        elif band >= 6.0:
            feedback = "Khá tốt! Bạn đã nắm được hầu hết thông tin chính, hãy rèn thêm vốn từ vựng nhé."
        else:
            feedback = "Cố gắng lên! Hãy xem lại các câu trả lời sai và luyện kỹ năng quét thông tin (Scanning) nhé."

        # 3. Tạo một UserSubmission nộp bài
        with transaction.atomic():
            UserSubmission.objects.create(
                user=request.user,
                skill_type="reading",
                task_title=f"Reading Test: {passage.title}",
                score_achieved=band,
                completed_at=timezone.now()
            )

        context = {
            "passage": passage,
            "questions": questions,
            "mode": "result",
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "band": band,
            "feedback": feedback,
            "results": results
        }
        return render(request, "core/reading_test.html", context)

    # 4. Hiển thị trang làm bài bình thường (GET)
    context = {
        "passage": passage,
        "questions": questions,
        "mode": "test"
    }
    return render(request, "core/reading_test.html", context)


# ---------------------------------------------------------------------------
# Giao diện thi Nghe hiểu (Listening Test)
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def listening_test_view(request, track_id):
    """
    Xử lý giao diện thi Nghe hiểu.
    GET: Render giao diện thi với bộ Audio Player cố định và danh sách câu hỏi.
    POST: Chấm điểm trắc nghiệm, tính điểm IELTS, ghi log UserSubmission.
    """
    from .models import ListeningTrack, ListeningQuestion, UserSubmission
    track = get_object_or_404(ListeningTrack, id=track_id)
    questions = track.questions.all()

    if not questions.exists():
        return redirect("dashboard")

    if request.method == "POST":
        score = 0
        total_questions = questions.count()
        results = {}

        for q in questions:
            user_answer = request.POST.get(f"q_{q.id}", "").strip()
            is_correct = (user_answer.lower() == q.correct_answer.lower())
            if is_correct:
                score += 1
            results[q.id] = {
                "user_answer": user_answer,
                "is_correct": is_correct,
                "correct_answer": q.correct_answer
            }

        percentage = round((score / total_questions) * 100, 2)
        
        # Quy đổi Band IELTS Listening
        if percentage >= 95:
            band = 9.0
        elif percentage >= 88:
            band = 8.5
        elif percentage >= 80:
            band = 8.0
        elif percentage >= 72:
            band = 7.5
        elif percentage >= 65:
            band = 7.0
        elif percentage >= 58:
            band = 6.5
        elif percentage >= 50:
            band = 6.0
        elif percentage >= 40:
            band = 5.5
        else:
            band = 5.0

        # Lưu hoạt động
        with transaction.atomic():
            UserSubmission.objects.create(
                user=request.user,
                skill_type="listening",
                task_title=f"Listening Test: {track.title}",
                score_achieved=band,
                completed_at=timezone.now()
            )

        context = {
            "track": track,
            "questions": questions,
            "mode": "result",
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "band": band,
            "results": results
        }
        return render(request, "core/listening_test.html", context)

    context = {
        "track": track,
        "questions": questions,
        "mode": "test"
    }
    return render(request, "core/listening_test.html", context)


# ---------------------------------------------------------------------------
# Giao diện thi Viết luận (Writing Test)
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def writing_test_view(request, task_id):
    """
    Xử lý giao diện thi Viết luận.
    GET: Render đề bài và khung soạn thảo bài viết.
    POST: Đếm từ, lưu lịch sử, chấm điểm giả lập dựa trên chiều dài bài và chuyển hướng.
    """
    from .models import WritingTask, UserSubmission
    task = get_object_or_404(WritingTask, id=task_id)

    if request.method == "POST":
        essay_text = request.POST.get("essay_text", "").strip()
        word_count = len(essay_text.split())

        # Đánh giá Band điểm sơ bộ dựa trên số lượng từ (để tạo cảm giác thực tế)
        if word_count < 100:
            band = 4.5
            feedback = "Bài viết quá ngắn. Bạn cần đạt tối thiểu 150 từ cho Task 1 và 250 từ cho Task 2."
        elif word_count < 150:
            band = 5.5
            feedback = "Bài viết còn thiếu ý và từ vựng chưa phong phú. Hãy mở rộng lập luận của bạn."
        elif word_count < 250:
            band = 6.5
            feedback = "Bài viết khá tốt, cấu trúc rõ ràng. Hãy nâng cấp từ vựng nâng cao và các liên từ để tăng điểm."
        else:
            band = 7.5
            feedback = "Xuất sắc! Bài viết rất phong phú, lập luận chặt chẽ và đạt độ dài tiêu chuẩn."

        # Lưu hoạt động nộp bài
        with transaction.atomic():
            UserSubmission.objects.create(
                user=request.user,
                skill_type="writing",
                task_title=f"Writing Essay: {task.title}",
                score_achieved=band,
                completed_at=timezone.now()
            )

        context = {
            "task": task,
            "essay_text": essay_text,
            "word_count": word_count,
            "band": band,
            "feedback": feedback,
            "mode": "result"
        }
        return render(request, "core/writing_test.html", context)

    context = {
        "task": task,
        "mode": "test"
    }
    return render(request, "core/writing_test.html", context)


# ---------------------------------------------------------------------------
# Giao diện thi Nói & Thu âm Micro (Speaking Test)
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def speaking_test_view(request, prompt_id):
    """
    Xử lý giao diện thi Nói và thu âm âm thanh.
    GET: Render Cue Card đề bài nói phản xạ.
    POST (AJAX): Tiếp nhận file ghi âm âm thanh (.webm / .wav) gửi lên qua Fetch API,
                 lưu vật lý vào thư mục media/speaking_uploads/, lưu kết quả học tập.
    """
    from .models import SpeakingPrompt, UserSubmission
    prompt = get_object_or_404(SpeakingPrompt, id=prompt_id)

    if request.method == "POST":
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return JsonResponse({"error": "Không tìm thấy dữ liệu âm thanh."}, status=400)

        # Cấu hình thư mục lưu trữ trong media
        from django.conf import settings
        import os
        upload_dir = os.path.join(settings.MEDIA_ROOT, "speaking_uploads")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)

        # Đặt tên file ghi âm độc nhất
        filename = f"user_{request.user.id}_prompt_{prompt.id}_{int(timezone.now().timestamp())}.webm"
        filepath = os.path.join(upload_dir, filename)

        # Lưu file vật lý
        try:
            with open(filepath, "wb+") as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
        except Exception as e:
            return JsonResponse({"error": f"Lỗi lưu file ghi âm: {str(e)}"}, status=500)

        # Chấm điểm giả lập IELTS Speaking (sinh ngẫu nhiên band 6.5 - 8.0 cho học viên)
        import random
        band = random.choice([6.5, 7.0, 7.5, 8.0])

        # Lưu hoạt động đóng góp
        with transaction.atomic():
            UserSubmission.objects.create(
                user=request.user,
                skill_type="speaking",
                task_title=f"Speaking Audio: {prompt.title}",
                score_achieved=band,
                completed_at=timezone.now()
            )

        return JsonResponse({
            "status": "success",
            "message": "Bài nói của bạn đã được tải lên và lưu trữ thành công!",
            "band": band,
            "filename": filename
        })

    context = {
        "prompt": prompt
    }
    return render(request, "core/speaking_test.html", context)


def api_lessons(request):
    """
    API endpoint to get list of lessons/exercises for a specific level.
    Usage: GET /api/lessons?level=a2
    """
    level = request.GET.get('level', 'A1').upper()
    if level not in ['A1', 'A2', 'B1']:
        return JsonResponse({"error": "Trình độ không hợp lệ. Vui lòng chọn A1, A2 hoặc B1."}, status=400)
    
    reading = list(ReadingPassage.objects.filter(level=level).values('id', 'title', 'created_at'))
    listening = list(ListeningTrack.objects.filter(level=level).values('id', 'title', 'created_at'))
    writing = list(WritingTask.objects.filter(level=level).values('id', 'title', 'created_at'))
    speaking = list(SpeakingPrompt.objects.filter(level=level).values('id', 'title', 'created_at'))
    
    return JsonResponse({
        "status": "success",
        "level": level,
        "data": {
            "reading": reading,
            "listening": listening,
            "writing": writing,
            "speaking": speaking
        }
    })


@login_required(login_url="login")
def api_flashcards(request):
    """
    API endpoint to get list of flashcards for the current user.
    Supports search, topic filtering, and pagination.
    """
    level = request.GET.get('level', request.session.get('active_level', 'A1')).upper()
    if level not in ['A1', 'A2', 'B1']:
        level = 'A1'
    request.session['active_level'] = level

    # 1. Sync missing flashcards for user and level
    user_flashcard_vocab_ids = Flashcard.objects.filter(user=request.user).values_list("vocabulary_id", flat=True)
    missing_vocabs = Vocabulary.objects.filter(
        Q(user=request.user) | Q(user__isnull=True),
        level=level
    ).exclude(id__in=user_flashcard_vocab_ids)

    if missing_vocabs.exists():
        new_cards = [
            Flashcard(user=request.user, vocabulary=v, is_mastered=False)
            for v in missing_vocabs
        ]
        Flashcard.objects.bulk_create(new_cards, ignore_conflicts=True)

    # 2. Get active flashcards (not mastered and due for review)
    queryset = Flashcard.objects.filter(
        user=request.user,
        vocabulary__level=level,
        is_mastered=False,
        next_review_date__lte=timezone.now().date()
    ).select_related("vocabulary")

    # 3. Apply search query
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(vocabulary__word__icontains=search_query) |
            Q(vocabulary__meaning__icontains=search_query)
        )

    # 4. Apply topic filter
    topic_query = request.GET.get('topic', '').strip()
    if topic_query:
        queryset = queryset.filter(vocabulary__topic=topic_query)

    queryset = queryset.order_by('id')

    # 5. Pagination
    try:
        page = int(request.GET.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    limit = 20
    offset = (page - 1) * limit

    total_count = queryset.count()
    import math
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    sliced_queryset = queryset[offset:offset + limit]

    flashcards_data = []
    for f in sliced_queryset:
        flashcards_data.append({
            "id": f.id,
            "is_mastered": f.is_mastered,
            "review_count": f.review_count,
            "repetition_count": f.repetition_count,
            "easiness_factor": f.easiness_factor,
            "interval": f.interval,
            "next_review_date": f.next_review_date.strftime("%Y-%m-%d") if f.next_review_date else None,
            "vocabulary": {
                "id": f.vocabulary.id,
                "word": f.vocabulary.word,
                "ipa": f.vocabulary.ipa,
                "meaning": f.vocabulary.meaning,
                "word_type": f.vocabulary.word_type,
                "word_type_display": f.vocabulary.get_word_type_display(),
                "example": f.vocabulary.example,
                "level": f.vocabulary.level,
                "topic": f.vocabulary.topic,
            }
        })

    return JsonResponse({
        "status": "success",
        "flashcards": flashcards_data,
        "total_pages": total_pages,
        "current_page": page,
        "total_count": total_count
    })