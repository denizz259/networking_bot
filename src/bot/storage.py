# bot/storage.py
from typing import List, Tuple, Optional
from . import db

async def setup_user(user_id: int):
    await db.ensure_user(user_id)

# ----- Категории -----

async def create_category(user_id: int, name: str) -> bool:
    return await db.add_category(user_id, name)

async def get_categories(user_id: int) -> List[str]:
    return await db.list_categories(user_id)

async def get_categories_full(user_id: int) -> List[Tuple[int, str]]:
    return await db.list_categories_full(user_id)

async def resolve_category_id(user_id: int, category_name: str) -> Optional[int]:
    return await db.get_category_id(user_id, category_name)

async def resolve_category_name(user_id: int, category_id: int) -> Optional[str]:
    return await db.get_category_name_by_id(user_id, category_id)

async def remove_category(user_id: int, category_id: int) -> str:
    """
    Удаляет категорию и все контакты внутри.
    """
    cat_name = await db.get_category_name_by_id(user_id, category_id)
    if cat_name is None:
        return "Категория не найдена."

    deleted = await db.delete_category(user_id, category_id)
    if deleted:
        return f"Категория '{cat_name}' удалена вместе со всеми её контактами 🗑️"
    else:
        return "Не удалось удалить категорию (возможно, уже удалена)."

# ----- Контакты -----

async def add_contact(
    user_id: int,
    category_id: int,
    display_name: str,
    contact_value: str
) -> str:
    await db.add_contact_in_category(category_id, display_name, contact_value)
    cat_name = await db.get_category_name_by_id(user_id, category_id)
    return f"Контакт '{display_name}' добавлен в '{cat_name}' ✅"

async def list_contacts_text(user_id: int, category_id: int) -> str:
    cat_name = await db.get_category_name_by_id(user_id, category_id)
    if cat_name is None:
        return "Категория не найдена."

    contacts = await db.list_contacts_in_category(category_id)
    if not contacts:
        return f"В '{cat_name}' пока нет контактов."

    lines = [f"Контакты в '{cat_name}':"]
    for display_name, contact_value in contacts:
        lines.append(f"- {display_name}: {contact_value}")
    return "\n".join(lines)

async def list_contacts_full(category_id: int) -> List[Tuple[str, str]]:
    return await db.list_contacts_in_category(category_id)

async def remove_contact(user_id: int, category_id: int, display_name: str) -> str:
    removed = await db.remove_contact_in_category(category_id, display_name)
    cat_name = await db.get_category_name_by_id(user_id, category_id)
    if removed:
        return f"Контакт '{display_name}' удалён из '{cat_name}' 🗑️"
    else:
        return f"Контакт '{display_name}' не найден в '{cat_name}'."
