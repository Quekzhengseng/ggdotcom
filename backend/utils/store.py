import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
from typing import Dict, List, Any
import logging
import os
from datetime import datetime
import requests
import json
from dotenv import load_dotenv
# import asyncio
# import nest_asyncio
# nest_asyncio.apply()
import openai

load_dotenv()

class WeaviateStore:
    def __init__(self):
        weaviate_url = os.environ["WEAVIATE_URL"]
        weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")}
        )
        self._create_collections()
        
    def _run_async(self, coro):
        """Helper method to run async operations"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


    def _create_collections(self):
        """Create collections if they don't exist"""
        try:
            # Schema for both collections
            collection_schema = {
                "properties": [
                    {"name": "text", "dataType": ["text"]},
                    {"name": "place_id", "dataType": ["text"]},
                    {"name": "name", "dataType": ["text"]},
                    {"name": "category", "dataType": ["text"]},
                    {"name": "source", "dataType": ["text"]},
                    {"name": "fact_type", "dataType": ["text"]},
                    {"name": "last_verified", "dataType": ["date"]},
                    {"name": "source_url", "dataType": ["text"]},
                    {"name": "has_scrape_content", "dataType": ["boolean"]},
                    {"name": "location", "dataType": ["text"]},
                    {"name": "attraction_type", "dataType": ["text"]}
                ],
                "vectorIndexConfig": {
                    "distance": "cosine"
                },
                "vectorizer": "none"  # Set vectorizer to none for manual vector management
            }

            # Create or check both collections
            for collection_name in ["WikipediaCollection", "SingaporeAttraction"]:
                try:
                    schema = collection_schema.copy()
                    schema["class"] = collection_name
                    
                    existing_collection = self.client.collections.get(collection_name)
                    logging.info(f"Collection '{collection_name}' already exists.")
                except weaviate.exceptions.WeaviateCollectionNotFoundException:
                    self.client.schema.create_class(schema)
                    logging.info(f"Collection '{collection_name}' created successfully.")
        except Exception as e:
            logging.error(f"Error creating collections: {e}")
            raise

    def store_documents(self, collection_name: str, documents: List[Dict[str, Any]], embeddings_list: List[List[float]]) -> List[str]:
        """Store documents with their embeddings"""
        try:
            document_ids = []

            with self.client.batch.dynamic() as batch:
                for doc, embedding in zip(documents, embeddings_list):
                    # Keep the original metadata structure
                    properties = {
                        "text": doc.get("text", ""),
                        "place_id": doc.get("metadata", {}).get("place_id", ""),
                        "name": doc.get("metadata", {}).get("name", ""),
                        "category": doc.get("metadata", {}).get("category", "tourist_attraction"),
                        "source": doc.get("metadata", {}).get("source", "wikipedia"),
                        "fact_type": doc.get("metadata", {}).get("fact_type", "historical"),
                        "last_verified": doc.get("metadata", {}).get("last_verified", datetime.now().isoformat()),
                        "source_url": doc.get("metadata", {}).get("source_url", ""),
                        "has_scrape_content": doc.get("metadata", {}).get("has_scrape_content", True),
                        "location": doc.get("metadata", {}).get("location", ""),
                        "attraction_type": doc.get("metadata", {}).get("attraction_type", "")
                    }

                    result = batch.add_object(
                        properties=properties,
                        collection=collection_name,
                        vector=embedding
                    )
                    document_ids.append(result)

            logging.info(f"Successfully stored {len(documents)} documents in {collection_name}")
            return document_ids

        except Exception as e:
            logging.error(f"Error storing documents in batch: {e}")
            raise
    def search_similar(self, collection_name: str, query: str, limit: int = 5) -> dict:
        """Search for similar documents using vector similarity"""
        try:
            collection = self.client.collections.get(collection_name)
            result = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=['distance', 'certainty', 'score']
            )
            return result

        except Exception as e:
            logging.error(f"Error in vector search: {e}")
            raise

    def search_similar_bm25(self, collection_name: str, query: str, limit: int = 5) -> dict:
        """Search using BM25 algorithm"""
        try:
            collection = self.client.collections.get(collection_name)
            result = collection.query.bm25(
                query=query,
                limit=limit,
                return_metadata=['score', 'explain_score']
            )
            return result

        except Exception as e:
            logging.error(f"Error in BM25 search: {e}")
            raise

    def search_hybrid(self, collection_name: str, query: str, alpha: float = 0.5, limit: int = 5) -> dict:
        """Hybrid search combining vector and keyword search"""
        try:
            # Generate embedding for query
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_vector = response.data[0].embedding
            
            collection = self.client.collections.get(collection_name)
            result = collection.query.hybrid(
                query=query,
                vector=query_vector,
                alpha=alpha,
                limit=limit,
                return_metadata=["score", "explain_score", "distance", "certainty"]
            )
            return result

        except Exception as e:
            logging.error(f"Error in hybrid search: {e}")
            raise
    def get_documents(self, collection_name: str, limit: int = 10000) -> List[Dict[str, Any]]:
        """Retrieve documents from specified collection"""
        try:
            collection = self.client.collections.get(collection_name)
            result = collection.query.fetch_objects(limit=limit)
            
            documents = []
            for obj in result.objects:
                doc = {
                    "text": obj.properties.get("text", ""),
                    "metadata": {
                        "place_id": obj.properties.get("place_id", ""),
                        "name": obj.properties.get("name", ""),
                        "category": obj.properties.get("category", ""),
                        "source": obj.properties.get("source", ""),
                        "fact_type": obj.properties.get("fact_type", ""),
                        "last_verified": obj.properties.get("last_verified", ""),
                        "source_url": obj.properties.get("source_url", ""),
                        "has_scrape_content": obj.properties.get("has_scrape_content", True),
                        "location": obj.properties.get("location", ""),
                        "attraction_type": obj.properties.get("attraction_type", "")
                    }
                }
                documents.append(doc)
            
            return documents

        except Exception as e:
            logging.error(f"Error retrieving documents: {e}")
            raise

    def clear_collection(self, collection_name: str) -> bool:
        """Clear all documents from specified collection"""
        try:
            collection = self.client.collections.get(collection_name)
            result = collection.data.delete_many(where={})
            
            if result.get("deleted", 0) > 0:
                logging.info(f"Successfully cleared collection {collection_name}")
                return True
            else:
                logging.warning(f"No documents were deleted from {collection_name}")
                return False

        except Exception as e:
            logging.error(f"Error clearing collection: {e}")
            raise

    def close(self):
        """Close the Weaviate client connection"""
        self.client.close()
        logging.info("Weaviate client connection closed.")

    def print_results(self, results):
        """Format and print search results"""
        try:
            print("\nFormatted Results:\n")
            # Print the entire results object for debugging (if necessary)
            # print(results)

            # Check if results contain 'objects'
            if not hasattr(results, 'objects') or not results.objects:
                print("No results found")
                return

            for idx, item in enumerate(results.objects, start=1):
                print(f"\nResult {idx}:")
                print("-" * 50)

                # Extract metadata and properties safely
                metadata = getattr(item, 'metadata', {})
                props = getattr(item, 'properties', {})

                # Print metadata scores if available
                if metadata:
                    print("\nMetadata:")
                    if hasattr(metadata, 'distance') and metadata.distance is not None:
                        print(f"Distance: {metadata.distance:.4f}")
                    if hasattr(metadata, 'certainty') and metadata.certainty is not None:
                        print(f"Certainty: {metadata.certainty:.4f}")
                    if hasattr(metadata, 'score') and metadata.score is not None:
                        print(f"Score: {metadata.score:.4f}")
                    if hasattr(metadata, 'explain_score') and metadata.explain_score:
                        print(f"Explanation: {metadata.explain_score}")

                # Print properties if available
                if props:
                    print("\nProperties:")
                    print(f"Name: {props.get('name', 'N/A')}")
                    print(f"Source: {props.get('source', 'N/A')}")
                    print(f"Category: {props.get('category', 'N/A')}")
                    print(f"URL: {props.get('source_url', 'N/A')}")

                    # Print text content if available
                    text = props.get('text', '')
                    if text:
                        print(f"\nText content:")
                        print(f"{text[:300]}...")  # First 300 characters of the text
                    else:
                        print("No text content available.")

                print("-" * 50)

        except Exception as e:
            logging.error(f"Error processing results: {e}")
            print(f"Error displaying results: {str(e)}")

  


if __name__ == "__main__":
    import json
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the store
    store = WeaviateStore()
    
    def print_separator():
        print("\n" + "="*50 + "\n")
    
    while True:
        print("\nWeaviate Store Management Console")
        print("1. View Document Embeddings")
        print("2. View Document Contents")
        print("3. Clear Collection")
        print("4. Search Documents (Vector)")
        print("5. Search Documents (BM25)")
        print("6. Search Documents (Hybrid)")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
        try:
            if choice == "1":
                embeddings = store.get_documents("WikipediaCollection")
                print_separator()
                print(f"Found {embeddings} documents")
                # for doc in embeddings:
                #     print(f"Document ID: {doc['document_id']}")
                #     print(f"Vector (first 5 dimensions): {doc['vector'][:5]}\n")
                
            elif choice == "2":
                documents = store.get_documents("SingaporeAttractions")
                print_separator()
                print(f"Found {len(documents)} documents")
                for doc in documents:
                    print(f"Document ID: {doc['document_id']}")
                    print(f"Title: {doc['title']}")
                    print(f"URL: {doc['url']}")
                    print(f"Publication Date: {doc['publication_date']}")
                    print(f"Content preview: {doc['content'][:100]}...\n")
                
            elif choice == "3":
                confirm = input("Are you sure you want to clear all documents? (yes/no): ")
                if confirm.lower() == 'yes':
                    store.clear_collection()
                    print("Collection cleared successfully!")
                else:
                    print("Operation cancelled.")
                
            elif choice == "4":
                query = input("Enter search query: ")
                collection_name = "WikipediaCollection"
                results = store.search_similar(collection_name, query)
                print_separator()
                store.print_results(results)
                
            elif choice == "5":
                query = input("Enter search query: ")
                collection_name = "WikipediaCollection"
                results = store.search_similar_bm25(collection_name, query)
                print_separator()
                store.print_results(results)
                
            elif choice == "6":
                query = input("Enter search query: ")
                alpha = float(input("Enter alpha value (0.0 to 1.0, default 0.5): ") or "0.5")

                results = store.search_hybrid("WikipediaCollection",query, 0.5)
                print_separator()
                store.print_results(results)
                
            elif choice == "7":
                print("Exiting...")
                store.close()
                break
                
            else:
                print("Invalid choice. Please try again.")
                
            print_separator()
                
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Please try again.")
            
        input("Press Enter to continue...")