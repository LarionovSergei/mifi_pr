from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🔄 Обновить базу знаний")],
        [KeyboardButton(text="⚙️ Фильтры"), KeyboardButton(text="ℹ️ О боте")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_article_keyboard(link: str, title: str):
    # Shorten title for callback data to avoid limit
    short_title = title[:20] 
    kb = [
        [InlineKeyboardButton(text="Читать полностью", url=link)],
        [InlineKeyboardButton(text="🔍 Похожие статьи", callback_data=f"similar:{short_title}")],
        [InlineKeyboardButton(text="❓ Создать тест", callback_data=f"quiz:{short_title}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_filter_keyboard():
    kb = [
        [InlineKeyboardButton(text="📅 За все время", callback_data="filter:date:all")],
        [InlineKeyboardButton(text="❌ Сбросить фильтры", callback_data="filter:reset")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

