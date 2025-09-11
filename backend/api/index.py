from dotenv import load_dotenv
from openai import OpenAI
import os, base64
from io import BytesIO
from typing import Optional
from pydantic import BaseModel, Field
from pypdf import PdfReader
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import Flask, request, jsonify
import json

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
load_dotenv()
app = Flask(__name__)
DEFAULT_PROMPT="""You are an AI assistant that summarizes entire documents given in text form seperated by Page in detail.
        Your job is to create a structured summary that follows this exact format:

        1. Page-by-Page Summaries

        For each page of the document, provide a clear summary of its contents. Keep the structure as:
        Page X: [summary of that page]

        Preserve important facts, data, arguments, definitions, or examples from each page.

        Be concise but do not skip over key points.

        2. Overall Summary

        After the page-by-page breakdown, write a long-form summary of the entire document that integrates the main ideas across all pages.

        3. Key Takeaways

        List 5–10 of the most important insights or conclusions from the document.

        4. What’s Next

        Suggest logical next steps, applications, or questions for further exploration based on the document’s content.

        Rules:

        Do not add outside information. Use only the document’s content.

        Keep everything clear, structured, and organized so the output can be easily read or exported to a PDF.

        Also make sure if the page is diagram you explain that diagram.
        """

def extract_text_from_pdf(fileHandle):
    text = []
    reader = PdfReader(fileHandle)
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        text.append(f"Page {i+1}: {page_text}")
    return "\n\n".join(text)
    


def AIModel(text, prompt):
   
    client = OpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    class JsonStructure(BaseModel):
        fileName: str = Field(description="Please just give File name and not the extension")
        title: str = Field(description="It should end with summary like xyz Summary")
        summary: str 

    completion = client.beta.chat.completions.parse(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content":  prompt},
            {"role": "user", "content": text},
        ],
        response_format=JsonStructure,
    )
    return completion.choices[0].message.parsed

def getCreds(SCOPES):
    token_json = base64.b64decode(os.getenv("GOOGLE_TOKEN_JSON_BASE64")).decode()
    if not token_json:
        raise RuntimeError("Missing GOOGLE_TOKEN_JSON env var. Paste your token.json there.")
    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
    return creds
# google 

def createDoc(title, creds):    
    try:
        service = build("docs", "v1", credentials=creds)
        body = {
            'title': title
        }
    
        doc = service.documents() \
            .create(body=body).execute()
    
        return doc.get("documentId"), service, creds
    except HttpError as err:
        print(err)

   
def insertText(text, DOCUMENT_ID, service, creds):
    requests = [
        {
        'insertText': {
            'location': {
                'index': 1,
            },
            'text': text
            }
        }
    ]

    result = service.documents().batchUpdate(
    documentId=DOCUMENT_ID, body={'requests': requests}).execute()

def insertToFolder(DOCUMENT_ID, creds):
    FOLDER_ID = os.getenv("FOLDER_ID")
    drive = build("drive", "v3", credentials=creds)
    # First get current parents
    file_meta = drive.files().get(fileId=DOCUMENT_ID, fields="parents").execute()
    prev_parents = ",".join(file_meta.get("parents", []))
    drive.files().update(
        fileId=DOCUMENT_ID,
        addParents=FOLDER_ID,
        removeParents=prev_parents if prev_parents else None,
        fields="id, parents"
    ).execute()

@app.get("/")
def helloMessage():
    return jsonify({"status": True, "message": "hello"}), 201

        
@app.post("/summaries")
def summarixe_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({"status": False, "message": "Please upload a file."}), 400
        pdf = request.files['file']

        if not pdf.filename.lower().endswith(".pdf"):
            return jsonify({"status": False, "message": "Please uplaod a PDF"}), 400
        
        
        file_bytes = pdf.read()
        textExtracted = extract_text_from_pdf(BytesIO(file_bytes))
        response = AIModel(textExtracted, DEFAULT_PROMPT)
        SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive.file",]
        creds = getCreds(SCOPES)
        documentId, service, creds = createDoc(response.title, creds)
        insertText(response.summary, documentId, service, creds)
        insertToFolder(documentId, creds)
        return (jsonify({"status": True, "documentId":documentId, "fileName": response.title})), 201
    except HttpError as gerr:
        return jsonify({"status": False, "message": str(gerr)}), 502
    except Exception as e:
        return jsonify({"status": False, "message": str(e)}), 500




