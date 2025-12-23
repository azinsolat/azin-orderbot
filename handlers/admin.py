# handlers/admin.py
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from db import (
    list_orders,
    get_order,
    get_order_items,
    update_order_status,
)
from utils.validators import is_admin
from utils.constants import STATUS_LABELS


async def send_latest_orders_list(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    orders = list_orders(limit=20, offset=0)

    if not orders:
        await context.bot.send_message(
            chat_id=chat_id, text="هنوز هیچ سفارشی ثبت نشده 💤"
        )
        return

    lines = ["📋 آخرین سفارش‌ها:\n"]
    kb_rows = []

    for row in orders:
        (
            order_id,
            u_id,
            national_id,
            full_name,
            phone,
            address,
            desc,
            status,
            created_at,
        ) = row
        status_label = STATUS_LABELS.get(status, status)
        lines.append(f"#{order_id} | {full_name} | {status_label}")
        kb_rows.append(
            [
                InlineKeyboardButton(
                    f"مشاهده #{order_id}",
                    callback_data=f"view_order:{order_id}",
                )
            ]
        )

    text = "\n".join(lines)
    keyboard = InlineKeyboardMarkup(kb_rows)

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
    )


async def send_all_orders_list(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    orders = list_orders(limit=1000, offset=0)

    if not orders:
        await context.bot.send_message(
            chat_id=chat_id, text="هنوز هیچ سفارشی ثبت نشده 💤"
        )
        return

    lines = ["📚 لیست همه سفارش‌ها (جدیدترین در بالا):\n"]
    kb_rows = []

    for row in orders:
        (
            order_id,
            u_id,
            national_id,
            full_name,
            phone,
            address,
            desc,
            status,
            created_at,
        ) = row
        status_label = STATUS_LABELS.get(status, status)
        lines.append(f"#{order_id} | {full_name} | {status_label}")
        kb_rows.append(
            [
                InlineKeyboardButton(
                    f"مشاهده #{order_id}",
                    callback_data=f"view_order:{order_id}",
                )
            ]
        )

    text = "\n".join(lines)
    keyboard = InlineKeyboardMarkup(kb_rows)

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
    )


async def send_unreviewed_orders_list(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE
):
    orders = list_orders(limit=1000, offset=0)
    pending_orders = [row for row in orders if row[7] == "new"]

    if not pending_orders:
        await context.bot.send_message(
            chat_id=chat_id,
            text="همه‌ی سفارش‌ها وضعیت دارند ✅\nسفارشی بدون وضعیت (new) پیدا نشد.",
        )
        return

    lines = ["⏳ سفارشات تعیین وضعیت نشده:\n"]
    kb_rows = []

    for row in pending_orders:
        (
            order_id,
            u_id,
            national_id,
            full_name,
            phone,
            address,
            desc,
            status,
            created_at,
        ) = row
        lines.append(f"#{order_id} | {full_name} | {created_at[:19]}")
        kb_rows.append(
            [
                InlineKeyboardButton(
                    f"مشاهده #{order_id}",
                    callback_data=f"view_order:{order_id}",
                )
            ]
        )

    text = "\n".join(lines)
    keyboard = InlineKeyboardMarkup(kb_rows)

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
    )


async def admin_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    if text == "لیست همه سفارشات":
        await send_all_orders_list(chat_id, context)
    elif text == "لیست آخرین سفارشات":
        await send_latest_orders_list(chat_id, context)
    elif text == "سفارشات تعیین وضعیت نشده":
        await send_unreviewed_orders_list(chat_id, context)


async def admin_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("شما ادمین نیستید ❌")
        return

    try:
        _, order_id_str = query.data.split(":")
        order_id = int(order_id_str)
    except ValueError:
        await query.edit_message_text("داده‌ی نامعتبر.")
        return

    row = get_order(order_id)
    if not row:
        await query.edit_message_text("این سفارش پیدا نشد.")
        return

    (
        o_id,
        u_id,
        national_id,
        full_name,
        phone,
        address,
        desc,
        status,
        created_at,
    ) = row
    status_label = STATUS_LABELS.get(status, status)

    items = get_order_items(o_id)
    items_lines = []
    total = 0
    if items:
        items_lines.append("\n🛒 محصولات این سفارش:")
        for title, qty, price in items:
            line_total = qty * price
            total += line_total
            items_lines.append(f"- {title} × {qty} = {line_total} تومان")
        items_lines.append(f"\nجمع کل کالاها: {total} تومان")
    items_text = "\n".join(items_lines)

    text = (
        f"🧾 جزئیات سفارش #{o_id}\n\n"
        f"👤 نام: {full_name}\n"
        f"🆔 کد ملی: {national_id}\n"
        f"📞 تلفن: {phone}\n"
        f"📍 آدرس: {address}\n"
        f"📅 زمان ثبت: {created_at}\n"
        f"وضعیت فعلی: {status_label}\n"
        f"\n📝 توضیحات: {desc or '—'}"
        f"{items_text}"
    )

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🆕 جدید", callback_data=f"set_status:{o_id}:new"
                ),
                InlineKeyboardButton(
                    "🟡 در حال بررسی",
                    callback_data=f"set_status:{o_id}:in_progress",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ تکمیل شده", callback_data=f"set_status:{o_id}:done"
                ),
                InlineKeyboardButton(
                    "🔴 لغو شده", callback_data=f"set_status:{o_id}:canceled"
                ),
            ],
        ]
    )

    await query.edit_message_text(text, reply_markup=kb)


async def admin_set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("شما ادمین نیستید ❌")
        return

    try:
        _, order_id_str, new_status = query.data.split(":")
        order_id = int(order_id_str)
    except ValueError:
        await query.edit_message_text("داده‌ی نامعتبر.")
        return

    row = get_order(order_id)
    if not row:
        await query.edit_message_text("این سفارش پیدا نشد.")
        return

    (
        o_id,
        u_id,
        national_id,
        full_name,
        phone,
        address,
        desc,
        old_status,
        created_at,
    ) = row

    updated = update_order_status(order_id, new_status)
    if not updated:
        await query.edit_message_text("آپدیت وضعیت انجام نشد.")
        return

    new_status_label = STATUS_LABELS.get(new_status, new_status)

    await query.edit_message_text(
        f"✅ وضعیت سفارش #{order_id} به «{new_status_label}» تغییر کرد."
    )

    try:
        await context.bot.send_message(
            chat_id=u_id,
            text=(
                f"سلام 👋\n"
                f"وضعیت سفارش شما با کد #{order_id} به «{new_status_label}» تغییر کرد."
            ),
        )
    except Exception:
        pass
