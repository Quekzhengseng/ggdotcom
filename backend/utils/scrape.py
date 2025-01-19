import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
import re
from langchain_community.llms import Ollama
import json
from typing import Dict, Any
import time
import logging

logging.basicConfig(level=logging.INFO)

class WebScraper:
    def __init__(self):
        self.browser = None
        self.llm = None
        
    async def initialize(self):
        """Initialize browser and LLM instances"""
        self.browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            ignoreHTTPSErrors=True
        )
        
        # Initialize Ollama with strict parameters
        self.llm = Ollama(
            model="llama3.1:latest",
            temperature=0
        )
        print("Initialized LLM and browser")

    async def cleanup(self):
        """Clean up resources"""
        if self.browser:
            await self.browser.close()
        print("Cleanup done")

    async def extract_main_content(self, page) -> str:
        """Extract only the most relevant content"""
        try:
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['nav', 'footer', 'header', 'aside', 'script', 'style']):
                element.decompose()

            # First try to get article content
            article = soup.find('article')
            if article:
                text = article.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return text

            # Try main content area
            main = soup.find('main')
            if main:
                text = main.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return text

            # Fallback to first large text block
            for div in soup.find_all(['div', 'section']):
                text = div.get_text(separator=' ', strip=True)
                if len(text) > 500:  # Only substantial content blocks
                    return text[:2000]  # Limit content length

            return ""
        except Exception as e:
            logging.error(f"Content extraction error: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common web elements
        patterns_to_remove = [
            r'Cookie Policy',
            r'Accept Cookies',
            r'Subscribe to our newsletter',
            r'Follow us on',
            r'Share this',
            r'Comments'
        ]
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Limit length while preserving meaning
        words = text.split()
        if len(words) > 300:  # Limit to ~300 words
            text = ' '.join(words[:300]) + '...'
            
        return text.strip()

    async def process_with_llm(self, text: str) -> Dict[str, Any]:
        """Process text with LLM focused on formatting for vector DB"""
        prompt = """Extract the key information from the following text and format it exactly as shown:
{
    "text": "<main content text, cleaned and summarized>",
    "metadata": {
        "title": "<inferred title>",
        "category": "<content category>",
        "summary": "<1-2 sentence summary>",
        "last_verified": "<current date>"
    }
}
Keep the response concise and ensure it matches this JSON structure exactly.

Text to process:
"""
        
        try:
            # Process with LLM
            start_time = time.time()
            response = self.llm.invoke(prompt + text[:1500])  # Limit input size
            print(f"LLM processing took {time.time() - start_time:.2f} seconds")

            # Parse response
            try:
                result = json.loads(response)
                if "text" in result and "metadata" in result:
                    return result
            except json.JSONDecodeError:
                pass

            # Fallback format if LLM response isn't proper JSON
            return {
                "text": text[:1500],
                "metadata": {
                    "title": "Extracted Content",
                    "category": "web_content",
                    "summary": text[:200],
                    "last_verified": time.strftime("%Y-%m-%d")
                }
            }
            
        except Exception as e:
            logging.error(f"LLM processing error: {e}")
            return {"error": str(e)}

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Main scraping function"""
        try:
            if not self.browser:
                await self.initialize()
                
            page = await self.browser.newPage()
            
            print(f"Navigating to {url}")
            await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 30000})
            
            print("Extracting content...")
            content = await self.extract_main_content(page)
            cleaned_content = self.clean_text(content)
            
            if not cleaned_content:
                return {"error": "No content extracted"}
            
            print("Processing with LLM...")
            result = await self.process_with_llm(cleaned_content)
            
            await page.close()
            return result
            
        except Exception as e:
            logging.error(f"Scraping error: {e}")
            return {"error": str(e)}

async def main():
    scraper = WebScraper()
    try:
        url = "https://thecuriousjournal.com/chinatown-street-art/"
        result = await scraper.scrape_url(url)
        print(json.dumps(result, indent=2))
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())