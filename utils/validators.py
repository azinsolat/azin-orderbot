import re
from config import ADMIN_IDS

# regex ساده برای شماره تلفن

PHONE_RE = re.compile(r"^\+?\d[\d\s\-]{7,}$")

# فقط حروف فارسی و فاصله (برای نام)
FA_NAME_RE = re.compile(r"^[\u0600-\u06FF\s]+$")

NATIONAL_ID_RE = re.compile(r"^\d{10}$")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_valid_national_id(code: str) -> bool:
    """چک کردن کد ملی ایران (۱۰ رقم + چک‌سام صحیح)."""
    code = (code or "").strip()
    if not NATIONAL_ID_RE.match(code):
        return False
    if len(set(code)) == 1:  # همه ارقام یکسان نباشند
        return False
    digits = [int(d) for d in code]
    check = digits[9]
    s = sum(digits[i] * (10 - i) for i in range(9))
    r = s % 11
    if r < 2:
        return check == r
    else:
        return check == 11 - r


def is_farsi_name(text: str) -> bool:
    text = (text or "").strip()
    return len(text) >= 3 and bool(FA_NAME_RE.match(text))


def is_valid_farsi_address_part(text: str, min_len: int = 2) -> bool:
    text = (text or "").strip()
    if len(text) < min_len:
        return False
    # حروف انگلیسی نداشته باشه
    if re.search(r"[A-Za-z]", text):
        return False
    return True