"""
Google Drive API utilities for RoboSynthesis
This module provides functions to interact with Google Drive:
- List all files
- List specific file types (e.g., Excel files)
- Read file contents
- Create files with content
"""

import os
import io
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import pandas as pd
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Path to the Google credentials file
CREDENTIALS_PATH = os.path.join('credentials', 'google_credentials.json')
TOKEN_PATH = os.path.join('credentials', 'drive_token.json')

def get_drive_service():
    """
    Create and return a Google Drive API service instance using OAuth credentials
    """
    try:
        creds = None
        
        # Check if credentials file exists
        if not os.path.exists(CREDENTIALS_PATH):
            logger.error("Google credentials file not found. Please connect Google Apps in MCP Config.")
            return None
            
        # Load credentials from token file if it exists
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_info(
                json.load(open(TOKEN_PATH)), SCOPES)
                
        # If credentials don't exist or are invalid, refresh or create new ones
        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Successfully refreshed Drive credentials")
                    except RefreshError as re:
                        logger.warning(f"Failed to refresh token: {str(re)}")
                        # If refresh fails, create new credentials
                        logger.info("Creating new credentials after refresh failure")
                        flow = InstalledAppFlow.from_client_secrets_file(
                            CREDENTIALS_PATH, SCOPES)
                        creds = flow.run_local_server(port=0)
                else:
                    # Create new credentials
                    logger.info("Creating new Drive credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)
            except Exception as auth_error:
                logger.error(f"Authentication error: {str(auth_error)}")
                return None
                
            # Save the credentials for the next run
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
                
        # Build and return the Drive service
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error creating Drive service: {str(e)}")
        return None

def list_files(page_size=100, query=None):
    """
    List files in Google Drive
    
    Args:
        page_size (int): Maximum number of files to return
        query (str): Search query (https://developers.google.com/drive/api/guides/search-files)
    
    Returns:
        list: List of file objects with id, name, mimeType, etc.
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("Failed to get Drive service")
            return []
            
        results = service.files().list(
            pageSize=page_size,
            fields="files(id, name, mimeType, createdTime, modifiedTime)",
            q=query
        ).execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return []
        logger.error(f"Unexpected error listing files: {str(e)}")
        raise

def list_files_by_type(file_type, page_size=100):
    """
    List files of a specific type in Google Drive
    
    Args:
        file_type (str): File type to filter by (e.g., 'excel', 'document', 'pdf')
        page_size (int): Maximum number of files to return
    
    Returns:
        list: List of file objects with id, name, mimeType, etc.
    """
    mime_types = {
        'excel': "application/vnd.google-apps.spreadsheet OR application/vnd.openxmlformats-officedocument.spreadsheetml.sheet OR application/vnd.ms-excel",
        'document': "application/vnd.google-apps.document OR application/vnd.openxmlformats-officedocument.wordprocessingml.document OR application/msword",
        'pdf': "application/pdf",
        'presentation': "application/vnd.google-apps.presentation OR application/vnd.openxmlformats-officedocument.presentationml.presentation OR application/vnd.ms-powerpoint",
        'image': "image/jpeg OR image/png OR image/gif",
        'video': "video/mp4 OR video/quicktime OR video/x-ms-wmv",
        'audio': "audio/mpeg OR audio/wav OR audio/ogg"
    }
    
    if file_type.lower() in mime_types:
        query = f"mimeType = {mime_types[file_type.lower()]}"
    else:
        # If the file type is not in our predefined list, try to use it directly
        query = f"mimeType contains '{file_type}'"
    
    return list_files(page_size=page_size, query=query)

def read_file_content(file_id):
    """
    Read the content of a file from Google Drive
    
    Args:
        file_id (str): ID of the file to read
    
    Returns:
        dict: Dictionary with file content, name, and mime_type
    """
    try:
        service = get_drive_service()
        
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id, fields="name,mimeType").execute()
        file_name = file_metadata.get('name', 'unknown')
        mime_type = file_metadata.get('mimeType', '')
        
        # Handle different file types for download
        file_content = io.BytesIO()
        
        # Check if this is a Google Workspace file that needs export
        google_workspace_types = [
            'application/vnd.google-apps.document',  # Google Docs
            'application/vnd.google-apps.spreadsheet',  # Google Sheets
            'application/vnd.google-apps.presentation',  # Google Slides
            'application/vnd.google-apps.drawing'  # Google Drawings
        ]
        
        if mime_type in google_workspace_types:
            logger.info(f"Exporting Google Workspace file: {file_name} ({mime_type})")
            
            # Determine export MIME type
            export_mime_type = 'application/pdf'  # Default to PDF
            
            if mime_type == 'application/vnd.google-apps.document':
                export_mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'  # Export as DOCX
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                export_mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # Export as XLSX
            elif mime_type == 'application/vnd.google-apps.presentation':
                export_mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'  # Export as PPTX
            
            # Export the file
            request = service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            logger.info(f"Exporting file {file_id} as {export_mime_type}")
        else:
            # For regular binary files, use get_media
            logger.info(f"Downloading binary file: {file_name} ({mime_type})")
            request = service.files().get_media(fileId=file_id)
        
        # Download the file content
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        file_content.seek(0)
        
        # Process content based on mime type
        content = None
        if 'spreadsheet' in mime_type or mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            # For Excel files, convert to DataFrame and then to a readable string format
            try:
                df = pd.read_excel(file_content)
                
                # Convert DataFrame to a readable string format
                if not df.empty:
                    # Get column headers
                    headers = df.columns.tolist()
                    
                    # Convert to a formatted string representation
                    string_content = "Excel File Contents:\n\n"
                    string_content += "Columns: " + ", ".join(headers) + "\n\n"
                    
                    # Add first 10 rows (or all if less than 10)
                    max_rows = min(10, len(df))
                    string_content += f"Showing first {max_rows} rows (total rows: {len(df)}):\n\n"
                    
                    # Format each row
                    for i in range(max_rows):
                        row = df.iloc[i]
                        row_str = f"Row {i+1}: " + ", ".join([f"{headers[j]}: {row[headers[j]]}" for j in range(len(headers))])
                        string_content += row_str + "\n"
                    
                    content = string_content
                else:
                    content = "Excel file is empty (no data found)."
            except Exception as excel_err:
                logger.error(f"Error processing Excel file: {str(excel_err)}")
                content = f"Could not read Excel file content: {str(excel_err)}"
                
            # Also include the dict representation for programmatic use
            try:
                content_dict = df.to_dict(orient='records')
                content = {
                    'text': content,
                    'data': content_dict
                }
            except:
                content = {
                    'text': content,
                    'data': []
                }
        elif mime_type in ['application/pdf']:
            # For PDF files, return binary content
            content = file_content.getvalue()
        elif mime_type in ['text/plain', 'text/csv']:
            # For text files, decode content
            content = file_content.getvalue().decode('utf-8')
        else:
            # For other files, return binary content
            content = file_content.getvalue()
        
        return {
            'name': file_name,
            'mime_type': mime_type,
            'content': content
        }
    except HttpError as error:
        logger.error(f"Error reading file content: {str(error)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading file content: {str(e)}")
        raise

def create_file(file_name, content, mime_type=None, folder_id=None):
    """
    Create a file in Google Drive with the given content
    
    Args:
        file_name (str): Name of the file to create
        content (str or bytes): Content to write to the file
        mime_type (str, optional): MIME type of the file
        folder_id (str, optional): ID of the folder to create the file in
    
    Returns:
        dict: File metadata including id, name, etc. or None if creation fails
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("Failed to get Drive service for file creation")
            return None
            
        # Determine MIME type if not provided
        if not mime_type:
            if file_name.endswith('.txt'):
                mime_type = 'text/plain'
            elif file_name.endswith('.csv'):
                mime_type = 'text/csv'
            elif file_name.endswith('.xlsx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif file_name.endswith('.docx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_name.endswith('.pdf'):
                mime_type = 'application/pdf'
            else:
                mime_type = 'text/plain'  # Default to text/plain
        
        logger.info(f"Creating file: {file_name} with mime type: {mime_type}")
        
        # Create file metadata
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create file content
        if isinstance(content, str):
            file_content = content.encode('utf-8')
        else:
            file_content = content
            
        # Create a temporary file to upload
        temp_file = io.BytesIO(file_content)
        
        # Create media
        media = MediaIoBaseUpload(
            temp_file,
            mimetype=mime_type,
            resumable=True
        )
        
        # Create the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,mimeType,webViewLink'
        ).execute()
        
        logger.info(f"File created successfully: {file.get('name')} with ID: {file.get('id')}")
        return file
        
    except HttpError as error:
        logger.error(f"Error creating file: {str(error)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating file: {str(e)}")
        return None

def create_excel_file(file_name, data, folder_id=None):
    """
    Create an Excel file in Google Drive with the given data
    
    Args:
        file_name (str): Name of the Excel file to create
        data (dict or DataFrame): Data to write to the Excel file
        folder_id (str, optional): ID of the folder to create the file in
    
    Returns:
        dict: File metadata including id, name, etc. or None if creation fails
    """
    try:
        # Ensure file has .xlsx extension
        if not file_name.endswith('.xlsx'):
            file_name += '.xlsx'
        
        logger.info(f"Creating Excel file: {file_name}")
        
        # Convert data to DataFrame if it's a dict
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            logger.error("Data must be a dictionary or DataFrame")
            return None
        
        # Create Excel file in memory
        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False)
        excel_data.seek(0)
        
        # Create file in Google Drive
        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return create_file(file_name, excel_data.getvalue(), mime_type, folder_id)
    except Exception as e:
        logger.error(f"Error creating Excel file: {str(e)}")
        return None
