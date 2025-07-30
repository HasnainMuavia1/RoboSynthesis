"""
Google Drive API views for RoboSynthesis
This module provides API endpoints to interact with Google Drive:
- List all files
- List specific file types (e.g., Excel files)
- Read file contents
- Create files with content
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from . import google_drive_utils

# Set up logging
logger = logging.getLogger(__name__)

@login_required
@require_GET
def list_drive_files(request):
    """
    API endpoint to list files in Google Drive
    
    Query parameters:
    - page_size: Maximum number of files to return (default: 100)
    - query: Search query (optional)
    """
    try:
        page_size = int(request.GET.get('page_size', 100))
        query = request.GET.get('query')
        
        files = google_drive_utils.list_files(page_size=page_size, query=query)
        
        return JsonResponse({
            'success': True,
            'files': files
        })
    except Exception as e:
        logger.error(f"Error listing Drive files: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_GET
def list_drive_files_by_type(request, file_type):
    """
    API endpoint to list files of a specific type in Google Drive
    
    Path parameters:
    - file_type: File type to filter by (e.g., 'excel', 'document', 'pdf')
    
    Query parameters:
    - page_size: Maximum number of files to return (default: 100)
    """
    try:
        page_size = int(request.GET.get('page_size', 100))
        
        files = google_drive_utils.list_files_by_type(file_type=file_type, page_size=page_size)
        
        return JsonResponse({
            'success': True,
            'file_type': file_type,
            'files': files
        })
    except Exception as e:
        logger.error(f"Error listing Drive files by type: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_GET
def read_drive_file(request, file_id):
    """
    API endpoint to read the content of a file from Google Drive
    
    Path parameters:
    - file_id: ID of the file to read
    
    Query parameters:
    - format: Format to return the content in (default: 'json')
    """
    try:
        format_type = request.GET.get('format', 'json')
        
        file_data = google_drive_utils.read_file_content(file_id=file_id)
        
        if format_type == 'raw' and isinstance(file_data['content'], bytes):
            # Return raw file content
            response = HttpResponse(
                file_data['content'],
                content_type=file_data['mime_type']
            )
            response['Content-Disposition'] = f'attachment; filename="{file_data["name"]}"'
            return response
        else:
            # Return JSON response
            return JsonResponse({
                'success': True,
                'file': {
                    'name': file_data['name'],
                    'mime_type': file_data['mime_type'],
                    'content': file_data['content'] if not isinstance(file_data['content'], bytes) else '[Binary content]'
                }
            })
    except Exception as e:
        logger.error(f"Error reading Drive file: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_POST
def create_drive_file(request):
    """
    API endpoint to create a file in Google Drive
    
    Request body:
    - file_name: Name of the file to create
    - content: Content to write to the file
    - mime_type: MIME type of the file (optional)
    - folder_id: ID of the folder to create the file in (optional)
    """
    try:
        data = json.loads(request.body)
        file_name = data.get('file_name')
        content = data.get('content')
        mime_type = data.get('mime_type')
        folder_id = data.get('folder_id')
        
        if not file_name or content is None:
            return JsonResponse({
                'success': False,
                'error': 'file_name and content are required'
            }, status=400)
        
        file = google_drive_utils.create_file(
            file_name=file_name,
            content=content,
            mime_type=mime_type,
            folder_id=folder_id
        )
        
        return JsonResponse({
            'success': True,
            'file': file
        })
    except Exception as e:
        logger.error(f"Error creating Drive file: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_POST
def create_drive_excel(request):
    """
    API endpoint to create an Excel file in Google Drive
    
    Request body:
    - file_name: Name of the Excel file to create
    - data: Data to write to the Excel file (as JSON)
    - folder_id: ID of the folder to create the file in (optional)
    """
    try:
        data = json.loads(request.body)
        file_name = data.get('file_name')
        excel_data = data.get('data')
        folder_id = data.get('folder_id')
        
        if not file_name or not excel_data:
            return JsonResponse({
                'success': False,
                'error': 'file_name and data are required'
            }, status=400)
        
        file = google_drive_utils.create_excel_file(
            file_name=file_name,
            data=excel_data,
            folder_id=folder_id
        )
        
        return JsonResponse({
            'success': True,
            'file': file
        })
    except Exception as e:
        logger.error(f"Error creating Drive Excel file: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
