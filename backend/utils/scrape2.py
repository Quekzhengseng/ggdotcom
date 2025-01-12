
import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from typing import Dict, Any
import time
import logging
import os
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)


class WebScraper:
    def __init__(self):
        self.browser = None
        self.api_key = os.getenv('OPENAI_API_KEY2')
        self.client = OpenAI(api_key=self.api_key)  # Initialize OpenAI client
        
    async def initialize(self):
        """Initialize browser instance"""
        self.browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            ignoreHTTPSErrors=True
        )
        logging.info("Initialized browser")

    async def cleanup(self):
        """Clean up resources"""
        if self.browser:
            await self.browser.close()
        logging.info("Cleanup complete")

    async def extract_main_content(self, page) -> str:
        """Extract the entire body content, remove CSS and tags, and clean the text."""
        try:
            content = await page.content()  # Get the full HTML content of the page
            soup = BeautifulSoup(content, 'html.parser')  # Parse the HTML with BeautifulSoup
            
            # Remove unwanted tags like style, script, and other non-content elements
            for element in soup.find_all(['style', 'script', 'header', 'footer', 'nav', 'aside']):
                element.decompose()  # Decompose removes the tag and its content
            
            # Now we extract all the remaining text from the page, cleaning up unnecessary whitespace
            text = soup.get_text(separator=' ', strip=True)
            
            # Remove extra whitespace and newlines
            text = ' '.join(text.split())  # This will remove excess spaces and newlines
            
            # If the resulting text is too short or empty, return an error message
            if len(text) < 200:  # You can adjust the threshold based on your needs
                return ""
            
            return text  # Return the cleaned text from the page
        
        except Exception as e:
            logging.error(f"Content extraction error: {e}")
            return ""

    async def process_with_llm(self, text: str, url: str) -> Dict[str, Any]:
        """Process text with GPT-3.5 to extract locations and format content"""
        prompt = f"""
        Analyze the following text about a tourist attraction in Singapore. Extract and format the following details:
        1. Main attractions or landmarks mentioned
        2. Location details (specific area, neighborhood, street)
        3. Any historical or cultural significance
        4. Type of attraction (e.g., mural, statue, temple, etc.)

        Text: {text}

        Format the response as a JSON object with these exact fields:
        {{
            "text": "<cleaned, well-formatted description>",
            "metadata": {{
                "source_url": "{url}",
                "name": "<main attraction name>",
                "locations": "<specific location in Singapore>",
                "attraction_type": "<type of attraction>",
                "content_type": "tourist_attraction",
                "last_verified": "<current date>"
            }}
        }}

        Make sure to preserve all specific details about the attraction while removing any navigation text or irrelevant content.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0,
                top_p=1.0
            )

            result = response.choices[0].message.content.strip()
            
            try:
                result_json = json.loads(result)
                if "text" in result_json and "metadata" in result_json:
                    return result_json
            except json.JSONDecodeError:
                logging.warning("Failed to parse LLM response as JSON")

            return {
                "text": text,
                "metadata": {
                    "source_url": url,
                    "name": "",
                    "locations": "",
                    "attraction_type": "",
                    "content_type": "tourist_attraction",
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
            
            start_time = time.time()
            logging.info(f"Navigating to {url}")
            await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 30000})
            
            logging.info("Extracting content...")
            content = await self.extract_main_content(page)
            
            if not content:
                return {"error": "No content extracted"}
            
            logging.info("Processing with LLM...")
            result = await self.process_with_llm(content, url)
            
            await page.close()
            
            total_time = time.time() - start_time
            logging.info(f"Total scraping time: {total_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logging.error(f"Scraping error: {e}")
            return {"error": str(e)}

async def main():
    scraper = WebScraper()
    try:
        url = "https://chinatown.sg/visit/bruce-lee-mural/"
        # url = "https://thecuriousjournal.com/chinatown-street-art/"  # Example URL
        result = await scraper.scrape_url(url)
        print(json.dumps(result, indent=2))
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())