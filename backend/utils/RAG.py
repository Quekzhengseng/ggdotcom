import os
import sys
import logging
from typing import Dict, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.store import WeaviateStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGManager:
    def __init__(self):
        self.store = WeaviateStore()
        logging.basicConfig(level=logging.INFO)

    def query_place(self, place_name: str, limit: int = 5) -> Dict[str, List[str]]:
        """
        Query both collections for relevant information about a place
        
        Args:
            place_name: Name of the place to search for
            limit: Maximum number of results to return per collection
                
        Returns:
            Dict containing results from both collections
        """
        try:
            # Search in Wikipedia collection first
            wiki_results = self.store.search_hybrid(
                collection_name="WikipediaCollection",
                query=place_name,
                alpha=0.5,
                limit=2
            )
            
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
            
            # Only try SingaporeAttraction if it exists
            try:
                attractions_results = self.store.search_hybrid(
                    collection_name="SingaporeAttraction",
                    query=place_name,
                    alpha=0.5,
                    limit=limit
                )
                
                # Process Attractions results
                if attractions_results and hasattr(attractions_results, 'objects'):
                    for obj in attractions_results.objects:
                        if obj.properties:
                            text = obj.properties.get("text", "").strip()
                            if text:
                                combined_results["attractions"].append(text)
            except Exception as e:
                logging.warning(f"Error querying SingaporeAttraction collection (may not exist): {str(e)}")
            
            logging.info(f"Found {len(combined_results['wikipedia'])} Wikipedia results and {len(combined_results['attractions'])} attraction results")
            return combined_results
                
        except Exception as e:
            logging.error(f"Error querying place {place_name}: {str(e)}")
            return {"wikipedia": [], "attractions": []}
        
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
