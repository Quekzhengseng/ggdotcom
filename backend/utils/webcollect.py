import os
import time
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions
import logging
from datetime import datetime
import asyncio
from scrape2 import WebScraper
import json  # To handle conversion of lists into a string

logging.basicConfig(level=logging.INFO)

class WebContentCollector:
    def __init__(self):
        """Initialize the collector with ChromaDB setup"""
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Delete the existing collection if it exists
        try:
            self.chroma_client.delete_collection("singapore_attractions")
            logging.info("Deleted existing collection 'singapore_attractions'")
        except:
            logging.info("No existing collection 'singapore_attractions' to delete.")

        # Create new collection
        self.collection = self.chroma_client.create_collection(
            name="singapore_attractions",
            metadata={"description": "Tourist attractions content from web scraping"},
            embedding_function=self.embedding_function
        )
        logging.info("Created new collection 'singapore_attractions'")

    async def process_urls(self, urls: List[str]):
        """Process a list of URLs and store their content"""
        scraper = WebScraper()

        try:
            for url in urls:
                try:
                    logging.info(f"Processing {url}")
                    result = await scraper.scrape_url(url)

                    if "error" in result:
                        logging.error(f"Error processing {url}: {result['error']}")
                        continue

                    # Convert metadata list to a comma-separated string or a JSON string
                    metadata = result["metadata"]
                    if isinstance(metadata.get("locations"), list):  # Check if 'locations' is a list
                        metadata["locations"] = ', '.join(metadata["locations"])  # Convert to string

                    # Store in ChromaDB
                    self.collection.add(
                        documents=[result["text"]],
                        metadatas=[metadata],
                        ids=[f"doc_{int(time.time())}_{hash(url) % 10000}"]
                    )

                    logging.info(f"Successfully stored content from {url}")

                except Exception as e:
                    logging.error(f"Error processing {url}: {e}")
                    continue

        finally:
            await scraper.cleanup()


async def main():
    # List of URLs to process
    urls = [
        "https://thecuriousjournal.com/chinatown-street-art/",
        "https://chinatown.sg/visit/bruce-lee-mural/",
        # Add more URLs here
    ]

    collector = WebContentCollector()
    await collector.process_urls(urls)

if __name__ == "__main__":
    asyncio.run(main())
