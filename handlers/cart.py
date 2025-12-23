# handlers/cart.py
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from db import get_cart, update_cart_item_quantity, remove_cart_item


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    items = get_cart(user_id)

    if not items:
        await query.edit_message_text("🧺 سبد خریدت خالیه.")
        return

    lines = ["🛒 سبد خرید شما:\n"]
    total = 0
    kb_rows = []

    for cart_id, product_id, qty, title, price in items:
        line_total = qty * price
        total += line_total
        lines.append(f"{title} × {qty} = {line_total} تومان")

        kb_rows.append(
            [
                InlineKeyboardButton("➕", callback_data=f"cart_inc:{cart_id}"),
                InlineKeyboardButton("➖", callback_data=f"cart_dec:{cart_id}"),
                InlineKeyboardButton("❌ حذف", callback_data=f"cart_del:{cart_id}"),
            ]
        )

    lines.append(f"\nجمع کل: {total} تومان")
    kb_rows.append([InlineKeyboardButton("✅ ثبت سفارش", callback_data="checkout")])

    keyboard = InlineKeyboardMarkup(kb_rows)
    await query.edit_message_text("\n".join(lines), reply_markup=keyboard)


async def cart_modify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    try:
        action, cart_id_str = data.split(":")
        cart_id = int(cart_id_str)
    except ValueError:
        await query.edit_message_text("داده‌ی نامعتبر برای سبد خرید.")
        return

    items = get_cart(user_id)
    target = None
    for item in items:
        if item[0] == cart_id:
            target = item
            break

    if not target:
        await query.edit_message_text("این آیتم در سبدت پیدا نشد.")
        return

    cart_id_db, product_id, qty, title, price = target

    if action == "cart_inc":
        new_qty = qty + 1
        update_cart_item_quantity(cart_id_db, new_qty)
    elif action == "cart_dec":
        new_qty = qty - 1
        update_cart_item_quantity(cart_id_db, new_qty)
    elif action == "cart_del":
        remove_cart_item(cart_id_db)

    await show_cart(update, context)
