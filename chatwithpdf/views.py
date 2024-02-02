# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import GPT2Tokenizer
from .main import parse_pdf, text_to_docs, docs_to_index
from io import BytesIO
from datetime import datetime
import openai
import csv
from .models import TokenUsage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView



# Set OpenAI API Key from settings
openai.api_key = settings.API_KEY

# Initialize documents and vector index
documents = []  # You may need to populate this based on your use case
vectordb = None  # You may need to initialize and populate this based on your use case

# Chatbot prompt template
PROMPT_TEMPLATE = """
You are a helpful Assistant who retrieves all related information about a specific topic from a provided document.

Provide all relevant information based on the user query from the content of the PDF extract with metadata.

Keep your answers exactly as they appear in the document without modifications or personal interpretation.

Match user queries with the exact text from the document.

Focus on the metadata, particularly 'filename' and 'page' when answering.

The evidence is solely from the content of the PDF extract.

Respond with "Not applicable" if the text is irrelevant.

The PDF content is:
{pdf_extract}
"""

# Initialize GPT-2 tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")


# Function to calculate tokens and cost
def calculate_tokens_and_cost(messages, cost_per_token):
    total_tokens = 0
    for message in messages:
        tokens = len(tokenizer.encode(message["content"]))
        total_tokens += tokens

    # Calculate cost based on the number of tokens
    cost = total_tokens * cost_per_token

    return total_tokens, cost


# Function to process user question
def process_user_question(user_question, vectordb):
    try:
        # Search the vectordb for similar content to the user's question
        search_results = vectordb.similarity_search(user_question, k=3)
        pdf_extract = "\n".join([result.page_content for result in search_results])

        # Update the prompt with the pdf extract
        prompt = [
            {"role": "system", "content": PROMPT_TEMPLATE.format(pdf_extract=pdf_extract)},
            {"role": "user", "content": user_question}
        ]

        # Call ChatGPT without streaming
        result = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt, stream=False)

        # Get the assistant's message from the result
        assistant_message = result['choices'][0]['message']['content']

        # Calculate tokens and cost
        messages = prompt + [{"role": "assistant", "content": assistant_message}]
        total_tokens, cost = calculate_tokens_and_cost(messages, settings.COST_PER_TOKEN)

        # Store token usage data in the database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for message in messages:
            # Create a TokenUsage object and save it to the database
            TokenUsage.objects.create(
                role=message['role'],
                content=message['content'],
                tokens=len(tokenizer.encode(message['content'])),
                cost=cost,
                timestamp=timestamp
            )

        return {'response': assistant_message}

    except Exception as e:
        # Handle unexpected errors
        print(f"Error processing user question: {e}")
        return {'response': 'Error: Unable to process the user question. Please Upload the Pdf.'}

# Django view to render the index page and redirect to the 'ask' page
def index(request):
    return redirect('ask_page')

# Django view to render the ask page
def ask_page(request):
    return render(request, 'ask_page.html')

# Django view to handle user question
@csrf_exempt
def ask(request):
    if request.method == 'POST':
        user_question = request.POST.get('question')
        result = process_user_question(user_question, vectordb)
        return JsonResponse(result)
    else:
        # If it's a GET request, just render the ask page
        return render(request, 'ask_page.html')

# Django view to render the upload page
def upload_page(request):
    return render(request, 'upload_page.html')

# Django view to handle uploaded PDF file
@csrf_exempt
def upload_pdf(request):
    try:
        # Check if the POST request has the file part
        if 'pdfFile' not in request.FILES:
            return JsonResponse({'response': 'Error: No file part'})

        pdf_file = request.FILES['pdfFile']

        # Check if the file is not empty
        if pdf_file.name == '':
            return JsonResponse({'response': 'Error: No selected file'})

        # Check if the file is a PDF
        if pdf_file.name.endswith('.pdf'):
            # Process the uploaded PDF file and update documents and vectordb
            text, filename = parse_pdf(BytesIO(pdf_file.read()), pdf_file.name)
            new_docs = text_to_docs(text, filename)

            # Add the new documents to the existing documents
            global documents
            documents.extend(new_docs)

            # Update the vector index with the new documents
            global vectordb
            if vectordb is None:
                vectordb = docs_to_index(documents, openai.api_key)
            else:
                vectordb.update(new_docs)

            return JsonResponse({'response': 'Upload successful'})
        else:
            return JsonResponse({'response': 'Error: Invalid file format. Please upload a PDF file'})
    except Exception as e:
        # Handle unexpected errors
        print(f"Error uploading PDF: {e}")
        return JsonResponse({'response': 'Error: Unable to upload the PDF. Please check the server logs for details.'})

# Django view to render the download CSV page
def download_csv_page(request):
    return render(request, 'download_csv_page.html')

# Django view to serve the CSV file
def download_csv(request):
    try:
        # Query token usage data from the database
        token_usage_data = TokenUsage.objects.values()

        # Generate CSV content
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="token_usage.csv"'

        # Write CSV headers
        csv_writer = csv.writer(response)
        csv_writer.writerow(['role', 'content', 'tokens', 'cost', 'timestamp'])

        # Write CSV data
        for row in token_usage_data:
            csv_writer.writerow([row['role'], row['content'], row['tokens'], row['cost'], row['timestamp']])

        return response

    except Exception as e:
        return JsonResponse({'response': f'Error: {str(e)}'})



class AskPageView(LoginRequiredMixin, View):
    login_url = 'login'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        return render(request, 'ask_page.html')

    @csrf_exempt
    def post(self, request):
        user_question = request.POST.get('question')
        result = process_user_question(user_question, vectordb)
        return JsonResponse(result)

class SignupView(View):
    template_name = 'signup.html'
    
    def get(self, request):
        form = UserCreationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # You may want to redirect to the login page or some other page after successful registration
            return redirect('login')
        return render(request, self.template_name, {'form': form})