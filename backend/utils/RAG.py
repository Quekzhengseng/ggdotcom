import os
import sys
import logging
from typing import Dict, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.store import WeaviateStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGManager:
    # def __init__(self):
    #     self.store = WeaviateStore()
    #     logging.basicConfig(level=logging.INFO)

    def __init__(self):
        self.store = None
        
    def _ensure_store(self):
        if not self.store:
            self.store = WeaviateStore()

    def query_place(self, place_name: str, limit: int = 5) -> Dict[str, List[str]]:
        """Query both collections for a place"""
        try:
            self._ensure_store()
            
            # Get results from both collections
            wiki_results = self.store.search_hybrid("WikipediaCollection", place_name, limit=limit)
            attr_results = self.store.search_hybrid("SingaporeAttraction", place_name, limit=limit)
            
            combined_results = {
                "wikipedia": [],
                "attractions": []
            }
            
            # Process Wikipedia results
            if wiki_results and hasattr(wiki_results, 'objects'):
                for obj in wiki_results.objects:
                    if obj.properties:
                        text = obj.properties.get("text", "").strip()
                        if text:
                            combined_results["wikipedia"].append(text)
            
            # Process Attraction results
            if attr_results and hasattr(attr_results, 'objects'):
                for obj in attr_results.objects:
                    if obj.properties:
                        text = obj.properties.get("text", "").strip()
                        if text:
                            combined_results["attractions"].append(text)
            
            return combined_results
            
        except Exception as e:
            logging.error(f"Error querying place {place_name}: {str(e)}")
            return {"wikipedia": [], "attractions": []}
        finally:
            if self.store:
                self.store.close()
                self.store = None  # Force recreation on next query

    # async def query_place(self, place_name: str, limit: int = 5) -> Dict[str, List[str]]:
    #     """Query both collections for relevant information about a place"""
    #     async with self.store.session() as store:
    #         try:
    #             # Query both collections concurrently
    #             wiki_results = await store.search_hybrid(
    #                 collection_name="WikipediaCollection",
    #                 query=place_name,
    #                 alpha=0.5,
    #                 limit=limit
    #             )
    #             if wiki_results is None:
    #                 logging.warning(f"Received None from WikipediaCollection query for {place_name}")

    #             attr_results = await store.search_hybrid(
    #                 collection_name="SingaporeAttraction",
    #                 query=place_name,
    #                 alpha=0.5,
    #                 limit=limit
    #             )
    #             if attr_results is None:
    #                 logging.warning(f"Received None from SingaporeAttraction query for {place_name}")

    #             combined_results = {
    #                 "wikipedia": [],
    #                 "attractions": []
    #             }

    #             # Process Wikipedia results
    #             if wiki_results and hasattr(wiki_results, 'objects'):
    #                 for obj in wiki_results.objects:
    #                     if obj.properties:
    #                         text = obj.properties.get("text", "").strip()
    #                         if text:
    #                             combined_results["wikipedia"].append(text)

    #             # Process Attraction results
    #             if attr_results and hasattr(attr_results, 'objects'):
    #                 for obj in attr_results.objects:
    #                     if obj.properties:
    #                         text = obj.properties.get("text", "").strip()
    #                         if text:
    #                             combined_results["attractions"].append(text)

    #             return combined_results

    #         except Exception as e:
    #             logging.error(f"Error querying place {place_name}: {str(e)}")
    #             return {"wikipedia": [], "attractions": []}

        
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
        # This would require geospatial search capabilities
        # For now, we'll return empty results
        return {"wikipedia": [], "attractions": []}
    
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