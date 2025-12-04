import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ELEVEN_LABS_API_KEY = os.environ.get('ELEVEN_LABS_API_KEY')
    VOICE_ID = os.environ.get('Voice_ID')
    OPENAI_SYSTEM_PROMPT = os.environ.get('OPENAI_SYSTEM_PROMPT') or \
        "You are a helpful nutritionist assistant. Analyze the food label text provided. " \
        "Return a JSON object with keys: ingredients (list), allergens (list), additives (list), " \
        "nutritional_concerns (list), recommendation (string), score (integer 0-100), " \
        "and explanation (string). Consider the user's allergies and conditions if provided."
