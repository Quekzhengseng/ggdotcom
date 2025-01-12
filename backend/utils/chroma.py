import chromadb
import os
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import get_chroma_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChromaDBManager:
    def __init__(self):
        settings = get_chroma_settings()
        
        # Ensure the directory exists
        os.makedirs(settings["persist_directory"], exist_ok=True)
        
        logging.info(f"Initializing local ChromaDB at: {settings['persist_directory']}")
        
        self.chroma_client = chromadb.PersistentClient(
            path=settings["persist_directory"]
        )

    def list_collections(self):
        """List all collections in the ChromaDB instance."""
        try:
            collection_names = self.chroma_client.list_collections()
            if not collection_names:
                logging.info("No collections found in ChromaDB.")
                return
            
            logging.info(f"Found {len(collection_names)} collections")
            print("\n=== ChromaDB Collections ===")
            
            for name in collection_names:
                print(f"\nCollection Name: {name}")
                self.view_collection(name)
                
        except Exception as e:
            logging.error(f"Error listing collections: {str(e)}")

    def view_collection(self, collection_name: str):
        """View all documents inside a collection."""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            result = collection.get()

            if not result or not result.get('ids'):
                logging.info(f"No documents found in collection '{collection_name}'")
                return

            doc_count = len(result['ids'])
            logging.info(f"Found {doc_count} documents in '{collection_name}'")
            
            if doc_count > 0:
                # Iterate over all documents in the collection
                for i in range(doc_count):
                    print(f"\nDocument {i+1}/{doc_count}:")
                    print("=" * 50)
                    print(f"ID: {result['ids'][i]}")
                    
                    # Display metadata
                    if result.get('metadatas'):
                        metadata = result['metadatas'][i]
                        print("\nMetadata:")
                        print("-" * 20)
                        for key, value in metadata.items():
                            print(f"{key}: {value}")
                    
                    # Display document content
                    if result.get('documents'):
                        print("\nDocument Content:")
                        print("-" * 20)
                        text = result['documents'][i]
                        # Preview the first 200 characters, ensuring it cuts cleanly
                        preview = text[:200]
                        if len(text) > 200:
                            preview = preview.rsplit(' ', 1)[0] + '...'
                        print(preview)
                    
                    print("=" * 50)
                
                # If there are more documents, indicate how many
                if doc_count > 1:
                    print(f"\nAnd {doc_count-1} more documents...")

        except Exception as e:
            logging.error(f"Error viewing collection '{collection_name}': {str(e)}")


def main():
    try:
        manager = ChromaDBManager()
        logging.info("ChromaDB Manager initialized successfully")
        manager.list_collections()
        
    except Exception as e:
        logging.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
