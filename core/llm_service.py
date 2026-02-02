from openai import OpenAI
import logging
import os
import sys

try:
    from config import config
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import config

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = None
        if config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        else:
            logger.warning("OpenAI API key not set. LLM features will use mock responses.")
    
    def generate_summary(self, articles_context: str, query: str) -> str:
        """
        Generates a summary based on found articles.
        """
        if not self.client:
            return "📝 Краткое резюме недоступно (не установлен API ключ OpenAI)."
        
        try:
            prompt = f"""Ты - AI-ассистент, помогающий анализировать статьи с Хабра.
На основе следующего контекста из найденных статей, создай краткое резюме по запросу пользователя.

Запрос: {query}

Контекст из статей:
{articles_context}

Создай краткое резюме (3-5 предложений), которое объединяет ключевые идеи из статей."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - эксперт по анализу технических статей."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM summary error: {e}")
            return f"❌ Ошибка генерации резюме: {str(e)}"
    
    def generate_quiz(self, article_title: str, article_content: str) -> str:
        """
        Generates a quiz based on article content.
        """
        if not self.client:
            return self._mock_quiz(article_title)
        
        try:
            prompt = f"""На основе следующей статьи создай короткий квиз из 3 вопросов с вариантами ответов.

Название статьи: {article_title}

Содержание (отрывок):
{article_content[:1500]}

Формат ответа:
1. Вопрос?
   a) Вариант 1
   b) Вариант 2
   c) Вариант 3
   
2. Вопрос?
...

В конце укажи правильные ответы."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - создатель образовательных квизов."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM quiz error: {e}")
            return self._mock_quiz(article_title)
    
    def _mock_quiz(self, article_title: str) -> str:
        return f"""🧠 **Мини-тест по статье '{article_title}'**:

1. О чем основная мысль статьи?
   a) Python это круто
   b) ИИ захватит мир
   c) Программирование это сложно

2. Какую технологию упоминает автор?
   a) RAG
   b) ChatGPT
   c) ChromaDB

3. Что рекомендует автор?
   a) Изучать новое
   b) Автоматизировать процессы
   c) Оба варианта

*(Это пример генерации теста. Для реальной генерации установите OPENAI_API_KEY)*"""

llm_service = LLMService()
