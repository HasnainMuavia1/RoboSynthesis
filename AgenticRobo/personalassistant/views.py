from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse
from django.views.decorators.http import require_POST
import json
import os
import requests
import uuid
import time
import base64
import io
import fitz  # PyMuPDF for PDF processing
import tempfile
import pandas as pd
from PIL import Image

from docx import Document
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import ConversationChain
from groq import AsyncGroq, Groq
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Load environment variables from .env file
load_dotenv()

# Initialize Tavily Search - match exactly what's in the Flask app
# Initialize Tavily Search
tavily_api_key = os.getenv('TAVILY_API_KEY')
tavily_search_searcher = TavilySearch(
    max_results=5,
    include_images=True,
    include_answer=True,
    api_key=tavily_api_key
)
print("Tavily Search initialized")
print(f"Tavily search type: {type(tavily_search_searcher)}")        
print(f"Tavily search dir: {dir(tavily_search_searcher)}")

# Dictionary to store conversation memories
conversation_memories = {}

def get_or_create_memory(session_id):
    """Get or create a conversation memory for the session"""
    if session_id not in conversation_memories:
        conversation_memories[session_id] = ConversationBufferMemory(return_messages=True)
    return conversation_memories[session_id]

def home(request):
    """View function for the home page of the site."""
    return render(request, 'personalassistant/index.html')

def signup(request):
    """View function for user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('personalassistant:home')
    else:
        form = UserCreationForm()
    return render(request, 'personalassistant/signup.html', {'form': form})


def login_view(request):
    """View function for user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('personalassistant:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'personalassistant/login.html', {'form': form})


def logout_view(request):
    """View function for user logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('personalassistant:home')


@login_required
def profile(request):
    """View function for user profile."""
    return render(request, 'personalassistant/profile.html')


@login_required
def dashboard(request):
    """View function for the dashboard page."""
    return render(request, 'personalassistant/dashboard.html')


@login_required
def agento_assistant(request):
    """View function for the Agento Assistant page."""
    return render(request, 'personalassistant/agento_assistant.html')


@login_required
def ai_tutor(request):
    """View for the AI Tutor page"""
    return render(request, 'personalassistant/ai_tutor.html')

@login_required
def mcp_config(request):
    """View for the MCP Configuration page"""
    return render(request, 'personalassistant/mcp_config.html')


# File processing functions
def process_image(file):
    """Extract text from image using Groq's vision model"""
    try:
        # Read the image file
        image_data = file.read()
        
        # Encode the image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Initialize Groq client
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Default query
        query = "What's in this image?"
        
        # Create chat completion with the image
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
        )
        
        # Extract the response
        response = chat_completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return f"Error processing image: {str(e)}"

def process_image_with_query(file, query):
    """Extract text from image using Groq's vision model with a specific query"""
    try:
        # Read the image file
        image_data = file.read()
        
        # Encode the image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Initialize Groq client
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Use the provided query or default
        if not query or query.strip() == "":
            query = "What's in this image?"
        
        # Create chat completion with the image
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
        )
        
        # Extract the response
        response = chat_completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return f"Error processing image: {str(e)}"


def process_pdf(file):
    """Extract text from PDF"""
    try:
        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        # Open the PDF with PyMuPDF
        doc = fitz.open(temp_file_path)
        text = ""
        
        # Extract text from each page
        for page in doc:
            text += page.get_text()
        
        # Close the document and remove the temporary file
        doc.close()
        os.unlink(temp_file_path)
        
        return text
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return f"Error processing PDF: {str(e)}"

def process_docx(file):
    """Extract text from DOCX"""
    try:
        doc = Document(file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error processing DOCX: {str(e)}")
        return f"Error processing DOCX: {str(e)}"

def process_txt(file):
    """Extract text from TXT"""
    try:
        text = file.read().decode('utf-8')
        return text
    except Exception as e:
        print(f"Error processing TXT: {str(e)}")
        return f"Error processing TXT: {str(e)}"

def process_csv(file):
    """Extract text from CSV"""
    try:
        df = pd.read_csv(file)
        return df.to_string()
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return f"Error processing CSV: {str(e)}"

def process_excel(file):
    """Extract text from Excel"""
    try:
        df = pd.read_excel(file)
        return df.to_string()
    except Exception as e:
        print(f"Error processing Excel: {str(e)}")
        return f"Error processing Excel: {str(e)}"

def process_file(file):
    """Process file based on its type"""
    filename = file.name.lower()
    
    if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        # Image processing is now handled separately in the upload route
        # This is to avoid double-processing
        return "Image processing handled separately"
    elif filename.endswith('.pdf'):
        return process_pdf(file)
    elif filename.endswith(('.doc', '.docx')):
        return process_docx(file)
    elif filename.endswith('.txt'):
        return process_txt(file)
    elif filename.endswith('.csv'):
        return process_csv(file)
    elif filename.endswith(('.xls', '.xlsx')):
        return process_excel(file)
    else:
        return "Unsupported file type"

def process_search_query(query):
    """Process a search query using Tavily Search API"""
    try:
        print(f"Searching with Tavily: {query}")
        
        # Use the correct method for TavilySearch
        search_results = tavily_search_searcher.invoke({"query": query})
        
        # Print the raw results for debugging
        print("Tavily search results:", json.dumps(search_results, indent=2))
        
        # Format the results for display
        formatted_results = {
            "query": query,
            "answer": search_results.get("answer", ""),
            "results": search_results.get("results", []),
            "images": search_results.get("images", []),
            "follow_up_questions": search_results.get("follow_up_questions", [])
        }
        
        return formatted_results
    except Exception as e:
        print(f"Error in Tavily search: {str(e)}")
        return {"error": str(e)}

# Get session ID from Django session
def get_session_id(request):
    """Get or create a session ID"""
    if 'session_id' not in request.session:
        request.session['session_id'] = str(uuid.uuid4())
    return request.session['session_id']

# API endpoints
@csrf_exempt
@login_required
def message_api(request):
    """Handle message API requests (both GET and POST)"""
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            # For POST requests, get data from JSON body
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                query = data.get('message', '')
                
                # Get session ID
                session_id = get_session_id(request)
                
                # Check if there's a file in the request
                if 'file' in data and data['file']:
                    base64_data = data['file']
                    extracted_text = process_base64_image(base64_data)
                    query = f"{query}\n\nContent extracted from image:\n{extracted_text}"
            else:
                # Handle form data if not JSON
                query = request.POST.get('message', '')
                session_id = get_session_id(request)
        else:
            # For GET requests, get data from query parameters
            query = request.GET.get('message', '')
            session_id = get_session_id(request)
        
        # Use fixed model ID as specified
        model = 'meta-llama/llama-4-scout-17b-16e-instruct'
        
        print(f"Using model: {model}")
        print(f"Query: {query}")
        
        # Always use streaming response
        return StreamingHttpResponse(
            generate_streaming_response(model, query, session_id, request),
            content_type='text/event-stream'
        )
    
    except Exception as e:
        print(f"Error in /api/message: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def upload_file(request):
    """Handle file upload requests"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file part'}, status=400)
        
        file = request.FILES['file']
        
        if file.name == '':
            return JsonResponse({'error': 'No selected file'}, status=400)
        
        # Get the query if provided
        query = request.POST.get('message', '')
        
        # Process the file based on its type
        filename = file.name.lower()
        
        if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # For images, use the vision model with query
            if query and query.strip():
                # Reset file pointer to beginning
                file.seek(0)
                extracted_text = process_image_with_query(file, query)
            else:
                # Reset file pointer to beginning
                file.seek(0)
                # Use default "What's in this image?" query
                extracted_text = process_image(file)
        else:
            # For other file types, use the regular processing
            extracted_text = process_file(file)
        
        return JsonResponse({'text': extracted_text})
    
    except Exception as e:
        print(f"Error in /api/upload: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def tavily_search(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            
            if not query:
                return JsonResponse({'error': 'Query is required'}, status=400)
            
            # Get session ID for memory management
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            
            search_results = process_search_query(query)
            
            # Add search response to memory buffer
            try:
                if session_id in conversation_memories:  # Use conversation_memories instead of conversation_memory
                    memory = conversation_memories[session_id]
                    
                    # Add user query to memory
                    memory.chat_memory.add_user_message(query)
                    
                    # Create a formatted response message from search results
                    search_response = ""
                    if search_results.get('answer'):
                        search_response = f"Search results: {search_results['answer']}"
                    elif search_results.get('results') and len(search_results['results']) > 0:
                        search_response = "Search results:\n"
                        for idx, result in enumerate(search_results['results'][:3]):
                            search_response += f"{idx+1}. {result['title']}: {result['content'][:100]}...\n"
                    else:
                        search_response = "No relevant search results found."
                    
                    # Add search response to memory
                    memory.chat_memory.add_ai_message(search_response)
            except Exception as mem_error:
                print(f"Memory error (non-critical): {str(mem_error)}")  # Log but don't fail the request
            
            return JsonResponse(search_results)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

def generate_streaming_response(model, query, session_id, request):
    """Generate a streaming response from the model with conversation memory"""
    try:
        print(f"Generating streaming response with model: {model}")
        print(f"Query: {query}")
        
        # Get or create memory for this session
        memory = get_or_create_memory(session_id)
        
        # Add the human message to memory
        memory.chat_memory.add_user_message(query)
        
        # Get the conversation history
        messages = memory.chat_memory.messages
        
        # Convert to the format expected by the Groq API
        groq_messages = []
        
        # Add system message
        groq_messages.append({
            "role": "system",
            "content": "You are a helpful assistant specialized in coding and study-related responses."
        })
        
        # Add conversation history
        for msg in messages:
            if isinstance(msg, HumanMessage):
                groq_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                groq_messages.append({"role": "assistant", "content": msg.content})
        
        # Initialize Groq client
        api_key = os.getenv('GROQ_API_KEY')
        client = Groq(api_key=api_key)
        
        # Create the streaming completion using the direct Groq client
        stream = client.chat.completions.create(
            messages=groq_messages,
            model='meta-llama/llama-4-scout-17b-16e-instruct',  # Use fixed model ID
            temperature=0.5,
            max_tokens=4000,
            top_p=1,
            stop=None,
            stream=True,
        )
        
        # Yield each chunk as a server-sent event
        yield f"data: {json.dumps({'status': 'start'})}\n\n"
        
        full_response = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                
                # Yield the chunk as a server-sent event
                yield f"data: {json.dumps({'content': content})}\n\n"
        
        # Add the full response to memory
        memory.chat_memory.add_ai_message(full_response)
        
        # Signal the end of the stream
        yield f"data: {json.dumps({'status': 'done'})}\n\n"
        
    except Exception as e:
        print(f"Error in generate_streaming_response: {str(e)}")
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
