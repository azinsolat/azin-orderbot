# handlers/products.py
from telegram import Update
from telegram.ext import ContextTypes

from db import get_product_by_code, create_product
from utils.validators import is_admin


async def add_test_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("شما ادمین نیستید ❌")
        return

    code = "test_product_1"
    title = "محصول تستی (نمونه)"
    price = 150000

    existing = get_product_by_code(code)
    if existing:
        pid, pcode, ptitle, pprice, is_active = existing
        await update.message.reply_text(
            f"این محصول تستی قبلاً وجود داره ✅\n\n"
            f"ID: {pid}\n"
            f"کد: {pcode}\n"
            f"عنوان: {ptitle}\n"
            f"قیمت: {pprice}"
        )
        return

    pid = create_product(code=code, title=title, price=price)

    await update.message.reply_text(
        "محصول تستی ساخته شد ✅\n\n"
        f"ID: {pid}\n"
        f"کد: {code}\n"
        f"عنوان: {title}\n"
        f"قیمت: {price}"
    )
