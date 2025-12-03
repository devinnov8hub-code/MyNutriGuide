import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from openai import OpenAI
from flask import current_app

def save_temp_image(image_data_base64, filename):
    """
    Saves base64 image to static/uploads for display.
    """
    try:
        if ',' in image_data_base64:
            header, encoded = image_data_base64.split(',', 1)
        else:
            encoded = image_data_base64
            
        image_bytes = base64.b64decode(encoded)
        image = Image.open(BytesIO(image_bytes))
        
        # Ensure uploads directory exists
        uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        filepath = os.path.join(uploads_dir, filename)
        image.save(filepath)
        return filename
    except Exception as e:
        current_app.logger.error(f"Image Save Error: {e}")
        return None

def save_temp_audio(audio_data_base64, filename):
    """
    Saves base64 audio to static/audio for playback.
    """
    try:
        audio_bytes = base64.b64decode(audio_data_base64)
        
        # Ensure audio directory exists
        audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        filepath = os.path.join(audio_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        return filename
    except Exception as e:
        current_app.logger.error(f"Audio Save Error: {e}")
        return None

def analyze_image_vision(image_data_base64, user_profile):
    """
    Sends image directly to OpenAI Vision model for analysis.
    """
    # Initialize OpenAI client with the key from config
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        current_app.logger.error("OpenAI API key is missing.")
        return "Error: OpenAI API key is not configured."

    client = OpenAI(api_key=api_key)

    # Ensure we have the data URL prefix for OpenAI
    if not image_data_base64.startswith('data:image'):
        image_data_base64 = f"data:image/jpeg;base64,{image_data_base64}"

    # Parse allergies if it's a JSON string
    allergies_data = user_profile.get('allergies', 'None')
    try:
        if allergies_data and allergies_data.strip().startswith('['):
            allergies_list = json.loads(allergies_data)
            # Format as "Peanuts (Severe), Gluten (Mild)"
            formatted_allergies = ", ".join([f"{a['name']} ({a['severity']})" for a in allergies_list])
            allergies_data = formatted_allergies
    except Exception:
        pass # Keep original string if parsing fails

    user_context = (
        f"User Profile:\n"
        f"Allergies: {allergies_data}\n"
        f"Chronic Conditions: {user_profile.get('chronic_conditions', 'None')}\n"
        f"Dietary Preferences: {user_profile.get('dietary_preferences', 'None')}\n"
        f"Medications: {user_profile.get('medications', 'None')}\n"
    )
    
    prompt_text = (
        f"Analyze this food image using a combination of visual recognition and text extraction. "
        f"1. Identify the product visually (like a reverse image search). "
        f"2. Read any visible text (ingredients, nutrition facts). "
        f"3. Search the web for additional product details if necessary. "
        f"4. Combine this with your internal knowledge to provide a complete analysis.\n\n"
        f"User Profile:\n{user_context}\n\n"
        f"Provide a structured JSON response with the following fields:\n"
        f"- product_name: The name of the product.\n"
        f"- warnings: A list of strings (health warnings based on user profile).\n"
        f"- summary: A conversational summary of whether it's healthy and a recommendation (plain text, no markdown).\n"
        f"- voice_response: A friendly audio summary suitable for the user based on their profile.\n\n"
        f"Return ONLY the JSON object, no markdown formatting. "
        f"If you don't recognize the food or cannot extract details, return 'Unknown Product' for product_name."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_base64
                            }
                        }
                    ]
                }
            ],
            tools=[
                {"type": "web_search"}
            ],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        print("OpenAI Response:", response.choices[0].message.content)
        
        return response.choices[0].message.content
    except Exception as e:
        current_app.logger.error(f"OpenAI Vision Error: {e}")
        return "Sorry, I couldn't analyze the image at this time."

def generate_audio(text):
    """
    Generates audio from text using ElevenLabs API.
    Returns base64 encoded audio.
    """
    api_key = current_app.config.get('ELEVEN_LABS_API_KEY')
    voice_id = current_app.config.get('VOICE_ID')
    
    if not api_key or not voice_id:
        current_app.logger.error("ElevenLabs credentials missing.")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        else:
            current_app.logger.error(f"ElevenLabs Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        current_app.logger.error(f"ElevenLabs Request Error: {e}")
        return None