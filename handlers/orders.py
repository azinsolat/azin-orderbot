# handlers/orders.py
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import ContextTypes, ConversationHandler

from db import (
    create_order,
    list_orders_by_user,
    get_order,
    get_order_items,
    get_cart,
    save_cart_to_order,
    clear_cart,
)
from config import ADMIN_IDS
from utils.constants import (
    PROVINCE,
    CITY,
    STREET,
    PLAQUE,
    ADDRESS_NOTE,
    DESC,
    CONFIRM,
    FULLNAME,
    NATIONAL_ID,
    PROVINCES_CITIES,
    STATUS_LABELS,
)
from utils.validators import (
    is_farsi_name,
    is_valid_national_id,
    PHONE_RE,
    is_valid_farsi_address_part,
)
from keyboards.main_keyboards import make_keyboard


# ---------- سفارش‌های من ----------
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    orders = list_orders_by_user(user_id, limit=10, offset=0)

    if not orders:
        await update.message.reply_text("هنوز هیچ سفارشی ثبت نکردی 💤")
        return

    lines = ["🧾 لیست آخرین سفارش‌های تو:\n"]
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
        lines.append(f"#{order_id} | {status_label} | {created_at[:19]}")
        kb_rows.append(
            [
                InlineKeyboardButton(
                    f"مشاهده #{order_id}",
                    callback_data=f"user_view_order:{order_id}",
                )
            ]
        )

    text = "\n".join(lines)
    keyboard = InlineKeyboardMarkup(kb_rows)
    await update.message.reply_text(text, reply_markup=keyboard)


async def user_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

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

    if u_id != user_id:
        await query.edit_message_text("به این سفارش دسترسی نداری ❌")
        return

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
        f"🧾 سفارش #{o_id}\n\n"
        f"📅 زمان ثبت: {created_at}\n"
        f"وضعیت: {status_label}\n"
        f"👤 نام: {full_name}\n"
        f"🆔 کد ملی: {national_id}\n"
        f"\n📍 آدرس ارسال: {address}\n"
        f"📞 تلفن: {phone}\n"
        f"\n📝 توضیحات: {desc or '—'}"
        f"{items_text}"
    )

    await query.edit_message_text(text)


# ---------- فلوی ثبت سفارش ----------
async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    items = get_cart(user_id)

    if not items:
        await query.edit_message_text("🧺 سبد خریدت خالیه، چیزی برای ثبت سفارش نیست.")
        return ConversationHandler.END

    lines = ["🛒 سبد خرید شما:\n"]
    total = 0
    for cart_id, product_id, qty, title, price in items:
        line_total = qty * price
        total += line_total
        lines.append(f"{title} × {qty} = {line_total} تومان")

    lines.append(f"\nجمع کل: {total} تومان")
    cart_text = "\n".join(lines)

    context.user_data["from_cart"] = True
    context.user_data["cart_summary"] = cart_text
    context.user_data["cart_total"] = total
    context.user_data["order"] = {}

    await query.edit_message_text(
        cart_text + "\n\nبرای نهایی کردن سفارش، اول اسم و فامیلت رو بنویس:"
    )

    return FULLNAME


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"] = {}
    keyboard = [["لغو"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )

    await update.message.reply_text(
        "✅ شروع ثبت سفارش\n\nاسم و فامیلت رو بنویس:",
        reply_markup=reply_markup,
    )
    return FULLNAME


async def got_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    if not is_farsi_name(name):
        await update.message.reply_text(
            "لطفاً نام و نام خانوادگی را به صورت فارسی و خوانا وارد کن (بدون حروف انگلیسی):"
        )
        return FULLNAME

    context.user_data["order"]["full_name"] = name
    await update.message.reply_text("کد ملی‌ات را وارد کن (10 رقم):")
    return NATIONAL_ID


async def got_national_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = (update.message.text or "").strip()
    if not is_valid_national_id(code):
        await update.message.reply_text(
            "کد ملی نامعتبر است. لطفاً دوباره 10 رقم کد ملی را درست وارد کن:"
        )
        return NATIONAL_ID

    context.user_data["order"]["national_id"] = code
    await update.message.reply_text("شماره تماس را بفرست (مثلاً 0912... یا +98...):")
    return PHONE


async def got_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = (update.message.text or "").strip()
    if not PHONE_RE.match(phone):
        await update.message.reply_text("شماره معتبر نیست. دوباره وارد کن:")
        return PHONE

    context.user_data["order"]["phone"] = phone

    provinces = list(PROVINCES_CITIES.keys())
    kb = make_keyboard(provinces, row_width=3, with_cancel=True)

    await update.message.reply_text(
        "لطفاً نام استان محل سکونت خود را از لیست زیر انتخاب کنید:",
        reply_markup=kb,
    )
    return PROVINCE


async def got_province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    province = (update.message.text or "").strip()

    if province not in PROVINCES_CITIES:
        provinces = list(PROVINCES_CITIES.keys())
        kb = make_keyboard(provinces, row_width=3, with_cancel=True)
        await update.message.reply_text(
            "استان واردشده معتبر نیست. لطفاً از روی دکمه‌ها یکی از استان‌ها را انتخاب کن:",
            reply_markup=kb,
        )
        return PROVINCE

    context.user_data["order"]["province"] = province

    cities = PROVINCES_CITIES[province]
    kb = make_keyboard(cities, row_width=3, with_cancel=True)

    await update.message.reply_text(
        f"نام شهر محل سکونت‌ات در استان {province} را از لیست زیر انتخاب کن:",
        reply_markup=kb,
    )
    return CITY


async def got_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = (update.message.text or "").strip()
    province = context.user_data["order"].get("province", "")

    valid_cities = PROVINCES_CITIES.get(province, [])

    if city not in valid_cities:
        kb = make_keyboard(valid_cities, row_width=3, with_cancel=True)
        await update.message.reply_text(
            "شهر انتخاب‌شده معتبر نیست. لطفاً از روی دکمه‌ها یکی از شهرها را انتخاب کن:",
            reply_markup=kb,
        )
        return CITY

    context.user_data["order"]["city"] = city

    kb = ReplyKeyboardMarkup(
        [["لغو"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

    await update.message.reply_text("نام خیابان را بنویس:", reply_markup=kb)
    return STREET


async def got_street(update: Update, context: ContextTypes.DEFAULT_TYPE):
    street = (update.message.text or "").strip()
    if not is_valid_farsi_address_part(street, min_len=2):
        await update.message.reply_text(
            "خیابان را به فارسی و بدون حروف انگلیسی وارد کن:"
        )
        return STREET

    context.user_data["order"]["street"] = street
    await update.message.reply_text("پلاک منزل را بنویس (می‌تواند عدد باشد):")
    return PLAQUE


async def got_plaque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plaque = (update.message.text or "").strip()
    if not is_valid_farsi_address_part(plaque, min_len=1):
        await update.message.reply_text(
            "پلاک را درست وارد کن (می‌تواند عدد/حروف فارسی باشد):"
        )
        return PLAQUE

    context.user_data["order"]["plaque"] = plaque
    await update.message.reply_text(
        "اگر توضیح اضافی برای آدرس داری بنویس (مثلاً واحد، طبقه، نشانی دقیق).\n"
        "اگر توضیحی نداری، یک خط تیره (-) بفرست."
    )
    return ADDRESS_NOTE


async def got_address_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = (update.message.text or "").strip()
    if note == "-":
        note = ""
    else:
        if not is_valid_farsi_address_part(note, min_len=2):
            await update.message.reply_text(
                "توضیحات آدرس را به فارسی و بدون حروف انگلیسی وارد کن، یا اگر نمی‌خواهی بنویسی فقط - بفرست:"
            )
            return ADDRESS_NOTE

    context.user_data["order"]["address_note"] = note
    await update.message.reply_text(
        "توضیحات سفارش (اختیاری). اگر توضیحی برای سفارش نداری بنویس: -"
    )
    return DESC


async def got_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = (update.message.text or "").strip()
    if desc == "-":
        desc = ""

    from_cart = context.user_data.get("from_cart", False)
    if from_cart:
        cart_summary = context.user_data.get("cart_summary", "")
        if cart_summary:
            if desc:
                desc = desc + "\n\n---\nسبد خرید:\n" + cart_summary
            else:
                desc = "سبد خرید:\n" + cart_summary

    context.user_data["order"]["description"] = desc

    o = context.user_data["order"]

    province = o.get("province", "")
    city = o.get("city", "")
    street = o.get("street", "")
    plaque = o.get("plaque", "")
    address_note = o.get("address_note", "")

    address_parts = [
        f"استان {province}",
        f"شهر {city}",
        f"خیابان {street}",
        f"پلاک {plaque}",
    ]
    if address_note:
        address_parts.append(f"توضیحات آدرس: {address_note}")

    full_address = "، ".join(address_parts)
    o["full_address"] = full_address

    summary = (
        "🧾 پیش‌نمایش سفارش:\n\n"
        f"👤 نام: {o['full_name']}\n"
        f"🆔 کد ملی: {o['national_id']}\n"
        f"📞 تلفن: {o['phone']}\n"
        f"📍 آدرس:\n"
        f"   استان: {province}\n"
        f"   شهر: {city}\n"
        f"   خیابان: {street}\n"
        f"   پلاک: {plaque}\n"
        f"   توضیحات آدرس: {address_note or '—'}\n"
        f"📝 توضیحات سفارش: {o['description'] or '—'}\n\n"
        "تایید می‌کنی ثبت بشه؟"
    )

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ تایید و ثبت", callback_data="confirm_order")],
            [InlineKeyboardButton("✏️ ویرایش از اول", callback_data="restart_order")],
            [InlineKeyboardButton("❌ لغو", callback_data="cancel_order")],
        ]
    )

    await update.message.reply_text(summary, reply_markup=kb)
    return CONFIRM


async def confirm_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "restart_order":
        context.user_data["order"] = {}
        await query.edit_message_text("از اول شروع می‌کنیم ✅\n\nاسم و فامیلت رو بنویس:")
        return FULLNAME

    if query.data == "cancel_order":
        for key in [
            "order",
            "from_cart",
            "cart_summary",
            "cart_total",
        ]:
            context.user_data.pop(key, None)

        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="فرآیند ثبت سفارش لغو شد ✅",
                reply_markup=ReplyKeyboardRemove(),
            )
        except Exception:
            pass

        await query.edit_message_text("لغو شد ✅")
        return ConversationHandler.END

    if query.data == "confirm_order":
        o = context.user_data.get("order") or {}
        user_id = query.from_user.id

        order_id = create_order(
            user_id=user_id,
            national_id=o.get("national_id", ""),
            full_name=o.get("full_name", ""),
            phone=o.get("phone", ""),
            address=o.get("full_address", ""),
            description=o.get("description", ""),
        )

        from_cart = context.user_data.pop("from_cart", False)
        if from_cart:
            save_cart_to_order(order_id, user_id)
            clear_cart(user_id)

        context.user_data.pop("cart_summary", None)
        context.user_data.pop("cart_total", None)
        context.user_data.pop("order", None)

        await query.edit_message_text(f"✅ سفارشت ثبت شد!\nکد سفارش: #{order_id}")

        keyboard = [
            ["ثبت سفارش جدید"],
            ["سفارش های من"],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
        )

        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✔️ فرآیند ثبت سفارش به پایان رسید.\n\nاز دکمه‌های زیر می‌تونی استفاده کنی:",
                reply_markup=reply_markup,
            )
        except Exception:
            pass

        admin_text = (
            f"📥 سفارش جدید ثبت شد\n"
            f"کد: #{order_id}\n"
            f"کاربر: {query.from_user.full_name} ({user_id})"
        )
        if from_cart:
            admin_text += "\nمنبع: 🛒 سبد خرید"

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=admin_text)
            except Exception:
                pass

        return ConversationHandler.END

    return CONFIRM


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for key in [
        "order",
        "from_cart",
        "cart_summary",
        "cart_total",
        "province",
        "city",
        "street",
        "plaque",
        "address_note",
    ]:
        context.user_data.pop(key, None)

    await update.message.reply_text(
        "فرآیند ثبت سفارش لغو شد ✅", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
