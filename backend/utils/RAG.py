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
        
        # Initialize collections
        self.collections = {
            "wikipedia_collection": None,
            "singapore_attractions": None
        }
        
        try:
            # Load the collections
            for collection_name in self.collections:
                self.collections[collection_name] = self.client.get_collection(collection_name)
                logging.info(f"Successfully connected to {collection_name}")
            
            # Load document content
            self.all_metadata = {}
            self.all_documents = {}
            
            for collection_name, collection in self.collections.items():
                if collection:
                    collection_data = collection.get()
                    self.all_metadata[collection_name] = collection_data['metadatas']
                    self.all_documents[collection_name] = collection_data['documents']
                    logging.info(f"Loaded {len(self.all_documents[collection_name])} documents from {collection_name}")
        
        except Exception as e:
            logging.error(f"Error initializing RAGManager: {str(e)}")
            raise

    def extract_key_terms(self, query_text: str, location: str = None, address: str = None) -> List[str]:
        """Extract meaningful terms from the query and location"""
        # Minimal stop words to preserve most meaningful terms
        stop_words = {'a', 'an', 'the', 'tell', 'me', 'about'}
        
        terms = []
        
        # Process query text first
        if query_text:
            # Clean and split query
            query_words = query_text.lower().strip().split()
            
            # Extract terms from query text
            i = 0
            while i < len(query_words):
                # Try 3-word phrases
                if i + 2 < len(query_words):
                    phrase = ' '.join(query_words[i:i+3])
                    if not any(word in stop_words for word in phrase.split()):
                        terms.append(phrase)
                
                # Try 2-word phrases
                if i + 1 < len(query_words):
                    phrase = ' '.join(query_words[i:i+2])
                    if not any(word in stop_words for word in phrase.split()):
                        terms.append(phrase)
                
                # Add individual words
                if query_words[i] not in stop_words:
                    terms.append(query_words[i])
                
                i += 1
        
        # Process location if provided
        if location:
            location_terms = location.lower().split(',')
            terms.extend([term.strip() for term in location_terms if term.strip()])
            
        # Process address if provided
        if address:
            address_parts = address.lower().split()
            # Keep important address parts
            terms.extend([part.strip('.,') for part in address_parts 
                        if part not in {'street', 'road', 'avenue', 'singapore'} 
                        and not part.isdigit()])
        
        # Remove duplicates while preserving order
        unique_terms = []
        seen = set()
        for term in terms:
            if term not in seen and len(term) > 1:  # Only keep terms longer than 1 character
                unique_terms.append(term)
                seen.add(term)
        
        logging.info(f"Extracted terms from query '{query_text}': {unique_terms}")
        return unique_terms

    def format_document_for_response(self, document: str, metadata: Dict) -> str:
        """Format document content for response"""
        # For Wikipedia content with sections
        if document.startswith("Summary:") or "History:" in document or "Description:" in document:
            sections = document.split('\n\n')
            relevant_info = []
            
            for section in sections:
                if any(section.startswith(prefix) for prefix in ["Summary:", "History:", "Description:"]):
                    cleaned_section = section.split(':', 1)[1].strip() if ':' in section else section
                    relevant_info.append(cleaned_section)
            
            return " ".join(relevant_info) if relevant_info else document
        
        # For scraped content
        return document.strip()

    def query_place(self, query_text: str, location: str = None, address: str = None, limit: int = 3):
        results = {"wikipedia": [], "singapore_attractions": []}
        
        try:
            # Get search terms
            search_terms = self.extract_key_terms(query_text, location, address)
            logging.info(f"Searching with terms: {search_terms}")
            
            # Search each collection
            for collection_name, collection in self.collections.items():
                if collection:
                    try:
                        # Do semantic search with both query and location
                        search_queries = [
                            query_text,  # Original query
                            " ".join(search_terms[:3])  # First few key terms
                        ]
                        
                        for search_query in search_queries:
                            query_results = collection.query(
                                query_texts=[search_query],
                                n_results=limit,
                                include=["documents", "metadatas"]
                            )
                            
                            if query_results and query_results['documents']:
                                documents = query_results['documents'][0]
                                metadatas = query_results['metadatas'][0]
                                
                                # Score and filter results
                                scored_results = []
                                for doc, metadata in zip(documents, metadatas):
                                    doc_lower = doc.lower()
                                    matches = 0
                                    
                                    # Count matches for each term
                                    for term in search_terms:
                                        if term in doc_lower:
                                            # Weight longer phrases higher
                                            term_words = len(term.split())
                                            matches += term_words  # More weight for longer matches
                                            logging.info(f"Found term '{term}' in document")
                                    
                                    if matches > 0:
                                        scored_results.append((matches, doc, metadata))
                                
                                # Add unique results
                                mapped_name = "wikipedia" if collection_name == "wikipedia_collection" else "singapore_attractions"
                                
                                for matches, doc, metadata in scored_results:
                                    formatted_doc = self.format_document_for_response(doc, metadata)
                                    if formatted_doc and formatted_doc not in results[mapped_name]:
                                        results[mapped_name].append(formatted_doc)
                                        logging.info(f"Adding document with {matches} matches to {mapped_name}")
                                        if len(results[mapped_name]) >= limit:
                                            break
                    
                    except Exception as e:
                        logging.error(f"Error querying collection {collection_name}: {str(e)}")
                        continue
            
            return results
            
        except Exception as e:
            logging.error(f"Error during query: {str(e)}")
            return results

    def score_document(self, doc: str, metadata: Dict, query: str, search_terms: List[str]) -> float:
        """Score document relevance with more detailed matching"""
        score = 0.0
        doc_lower = doc.lower()
        query_lower = query.lower()
        
        # Log document being scored
        logging.info(f"Scoring document: {doc[:100]}...")

        # Score exact phrase matches from the query
        if query_lower in doc_lower:
            score += 2.0
            logging.info(f"Exact query match found: +2.0")
        
        # Score individual term matches
        for term in search_terms:
            if term in doc_lower:
                # Weight longer terms (likely phrases) higher
                term_score = 0.3 * len(term.split())
                score += term_score
                logging.info(f"Term '{term}' found: +{term_score}")
        
        # Score metadata matches
        if metadata:
            if metadata.get('name', '').lower() in query_lower:
                score += 1.0
                logging.info("Metadata name match: +1.0")
            if metadata.get('attraction_type', '').lower() in query_lower:
                score += 0.5
                logging.info("Metadata type match: +0.5")
        
        logging.info(f"Final document score: {score}")
        return score

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
