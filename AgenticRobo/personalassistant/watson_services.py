"""
IBM Watson Speech Services for Text-to-Speech and Speech-to-Text integration.
"""
import os
import json
import logging
from ibm_watson import TextToSpeechV1, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from django.conf import settings

logger = logging.getLogger(__name__)

# IBM Watson credentials - hardcoded from .env file for testing
TTS_API_KEY = "uRfjVO8Vh3h4iuzINXVkqZwBvwbHnCmQYptEcjmaL39o"
TTS_URL = "https://api.au-syd.text-to-speech.watson.cloud.ibm.com/instances/67420730-5171-4cca-928a-f550a259ba20"
TTS_AUTH_TYPE = "iam"
STT_API_KEY = "SHDe9-EQHCobIRbIMLwRPN_9HYOSggRRbMF2S4IFy8Uh"
STT_URL = "https://api.au-syd.speech-to-text.watson.cloud.ibm.com/instances/b088efec-be09-4d11-8b27-09a420dc010c"
STT_AUTH_TYPE = "iam"

# Log the values for debugging
logger.info(f"TTS URL: {TTS_URL}")
logger.info(f"STT URL: {STT_URL}")

def get_tts_service():
    """
    Initialize and return the IBM Watson Text-to-Speech service.
    """
    try:
        if not TTS_API_KEY or not TTS_URL:
            logger.error("Text-to-Speech API key or URL is missing")
            return None
            
        # Set up authenticator
        authenticator = IAMAuthenticator(TTS_API_KEY)
        
        # Set up service
        tts_service = TextToSpeechV1(authenticator=authenticator)
        tts_service.set_service_url(TTS_URL)
        
        logger.info("Text-to-Speech service initialized successfully")
        return tts_service
    except Exception as e:
        logger.error(f"Error initializing Text-to-Speech service: {str(e)}")
        return None

def get_stt_service():
    """
    Initialize and return the IBM Watson Speech-to-Text service.
    """
    try:
        if not STT_API_KEY or not STT_URL:
            logger.error("Speech-to-Text API key or URL is missing")
            return None
            
        # Set up authenticator
        authenticator = IAMAuthenticator(STT_API_KEY)
        
        # Set up service
        stt_service = SpeechToTextV1(authenticator=authenticator)
        stt_service.set_service_url(STT_URL)
        
        logger.info("Speech-to-Text service initialized successfully")
        return stt_service
    except Exception as e:
        logger.error(f"Error initializing Speech-to-Text service: {str(e)}")
        return None

def text_to_speech(text, voice="en-US_AllisonV3Voice"):
    """
    Convert text to speech using IBM Watson Text-to-Speech service.
    
    Args:
        text (str): The text to convert to speech
        voice (str): The voice to use (default: en-US_AllisonV3Voice)
        
    Returns:
        bytes: Audio data in WAV format
    """
    try:
        # Get TTS service
        tts_service = get_tts_service()
        if not tts_service:
            logger.error("Failed to initialize Text-to-Speech service")
            return None
        
        # Convert text to speech
        response = tts_service.synthesize(
            text=text,
            accept='audio/wav',
            voice=voice
        ).get_result().content
        
        return response
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return None

def speech_to_text(audio_data, content_type="audio/webm"):
    """
    Convert speech to text using IBM Watson Speech-to-Text service.
    
    Args:
        audio_data (bytes): The audio data to transcribe
        content_type (str): The content type of the audio data (default: audio/webm)
        
    Returns:
        str: Transcribed text
    """
    try:
        # Get STT service
        stt_service = get_stt_service()
        if not stt_service:
            logger.error("Failed to initialize Speech-to-Text service")
            return None
        
        # Convert speech to text
        response = stt_service.recognize(
            audio=audio_data,
            content_type=content_type,
            model='en-US_BroadbandModel'
        ).get_result()
        
        # Extract transcription
        if response.get('results'):
            transcription = ' '.join(
                result.get('alternatives', [{}])[0].get('transcript', '')
                for result in response['results']
            )
            return transcription
        
        return ""
    except Exception as e:
        logger.error(f"Error in speech_to_text: {str(e)}")
        return None
