

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from db import get_product_by_code, add_to_cart, list_orders_by_user
from utils.validators import is_admin
from keyboards.main_keyboards import user_main_menu, admin_main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # اگر /start با پارامتر بود (برای سبد خرید از کانال)
    args = context.args
    if args:
        key = args[0]  # مثلا: "add_test_product_1"
        if key.startswith("add_"):
            code = key[len("add_") :]  # مثلا: "test_product_1"

            product = get_product_by_code(code)
            if not product:
                await update.message.reply_text("محصول مورد نظر پیدا نشد ❌")
                return

            pid, pcode, title, price, is_active = product
            if not is_active:
                await update.message.reply_text("این محصول فعلاً غیرفعاله ❌")
                return

            # اضافه کردن به سبد خرید
            add_to_cart(user_id, pid)

            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🛒 ادامه‌ی خرید",
                            url="https://t.me/YOUR_CHANNEL_USERNAME",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "👀 مشاهده‌ی سبد خرید", callback_data="view_cart"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✅ ثبت سفارش", callback_data="checkout"
                        )
                    ],
                ]
            )

            await update.message.reply_text(
                f"✅ «{title}» به سبد خریدت اضافه شد.\n"
                "می‌تونی خریدت رو ادامه بدی، سبد رو ببینی یا ثبت سفارش کنی:",
                reply_markup=kb,
            )
            return

    # /start بدون پارامتر
    if is_admin(user_id):
        reply_markup = admin_main_menu()
        await update.message.reply_text(
            "سلام ادمین عزیز 👑\n"
            "از منوی زیر می‌تونی سفارش‌ها رو مدیریت کنی.",
            reply_markup=reply_markup,
        )
    else:
        has_orders = bool(list_orders_by_user(user_id, limit=1, offset=0))
        reply_markup = user_main_menu(has_orders)

        await update.message.reply_text(
            "سلام! 👋\n"
            "برای ثبت سفارش روی دکمه‌ی «ثبت سفارش جدید» بزن.\n"
            "بعد از اولین سفارش، می‌تونی از دکمه‌ی «سفارش های من» هم استفاده کنی.\n"
            "برای لغو در هر مرحله: /cancel",
            reply_markup=reply_markup,
        )
