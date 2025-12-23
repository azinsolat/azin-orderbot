# keyboards/main_keyboards.py
from telegram import ReplyKeyboardMarkup


def make_keyboard(options, row_width: int = 3, with_cancel: bool = True):
    """ساخت ReplyKeyboardMarkup با چند ستون و دکمه لغو در انتها."""
    rows = []
    for i in range(0, len(options), row_width):
        rows.append(options[i : i + row_width])
    if with_cancel:
        rows.append(["لغو"])
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def user_main_menu(has_orders: bool):
    """کیبورد اصلی کاربر عادی."""
    if has_orders:
        keyboard = [
            ["ثبت سفارش جدید"],
            ["سفارش های من"],
        ]
    else:
        keyboard = [
            ["ثبت سفارش جدید"],
        ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def admin_main_menu():
    """کیبورد اصلی ادمین."""
    keyboard = [
        ["لیست همه سفارشات"],
        ["لیست آخرین سفارشات"],
        ["سفارشات تعیین وضعیت نشده"],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )
