"""
Email handling module for processing and sending emails via Gmail API.
"""
import json
import logging
from .gmail_utils import process_email_request

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_email_response(model, prompt, original_query, session_id, request):
    """
    Generator function for handling email requests.
    
    Args:
        model (str): The LLM model to use
        prompt (str): The prompt with email instructions
        original_query (str): The original user query
        session_id (str): The session ID
        request (HttpRequest): The Django request object
        
    Yields:
        str: Server-sent event data for streaming response
    """
    from .views import generate_streaming_response
    
    # Initialize variables
    full_response = ""
    email_sent = False
    
    # Stream the LLM response
    for chunk in generate_streaming_response(model, prompt, session_id, request):
        # Decode the chunk if it's bytes, otherwise use as is
        if isinstance(chunk, bytes):
            chunk_str = chunk.decode('utf-8')
        else:
            chunk_str = chunk
        
        # Check if it's a data chunk
        if chunk_str.startswith('data: '):
            data_str = chunk_str[6:]  # Remove 'data: ' prefix
            
            # Skip heartbeat messages
            if data_str.strip() == '[HEARTBEAT]':
                yield chunk
                continue
                
            try:
                # Try to parse as JSON
                data = json.loads(data_str)
                
                # Accumulate the response
                if 'content' in data:
                    full_response += data['content']
                    
                # Pass through the chunk
                yield chunk
                
            except json.JSONDecodeError:
                # Not JSON, just pass through
                yield chunk
        else:
            # Not a data chunk, pass through
            yield chunk
    
    # After streaming is complete, process the email
    if not email_sent and full_response:
        try:
            logger.info(f"Processing email from full response (length: {len(full_response)})")
            logger.info(f"Response preview: {full_response[:100]}...")
            
            # Process and send the email
            email_result = process_email_request(original_query, full_response)
            logger.info(f"Email processing result: {email_result}")
            
            # Prepare result message
            if email_result['success']:
                logger.info("Email sent successfully!")
                result_message = {
                    'type': 'email_sent',
                    'content': f"\n\n✅ Email has been sent successfully!"
                }
            else:
                logger.error(f"Email sending failed: {email_result['message']}")
                result_message = {
                    'type': 'email_error',
                    'content': f"\n\n❌ Failed to send email: {email_result['message']}"
                }
            
            # Send the result as a new chunk
            yield f"data: {json.dumps(result_message)}\n\n".encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error in email processing: {str(e)}")
            error_message = {
                'type': 'email_error',
                'content': f"\n\n❌ An error occurred while processing the email: {str(e)}"
            }
            yield f"data: {json.dumps(error_message)}\n\n".encode('utf-8')
