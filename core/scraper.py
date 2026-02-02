import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict
import time

try:
    from config import config
except ImportError:
    # Fallback for testing when running script directly from core/
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HabrScraper:
    def __init__(self):
        self.rss_url = config.HABR_RSS_URL
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_rss_feed(self) -> List[Dict]:
        """Fetches the RSS feed and returns a list of articles (metadata)."""
        try:
            response = requests.get(self.rss_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            articles = []
            for item in items:
                article = {
                    'title': item.title.text if item.title else 'No Title',
                    'link': item.link.text if item.link else '',
                    'pub_date': item.pubDate.text if item.pubDate else '',
                    'description': BeautifulSoup(item.description.text, 'html.parser').get_text(separator=' ', strip=True) if item.description else '',
                    'creator': item.find('creator').text if item.find('creator') else (item.find('dc:creator').text if item.find('dc:creator') else 'Habr User')
                }
                articles.append(article)
            
            logger.info(f"Fetched {len(articles)} articles from RSS.")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return []

    def fetch_article_content(self, url: str) -> str:
        """Fetches the full content of a specific article."""
        try:
            time.sleep(1) # Be polite
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This selector might need adjustment based on Habr's current layout
            # Usually content is in a div with class 'article-formatted-body' or similar
            content_div = soup.find('div', id='post-content-body')
            
            if not content_div:
                # Try alternative classes if ID search fails
                content_div = soup.find('div', class_='article-formatted-body')
            
            if content_div:
                return content_div.get_text(separator=' ', strip=True)
            else:
                logger.warning(f"Could not find content for {url}")
                return ""
                
        except Exception as e:
            logger.error(f"Error fetching article content {url}: {e}")
            return ""

    def get_latest_articles(self, limit: int = 5) -> List[Dict]:
        """Orchestrator: fetches RSS, then fetches full content for top N articles."""
        articles = self.fetch_rss_feed()
        results = []
        
        for article in articles[:limit]:
            content = self.fetch_article_content(article['link'])
            if content:
                article['full_text'] = content
                results.append(article)
        
        return results

if __name__ == "__main__":
    scraper = HabrScraper()
    articles = scraper.get_latest_articles(2)
    for a in articles:
        print(f"Title: {a['title']}")
        print(f"Link: {a['link']}")
        print(f"Content Preview: {a['full_text'][:200]}...")
        print("-" * 50)
