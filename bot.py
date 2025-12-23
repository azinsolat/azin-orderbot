from config import TOKEN, ADMIN_IDS

# -*- coding: utf-8 -*-
from config import TOKEN
from db import init_db

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)

# ===================== handlers =====================
from handlers.start import start
from handlers.orders import (
    order_start,
    checkout_start,
    got_fullname,
    got_national_id,
    got_phone,
    got_province,
    got_city,
    got_street,
    got_plaque,
    got_address_note,
    got_desc,
    confirm_buttons,
    cancel,
    my_orders,
    user_view_order,
)
from handlers.admin import (
    admin_menu_buttons,
    admin_view_order,
    admin_set_status,
)
from handlers.cart import (
    show_cart,
    cart_modify,
)
from handlers.products import add_test_product

# ===================== utils =====================
from utils.constants import (
    FULLNAME,
    NATIONAL_ID,
    PHONE,
    PROVINCE,
    CITY,
    STREET,
    PLAQUE,
    ADDRESS_NOTE,
    DESC,
    CONFIRM,
)

# ===================== main =====================
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("order", order_start),
            CallbackQueryHandler(checkout_start, pattern=r"^checkout$"),
            MessageHandler(
                filters.TEXT
                & ~filters.COMMAND
                & filters.Regex(r"^(ثبت سفارش مرحله‌ای|ثبت سفارش جدید)$"),
                order_start,
            ),
        ],
        states={
            FULLNAME: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_fullname),
            ],
            NATIONAL_ID: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_national_id),
            ],
            PHONE: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone),
            ],
            PROVINCE: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_province),
            ],
            CITY: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_city),
            ],
            STREET: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_street),
            ],
            PLAQUE: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_plaque),
            ],
            ADDRESS_NOTE: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_address_note),
            ],
            DESC: [
                MessageHandler(filters.Regex(r"^لغو$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_desc),
            ],
            CONFIRM: [CallbackQueryHandler(confirm_buttons)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ----- ثبت هندلرها -----
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    app.add_handler(CommandHandler("my_orders", my_orders))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r"^سفارش های من$"),
            my_orders,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.Regex(
                r"^(لیست همه سفارشات|لیست آخرین سفارشات|سفارشات تعیین وضعیت نشده)$"
            ),
            admin_menu_buttons,
        )
    )

    app.add_handler(CallbackQueryHandler(admin_view_order, pattern=r"^view_order:\d+$"))
    app.add_handler(
        CallbackQueryHandler(admin_set_status, pattern=r"^set_status:\d+:.+$")
    )

    app.add_handler(CommandHandler("add_test_product", add_test_product))

    app.add_handler(CallbackQueryHandler(show_cart, pattern=r"^view_cart$"))
    app.add_handler(
        CallbackQueryHandler(cart_modify, pattern=r"^cart_(inc|dec|del):\d+$")
    )

    app.add_handler(
        CallbackQueryHandler(user_view_order, pattern=r"^user_view_order:\d+$")
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
