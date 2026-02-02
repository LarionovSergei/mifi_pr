from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards import get_main_keyboard, get_article_keyboard, get_filter_keyboard
from core.rag_engine import RagEngine
from core.scraper import HabrScraper
from core.llm_service import llm_service
import logging

router = Router()
logger = logging.getLogger(__name__)

rag = RagEngine()
scraper = HabrScraper()

# Simple in-memory storage for user filters (chat_id -> filter_dict)
user_filters = {}

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я AI-агент для поиска по статьям Хабра.\n"
        "Просто напиши мне свой вопрос или тему, и я найду релевантные материалы.\n"
        "Используй '🔄 Обновить базу знаний' для загрузки свежих статей.",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "🔄 Обновить базу знаний")
async def sync_knowledge_base(message: Message):
    status_msg = await message.answer("Начинаю загрузку свежих статей с Хабра...")
    try:
        articles = scraper.get_latest_articles(limit=5)
        if articles:
            rag.add_documents(articles)
            await status_msg.edit_text(f"✅ Успешно загружено {len(articles)} статей в базу знаний!")
        else:
            await status_msg.edit_text("⚠️ Не удалось получить статьи или нет новых.")
    except Exception as e:
        logger.error(f"Sync error: {e}")
        await status_msg.edit_text("❌ Произошла ошибка при обновлении базы.")

@router.message(F.text == "⚙️ Фильтры")
async def show_filters(message: Message):
    current_filters = user_filters.get(message.chat.id, {})
    filter_text = "Активные фильтры:\n"
    if not current_filters:
        filter_text += "Нет активных фильтров."
    else:
        for k, v in current_filters.items():
            filter_text += f"- {k}: {v}\n"
            
    await message.answer(filter_text, reply_markup=get_filter_keyboard())

@router.callback_query(F.data.startswith("filter:"))
async def handle_filter_callback(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    
    if action == "reset":
        user_filters.pop(callback.message.chat.id, None)
        await callback.message.edit_text("Фильтры сброшены.", reply_markup=get_filter_keyboard())
    elif action == "date":
        # Placeholder for date filtering logic customization
        # making it simple for now
        await callback.answer("Фильтр по дате пока не настроен детально (mock).")
    
    await callback.answer()

@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    await message.answer(
        "Этот бот использует RAG (Retrieval-Augmented Generation) для поиска ответов.\n"
        "Стек: Python, aiogram, ChromaDB, SentenceTransformers."
    )

@router.callback_query(F.data.startswith("similar:"))
async def handle_similar_articles(callback: CallbackQuery):
    # Format: similar:ShortTitle
    # We need to find the full title or just use the short one for search
    short_title = callback.data.split(":", 1)[1]
    await callback.message.answer(f"🔍 Ищу статьи, похожие на: {short_title}...")
    
    results = rag.get_recommendations(short_title, n_results=3)
    await send_search_results(callback.message, results)
    await callback.answer()

@router.callback_query(F.data.startswith("quiz:"))
async def handle_quiz(callback: CallbackQuery):
    short_title = callback.data.split(":", 1)[1]
    
    # Try to fetch article content from DB for better quiz
    results = rag.search(short_title, n_results=1)
    content = results[0]['content'] if results else ""
    
    quiz_text = llm_service.generate_quiz(short_title, content)
    await callback.message.answer(quiz_text)
    await callback.answer()

async def send_search_results(message: Message, results: list):
    if not results:
        await message.answer("Ничего не найдено.")
        return

    for idx, res in enumerate(results, 1):
        meta = res['metadata']
        # Expanded snippet as summary
        # Prefer RSS description (clean summary) over random chunk
        description = meta.get('description', '')
        if len(description) > 50:
            snippet = description[:500] + ("..." if len(description) > 500 else "")
        else:
            # Fallback to chunk content if description is missing/too short
            snippet = res['content'][:400].replace('\n', ' ') + "..."
        
        await message.answer(
            f"**{idx}. {meta['title']}**\n\n"
            f"📝 **Аннотация:**\n{snippet}\n\n"
            f"📅 {meta['pub_date']}\n"
            f"✍️ {meta.get('creator', 'Habr User')}",
            reply_markup=get_article_keyboard(meta['link'], meta['title']),
            parse_mode="Markdown"
        )

@router.message()
async def handle_search(message: Message):
    query = message.text
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    filters = user_filters.get(message.chat.id)
    results = rag.search(query, n_results=3, filters=filters)
    
    # Generate AI summary if results found
    if results and llm_service.client:
        # Prepare context from results
        context = "\n\n".join([f"Статья: {r['metadata']['title']}\n{r['content'][:500]}" for r in results[:2]])
        try:
            summary = llm_service.generate_summary(context, query)
            await message.answer(f"📝 **Краткое резюме по вашему запросу:**\n\n{summary}\n\n---\n")
        except:
            pass  # If summary fails, just show results
    
    await send_search_results(message, results)

