import os
from dotenv import find_dotenv, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import json

# Load environment variables from .env file
load_dotenv(find_dotenv())

# API Environment Variables

API_HOST = str(os.environ.get('API_HOST'))
API_PORT = int(os.environ.get('API_PORT'))

# MongoDB Database Variables

MONGO_URI = str(os.environ.get('MONGO_URI'))
try:
    client = AsyncIOMotorClient(MONGO_URI)
    print("Connected to DataBase!")
except Exception as e:
    print(f"Error connecting to database: {e}")
db = client["dev_platform"]
user_collection = db["users"]
images_collection = db["images"]
posts_collection = db["posts"]
communities_collection = db["communities"]
community_collection = db["community"]
reports_collection = db["reports"]
read_posts_collection = db["read_posts"]
banned_collection = db["banned"]

# AI model variables

MODEL_TO_USE = str(os.environ.get('MODEL_TO_USE'))

# Email Variables
MAIL_USERNAME = str(os.environ.get('MAIL_USERNAME'))
MAIL_PASSWORD = str(os.environ.get('MAIL_PASSWORD'))
MAIL_FROM = str(os.environ.get('MAIL_FROM'))
MAIL_PORT = int(os.environ.get('MAIL_PORT'))
MAIL_SERVER = str(os.environ.get('MAIL_SERVER'))
MAIL_STARTTLS = os.environ.get('MAIL_STARTTLS')
MAIL_SSL_TLS = os.environ.get('MAIL_SSL_TLS')
MAIL_USECREDENTIALS =os.environ.get('USE_CREDENTIALS')
MAIL_REDIRECT_URI = str(os.environ.get('EMAIL_REDIRECT_URI'))

# JWT Variables

EXPIRATION_MINUTES = 10  # Verification code expires in 10 minutes
SECRET_KEY = """
    RUNCMEIzRTk5QTgyMkQxRDY2NjY4MEJDMjZBNDU1RUUxQTdCMEU1QUFEQkZDMTBENEZCMUREMEYwNUJGRTdCNzNFRDc5NUM3MTA3MUYzNUJFNTM0QUJDOTFBOTZEMDFFNTA1RTNGNkU4NTc5MjIzOEZBRDhBMEZGMjcyNTZGOTk=
    OEUzMEU3Qzc4NzRCMzhBMTFGRTdCODRGQzM3MUY2MDNCNjk4MzRFRjZEQzk5NUIwM0QzNzdFODUzNDg4MkU2MDM5N0NDQjJDQTJDOTA0NzZBODMzNDRGRUUzRTZGMzBCODBDMUFBRkM3OTdBQzA2QkJDNUU2MUY0NzQ3OUEwOUU=
    NDY1NjM4MzM4MjlDNzY5Nzg1NTIxMzg3NjU2MzY3MzYyNjU3NDk2OTFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUKFBQU=
    NERCMEM3OTUxREVEQjNEQkQ4ODZEQjNCOUVDOUM0ODBGRENEOUZGMjE0MzlENzJDQUI0QTY0RkY4ODk1NDlCODE3RjlBRUQ2QjdGRkM5MUFBRUFGOTY4MUQ0Njk2OTU2NzhBQzg2RTQ5RTI4RTgwNUJFMDBBNEI5NTE2OTBDNzk=
    RUYxQUQ3MzhFMDUxMzExQUM1QkEwOTdFQzBCRkJDNDExMDAxMzdDOUNBMkI5RUJFREMyNUVFQ0MzMTM2RjE3QzcxMTVFOTBFM0I3NjNFRTQ5MTNEOTY0QUY3RjMzQzkyRTNCM0IzODM5NEM4MzFGNDY2RThCMzE4MDgzMTQzMjU=
    RjQ3RjY4QkM0MjEwMEM5NjFGOUNDREY1RjM3RTQ3Mjk2OEJDRjJFNTE3M0FCMEI5RTMyNzI0MjY1M0JBQUJBREQ4MzhCRkY0RDQ0REVCN0IyQjI2OTk2MkFEOEJCMjgwRkY5MTI2Q0M4REUwMUMwMzBFQURGNEIyMDkwN0Q1QkY=
    OEE3ODk5NjMyOTgzMDg3RjAyREExRjZGMDBGMTQ2RDRFOEM3RDc2RkE3MzA0QzU5RjZEQjlERDk1Q0U4Qjk5NEY0NzI5NjFBRDk3NjREMEQwNEYyRDcxM0NERjQzQ0M0NDlCRkEyODIwOUU2MTBERDEwNTJGNDYyQjMwNjMxQkU=
    MUZBODQxN0M3RTdGNTI1QzBEN0Q1QUZCMUVBMTEwRjM1QURBMzRBRkVEQjU2RUE2MjI3QzJEMjA1OUM0MDQ2RUNGNkVCNzMxQzE4ODc5QjQzNTA3QzNCNjUzMkVDNEE5MDE2MTRCRDBGODQwMzdGRjg0MUVCRUU1NzNFN0NFODg=
    QzY0RjhBM0M5MjhCODk2N0FDRkE2ODhDNTY3Q0M3NzJFRkM5RjM3N0M0N0UxMENGOTU2MTU4MUJERUUyNDk1OTM1OTdBQ0M3RjM5MzNDOUVFNTIzOTkwNUUzMzdBM0ZFRjM0NTNBRUY3MEJBMENCNDczODk4QjA4RTA3MTU2Q0M=
    N0FEMjJEOEFBRjQ5NTFBQjVBMTlFODNENUQ5OEZCOThEMjNGQ0ZBREMyMkUwQjFGREM4MTYwOTg0OTU5MjI3NUY4RkE4QzhFRDlGMjMzOEEyQzBDQTgzNUJGOUFFMjdBMkU5MTk4NTcxODZENjY3MDFENTNFQkQwMTVGOTU3QTc=
    """
ALGORITHM="HS256"

# Apple SSO Oauth Variables

APPLE_CLIENT_ID = str(os.environ.get('APPLE_CLIENT_ID'))
APPLE_REDIRECT_URI = str(os.environ.get('APPLE_REDIRECT_URI'))
# APPLE_KEY_ID = str(os.environ.get('APPLE_KEY_ID'))
# APPLE_TEAM_ID = str(os.environ.get('APPLE_TEAM_ID'))
# APPLE_PRIVATE_KEY = str(os.environ.get('APPLE_PRIVATE_KEY'))

# Google SSO OAuth Variables

GOOGLE_CLIENT_ID = str(os.environ.get('GOOGLE_CLIENT_ID'))
GOOGLE_CLIENT_SECRET = str(os.environ.get('GOOGLE_CLIENT_SECRET'))
GOOGLE_REDIRECT_URI = str(os.environ.get('GOOGLE_REDIRECT_URI'))

# Github SSO OAuth Variables

GITHUB_CLIENT_ID = str(os.environ.get('GITHUB_CLIENT_ID'))
GITHUB_CLIENT_SECRET = str(os.environ.get('GITHUB_CLIENT_SECRET'))
GITHUB_REDIRECT_URI = str(os.environ.get('GITHUB_REDIRECT_URI'))

# Discord SSO OAuth Variables

DISCORD_CLIENT_ID = str(os.environ.get('DISCORD_CLIENT_ID'))
DISCORD_CLIENT_SECRET = str(os.environ.get('DISCORD_CLIENT_SECRET'))
DISCORD_REDIRECT_URI = str(os.environ.get('DISCORD_REDIRECT_URI'))

# Team member variables
team_members_str = os.environ.get('TEAM_MEMBER_HANDLES')
if team_members_str:
    TEAM_MEMBERS_HANDLES = team_members_str.split(",")
else:
    TEAM_MEMBERS_HANDLES = []

# Algorithm tag variables
TAG_FILE_PATH = os.path.join("resources", "tags.json")

with open(TAG_FILE_PATH, "r") as file:
    data = json.load(file)

all_subcategories = [
    subcategory
    for category in data["categories"]  # Iterate through the list of categories
    for subcategory in category["subcategories"]
]
