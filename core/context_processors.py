"""Biến dùng chung cho thanh chọn trình độ trên mọi template."""
from .models import LEVELS, UserProfile


def learner_level(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}

    profile = UserProfile.objects.filter(user=user).only("assigned_level").first()
    assigned = (profile.assigned_level if profile else "") or "A1"
    assigned_index = LEVELS.index(assigned)
    return {
        "assigned_level": assigned,
        "active_level": request.session.get("active_level", assigned),
        "level_tabs": [
            {"code": code, "slug": code.lower(), "locked": index > assigned_index}
            for index, code in enumerate(LEVELS)
        ],
    }
