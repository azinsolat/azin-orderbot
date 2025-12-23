import re
from config import ADMIN_IDS
# الگوی کد ملی: دقیقاً ۱۰ رقم
NATIONAL_ID_RE = re.compile(r"^\d{10}$")

# فقط حروف فارسی + فاصله برای نام
FA_NAME_RE = re.compile(r"^[\u0600-\u06FF\s]+$")

# regex ساده برای شماره تلفن
PHONE_RE = re.compile(r"^\+?\d[\d\s\-]{7,}$")


# تبدیل اعداد فارسی/عربی به انگلیسی
def normalize_digits(text: str) -> str:
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"
    english = "0123456789"

    mapping = {}
    for p, e in zip(persian, english):
        mapping[p] = e
    for a, e in zip(arabic, english):
        mapping[a] = e

    text = (text or "").strip()
    return "".join(mapping.get(ch, ch) for ch in text)


def is_valid_national_id(code: str) -> bool:
    """چک کردن کد ملی ایران (۱۰ رقم + چک‌سام)."""
    # ۱) نرمال‌سازی
    code = normalize_digits(code)

    # ۲) فقط رقم‌ها را نگه داریم (اگر بینش اسپیس/کاراکتر عجیب بود)
    code = "".join(ch for ch in code if ch.isdigit())

    # ۳) دقیقاً ۱۰ رقم؟
    if len(code) != 10:
        return False

    # ۴) همه رقم‌ها یکسان نباشد (مثلاً ۱۱۱۱۱۱۱۱۱۱)
    if len(set(code)) == 1:
        return False

    # ۵) چک‌سام استاندارد
    digits = [int(d) for d in code]
    check = digits[9]
    s = sum(digits[i] * (10 - i) for i in range(9))
    r = s % 11

    if r < 2:
        return check == r
    else:
        return check == 11 - r


def is_farsi_name(text: str) -> bool:
    """نام و نام‌خانوادگی فارسی حداقل ۳ کاراکتر."""
    text = (text or "").strip()
    return len(text) >= 3 and bool(FA_NAME_RE.match(text))


def is_valid_farsi_address_part(text: str, min_len: int = 2) -> bool:
    """بخشی از آدرس به فارسی (بدون حروف انگلیسی)."""
    text = (text or "").strip()
    if len(text) < min_len:
        return False
    # حروف انگلیسی نداشته باشه
    if re.search(r"[A-Za-z]", text):
        return False
    return True

def is_admin(user_id: int) -> bool:
    """بررسی می‌کند که این کاربر ادمین هست یا نه."""
    return user_id in ADMIN_IDS
