import logging
import json
import re
from groq import Groq
import os

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_api_key = os.environ.get('GROQ_API_KEY')
groq_client = Groq(api_key=groq_api_key)

def detect_identity_update_intent(query):
    """
    Detect if the user is trying to update their identity information using LLM.
    
    Args:
        query (str): The user's query
        
    Returns:
        dict: Information about the detected intent
    """
    # Initialize result
    result = {
        'is_identity_update': False,
        'name': None,
        'email': None,
        'organization': None
    }
    
    # Quick check for common identity update phrases to avoid unnecessary LLM calls
    identity_indicators = ['my name is', 'set my name', 'change my name', 'call me', 
                          'my email is', 'my organization', 'i work for', 'i work at']
    
    # Only proceed with LLM if there's a potential identity update
    if not any(indicator in query.lower() for indicator in identity_indicators):
        return result
    
    try:
        # Prepare prompt for LLM
        prompt = f"""
        Extract user identity information from the following text. The user might be trying to update their name, email, or organization.
        
        Text: "{query}"
        
        Extract ONLY the following fields if present:
        1. Name: The user's name (if they're trying to update it)
        2. Email: The user's email (if they're trying to update it)
        3. Organization: The user's organization or company (if they're trying to update it)
        
        If any field is not being updated, return null for that field.
        Is this an identity update request? Return true or false.
        
        Format your response as a valid JSON object with these fields: {{"is_identity_update": boolean, "name": string or null, "email": string or null, "organization": string or null}}
        """
        
        # Call LLM
        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        # Extract and parse JSON from response
        llm_response = response.choices[0].message.content
        
        # Find JSON in the response
        json_match = re.search(r'\{[^\{\}]*"is_identity_update"[^\{\}]*\}', llm_response)
        if json_match:
            extracted_json = json_match.group(0)
            parsed_result = json.loads(extracted_json)
            
            # Update result with LLM output
            result['is_identity_update'] = parsed_result.get('is_identity_update', False)
            
            if parsed_result.get('name'):
                result['name'] = parsed_result['name'].strip()
                
            if parsed_result.get('email'):
                result['email'] = parsed_result['email'].strip()
                
            if parsed_result.get('organization'):
                result['organization'] = parsed_result['organization'].strip()
        
        # Log the detection result
        if result['is_identity_update']:
            logger.info(f"LLM identity update detected: {result}")
            
    except Exception as e:
        logger.error(f"Error in LLM identity detection: {str(e)}")
        # Fall back to basic detection for critical errors
        if 'my name is' in query.lower():
            result['is_identity_update'] = True
            name_match = re.search(r'my name is ([\w\s]+?)(?:\.|$|\band\b)', query.lower())
            if name_match:
                result['name'] = name_match.group(1).strip().title()
    
    return result

def process_identity_update(request, identity_info):
    """
    Process an identity update request and store in session.
    
    Args:
        request: The HTTP request object
        identity_info (dict): Information about the identity update
        
    Returns:
        str: A response message confirming the update
    """
    response_parts = []
    
    # Update name if provided
    if identity_info['name']:
        request.session['user_name'] = identity_info['name']
        response_parts.append(f"✅ Your name has been updated to: {identity_info['name']}")
    
    # Update email if provided
    if identity_info['email']:
        request.session['user_email'] = identity_info['email']
        response_parts.append(f"✅ Your email has been updated to: {identity_info['email']}")
    
    # Update organization if provided
    if identity_info['organization']:
        request.session['user_org'] = identity_info['organization']
        response_parts.append(f"✅ Your organization has been updated to: {identity_info['organization']}")
    
    # Save the session
    request.session.save()
    
    # Return confirmation message
    if response_parts:
        return "\n".join(response_parts)
    else:
        return "⚠️ No identity information was updated."

def get_user_identity(request):
    """
    Get the user's identity information from the session or profile.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: The user's identity information
    """
    user = request.user
    
    # Get identity information from session or defaults
    identity = {
        'name': request.session.get('user_name', user.get_full_name() or user.username),
        'email': request.session.get('user_email', user.email),
        'organization': request.session.get('user_org', '')
    }
    
    return identity
