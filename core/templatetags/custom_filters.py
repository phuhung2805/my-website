import random
import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='dict_get')
def dict_get(dictionary, key):
    """Lấy giá trị từ dictionary bằng key, hỗ trợ cả key dạng int và string."""
    if not isinstance(dictionary, dict):
        return None
    val = dictionary.get(key)
    if val is None:
        val = dictionary.get(str(key))
    return val

@register.filter(name='char_choice')
def char_choice(value):
    """Chuyển đổi số thứ tự (1-based) thành chữ cái A, B, C, D..."""
    try:
        return chr(64 + int(value))
    except (ValueError, TypeError):
        return ''

@register.filter(name='split_string')
def split_string(value, arg):
    """Cắt chuỗi dựa trên ký tự phân tách."""
    try:
        return value.split(arg)
    except AttributeError:
        return [value]


@register.filter(name='shuffled')
def shuffled(values):
    """Trộn thứ tự đáp án khi hiển thị để vị trí không gợi ý đáp án đúng."""
    items = list(values)
    random.shuffle(items)
    return items


@register.filter(name='bold_markdown')
def bold_markdown(value):
    """Hiển thị **chữ** thành in đậm; thoát HTML trước vì nhận xét có thể đến từ Gemini."""
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(escape(value or "")))
    return mark_safe(html)
