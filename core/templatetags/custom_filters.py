from django import template

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
