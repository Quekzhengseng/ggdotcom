import os
import sys
import logging
from typing import Dict, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.store import WeaviateStore
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGManager:
    def __init__(self):
        self.store = WeaviateStore()
        logging.basicConfig(level=logging.INFO)

    def _ensure_store(self):
        """Ensure store is initialized"""
        if not self.store:
            self.store = WeaviateStore()
    
    def _close_store(self):
        """Safely close store connection"""
        try:
            if self.store:
                self.store.close()
                self.store = None
        except Exception as e:
            logging.error(f"Error closing store: {e}")
        
    def _run_async(self, coro):
        """Helper method to run async operations"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


    def query_place(self, place_name: str, limit: int = 5) -> Dict[str, List[str]]:
        """Query both collections for relevant information about a place"""
        try:
            # Search in Wikipedia collection
            wiki_results = self.store.search_hybrid(
                collection_name="WikipediaCollection",
                query=place_name,
                alpha=0.5,
                limit=limit
            )
            
            # Process Wikipedia results
            combined_results = {
                "wikipedia": [],
                "attractions": []
            }
            
            if wiki_results and hasattr(wiki_results, 'objects'):
                for obj in wiki_results.objects:
                    if obj.properties:
                        text = obj.properties.get("text", "").strip()
                        if text:
                            combined_results["wikipedia"].append(text)
            
            # Try SingaporeAttraction collection
            try:
                attractions_results = self.store.search_hybrid(
                    collection_name="SingaporeAttraction",
                    query=place_name,
                    alpha=0.5,
                    limit=limit
                )
                
                if attractions_results and hasattr(attractions_results, 'objects'):
                    for obj in attractions_results.objects:
                        if obj.properties:
                            text = obj.properties.get("text", "").strip()
                            if text:
                                combined_results["attractions"].append(text)
            except Exception as e:
                logging.warning(f"Error querying SingaporeAttraction collection: {str(e)}")
            
            return combined_results
            
        except Exception as e:
            logging.error(f"Error querying place {place_name}: {str(e)}")
            return {"wikipedia": [], "attractions": []}
        finally:
            self.store.close()

    def query_by_location(self, lat: float, lng: float, radius: float = 500) -> Dict[str, List[str]]:
        """
        Query attractions near a specific location
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in meters
            
        Returns:
            Dict containing nearby attractions information
        """
        try:
            self._ensure_store()
            # ... rest of your existing code ...
            
        except Exception as e:
            logging.error(f"Error in location query: {str(e)}")
            return {"wikipedia": [], "attractions": []}
        finally:
            self._close_store()        

    
    def close(self):
        """Clean up resources"""
        self.store.close()

# Create a single instance to be imported
rag_manager = RAGManager()

# Flask app setup
if __name__ == '__main__':
    app = Flask(__name__)
    CORS(app)

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
