"""
Google Drive handling module for processing and handling Google Drive operations via Google Drive API.
"""
import json
import re
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Import Google Drive utilities
from .google_drive_utils import (
    list_files, list_files_by_type, read_file_content,
    create_file, create_excel_file
)
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_drive_intent(query):
    """
    Detect if the user query contains an intent to interact with Google Drive.
    Uses a more flexible approach to detect Drive intents and extract parameters.
    
    Args:
        query (str): The user's query
        
    Returns:
        tuple: (bool, str, dict) - (is_drive_intent, intent_type, parameters)
        intent_type can be: 'list', 'read', 'create', 'list_type', None
        parameters contains extracted parameters like file_name, file_type, content, etc.
    """
    print(f"\nDrive intent detection called with query: '{query}'")
    
    # Convert to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Initialize parameters dictionary
    parameters = {}
    
    # First, check if the query mentions Google Drive at all
    drive_keywords = ['drive', 'google drive', 'gdrive', 'g-drive', 'google docs']
    file_keywords = ['files', 'documents', 'spreadsheets', 'file']
    
    # Get list of files to check if query mentions a specific file name
    try:
        all_files = list_files()
        file_names = [f['name'].lower() for f in all_files]
    except:
        file_names = []
    
    has_drive_mention = any(keyword in query_lower for keyword in drive_keywords)
    has_file_mention = any(keyword in query_lower for keyword in file_keywords)
    
    # Check if query mentions a specific file name from the user's Drive
    has_specific_file_mention = any(file_name in query_lower for file_name in file_names)
    
    # Special case: if the query is very clearly about files, consider it a drive query
    if any(phrase in query_lower for phrase in ['list all my files', 'show me my files', 'what files do i have']):
        print("File listing request detected, treating as Drive query")
        return True, 'list', parameters
    
    # If no direct Drive mention and not clearly about files, it's not a Drive intent
    if not has_drive_mention and not has_file_mention:
        print("No mention of Drive or files in query, not a Drive intent")
        return False, None, {}
    
    # Extract file types if mentioned
    file_types = {
        'excel': ['excel', 'spreadsheet', 'xlsx', 'xls', 'sheet', 'table'],
        'document': ['doc', 'docx', 'word', 'document', 'text'],
        'pdf': ['pdf'],
        'text': ['txt', 'text file', 'plain text'],
        'presentation': ['ppt', 'pptx', 'presentation', 'slide']
    }
    
    for file_type, keywords in file_types.items():
        if any(keyword in query_lower for keyword in keywords):
            parameters['file_type'] = file_type
            break
    
    # Extract file name if mentioned
    # Look for patterns like "file called X", "X.docx", "named X", etc.
    file_name_patterns = [
        r'(?:file|document|spreadsheet)\s+(?:called|named)\s+["\']?([\w\s.-]+)["\']?',
        r'(?:called|named)\s+["\']?([\w\s.-]+\.\w+)["\']?',
        r'["\']([\w\s.-]+\.\w+)["\']',
        r'(?:create|make|add|new)\s+(?:a|an)?\s+(?:file|document|spreadsheet)\s+["\']?([\w\s.-]+)["\']?'
    ]
    
    for pattern in file_name_patterns:
        match = re.search(pattern, query)
        if match:
            parameters['file_name'] = match.group(1).strip()
            break
    
    # Detect intent based on query analysis
    # List files intent
    list_keywords = ['list', 'show', 'get', 'what', 'all', 'display', 'find']
    if any(keyword in query_lower for keyword in list_keywords) and has_file_mention:
        if 'file_type' in parameters:
            print(f"Drive list_type intent detected for {parameters['file_type']} files")
            return True, 'list_type', parameters
        else:
            print("Drive list intent detected")
            return True, 'list', parameters
    
    # Read file intent
    read_keywords = ['read', 'open', 'show', 'display', 'view', 'get', 'fetch']
    if any(keyword in query_lower for keyword in read_keywords) and ('file_name' in parameters or has_file_mention or has_specific_file_mention):
        print("Drive read intent detected")
        # If we don't have a file name yet, try to extract it from the query
        if not parameters.get('file_name') and has_specific_file_mention:
            # Find which file name from our list is in the query
            for file_name in file_names:
                if file_name in query_lower:
                    parameters['file_name'] = file_name
                    print(f"Extracted file name from Drive files: {file_name}")
                    break
        return True, 'read', parameters
    
    # Create file intent
    create_keywords = ['create', 'make', 'new', 'add', 'write']
    if any(keyword in query_lower for keyword in create_keywords) and has_file_mention:
        # Try to extract content or topic for the file
        content_match = re.search(r'(?:with|containing|about)\s+(.+?)(?:\.|$)', query)
        if content_match:
            parameters['content'] = content_match.group(1).strip()
        
        print("Drive create intent detected")
        return True, 'create', parameters
    
    # Special case for when the query is just a file name or very close to it
    # This handles cases like "read heroes" where the query is just the action + filename
    if has_specific_file_mention and len(query_lower.split()) <= 3:
        for file_name in file_names:
            if file_name in query_lower:
                print(f"Direct file reference detected: {file_name}")
                parameters['file_name'] = file_name
                # If there's a read-like word, it's a read intent
                if any(keyword in query_lower for keyword in ['read', 'open', 'show', 'view', 'get']):
                    return True, 'read', parameters
                # Otherwise default to read intent for simple file mentions
                return True, 'read', parameters
    
    # If we have a drive or file mention but no specific intent detected,
    # default to list files as the most common operation
    if has_drive_mention or has_file_mention:
        print("Drive/files mentioned but no specific intent detected, defaulting to list")
        return True, 'list', parameters
        
    print("No drive intent detected at all")
    return False, None, {}

def process_drive_request(intent_type, query, parameters=None):
    """
    Process a Google Drive request based on the detected intent and parameters.
    
    Args:
        intent_type (str): The type of drive intent ('list', 'read', 'create', 'list_type')
        query (str): The user's original query
        parameters (dict): Optional extracted parameters from the query
        
    Returns:
        dict: Response with success status, message, and any relevant data
    """
    try:
        if parameters is None:
            parameters = {}
            
        query_lower = query.lower()
        
        if intent_type == 'list':
            # List all files in Google Drive
            files = list_files()
            
            if not files:
                return {
                    'success': True,
                    'message': 'No files found in your Google Drive.',
                    'files': []
                }
            
            return {
                'success': True,
                'message': f'Found {len(files)} files in your Google Drive.',
                'files': files
            }
            
        elif intent_type == 'list_type':
            # Determine file type to list
            file_type = None
            
            if any(word in query for word in ['excel', 'spreadsheet', 'xlsx', 'xls']):
                file_type = 'excel'
            elif any(word in query for word in ['pdf']):
                file_type = 'pdf'
            elif any(word in query for word in ['word', 'doc', 'docx']):
                file_type = 'word'
            elif any(word in query for word in ['text', 'txt']):
                file_type = 'text'
            
            if not file_type:
                return {
                    'success': False,
                    'message': 'Could not determine which file type you want to list.'
                }
            
            # List files of the specified type
            files = list_files_by_type(file_type)
            
            if not files:
                return {
                    'success': True,
                    'message': f'No {file_type} files found in your Google Drive.',
                    'files': []
                }
            
            return {
                'success': True,
                'message': f'Found {len(files)} {file_type} files in your Google Drive.',
                'files': files
            }
            
        elif intent_type == 'read':
            # Get file name from parameters if available
            file_name = parameters.get('file_name')
            
            # If no file name in parameters, try to extract from query
            if not file_name:
                # Try to find file name in query
                # Look for patterns like "read heroes file" or "show me heroes"
                
                # First look for quoted file names
                quoted_match = re.search(r'["\'](.*?)["\']\.?\s*(?:file|spreadsheet|document|xlsx|xls)?', query)
                if quoted_match:
                    file_name = quoted_match.group(1).strip()
                
                # Then look for file name after specific keywords
                if not file_name:
                    for keyword in ['file', 'named', 'called', 'titled', 'read', 'open', 'show', 'get']:
                        if keyword in query.lower().split():
                            idx = query.lower().split().index(keyword)
                            if idx + 1 < len(query.split()):
                                file_name = query.split()[idx + 1].strip(',."\';:()')
                                break
                
                # If still no match, look for any potential filename
                if not file_name:
                    # Try to extract any word that could be a filename
                    words = query.split()
                    for word in words:
                        if len(word) > 2 and word.lower() not in ['the', 'and', 'for', 'from', 'with', 'file', 'drive', 'google']:
                            file_name = word.strip(',."\';:()')
                            break
            
            if not file_name:
                return {
                    'success': False,
                    'message': 'Please specify a file name to read.'
                }
            
            # Log the extracted file name for debugging
            logger.info(f"Looking for file: {file_name}")
            
            # Try multiple search strategies
            files = []
            
            # Strategy 1: Exact match
            files = list_files(query=f"name = '{file_name}'")
            
            # Strategy 2: Contains match
            if not files:
                files = list_files(query=f"name contains '{file_name}'")
                logger.info(f"Contains search found {len(files)} files")
            
            # Strategy 3: Case-insensitive search through all files
            if not files:
                logger.info("Trying case-insensitive search")
                all_files = list_files()
                matched_files = []
                
                for f in all_files:
                    if file_name.lower() in f['name'].lower():
                        matched_files.append(f)
                        logger.info(f"Found matching file: {f['name']}")
                
                files = matched_files
            
            if files:
                # If multiple files match, pick the most relevant one
                if len(files) > 1:
                    # Try to find exact match first
                    exact_matches = [f for f in files if f['name'].lower() == file_name.lower()]
                    if exact_matches:
                        file_id = exact_matches[0]['id']
                        logger.info(f"Selected exact match: {exact_matches[0]['name']}")
                    else:
                        # Otherwise pick the first match
                        file_id = files[0]['id']
                        logger.info(f"Selected first match: {files[0]['name']}")
                else:
                    file_id = files[0]['id']
                    logger.info(f"Selected only match: {files[0]['name']}")
            else:
                return {
                    'success': False,
                    'message': f'Could not find a file named "{file_name}" in your Google Drive. Please check the file name and try again.'
                }
            
            # Read the file content
            try:
                file_content = read_file_content(file_id)
                mime_type = file_content['mime_type']
                content = file_content['content']
                
                # For Excel files, ensure we have proper content
                if 'spreadsheet' in mime_type or any(ext in mime_type for ext in ['excel', 'xlsx', 'xls']):
                    # If content is already in our special format
                    if isinstance(content, dict) and 'text' in content and 'data' in content:
                        display_content = content['text']
                    else:
                        # If we got raw data, convert it to a readable format
                        if isinstance(content, list):
                            # Format the Excel data for display
                            display_content = "Excel File Contents:\n\n"
                            
                            if content and len(content) > 0:
                                # Get column headers from first row
                                headers = list(content[0].keys())
                                display_content += "Columns: " + ", ".join(headers) + "\n\n"
                                
                                # Add rows (up to 10)
                                max_rows = min(10, len(content))
                                display_content += f"Showing first {max_rows} rows (total rows: {len(content)}):\n\n"
                                
                                for i in range(max_rows):
                                    row = content[i]
                                    row_str = f"Row {i+1}: " + ", ".join([f"{h}: {row.get(h, '')}" for h in headers])
                                    display_content += row_str + "\n"
                            else:
                                display_content += "Excel file appears to be empty."
                        else:
                            display_content = str(content)
                            
                    return {
                        'success': True,
                        'message': f'Here is the content of "{file_name}":',
                        'file_name': file_name,
                        'content': display_content,
                        'mime_type': mime_type
                    }
                else:
                    # For non-Excel files, return content directly
                    return {
                        'success': True,
                        'message': f'Here is the content of "{file_name}":',
                        'file_name': file_name,
                        'content': content,
                        'mime_type': mime_type
                    }
            except Exception as e:
                logger.error(f"Error reading file content: {str(e)}")
                return {
                    'success': False,
                    'message': f'Error reading file content: {str(e)}',
                    'file_name': file_name
                }
            
        elif intent_type == 'create':
            # Get file name and content from parameters or extract from query
            file_name = parameters.get('file_name')
            content = parameters.get('content')
            file_type = parameters.get('file_type')
            
            # Log what we received from parameters
            logger.info(f"Create file parameters: name={file_name}, type={file_type}, content length={len(content) if content else 0}")
            
            # If file name not in parameters, try to extract from query
            if not file_name:
                # Try multiple patterns to extract file name
                patterns = [
                    # Quoted file name
                    r'(?:file|document|spreadsheet)\s+(?:called|named)\s+["\'](.*?)["\']\.?\s*(?:file|spreadsheet|document|xlsx|xls)?',
                    # Unquoted file name
                    r'(?:file|document|spreadsheet)\s+(?:called|named)\s+(\w+)\.?\s*(?:file|spreadsheet|document|xlsx|xls)?',
                    # Create a file named X
                    r'create\s+(?:a|an)?\s+(?:file|document|spreadsheet)\s+(?:called|named)?\s+["\'](.*?)["\']\.?',
                    # Create a file named X (unquoted)
                    r'create\s+(?:a|an)?\s+(?:file|document|spreadsheet)\s+(?:called|named)?\s+(\w+)\.?',
                    # File name at end of query
                    r'(?:file|document|spreadsheet)\s+(\w+)$',
                    # Named X
                    r'named\s+["\'](.*?)["\']\.?',
                    # Named X (unquoted)
                    r'named\s+(\w+)\.?'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, query, re.IGNORECASE)
                    if match:
                        file_name = match.group(1).strip()
                        logger.info(f"Extracted file name: {file_name} using pattern: {pattern}")
                        break
                
                # If still no file name, generate a default with timestamp
                if not file_name:
                    import time
                    file_name = f"new_file_{int(time.time())}.txt"
                    logger.info(f"Using default file name: {file_name}")
            
            # If content not in parameters, try to extract from query
            if not content:
                # Try multiple patterns to extract content
                content_patterns = [
                    # With content X
                    r'with\s+(?:content|text)\s+["\'](.*?)["\']\.?',
                    # Containing X
                    r'containing\s+["\'](.*?)["\']\.?',
                    # About X
                    r'about\s+["\'](.*?)["\']\.?',
                    # With content/text X (unquoted)
                    r'with\s+(?:content|text)\s+(.+?)(?:\.|$)',
                    # Containing X (unquoted)
                    r'containing\s+(.+?)(?:\.|$)',
                    # About X (unquoted)
                    r'about\s+(.+?)(?:\.|$)',
                    # Content: X
                    r'content:\s*(.+?)(?:\.|$)'
                ]
                
                for pattern in content_patterns:
                    match = re.search(pattern, query, re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()
                        logger.info(f"Extracted content: {content[:30]}... using pattern: {pattern}")
                        break
                
                # If still no content, use default
                if not content:
                    content = "This is a new file created by Agento Assistant."
                    logger.info("Using default content")
                    
            # Log what we extracted
            logger.info(f"Final file creation parameters: name={file_name}, content={content[:30]}...")
            
            # If no file type specified, try to infer from query or file name
            if not file_type:
                if any(keyword in query_lower for keyword in ['excel', 'spreadsheet', 'xlsx', 'xls']):
                    file_type = 'excel'
                elif any(keyword in query_lower for keyword in ['text', 'txt', 'document']):
                    file_type = 'text'
                elif file_name.endswith(('.xlsx', '.xls')):
                    file_type = 'excel'
                elif file_name.endswith(('.txt', '.md', '.csv', '.json', '.html', '.xml', '.log')):
                    file_type = 'text'
                else:
                    # Default to text
                    file_type = 'text'
            
            # Check if it's an Excel file request
            is_excel = file_type == 'excel' or 'excel' in query_lower or 'spreadsheet' in query_lower or file_name.endswith('.xlsx') or file_name.endswith('.xls')
            
            if is_excel:
                # For Excel files, try to parse content into tabular data or use sample data
                try:
                    # Try to convert content to structured data
                    import random
                    
                    # Check if content looks like structured data
                    structured_data = None
                    
                    # If content contains commas or tabs, try to parse as CSV-like data
                    if ',' in content or '\t' in content:
                        logger.info("Content contains commas or tabs, trying to parse as CSV data")
                        lines = content.strip().split('\n')
                        if len(lines) > 1:
                            # Try to parse as CSV
                            if ',' in lines[0]:
                                delimiter = ','
                            else:
                                delimiter = '\t'
                                
                            # Get headers from first line
                            headers = [h.strip() for h in lines[0].split(delimiter)]
                            
                            # Create data dictionary
                            structured_data = {header: [] for header in headers}
                            
                            # Add data rows
                            for i in range(1, len(lines)):
                                values = lines[i].split(delimiter)
                                for j, header in enumerate(headers):
                                    if j < len(values):
                                        structured_data[header].append(values[j].strip())
                                    else:
                                        structured_data[header].append('')
                    
                    # If we couldn't parse structured data, create sample data based on content
                    if not structured_data:
                        logger.info("Creating sample Excel data based on content")
                        
                        # Try to extract potential column names from content
                        potential_columns = re.findall(r'\b([A-Z][a-z]+)\b', content)
                        
                        if len(potential_columns) >= 2:
                            # Use extracted column names
                            columns = potential_columns[:3]  # Use up to 3 columns
                            structured_data = {}
                            
                            for i, col in enumerate(columns):
                                if i == 0:
                                    # First column uses content words
                                    words = [w for w in content.split() if len(w) > 3]
                                    if words:
                                        structured_data[col] = words[:5]  # Use up to 5 words
                                    else:
                                        structured_data[col] = [f"{col} {i}" for i in range(1, 6)]
                                elif i == 1:
                                    # Second column uses numbers
                                    structured_data[col] = [random.randint(1, 100) for _ in range(5)]
                                else:
                                    # Third column uses letters
                                    structured_data[col] = ['A', 'B', 'C', 'D', 'E']
                        else:
                            # Use default column names
                            structured_data = {
                                'Name': [f"{content.split()[0] if content.split() else 'Item'} {i}" for i in range(1, 6)],
                                'Value': [random.randint(1, 100) for _ in range(5)],
                                'Category': ['A', 'B', 'C', 'D', 'E']
                            }
                    
                    # Use the structured data
                    data = structured_data
                    
                    # Ensure file has .xlsx extension
                    if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                        file_name += '.xlsx'
                    
                    result = create_excel_file(file_name, data)
                    
                    if result:
                        # Log successful creation
                        logger.info(f"Successfully created Excel file: {file_name} with ID: {result['id']}")
                        return {
                            'success': True,
                            'message': f'Successfully created Excel file "{file_name}" in Google Drive.',
                            'file_id': result['id'],
                            'file_name': result['name']
                        }
                    else:
                        logger.error(f"Failed to create Excel file: {file_name} - create_excel_file returned None")
                        return {
                            'success': False,
                            'message': f'Failed to create Excel file "{file_name}" in Google Drive. Please check your Google Drive permissions.'
                        }
                except Exception as e:
                    logger.error(f"Error creating Excel file: {file_name} - {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error creating Excel file: {str(e)}. Please try again with a simpler file name or content.'
                    }
            else:
                # Create a regular text file
                # Ensure file has appropriate extension
                if not any(file_name.endswith(ext) for ext in ['.txt', '.md', '.csv', '.json', '.html', '.xml', '.log']):
                    file_name += '.txt'
                
                try:
                    # Log the attempt
                    logger.info(f"Creating text file: {file_name} with content length: {len(content)}")
                    result = create_file(file_name, content)
                    
                    if result:
                        # Log successful creation
                        logger.info(f"Successfully created text file: {file_name} with ID: {result['id']}")
                        return {
                            'success': True,
                            'message': f'Successfully created file "{file_name}" in Google Drive.',
                            'file_id': result['id'],
                            'file_name': result['name']
                        }
                    else:
                        # Log failure
                        logger.error(f"Failed to create text file: {file_name} - create_file returned None")
                        return {
                            'success': False,
                            'message': f'Failed to create file "{file_name}" in Google Drive. Please check your Google Drive permissions.'
                        }
                except Exception as e:
                    # Log exception
                    logger.error(f"Error creating text file: {file_name} - {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error creating file: {str(e)}. Please try again with a simpler file name or content.'
                    }
        
        return {
            'success': False,
            'message': 'Unknown Google Drive intent.'
        }
        
    except Exception as e:
        logger.error(f"Error processing Google Drive request: {str(e)}")
        return {
            'success': False,
            'message': f'Error processing Google Drive request: {str(e)}'
        }

def generate_drive_response(model, prompt, original_query, intent_type, session_id, request, parameters=None):
    """
    Generator function for handling Google Drive requests.
    
    Args:
        model (str): The LLM model to use
        prompt (str): The prompt with drive instructions
        original_query (str): The original user query
        intent_type (str): The type of drive intent
        session_id (str): The session ID
        request (HttpRequest): The Django request object
        parameters (dict): Optional extracted parameters from the query
        
    Yields:
        str: Server-sent event data for streaming response
    """
    # Import here to avoid circular imports
    import importlib
    views_module = importlib.import_module('.views', package='personalassistant')
    generate_streaming_response = views_module.generate_streaming_response
    
    # Process the drive request with parameters
    drive_result = process_drive_request(intent_type, original_query, parameters)
    
    # Create a prompt that includes the drive operation result
    if drive_result['success']:
        if intent_type == 'list' or intent_type == 'list_type':
            files_info = "\n".join([f"- {f['name']} ({f['mimeType']})" for f in drive_result.get('files', [])[:10]])
            if len(drive_result.get('files', [])) > 10:
                files_info += f"\n- ... and {len(drive_result.get('files', [])) - 10} more files"
                
            enhanced_prompt = (
                f"{prompt}\n\n"
                f"I've listed the files in your Google Drive. Here are the results:\n"
                f"{drive_result['message']}\n"
                f"{files_info}\n\n"
                f"Please summarize this information for the user in a helpful way."
            )
        elif intent_type == 'read':
            content_preview = drive_result.get('content', '')
            mime_type = drive_result.get('mime_type', '')
            
            # Handle Excel files specially
            if 'spreadsheet' in mime_type or any(ext in mime_type for ext in ['excel', 'xlsx', 'xls']):
                # Excel content is already formatted for readability
                enhanced_prompt = (
                    f"{prompt}\n\n"
                    f"I've read the Excel file '{drive_result.get('file_name', '')}' from your Google Drive.\n"
                    f"Here's the EXACT content of the file that I want you to display to the user:\n\n"
                    f"{content_preview}\n\n"
                    f"IMPORTANT: Do NOT give instructions on how to read the file. Instead, display the actual content shown above in a clear, formatted way.\n"
                    f"The file has already been read successfully, so just present the data I've provided above.\n"
                    f"DO NOT mention Google Drive API or code snippets unless specifically asked.\n"
                    f"Simply present the data in a readable format with appropriate formatting."
                )
            else:
                # For other file types
                if len(content_preview) > 500:
                    content_preview = content_preview[:500] + "... (content truncated)"
                    
                enhanced_prompt = (
                    f"{prompt}\n\n"
                    f"I've read the file '{drive_result.get('file_name', '')}' from your Google Drive. Here's the content:\n"
                    f"{content_preview}\n\n"
                    f"Please summarize this information for the user in a helpful way."
                )
        elif intent_type == 'create':
            enhanced_prompt = (
                f"{prompt}\n\n"
                f"I've created a file in your Google Drive:\n"
                f"File name: {drive_result.get('file_name', '')}\n"
                f"File ID: {drive_result.get('file_id', '')}\n\n"
                f"Please inform the user that the file was created successfully."
            )
        else:
            enhanced_prompt = prompt
    else:
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"There was an issue with the Google Drive operation:\n"
            f"{drive_result['message']}\n\n"
            f"Please inform the user about this issue and suggest alternatives if appropriate."
        )
    
    # Stream the LLM response with the enhanced prompt
    for chunk in generate_streaming_response(model, enhanced_prompt, session_id, request):
        yield chunk
