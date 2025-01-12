# import os
# from dotenv import load_dotenv

# load_dotenv()

# # CHROMA_HOST = os.getenv('CHROMA_HOST', 'https://ggdotcom-chromadb.onrender.com')
# # CHROMA_PORT = int(os.getenv('CHROMA_PORT', 8000))
# # CHROMA_API_KEY = os.getenv('CHROMA_API_KEY', '')
# # CHROMA_SSL = os.getenv('CHROMA_SSL', 'false').lower() == 'true'
# # FIREBASE_BUCKET = "ggdotcom-254aa.firebasestorage.app"

# CHROMA_HOST = 'ggdotcom-production.up.railway.app'  # Point to Railway project
# CHROMA_PORT = 443
# CHROMA_API_KEY = os.getenv('CHROMA_API_KEY', '')
# CHROMA_SSL = True
# FIREBASE_BUCKET = "ggdotcom-254aa.firebasestorage.app"

# def get_chroma_settings():
#     return {
#         "chroma_host": CHROMA_HOST,
#         "chroma_port": CHROMA_PORT,
#         "chroma_ssl": CHROMA_SSL,
#         "chroma_api_key": CHROMA_API_KEY,
#         "chroma_api_version": "v1",  # Add this line
#         "allow_reset": True,
#         "firebase_backup": get_firebase_backup()
#     }

# def get_firebase_backup():
#     return {
#         "bucket_name": FIREBASE_BUCKET,
#         "base_path": "ggdotcom/chromadb"
#     }


import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_LOCAL_PATH = os.path.join(os.path.dirname(__file__), 'utils', 'chroma_db')
FIREBASE_BUCKET = "ggdotcom-254aa.firebasestorage.app"

def get_chroma_settings():
    return {
        "persist_directory": CHROMA_LOCAL_PATH,
        "allow_reset": True,
        "firebase_backup": get_firebase_backup()
    }

def get_firebase_backup():
    return {
        "bucket_name": FIREBASE_BUCKET,
        "base_path": "ggdotcom/chromadb"
    }