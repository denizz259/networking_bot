import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from . import db
from . import storage
from .states import CreateCategory, AddContact

router = Router()

# ======================
# Клавиатуры
# ======================

def main_menu_kb() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text="📂 Категории",
                callback_data="menu:cats"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def categories_kb(categories: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = []
    for cat_id, name in categories:
        rows.append([
            InlineKeyboardButton(
                text=f"📁 {name}",
                callback_data=f"cat:{cat_id}"
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text="➕ Новая категория",
            callback_data="catnew"
        )
    ])
    rows.append([
        InlineKeyboardButton(
            text="⬅ Назад",
            callback_data="menu:root"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def category_menu_kb(cat_id: int, cat_name: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="👁 Показать контакты",
                callback_data=f"cat:{cat_id}:contacts"
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Добавить контакт",
                callback_data=f"cat:{cat_id}:addcontact"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 Удалить контакт",
                callback_data=f"cat:{cat_id}:delcontact"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔥 Удалить категорию",
                callback_data=f"cat:{cat_id}:rmcat"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅ Назад к категориям",
                callback_data="menu:cats"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def delete_contact_kb(cat_id: int, contacts: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = []
    for display_name, contact_value in contacts:
        rows.append([
            InlineKeyboardButton(
                text=f"❌ {display_name}",
                callback_data=f"delc:{cat_id}:{display_name}"
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text="⬅ Назад",
            callback_data=f"cat:{cat_id}"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_delete_category_kb(cat_id: int, cat_name: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"❗ Удалить '{cat_name}'",
                callback_data=f"delcat:{cat_id}:confirm"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"cat:{cat_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ======================
# Общие команды (/start, /menu, /cancel)
# ======================

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await storage.setup_user(user_id)

    text = (
        "Привет! Это твоя личная книжка нетворкинга 👋\n\n"
        "Я храню категории (например «Дизайнеры», «Инвесторы») "
        "и контакты внутри каждой категории.\n\n"
        "Нажми кнопку ниже, чтобы смотреть и управлять категориями."
    )
    await message.answer(text, reply_markup=main_menu_kb())

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user_id = message.from_user.id
    await storage.setup_user(user_id)
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ок, отменил действие.", reply_markup=main_menu_kb())

# ======================
# Навигация по меню через callback_data
# ======================

@router.callback_query(F.data == "menu:root")
async def cb_menu_root(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "menu:cats")
async def cb_menu_cats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    await storage.setup_user(user_id)

    cats = await storage.get_categories_full(user_id)
    if not cats:
        text = (
            "У тебя пока нет категорий.\n"
            "Создай первую 👇"
        )
    else:
        text = "Твои категории:"

    await callback.message.edit_text(
        text,
        reply_markup=categories_kb(cats)
    )
    await callback.answer()

# ======================
# Создание категории
# ======================

@router.callback_query(F.data == "catnew")
async def cb_catnew(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await storage.setup_user(user_id)

    await state.set_state(CreateCategory.waiting_name)

    await callback.message.edit_text(
        "Введи название новой категории (например: Дизайнеры):\n\n"
        "Или /cancel чтобы выйти."
    )
    await callback.answer()

@router.message(CreateCategory.waiting_name)
async def fsm_create_category_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await storage.setup_user(user_id)

    new_cat_name = message.text.strip()
    if not new_cat_name:
        await message.answer("Пустое имя не подходит. Введи нормальное или /cancel.")
        return

    created = await storage.create_category(user_id, new_cat_name)

    if created:
        await message.answer(
            f"Категория '{new_cat_name}' создана ✅",
            reply_markup=main_menu_kb()
        )
    else:
        await message.answer(
            f"Категория '{new_cat_name}' уже существует ⚠️",
            reply_markup=main_menu_kb()
        )

    await state.clear()

# ======================
# Работа с конкретной категорией
# callback_data формата:
#   cat:<id>
#   cat:<id>:contacts
#   cat:<id>:addcontact
#   cat:<id>:delcontact
#   cat:<id>:rmcat
# ======================

@router.callback_query(F.data.startswith("cat:"))
async def cb_category_any(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await storage.setup_user(user_id)

    parts = callback.data.split(":")
    # ["cat", "<id>"] или ["cat", "<id>", "<action>"]
    if len(parts) < 2:
        await callback.answer("Некорректная категория", show_alert=True)
        return

    try:
        cat_id = int(parts[1])
    except ValueError:
        await callback.answer("Некорректная категория", show_alert=True)
        return

    cat_name = await storage.resolve_category_name(user_id, cat_id)
    if cat_name is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    # без action -> просто меню категории
    if len(parts) == 2:
        text = f"Категория: {cat_name}"
        await state.clear()
        await callback.message.edit_text(
            text,
            reply_markup=category_menu_kb(cat_id, cat_name)
        )
        await callback.answer()
        return

    action = parts[2]

    # показать контакты
    if action == "contacts":
        contacts_text = await storage.list_contacts_text(user_id, cat_id)
        await callback.message.edit_text(
            contacts_text,
            reply_markup=category_menu_kb(cat_id, cat_name)
        )
        await state.clear()
        await callback.answer()
        return

    # добавить контакт -> FSM
    if action == "addcontact":
        await state.set_state(AddContact.waiting_display_name)
        await state.update_data(category_id=cat_id)

        await callback.message.edit_text(
            f"Добавляем контакт в '{cat_name}' 👇\n"
            "Введи имя контакта (например: Олег Бех):\n\n"
            "Или /cancel чтобы выйти."
        )
        await callback.answer()
        return

    # удалить контакт -> список кнопок ❌
    if action == "delcontact":
        contacts = await storage.list_contacts_full(cat_id)
        if not contacts:
            await callback.message.edit_text(
                f"В '{cat_name}' пока нет контактов для удаления.",
                reply_markup=category_menu_kb(cat_id, cat_name)
            )
            await state.clear()
            await callback.answer()
            return

        await callback.message.edit_text(
            f"Кого удалить из '{cat_name}'?",
            reply_markup=delete_contact_kb(cat_id, contacts)
        )
        await state.clear()
        await callback.answer()
        return

    # rmcat -> запросить подтверждение удаления категории
    if action == "rmcat":
        await state.clear()
        await callback.message.edit_text(
            f"Удалить всю категорию '{cat_name}' со ВСЕМИ её контактами?\n"
            "Это действие необратимо.",
            reply_markup=confirm_delete_category_kb(cat_id, cat_name)
        )
        await callback.answer()
        return

    await callback.answer("Неизвестное действие", show_alert=True)

# ======================
# FSM: добавление контакта (2 шага)
# ======================

@router.message(AddContact.waiting_display_name)
async def fsm_addcontact_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await storage.setup_user(user_id)

    display_name = message.text.strip()
    if not display_name:
        await message.answer("Имя не может быть пустым. Попробуй ещё раз или /cancel.")
        return

    data = await state.get_data()
    data["display_name"] = display_name
    await state.update_data(**data)

    await state.set_state(AddContact.waiting_contact_value)
    await message.answer(
        "Ок. Теперь введи контакт.\n"
        "Это может быть @ник или номер телефона.\n\n"
        "Или /cancel чтобы выйти."
    )

@router.message(AddContact.waiting_contact_value)
async def fsm_addcontact_value(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await storage.setup_user(user_id)

    contact_value = message.text.strip()
    if not contact_value:
        await message.answer("Контакт не может быть пустым. Попробуй ещё или /cancel.")
        return

    data = await state.get_data()
    cat_id = data.get("category_id")
    display_name = data.get("display_name")

    if cat_id is None or display_name is None:
        await state.clear()
        await message.answer(
            "Что-то пошло не так, попробуй заново через меню 😢",
            reply_markup=main_menu_kb()
        )
        return

    resp_text = await storage.add_contact(
        user_id=user_id,
        category_id=cat_id,
        display_name=display_name,
        contact_value=contact_value
    )

    await state.clear()
    await message.answer(resp_text, reply_markup=main_menu_kb())

# ======================
# Удаление контакта по кнопке ❌
# callback_data:
#   delc:<cat_id>:<display_name>
# ======================

@router.callback_query(F.data.startswith("delc:"))
async def cb_delete_contact(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await storage.setup_user(user_id)

    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Некорректные данные", show_alert=True)
        return

    try:
        cat_id = int(parts[1])
    except ValueError:
        await callback.answer("Некорректные данные", show_alert=True)
        return

    display_name = ":".join(parts[2:])  # если вдруг в имени есть двоеточие

    resp = await storage.remove_contact(user_id, cat_id, display_name)
    cat_name = await storage.resolve_category_name(user_id, cat_id)

    await callback.message.edit_text(
        f"{resp}\n\nКатегория: {cat_name}",
        reply_markup=category_menu_kb(cat_id, cat_name or "Категория")
    )

    await state.clear()
    await callback.answer()

# ======================
# Удаление категории целиком
# callback_data:
#   delcat:<cat_id>:confirm
# ======================

@router.callback_query(F.data.startswith("delcat:"))
async def cb_delete_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await storage.setup_user(user_id)

    parts = callback.data.split(":")
    # ожидаем ["delcat", "<cat_id>", "confirm"]
    if len(parts) < 3 or parts[2] != "confirm":
        await callback.answer("Некорректные данные", show_alert=True)
        return

    try:
        cat_id = int(parts[1])
    except ValueError:
        await callback.answer("Некорректные данные", show_alert=True)
        return

    # Удаляем категорию
    resp = await storage.remove_category(user_id, cat_id)

    # После удаления показываем обновлённый список категорий
    cats = await storage.get_categories_full(user_id)
    if not cats:
        text = (
            f"{resp}\n\n"
            "У тебя больше нет категорий.\n"
            "Создай первую 👇"
        )
    else:
        text = f"{resp}\n\nТвои категории:"

    await state.clear()
    await callback.message.edit_text(
        text,
        reply_markup=categories_kb(cats)
    )
    await callback.answer()

# ======================
# RUN
# ======================

async def main():
    await db.init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
