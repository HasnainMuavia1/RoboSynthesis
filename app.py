import base64
from flask import Flask, request, jsonify, render_template, Response, stream_with_context, session
from groq import Groq
import os
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from docx import Document
import tempfile
import json
import uuid
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_tavily import TavilySearch
import pandas as pd
import io
import fitz  # PyMuPDF for PDF processing

load_dotenv()

# Initialize Groq client
api_key = os.getenv('GROQ_API_KEY')
client = Groq(api_key=api_key)

# Initialize Tavily Search
tavily_api_key = os.getenv('TAVILY_API_KEY')
tavily_search = TavilySearch(
    max_results=5,
    include_images=True,
    include_answer=True,
    api_key=tavily_api_key
)

# Function to get LangChain Groq client with the selected model
def get_langchain_client(model_name="llama-3.3-70b-versatile"):
    """Get a LangChain Groq client with the specified model"""
    return ChatGroq(
        api_key=api_key,
        model_name=model_name,
        temperature=0.5
    )

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key-for-sessions')

# Dictionary to store conversation memories
conversation_memories = {}

def get_or_create_memory(session_id):
    """Get or create a conversation memory for the session"""
    if session_id not in conversation_memories:
        conversation_memories[session_id] = ConversationBufferMemory(return_messages=True)
    return conversation_memories[session_id]

def get_session_id():
    """Get or create a session ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

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

def process_base64_image(base64_data):
    """Extract text from base64 encoded image using OCR"""
    try:
        # Remove the data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode the base64 data
        image_data = base64.b64decode(base64_data)
        
        # Create an image from the binary data
        img = Image.open(io.BytesIO(image_data))
        
        # Perform OCR
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error processing base64 image: {str(e)}")
        return f"Error processing base64 image: {str(e)}"

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
    filename = file.filename.lower()
    
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
        
        # Invoke Tavily search
        search_results = tavily_search.invoke({"query": query})
        
        # Print the raw results for debugging
        print("Tavily search results:", json.dumps(search_results, indent=2))
        
        # Format the results for display
        formatted_results = {
            "query": search_results.get("query", ""),
            "answer": search_results.get("answer", ""),
            "results": search_results.get("results", []),
            "images": search_results.get("images", []),
            "follow_up_questions": search_results.get("follow_up_questions", [])
        }
        
        return formatted_results
    except Exception as e:
        print(f"Error in Tavily search: {str(e)}")
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/message', methods=['GET', 'POST'])
def message():
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            # For POST requests, get data from JSON body
            if request.is_json:
                data = request.json
                query = data.get('message', '')
                model = data.get('model', 'llama-3.3-70b-versatile')
                
                # Get session ID
                session_id = get_session_id()
                
                # Check if there's a file in the request
                if 'file' in data and data['file']:
                    base64_data = data['file']
                    extracted_text = process_base64_image(base64_data)
                    query = f"{query}\n\nContent extracted from image:\n{extracted_text}"
            else:
                # Handle form data if not JSON
                query = request.form.get('message', '')
                model = request.form.get('model', 'llama-3.3-70b-versatile')
                session_id = get_session_id()
        else:
            # For GET requests, get data from query parameters
            query = request.args.get('message', '')
            model = request.args.get('model', 'llama-3.3-70b-versatile')
            session_id = get_session_id()
        
        # Validate model name
        valid_models = [
            'llama-3.3-70b-versatile', 
            'mixtral-8x7b-32768', 
            'gemma-7b-it',
            'mistral-saba-24b',
            'qwen-2.5-coder-32b',
            'deepseek-r1-distill-qwen-32b',
            'deepseek-r1-distill-llama-70b',
            'llama-3.3-70b-specdec',
            'llama-guard-3-8b'
        ]
        model_mapping = {
            'groq': 'llama-3.3-70b-versatile',
            'groq-mixtral': 'mixtral-8x7b-32768',
            'groq-gemma': 'gemma-7b-it',
            'groq-mistral-saba': 'mistral-saba-24b',
            'groq-qwen-coder': 'qwen-2.5-coder-32b',
            'groq-deepseek-qwen': 'deepseek-r1-distill-qwen-32b',
            'groq-deepseek-llama': 'deepseek-r1-distill-llama-70b',
            'groq-llama-specdec': 'llama-3.3-70b-specdec',
            'groq-llama-guard': 'llama-guard-3-8b'
        }
        
        # Map frontend model selection to actual model names
        if model in model_mapping:
            model = model_mapping[model]
        
        # Ensure model is valid
        if model not in valid_models:
            model = 'llama-3.3-70b-versatile'  # Default to LLaMA 3 if invalid
        
        print(f"Using model: {model}")
        print(f"Query: {query}")
        
        # Always use streaming response
        return Response(
            stream_with_context(generate_streaming_response(model, query, session_id)),
            content_type='text/event-stream'
        )
    
    except Exception as e:
        print(f"Error in /api/message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Get the query if provided
        query = request.form.get('message', '')
        
        # Process the file based on its type
        filename = file.filename.lower()
        
        if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # For images, use the new vision model with query
            if query and query.strip():
                extracted_text = process_image_with_query(file, query)
            else:
                # Use default "What's in this image?" query
                extracted_text = process_image(file)
        else:
            # For other file types, use the regular processing
            extracted_text = process_file(file)
        
        return jsonify({'text': extracted_text})
    
    except Exception as e:
        print(f"Error in /api/upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Handle search requests using Tavily Search API"""
    try:
        data = request.json if request.is_json else request.form
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No search query provided"}), 400
        
        # Process the search query
        results = process_search_query(query)
        
        return jsonify(results)
    
    except Exception as e:
        print(f"Error in /api/search: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_streaming_response(model, query, session_id):
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
        
        # Create the streaming completion using the direct Groq client
        # This is simpler than using LangChain for streaming
        stream = client.chat.completions.create(
            messages=groq_messages,
            model=model,
            temperature=0.5,
            max_tokens=4000,
            top_p=1,
            stop=None,
            stream=True,
        )
        
        # Yield each chunk as a server-sent event
        yield "data: {\"status\":\"start\"}\n\n"
        
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
        yield "data: {\"status\":\"done\"}\n\n"
        
    except Exception as e:
        print(f"Error in generate_streaming_response: {str(e)}")
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

if __name__ == '__main__':
    app.run(debug=True)
