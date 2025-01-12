import chromadb
import os
import sys
import logging
from typing import Dict, List, Optional
from difflib import SequenceMatcher
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import get_chroma_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def similar(a: str, b: str) -> float:
    """Calculate string similarity ratio"""
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()

class RAGManager:
    def __init__(self):
        settings = get_chroma_settings()
        self.db_path = settings["persist_directory"]
        logging.info(f"Initializing local ChromaDB at: {self.db_path}")
        
        self.client = chromadb.PersistentClient(
            path=self.db_path
        )
        
        try:
            self.wikipedia_collection = self.client.get_collection("wikipedia_collection")
            logging.info("Successfully connected to wikipedia_collection")
            # Get all metadata to use for matching
            self.all_metadata = self.wikipedia_collection.get()['metadatas']
            self.all_names = [meta.get('name', '').lower() for meta in self.all_metadata]
            logging.info(f"Loaded {len(self.all_names)} place names")
        except Exception as e:
            logging.error(f"Error accessing wikipedia collection: {str(e)}")
            self.wikipedia_collection = None
            self.all_metadata = []
            self.all_names = []

    @property
    def collections(self) -> List[str]:
        return ["wikipedia_collection", "singapore_attractions"]

    def find_best_matching_place(self, text: str) -> Optional[str]:
        """Find the best matching place name from our collection"""
        text = text.lower()
        best_match = None
        best_score = 0.3  # Minimum threshold
        
        # Extract key parts from the input
        parts = [p.strip() for p in text.split(',')[0].split()]
        
        for name in self.all_names:
            # Try exact matches first
            if name in text or text in name:
                return name
            
            # Try partial matches
            for part in parts:
                if len(part) > 3:  # Only check substantial words
                    score = similar(part, name)
                    if score > best_score:
                        best_score = score
                        best_match = name
        
        return best_match

    def format_document_for_response(self, document: str, metadata: Dict) -> str:
        """Format document content for response"""
        sections = document.split('\n\n')
        relevant_info = []
        
        for section in sections:
            if section.startswith("Summary:"):
                relevant_info.append(section.replace("Summary:", "").strip())
            elif section.startswith("History:") and len(section) > 10:
                relevant_info.append(section.replace("History:", "").strip())
            elif section.startswith("Description:") and len(section) > 10:
                relevant_info.append(section.replace("Description:", "").strip())
        
        return " ".join(relevant_info) if relevant_info else document

    def query_place(self, input_text: str, limit: int = 3) -> Dict[str, List[str]]:
        """Query function with improved place matching"""
        results = {"wikipedia": []}
        
        if not self.wikipedia_collection:
            return results

        try:
            # Find best matching place name
            place_name = self.find_best_matching_place(input_text)
            logging.info(f"Best matching place: {place_name}")
            
            if place_name:
                # Query using the matched place name
                query_results = self.wikipedia_collection.query(
                    query_texts=[place_name],
                    n_results=limit,
                    include=["documents", "metadatas"]
                )
                
                if query_results and 'documents' in query_results:
                    documents = query_results['documents'][0]
                    metadatas = query_results['metadatas'][0]
                    
                    for doc, metadata in zip(documents, metadatas):
                        formatted_doc = self.format_document_for_response(doc, metadata)
                        if formatted_doc:
                            results["wikipedia"].append(formatted_doc)
            
            logging.info(f"Found {len(results['wikipedia'])} relevant results")

        except Exception as e:
            logging.error(f"Error during query: {str(e)}")

        return results

# Create a single instance to be imported
rag_manager = RAGManager()

# Flask app setup
if __name__ == '__main__':
    app = Flask(__name__)
    CORS(app)

    @app.route('/chromadb', defaults={'path': ''})
    @app.route('/chromadb<path:path>', methods=['HEAD'])
    def ping(path):
        try:
            rag_manager.client.heartbeat()
            return '', 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return '', 503

    @app.route('/RAG', methods=['POST'])
    def query_location():
        try:
            data = request.get_json()
            place_name = data.get('place_name')
            limit = data.get('limit', 3)
            
            if not place_name:
                return jsonify({'error': 'No place name provided'}), 400
                
            results = rag_manager.query_place(place_name, limit)
            return jsonify(results)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    port = int(os.environ.get("PORT", 10001))
    app.run(host="0.0.0.0", port=port)