# FastAPI and related imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import logging
import traceback
from typing import Optional

# Standard library imports
from typing import Optional, List, Dict, Any
from functools import partial
from datetime import datetime
import asyncio
import uuid
import io
import base64
import os
import logging

# Third-party service imports
import googlemaps
import openai
import uvicorn

# Firebase related imports
from firebase_admin import firestore
from firebase_init import initialize_firebase

# Custom utils imports
from utils.RAG import rag_manager
from utils.store import WeaviateStore

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation
class ChatRequest(BaseModel):
    location: Optional[str] = None
    text: Optional[str] = None
    image: Optional[str] = None
    visitedPlaces: Optional[List[str]] = []

class AudioRequest(BaseModel):
    text: str

class ImageRequest(BaseModel):
    photo_reference: str

class ScanRequest(BaseModel):
    location: str
    is_distance: Optional[bool] = False

class PhotoRequest(BaseModel):
    photo_reference: str

class PhotoResponse(BaseModel):
    base64_image: str

# Firebase initialization
bucket_name = 'ggdotcom-254aa.firebasestorage.app'
firebase_app = initialize_firebase(bucket_name)

# Firestore Client
db = firestore.client()

try:
    store = WeaviateStore()
except Exception as e:
    logging.error(f"Failed to initialize WeaviateStore: {e}")
    store = None

gmap = googlemaps.Client(key=os.getenv("GOOGLE_API_KEY"))
openai.api_key = os.getenv('OPENAI_API_KEY')

async def run_sync_in_background(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    func_with_args = partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, func_with_args)

@app.get("/")
async def home():
    return {"message": "Tour Guide API is running!"}

#method to fetch rag context

def get_rag_information(place_name: str, text: str = None, lat: float = None, lng: float = None) -> Dict[str, List[str]]:
    """Fetch contextual information"""
    try:
        search_terms = []
        if ',' in place_name:
            location_parts = place_name.split(',')[0].strip()
            search_terms.append(location_parts)
        else:
            search_terms.append(place_name)
            
        if text:
            words = text.split()
            for i in range(len(words)-1):
                if words[i][0].isupper():
                    search_terms.append(f"{words[i]} {words[i+1]}")
            search_terms.extend([word for word in words if word[0].isupper()])
        
        search_terms = list(dict.fromkeys(search_terms))
        logging.info(f"Searching RAG with terms: {search_terms}")
        
        combined_results = {"wikipedia": [], "attractions": []}
        
        for term in search_terms:
            results = rag_manager.query_place(term)
            if results:
                for key in results:
                    existing_results = set(combined_results[key])
                    combined_results[key].extend([r for r in results[key] if r not in existing_results])
        
        return combined_results
        
    except Exception as e:
        logging.error(f"Error in RAG query: {str(e)}")
        return {"wikipedia": [], "attractions": []}
    


# async def get_rag_information(place_name: str, text: str = None, lat: float = None, lng: float = None) -> Dict[str, List[str]]:
#     """Async function to fetch contextual information"""
#     try:
#         search_terms = []
#         if ',' in place_name:
#             location_parts = place_name.split(',')[0].strip()
#             search_terms.append(location_parts)
#         else:
#             search_terms.append(place_name)
            
#         if text:
#             words = text.split()
#             for i in range(len(words)-1):
#                 if words[i][0].isupper():
#                     search_terms.append(f"{words[i]} {words[i+1]}")
#             search_terms.extend([word for word in words if word[0].isupper()])
        
#         search_terms = list(dict.fromkeys(search_terms))
#         logging.info(f"Searching RAG with terms: {search_terms}")
        
#         combined_results = {"wikipedia": [], "attractions": []}
        
#         # Ensure query_place is awaited correctly
#         for term in search_terms:
#             results = await rag_manager.query_place(term)
#             if results:  # Check if results are not None or empty
#                 for key in results:
#                     existing_results = set(combined_results[key])
#                     combined_results[key].extend([r for r in results[key] if r not in existing_results])
        
#         return combined_results
        
#     except Exception as e:
#         logging.error(f"Error in RAG query: {str(e)}")
#         return {"wikipedia": [], "attractions": []}

#method to mix prompt with rag context
def create_chat_messages(prompt: str, context: Dict[str, List[str]], is_image: bool = False, image_data: str = None) -> List[dict]:
    messages = []
    
    # System message
    system_msg = {
        "role": "system",
        "content": "You are a knowledgeable Singapore Tour Guide. Use the provided context to give accurate, engaging responses, but maintain a natural conversational tone."
    }
    messages.append(system_msg)
    
    # Add context as a separate message if available
    if context:
        context_msg = []
        
        # Add Wikipedia information
        if context.get("wikipedia"):
            context_msg.append("Historical and Wikipedia Information:")
            for fact in context["wikipedia"]:
                context_msg.append(fact)
        
        # Add attraction information
        if context.get("attractions"):
            context_msg.append("\nLocal Attraction Information:")
            for fact in context["attractions"]:
                context_msg.append(fact)
        
        if context_msg:
            messages.append({
                "role": "system",
                "content": "\n".join(context_msg)
            })
    
    # Add the user's prompt
    if is_image and image_data:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data}}
            ]
        })
    else:
        messages.append({
            "role": "user",
            "content": prompt
        })
    
    return messages

# main route for frontend integration
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        #fetch data from user
        location = request.location
        image = request.image
        text = request.text
        visited_places = request.visitedPlaces or []

        if not any([location, image, text]):
            raise HTTPException(status_code=400, detail="No data provided")


        # Need factor cases with location, image (Base64)
        # if there is user input, add in to DB as well

        
        # location = data.get('location')
        # image = data.get('image')
        # text = data.get('text')
        print(f"Location: {location}")
        # print(f"Image: {image}")
        print(f"Text: {text}")

        # LOCATION WITH IMAGE WITH TEXT
        if location and text and image:
            try:
                #Get text data
                text_data = text

                #Get location data
                # location = data.get('location', "")
                print(f"Location Received: {location}")
                lat, lng = map(float, location.split(','))

                # Get address using Google Maps
                gmaps_result = gmap.reverse_geocode((lat, lng))

                if gmaps_result and len(gmaps_result) > 0:
                    address = gmaps_result[0]['formatted_address']
                else:
                    address = location  # Fallback to coordinates if geocoding fails
                
                print(f"Address: {address}")

            except Exception as e:
                print(f"Geocoding error: {str(e)}")
            
            image_data = image

            try:
                # Check if it already has the prefix
                if image_data.startswith('data:image/jpeg;base64,'):
                    # Remove the prefix to clean the base64 string
                    base64_string = image_data.replace('data:image/jpeg;base64,', '')
                else:
                    base64_string = image_data
                    
                # Remove any whitespace or newlines
                base64_string = base64_string.strip().replace('\n', '').replace('\r', '')
                
                # Add the prefix back to image_data
                image_data = f"data:image/jpeg;base64,{base64_string}"
            except Exception as e:
                print(f"Error cleaning base64 image: {str(e)}")
                raise ValueError("Invalid base64 image data")

            context = get_rag_information(address)
            print("ADDED CONTEXT", context)

            #Initalize prompt with text
            prompt = f"""You are a Singapore Tour Guide, please provide details regarding the text and photo that is given.
                You are also given the user's address of {address} to provide more context in regards to the users location.
                Do not mention the address in your answer.
                Answer what is given in the user's text and photo and describe in detail regarding history or context that is applicable.
                Here is the Users text: {text_data}"""

            print(prompt)
            # Create messages with context
            messages = create_chat_messages(prompt, context, is_image=True)
                
            try:
                # create USER msg data for firestore
                message_data = {
                    'timestamp': datetime.now(),
                    'message_Id': "",
                    'chatText': text_data,
                    'image': "",
                    'location': location,
                    'userCheck': "true",
                    'repeat': 0,
                }

                #Add to firestore
                db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
                .collection('messages').add(message_data)
                
                print("Success: Added to Firestore")

            except Exception as e:
                print(f"Error: Failed to add to Firestore - {str(e)}")

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                
                # DEPREICIATED CAN UNCOMMENT THIS BLOCK OF CODE and replace the messages right above to compare w and w/o RAG
                # [
                #     {
                #         "role": "user",
                #         "content": [
                #             {
                #                 "type": "text",
                #                 "text": prompt,
                #             }, 
                #             {
                #                 "type": "image_url",
                #                 "image_url": {
                #                     "url": image_data
                #                 }
                #             }
                #         ],
                #     },
                # ],
                max_tokens=500,
                temperature=0
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")

            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text
            }

            try:
                # create REPLY msg data for firestore
                message_data = {
                    'timestamp': datetime.now(),
                    'message_Id': "",
                    'chatText': response_text,
                    'image': image_data,
                    'location': location,
                    'userCheck': "false",
                    'repeat': 0,
                }

                #Add to firestore
                db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
                .collection('messages').add(message_data)
                
                print("Success: Added to Firestore")
            except Exception as e:
                print(f"Error: Failed to add to Firestore - {str(e)}")

            return JSONResponse(content=response_data)
        #END LOCATION WITH TEXT WITH IMAGE -------------------------------------------------------------

        #LOCATION WITH TEXT -------------------------------------------------------------
        elif location and text:
            try:
                #Get text data
                text_data = text

                #Get location data
                # location = data.get('location', "")
                print(f"Location Received: {location}")
                lat, lng = map(float, location.split(','))

                # Get address using Google Maps
                gmaps_result = gmap.reverse_geocode((lat, lng))

                if gmaps_result and len(gmaps_result) > 0:
                    address = gmaps_result[0]['formatted_address']
                else:
                    address = location  # Fallback to coordinates if geocoding fails
                
                print(f"Address: {address}")

                #Get by distance instead
                places_result = gmap.places_nearby(
                    location=(lat, lng),
                    rank_by='distance',  # This will sort by distance automatically
                    type=['tourist_attraction', 'museum', 'art_gallery', 'park', 'shopping_mall', 
                        'hindu_temple', 'church', 'mosque', 'place_of_worship', 
                        'amusement_park', 'aquarium', 'zoo', 
                        'restaurant', 'cafe'],
                    language='en'
                )

                # Initialize place and number of repeats variable
                selected_place = None

                if places_result.get('results'):
                    for place in places_result['results']:
                        selected_place = place['name']
                        print("SELECTED PLACE: " , selected_place)
                        break

                if not selected_place:
                    selected_place = address
            
            except Exception as e:
                print(f"Geocoding error: {str(e)}")
            search_term = selected_place if selected_place else address
            context = get_rag_information(search_term, text=text_data, lat=lat, lng=lng)
            print("ADDED CONTEXT", context)

            # Initialise prompt
            prompt = f"""
                Due to insufficient information in the RAG, if the location provided below differs greatly from the context in the RAG, completely disregard the RAG and craft original content about the provided location instead.

                You are a friendly Singapore Tour Guide giving a walking tour. If {selected_place} matches with {address}, this means you are in a residential or developing area. 
                If both are the same, you might have talked about this location already.
                If empty, it means this is the first time you are talking about it.  
                If not empty, do not state the same thing again. Talk about something else about the area.

                For residential/developing areas:
                - Focus exclusively on the neighborhood or district, disregarding unrelated RAG content.
                - Describe the most interesting aspects of the neighborhood or district you're in.
                - Mention any nearby parks, nature areas, or community spaces.
                - Include interesting facts about the area's development or future plans.
                - Highlight what makes this area unique in Singapore.

                For tourist landmarks:
                - Name and describe the specific landmark.
                - Use the RAG only if it directly mentions the landmark and matches the provided location. If the RAG does not match, ignore it entirely.
                - Share its historical significance and background.
                - Explain its cultural importance in Singapore.
                - Describe unique architectural features.
                - Include interesting facts that make it special.

                The user have asked a question here: {text_data} Answer what is given in the user's text and describe in detail regarding history or context that is applicable.
                """

            print(prompt)
            messages = create_chat_messages(prompt, context)
                
            try:
                # create USER msg data for firestore
                message_data = {
                    'timestamp': datetime.now(),
                    'message_Id': "",
                    'chatText': text_data,
                    'image': "",
                    'location': location,
                    'userCheck': "true",
                    'repeat': 0,
                }

                #Add to firestore
                db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
                .collection('messages').add(message_data)
                
                print("Success: Added to Firestore")

            except Exception as e:
                print(f"Error: Failed to add to Firestore - {str(e)}")

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")

            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text
            }

            try:
                # create REPLY msg data for firestore
                message_data = {
                    'timestamp': datetime.now(),
                    'message_Id': "",
                    'chatText': response_text,
                    'image': "",
                    'location': location,
                    'userCheck': "false",
                    'repeat': 0,
                }

                #Add to firestore
                db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
                .collection('messages').add(message_data)
                
                print("Success: Added to Firestore")
            except Exception as e:
                print(f"Error: Failed to add to Firestore - {str(e)}")

            return JSONResponse(content=response_data)
        #END LOCATION WITH TEXT -------------------------------------------------------------
        
        #LOCATION WITH IMAGE CHECK ----------------------------------------
        elif location and image:
            try:
                image_data = image
                # location = data.get('location', "")
                print(f"Location Received: {location}")
                lat, lng = map(float, location.split(','))

                # Get address using Google Maps
                gmaps_result = gmap.reverse_geocode((lat, lng))
                
                if gmaps_result and len(gmaps_result) > 0:
                    address = gmaps_result[0]['formatted_address']
                else:
                    address = location  # Fallback to coordinates if geocoding fails
                
                print(f"Address: {address}")

            except Exception as e:
                print(f"Geocoding error: {str(e)}")
            search_term = selected_place if selected_place else address
            context = get_rag_information(search_term, lat=lat, lng=lng)
            print("ADDED CONTEXT", context)
            #Initalize prompt with IMAGE
            prompt = f"""You are a Singapore Tour Guide, please provide details regarding the photo that is given.
                You are also given the user's address of {address} to provide more context in regards to where the photo is taken.
                Start by saying, You see [Point of interest]. Do not mention anything about the address in your answer.
                Include only what is given in the photo and describe in detail regarding history or context."""


            messages = create_chat_messages(prompt, context, is_image=True, image_data=image_data)

            try:
                # Check if it already has the prefix
                if image_data.startswith('data:image/jpeg;base64,'):
                    # Remove the prefix to clean the base64 string
                    base64_string = image_data.replace('data:image/jpeg;base64,', '')
                else:
                    base64_string = image_data
                    
                # Remove any whitespace or newlines
                base64_string = base64_string.strip().replace('\n', '').replace('\r', '')
                
                # Add the prefix back to image_data
                image_data = f"data:image/jpeg;base64,{base64_string}"
            except Exception as e:
                print(f"Error cleaning base64 image: {str(e)}")
                raise ValueError("Invalid base64 image data")

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                
                # DEPRECIATED
                # [
                #     {
                #         "role": "user",
                #         "content": [
                #             {
                #                 "type": "text",
                #                 "text": prompt,
                #             }, 
                #             {
                #                 "type": "image_url",
                #                 "image_url": {
                #                     "url": image_data
                #                 }
                #             }
                #         ],
                #     },
                # ],
                max_tokens=500,
                temperature=0
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")
                
            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text
            }

            try:
                # create msg data for firestore
                message_data = {
                    'timestamp': datetime.now(),
                    'message_Id': "",
                    'chatText': response_text,
                    'image': image_data,
                    'location': location,
                    'userCheck': "false",
                    'repeat': 0,
                }

                #Add to firestore
                db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
                .collection('messages').add(message_data)
                
                print("Success: Added to Firestore")
            except Exception as e:
                print(f"Error: Failed to add to Firestore - {str(e)}")

            return JSONResponse(content=response_data)
        #END LOCATION WITH IMAGE -------------------------------------------------------------

        #PURE LOCATION CHECK ----------------------------------------------------------------
        else:
            try:
                # Parse location string into lat, lng
                # location = data.get('location', "")
                print(f"Location Received: {location}")
                lat, lng = map(float, location.split(','))
                
                # Get address using Google Maps
                gmaps_result = gmap.reverse_geocode((lat, lng))
                
                if gmaps_result and len(gmaps_result) > 0:
                    address = gmaps_result[0]['formatted_address']
                else:
                    address = location  # Fallback to coordinates if geocoding fails
                
                print(f"Address: {address}")

                # Get nearby tourist attractions
                # places_result = gmap.places_nearby(
                #     location=(lat, lng),
                #     radius= 500,  # 500m radius
                #     type=['tourist_attraction', 'museum', 'art_gallery', 'park', 'shopping_mall', 
                #         'hindu_temple', 'church', 'mosque', 'place_of_worship', 
                #         'amusement_park', 'aquarium', 'zoo', 
                #         'restaurant', 'cafe'],  # Specifically search for tourist attractions
                #     language='en'  # Ensure English results
                #         )
            
                #Get by distance instead
                places_result = gmap.places_nearby(
                    location=(lat, lng),
                    rank_by='distance',  # This will sort by distance automatically
                    type=['tourist_attraction', 'museum', 'art_gallery', 'park', 'shopping_mall', 
                        'hindu_temple', 'church', 'mosque', 'place_of_worship', 
                        'amusement_park', 'aquarium', 'zoo', 
                        'restaurant', 'cafe'],
                    language='en'
                )

                if visited_places:
                    landmarks = visited_places
                else:
                    landmarks = []

                print("VISITED PLACES: " , landmarks)

                # Initialize place and number of repeats variable
                selected_place = None
                repeat = 0
                past_messages = []

                if places_result.get('results'):
                    for place in places_result['results']:
                        if (place['name'] in landmarks) :
                            continue
                        else :
                            landmarks.append(place['name'])
                            selected_place = place['name']
                            print("SELECTED PLACE: " , selected_place)
                            break
                            
                if not selected_place:
                    selected_place = address
                    #If place is repeated, start the firestore collection to retrieve past messages that was send out
                    most_recent_message = (
                                            db.collection('tour')
                                            .document("yDLsVQhwoDF9ZHoG0Myk")
                                            .collection('messages')
                                            .order_by('timestamp', direction='DESCENDING')
                                            .limit(1)
                                            .stream()
                                                )
                    for message in most_recent_message:
                        message_data = message.to_dict()
                        repeat = message_data.get('repeat')
                    #Retrieve that number of past messages that will be added to the prompt
                    repeated_messages = (
                                            db.collection('tour')
                                            .document("yDLsVQhwoDF9ZHoG0Myk")
                                            .collection('messages')
                                            .order_by('timestamp', direction='DESCENDING')
                                            .limit(repeat)
                                            .stream()
                                                )
                    chat_texts = []
                    for message in repeated_messages:
                        chat_text = message.to_dict().get('chatText', "")
                        if chat_text:
                            chat_texts.append(chat_text)
                    past_messages = " ".join(chat_texts)
                    repeat += 1


            except Exception as e:
                print(f"Geocoding error: {str(e)}")

            context = get_rag_information(selected_place)
            print("ADDED CONTEXT", context)

            # Add address to prompt
            prompt = f"""
                Due to insufficient information in the RAG, if the location provided below differs greatly from the context in the RAG, completely disregard the RAG and craft original content about the provided location instead.

                You are a friendly Singapore Tour Guide giving a walking tour. If {selected_place} matches with {address}, this means you are in a residential or developing area. 
                If both are the same, you might have talked about this location already. Here are past messages you have sent: [{past_messages}]. 
                If empty, it means this is the first time you are talking about it.  
                If not empty, do not state the same thing again. Talk about something else about the area.

                For residential/developing areas:
                - Focus exclusively on the neighborhood or district, disregarding unrelated RAG content.
                - Describe the most interesting aspects of the neighborhood or district you're in.
                - Mention any nearby parks, nature areas, or community spaces.
                - Include interesting facts about the area's development or future plans.
                - Highlight what makes this area unique in Singapore.

                For tourist landmarks:
                - Name and describe the specific landmark.
                - Share its historical significance and background.
                - Explain its cultural importance in Singapore.
                - Describe unique architectural features.
                - Include interesting facts that make it special.

                Start with "You see [Point of interest/Area name]" and keep the tone friendly and conversational, as if speaking to tourists in person. Don't mention exact addresses or coordinates. Use the RAG only if it directly mentions the landmark and matches the provided location. If the RAG does not match, ignore it entirely.
                """

            
            print("PROMPT", prompt)

            messages = create_chat_messages(prompt, context)

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                
                # [
                #     {"role": "user", "content": prompt}
                # ],
                max_tokens=500,
                temperature=0.5
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")

            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text,
                'visitedPlace' : selected_place
            }

            try:
                # create msg data for firestore
                message_data = {
                    'timestamp': datetime.now(),
                    'message_Id': "",
                    'chatText': response_text,
                    'image': "",
                    'location': location,
                    'userCheck': "false",
                    'repeat': repeat,
                }

                #Add to firestore
                db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
                .collection('messages').add(message_data)
                
                print("Success: Added to Firestore")
            except Exception as e:
                print(f"Error: Failed to add to Firestore - {str(e)}")

            return JSONResponse(content=response_data)

    except Exception as e:
        logging.error("Error in /chat endpoint", exc_info=True)
        return JSONResponse(content={'error': str(e)}, status_code=500)

    
    finally:
        # Close connections if any were opened during this request
        if 'store' in locals():
            store.close()
    #END PURE LOCATION CHECK ----------------------------------------------------------------




@app.post("/chat2")
async def chat2(request: ChatRequest):

    try:
            #fetch data from user
        # Need factor cases with location, image (Base64)
        # if there is user input, add in to DB as well
        location = request.location
        image_data = request.image
        text = request.text
        visited_places = request.visitedPlaces or []

        if not any([location, image_data, text]):
            raise HTTPException(status_code=400, detail="No data provided")

        
        # location = data.get('location')
        # image_data = data.get('image')
        # text = data.get('text')

    except Exception as e:
        print(f"Error: Failed - {str(e)}")

    if location and text and image_data:
        try:
            print(f"Location Received: {location}")
            lat, lng = map(float, location.split(','))

            # Get address using Google Maps
            selected_place = gmap.reverse_geocode((lat, lng))[0]['formatted_address']

            try:
                # Check if it already has the prefix
                if image_data.startswith('data:image/jpeg;base64,'):
                    # Remove the prefix to clean the base64 string
                    base64_string = image_data.replace('data:image/jpeg;base64,', '')
                else:
                    base64_string = image_data
                    
                # Remove any whitespace or newlines
                base64_string = base64_string.strip().replace('\n', '').replace('\r', '')
                
                # Add the prefix back to image_data
                image_data = f"data:image/jpeg;base64,{base64_string}"
            except Exception as e:
                print(f"Error cleaning base64 image: {str(e)}")
                raise ValueError("Invalid base64 image data")

            context = get_rag_information(selected_place)
            print("ADDED CONTEXT", context)

            # Add address to prompt
            prompt = f"""
                Due to insufficient information in the RAG, if the location provided below differs greatly from the context in the RAG, completely disregard the RAG and craft original content about the provided location instead.

                You are a friendly Singapore Tour Guide giving a walking tour. The place that the tourist has selected is {selected_place} You are also provided with a photo.


                Answer the question that the tourist has asked here. {text} Use the RAG only if it directly mentions the landmark and matches the provided location. 
                If the RAG does not match, ignore it entirely.
                """

            print("PROMPT", prompt)

            messages = create_chat_messages(prompt, context, is_image=True)

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")

            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text
            }

            #Create User message for firestore
            message_data = {
                'timestamp': datetime.now(),
                'chatText': text,
                'image': image_data,
                'location': location,
                'userCheck': "true",
            }

            #Add to firestore
            db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
            .collection('messages2').add(message_data)

            # create ChatGPT reply for firestore
            message_data = {
                'timestamp': datetime.now(),
                'chatText': response_text,
                'image': "",
                'location': location,
                'userCheck': "false",
            }

            #Add to firestore
            db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
            .collection('messages2').add(message_data)

            return JSONResponse(content=response_data)

        except Exception as e:
            print(f"Error: Failed - {str(e)}")

        # In your chat endpoint finally block:
        finally:
            # Close connections if any were opened during this request
            if 'store' in locals():
                store.close()  # Note the await here
    elif location and text:
        try:
            print(f"Location Received: {location}")
            lat, lng = map(float, location.split(','))

            # Get address using Google Maps
            selected_place = gmap.reverse_geocode((lat, lng))[0]['formatted_address']

            context = get_rag_information(selected_place)
            print("ADDED CONTEXT", context)

            # Add address to prompt
            prompt = f"""
                Due to insufficient information in the RAG, if the location provided below differs greatly from the context in the RAG, completely disregard the RAG and craft original content about the provided location instead.

                You are a friendly Singapore Tour Guide giving a walking tour. The place that the tourist has selected is {selected_place}. 

                Answer the question that the tourist has asked here. {text} Use the RAG only if it directly mentions the landmark and matches the provided location. 
                If the RAG does not match, ignore it entirely.
                """

            print("PROMPT", prompt)

            messages = create_chat_messages(prompt, context)

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.5
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")

            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text,
            }
    
            #Create User message for firestore
            message_data = {
                'timestamp': datetime.now(),
                'chatText': text,
                'image': "",
                'location': location,
                'userCheck': "true",
            }

            #Add to firestore
            db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
            .collection('messages2').add(message_data)

            # create ChatGPT reply for firestore
            message_data = {
                'timestamp': datetime.now(),
                'chatText': response_text,
                'image': "",
                'location': location,
                'userCheck': "false",
            }

            #Add to firestore
            db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
            .collection('messages2').add(message_data)

            return JSONResponse(content=response_data)

        except Exception as e:
            print(f"Error: Failed - {str(e)}")

        # In your chat endpoint finally block:
        finally:
            # Close connections if any were opened during this request
            if 'store' in locals():
                store.close()  # Note the await here
    elif location and image_data:
        try:
            print(f"Location Received: {location}")
            lat, lng = map(float, location.split(','))

            # Get address using Google Maps
            selected_place = gmap.reverse_geocode((lat, lng))[0]['formatted_address']

            context = get_rag_information(selected_place)
            print("ADDED CONTEXT", context)

            # Add address to prompt
            prompt = f"""
                Due to insufficient information in the RAG, if the location provided below differs greatly from the context in the RAG, completely disregard the RAG and craft original content about the provided location instead.

                You are a friendly Singapore Tour Guide giving a walking tour. The place that the tourist has selected is {selected_place}. You are also provided with a photo.

                For residential/developing areas:
                - Focus exclusively on the neighborhood or district, disregarding unrelated RAG content.
                - Describe the most interesting aspects of the neighborhood or district you're in.
                - Mention any nearby parks, nature areas, or community spaces.
                - Include interesting facts about the area's development or future plans.
                - Highlight what makes this area unique in Singapore.

                For tourist landmarks:
                - Name and describe the specific landmark.
                - Share its historical significance and background.
                - Explain its cultural importance in Singapore.
                - Describe unique architectural features.
                - Include interesting facts that make it special.

                Start with "You see [Point of interest/Area name] in the photo" and keep the tone friendly and conversational, as if speaking to tourists in person.
                Don't mention exact addresses or coordinates. Use the RAG only if it directly mentions the landmark and matches the provided location. 
                If the RAG does not match, ignore it entirely.
                """

            print("PROMPT", prompt)

            messages = create_chat_messages(prompt, context, is_image=True)

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")

            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text,
            }

            #Create User message for firestore
            message_data = {
                'timestamp': datetime.now(),
                'chatText': "",
                'image': image_data,
                'location': location,
                'userCheck': "true",
            }

            #Add to firestore
            db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
            .collection('messages2').add(message_data)

            # create ChatGPT reply for firestore
            message_data = {
                'timestamp': datetime.now(),
                'chatText': response_text,
                'image': "",
                'location': location,
                'userCheck': "false",
            }

            #Add to firestore
            db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
            .collection('messages2').add(message_data)

            return JSONResponse(content=response_data)


        except Exception as e:
            print(f"Error: Failed - {str(e)}")
        # In your chat endpoint finally block:
        finally:
            # Close connections if any were opened during this request
            if 'store' in locals():
                store.close()  # Note the await here
    else:
        try:
            print(f"Location Received: {location}")
            lat, lng = map(float, location.split(','))

            # Get address using Google Maps
            selected_place = gmap.reverse_geocode((lat, lng))[0]['formatted_address']

            # context = get_rag_information(selected_place)
            # print("ADDED CONTEXT", context)

            # Add address to prompt
            prompt = f"""
                Due to insufficient information in the RAG, if the location provided below differs greatly from the context in the RAG, completely disregard the RAG and craft original content about the provided location instead.

                You are a friendly Singapore Tour Guide giving a walking tour. The place that the tourist has selected is {selected_place}.

                For residential/developing areas:
                - Focus exclusively on the neighborhood or district, disregarding unrelated RAG content.
                - Describe the most interesting aspects of the neighborhood or district you're in.
                - Mention any nearby parks, nature areas, or community spaces.
                - Include interesting facts about the area's development or future plans.
                - Highlight what makes this area unique in Singapore.

                For tourist landmarks:
                - Name and describe the specific landmark.
                - Share its historical significance and background.
                - Explain its cultural importance in Singapore.
                - Describe unique architectural features.
                - Include interesting facts that make it special.

                Start with "You see [Point of interest/Area name]" and keep the tone friendly and conversational, as if speaking to tourists in person.
                Don't mention exact addresses or coordinates. Use the RAG only if it directly mentions the landmark and matches the provided location. 
                If the RAG does not match, ignore it entirely.
                """

            print("PROMPT", prompt)

            messages = create_chat_messages(prompt, context)

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.5
            )

            # Extract response text
            response_text = response.choices[0].message.content

            print(f"Response: {response_text}")

            # Create response object
            response_data = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response_text,
            }

            # create ChatGPT reply for firestore
            message_data = {
                'timestamp': datetime.now(),
                'chatText': response_text,
                'image': "",
                'location': location,
                'userCheck': "false",
            }

            #Add to firestore
            db.collection("tour").document("yDLsVQhwoDF9ZHoG0Myk")\
            .collection('messages2').add(message_data)

        except Exception as e:
            print(f"Error: Failed - {str(e)}")

        # In your chat endpoint finally block:
        finally:
            # Close connections if any were opened during this request
            if 'store' in locals():
                store.close()  # Note the await here

# @app.route('/image', methods = ['POST'])
@app.route("/image", methods=["POST"])
async def photo(        
        photo_reference: str = Header(..., description="Google Places photo reference"),
        max_width: Optional[int] = Header(400, description="Maximum width of the image") 
                ) -> PhotoResponse:
    try:

        image_data = bytearray()
        
        for chunk in gmap.places_photo(
            photo_reference=photo_reference,
            max_width=max_width
        ):
            if chunk:
                image_data.extend(chunk)
                
        if not image_data:
            raise ValueError("No image data received")

        base64_image = base64.b64encode(image_data).decode('utf-8')

        return {"base64_image": base64_image}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve photo: {str(e)}"
        )

@app.post("/scan")
async def scan(request: ScanRequest):
    try:
        lat, lng = map(float, request.location.split(','))
        
        places_result = gmap.places_nearby(
            location=(lat, lng),
            rank_by='distance' if not request.is_distance else None,
            radius=500 if request.is_distance else None,
            type=['tourist_attraction', 'museum', 'art_gallery', 'park', 'shopping_mall', 
                  'hindu_temple', 'church', 'mosque', 'place_of_worship', 
                  'amusement_park', 'aquarium', 'zoo', 
                  'restaurant', 'cafe'],
            language='en'
        )
        
        all_locations = []
        if places_result.get('results'):
            for place in places_result['results']:
                all_locations.append([
                    place['name'], 
                    place['geometry']['location'], 
                    place['photos'][0]['photo_reference']
                ])

        return {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'locations': all_locations,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve scan results: {str(e)}"
        )


@app.get("/messages")
async def retrieve():
    try:
        messages = await run_sync_in_background(
            db.collection('tour').document("yDLsVQhwoDF9ZHoG0Myk")
            .collection('messages')
            .order_by('timestamp', direction='DESCENDING')
            .stream
        )
        message_list = [msg.to_dict() for msg in messages]
        return JSONResponse(content=message_list)
    except Exception as e:
        logging.error(f"Error in /messages endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/image", response_model=PhotoResponse)
async def photo(
    photo_reference: str = Header(..., description="Google Places photo reference"),
    max_width: Optional[int] = Header(400, description="Maximum width of the image")
):
    """
    Retrieve a photo from Google Places API and return it as a base64-encoded string.
    The photo reference should be provided in the request headers.
    """
    try:
        # Log the start of the request
        logging.info(f"Processing photo request with reference: {photo_reference[:20]}...")
        
        # Initialize image data buffer
        image_data = bytearray()
        
        # Retrieve photo chunks from Google Maps API
        try:
            for chunk in gmap.places_photo(
                photo_reference=photo_reference,
                max_width=max_width
            ):
                if chunk:
                    image_data.extend(chunk)
        except Exception as photo_error:
            logging.error(f"Error retrieving photo from Google Maps API: {photo_error}")
            logging.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve photo from Google Maps: {str(photo_error)}"
            )
                
        if not image_data:
            logging.error("No image data received from Google Maps API")
            raise HTTPException(
                status_code=404,
                detail="No image data received from Google Maps API"
            )

        # Encode image data to base64
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            logging.info("Successfully processed and encoded image")
            
            # Return response using Pydantic model
            return PhotoResponse(base64_image=base64_image)
            
        except Exception as encode_error:
            logging.error(f"Error encoding image data: {encode_error}")
            logging.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to encode image data: {str(encode_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected errors with full traceback
        logging.error(f"Unexpected error in photo endpoint: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/test")
async def test(request: ChatRequest):
    try:
        text = request.text
        if not text:
            return JSONResponse(content={"error": "No text provided"}, status_code=400)
        response_data = {
            "id": uuid.uuid4().hex,
            "timestamp": datetime.now().isoformat(),
            "text": text
        }
        return JSONResponse(content=response_data)
    except Exception as e:
        logging.error(f"Error in /test endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/audio")
async def audio(request: AudioRequest):
    try:
        text = request.text
        response = openai.Audio.create(model="tts-1", voice="alloy", input=text)
        audio_buffer = io.BytesIO()
        for chunk in response.iter_bytes():
            audio_buffer.write(chunk)
        audio_buffer.seek(0)
        return StreamingResponse(audio_buffer, media_type="audio/mpeg")
    except Exception as e:
        logging.error(f"Error in /audio endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# for uptimerobot ping to keep server active
@app.api_route("/ping", methods=["GET", "HEAD"])
async def ping():
    return {"message": "Service is up!"}

# Configure for gunicorn
# if __name__ == "__main__":
#     # If running directly
#     # port = int(os.environ.get("PORT", 10000))
#     # app.run(host="0.0.0.0", port=port)
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)

else:
    # For gunicorn
    application = app
