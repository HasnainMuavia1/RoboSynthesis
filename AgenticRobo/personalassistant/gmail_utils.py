"""
Gmail utility functions for sending emails using Google API credentials.
"""
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """
    Get an authorized Gmail API service instance using credentials from the credentials folder.
    
    Returns:
        A Gmail API service object or None if authentication fails.
    """
    try:
        creds = None
        credentials_path = os.path.join('credentials', 'google_credentials.json')
        token_path = os.path.join('credentials', 'token.json')
        
        # Check if credentials file exists
        if not os.path.exists(credentials_path):
            logger.error("Google credentials file not found. Please connect Google Apps in MCP Config.")
            return None
            
        # Load credentials from file
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_info(
                json.load(open(token_path)), SCOPES)
                
        # If credentials don't exist or are invalid, refresh or create new ones
        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Successfully refreshed Gmail credentials")
                    except RefreshError as re:
                        logger.warning(f"Failed to refresh token: {str(re)}")
                        # If refresh fails, create new credentials
                        logger.info("Creating new credentials after refresh failure")
                        flow = InstalledAppFlow.from_client_secrets_file(
                            credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                else:
                    # Create new credentials
                    logger.info("Creating new Gmail credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
            except Exception as auth_error:
                logger.error(f"Authentication error: {str(auth_error)}")
                return None
                
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                
        # Build and return the Gmail service
        return build('gmail', 'v1', credentials=creds)
        
    except Exception as e:
        logger.error(f"Error getting Gmail service: {str(e)}")
        return None

def send_email(to, subject, body, cc=None, bcc=None):
    """
    Send an email using the Gmail API.
    
    Args:
        to (str): Email address of the recipient
        subject (str): Subject of the email
        body (str): Body content of the email (HTML supported)
        cc (str, optional): CC recipients (comma-separated)
        bcc (str, optional): BCC recipients (comma-separated)
        
    Returns:
        dict: Response containing success status and message
    """
    try:
        logger.info(f"Attempting to send email to: {to}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body length: {len(body)} characters")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            logger.error("Failed to get Gmail service - authentication failed")
            return {
                'success': False,
                'message': 'Server error: Failed to authenticate with Gmail. Please try again or reconnect your Google account in MCP Config.'
            }
            
        # Create message
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
            
        # Attach body
        message.attach(MIMEText(body, 'html'))
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        logger.info(f"Email sent successfully. Message ID: {sent_message['id']}")
        
        return {
            'success': True,
            'message': 'Email sent successfully',
            'message_id': sent_message['id']
        }
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        # Provide a more user-friendly error message
        error_message = 'Server failed, please try again. '
        
        if 'invalid_grant' in str(e).lower():
            error_message += 'Your Google authentication has expired. Please reconnect your Google account in MCP Config.'
        elif 'credentials' in str(e).lower():
            error_message += 'There was an issue with your Google credentials. Please reconnect your Google account.'
        elif 'network' in str(e).lower() or 'timeout' in str(e).lower():
            error_message += 'Network connection issue. Please check your internet connection and try again.'
        else:
            error_message += f'Error details: {str(e)}'
            
        return {
            'success': False,
            'message': error_message
        }

def detect_email_intent(query):
    """
    Detect if the user is asking to send an email.
    Only explicit email sending requests should return True.
    
    Args:
        query (str): The user's query
        
    Returns:
        dict or None: Email information if detected, None otherwise
    """
    if not query:
        return None
        
    query_lower = query.lower()
    
    # Log the query for debugging
    logger.info(f"Checking email intent for query: {query_lower}")
    
    # Explicit action phrases that clearly indicate sending an email
    explicit_actions = [
        'send email', 'send an email', 'send a mail', 'send a formal email',
        'email this to', 'mail this to', 'send this email to',
        'compose and send', 'write and send', 'draft and send'
    ]
    
    # Check for explicit action phrases
    is_explicit_request = any(action in query_lower for action in explicit_actions)
    
    if not is_explicit_request:
        # Check for "write/compose/draft email" followed by "send" or "to"
        writing_actions = ['write email', 'write an email', 'compose email', 'compose an email', 'draft email', 'draft an email']
        sending_indicators = ['send', 'to:', 'to ', 'for ', 'address']
        
        # More lenient detection patterns
        has_email_keyword = 'email' in query_lower
        has_email_address = '@' in query_lower and '.' in query_lower
        
        # Check for writing actions
        has_writing_action = any(action in query_lower for action in writing_actions) or \
                           any(phrase in query_lower for phrase in ['write a', 'write an', 'create a', 'create an']) and has_email_keyword
        
        has_sending_indicator = any(indicator in query_lower for indicator in sending_indicators)
        
        # Consider it an email request if ANY of these conditions are met:
        # 1. It has a writing action AND a sending indicator
        # 2. It has the 'email' keyword AND contains an email address
        # 3. It explicitly mentions writing an email (even without recipient)
        is_explicit_request = (has_writing_action and has_sending_indicator) or \
                             (has_email_keyword and has_email_address) or \
                             (has_writing_action and has_email_keyword)
    
    # Log the detection result
    logger.info(f"Email intent detection result: {is_explicit_request}")
    
    # Return None if not an explicit email request
    if not is_explicit_request:
        return None
        
    # Email request detected
    email_info = {
        'is_email_request': True,
        'query': query,
        # These will be extracted by the LLM in process_email_request
        'to': None,
        'subject': None,
        'body': None
    }
    
    return email_info

def process_email_request(query, llm_response):
    """
    Process an email request using the LLM response.
    
    Args:
        query (str): Original user query
        llm_response (str): LLM response containing email details
        
    Returns:
        dict: Result of the email sending operation
    """
    try:
        logger.info(f"Starting to process email from response: {llm_response[:100]}...")
        
        # Extract email components from LLM response with improved parsing
        lines = llm_response.strip().split('\n')
        
        # Initialize email components
        to = None
        subject = None
        body_lines = []
        parsing_body = False
        found_to = False
        found_subject = False
        
        # First pass: look for To: and Subject: headers
        for line in lines:
            line_lower = line.lower().strip()
            
            # Extract recipient
            if line_lower.startswith('to:'):
                to = line[3:].strip()
                found_to = True
                logger.info(f"Found TO: {to}")
            
            # Extract subject
            elif line_lower.startswith('subject:'):
                subject = line[8:].strip()
                found_subject = True
                logger.info(f"Found SUBJECT: {subject}")
        
        # If we couldn't find a recipient in the properly formatted headers,
        # try to extract from the query
        if not to:
            # Look for email addresses in the query
            import re
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_matches = re.findall(email_pattern, query)
            if email_matches:
                to = email_matches[0]
                logger.info(f"Extracted TO from query: {to}")
        
        # Second pass: extract the body - more precise extraction
        body_started = False
        body_ended = False
        signature_markers = ['best regards', 'sincerely', 'regards,', 'thank you,', 'yours truly', 'warm regards']
        
        # First look for explicit Body: marker
        has_body_marker = False
        body_marker_index = -1
        for i, line in enumerate(lines):
            if line.lower().strip() == 'body:' or line.lower().strip() == 'email body:':
                has_body_marker = True
                body_marker_index = i
                break
        
        # If we found an explicit body marker, start collecting from there
        if has_body_marker and body_marker_index >= 0:
            logger.info(f"Found explicit body marker at line {body_marker_index}")
            # Skip the body marker line itself
            for i in range(body_marker_index + 1, len(lines)):
                line = lines[i]
                line_lower = line.lower().strip()
                
                # Stop at note about sending email
                if "i'll send this email for you" in line_lower or "i will send this email for you" in line_lower:
                    break
                    
                # Add line to body
                body_lines.append(line)
        else:
            # No explicit body marker, try to find where the body starts after headers
            logger.info("No explicit body marker found, using header detection")
            
            # Find the last header line (To: or Subject:)
            last_header_index = -1
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if line_lower.startswith('to:') or line_lower.startswith('subject:'):
                    last_header_index = i
            
            # Start collecting body after the headers and any blank lines
            if last_header_index >= 0:
                body_started = False
                for i in range(last_header_index + 1, len(lines)):
                    line = lines[i]
                    line_lower = line.lower().strip()
                    
                    # Skip blank lines until we find content
                    if not body_started and not line.strip():
                        continue
                    
                    body_started = True
                    
                    # Stop at signature or note about sending
                    if any(marker in line_lower for marker in signature_markers):
                        body_lines.append(line)  # Include the signature line
                        
                        # Check if this is followed by a name
                        if i + 1 < len(lines) and len(lines[i+1].strip()) < 30:  # Short line likely a name
                            body_lines.append(lines[i+1])  # Include the name line
                        
                        break
                    
                    # Stop at note about sending email
                    if "i'll send this email for you" in line_lower or "i will send this email for you" in line_lower:
                        break
                        
                    # Add line to body
                    body_lines.append(line)
        
        # If we still didn't get a body, try a more aggressive approach
        if not body_lines:
            logger.warning("Falling back to aggressive body extraction")
            in_body = False
            for line in lines:
                line_lower = line.lower().strip()
                
                # Skip until we're past the headers
                if not in_body:
                    if line_lower.startswith('to:') or line_lower.startswith('subject:'):
                        continue
                    elif line.strip() == '':
                        continue
                    else:
                        in_body = True
                
                # Skip note about sending email
                if "i'll send this email for you" in line_lower or "i will send this email for you" in line_lower:
                    break
                    
                # Add line to body
                if in_body:
                    body_lines.append(line)
        
        # Format the body with proper HTML
        body_text = '\n'.join(body_lines).strip()
        logger.info(f"Extracted BODY (first 100 chars): {body_text[:100]}...")
        
        # Convert plain text to simple HTML with paragraphs
        body_html = f"<div style='font-family: Arial, sans-serif; line-height: 1.6;'>"
        
        # Split by double newlines to identify paragraphs
        paragraphs = body_text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Replace single newlines with <br> tags
                paragraph = paragraph.replace('\n', '<br>')
                body_html += f"<p>{paragraph}</p>"
                
        body_html += "</div>"
        
        # Validate email components
        if not to:
            logger.error("Could not extract recipient email address")
            return {
                'success': False,
                'message': 'Could not extract recipient email address. Please specify an email address.'
            }
            
        if not subject:
            # Generate a subject if none was provided
            subject = "Email from Agento Assistant"
            logger.info(f"Using default subject: {subject}")
            
        if not body_text.strip():
            logger.error("Could not extract email body content")
            return {
                'success': False,
                'message': 'Could not extract email body content'
            }
            
        # Send the email with HTML formatting
        logger.info(f"Attempting to send email to: {to} with subject: {subject}")
        result = send_email(to, subject, body_html)
        logger.info(f"Email sending result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing email request: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to process email request: {str(e)}'
        }
