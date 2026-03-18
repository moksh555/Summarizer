# 📄 PDF Summarizer

A full-stack web application that accepts a PDF upload, uses Google Gemini to generate a structured document summary, and saves the result directly to Google Docs in a designated Drive folder — giving you a shareable, editable summary in seconds.

## How It Works

1. User uploads a PDF via the React frontend
2. The Flask backend extracts text from every page using `pypdf`
3. The extracted text is sent to **Gemini 2.0 Flash** via the OpenAI-compatible Google Generative Language API
4. Gemini returns a structured JSON response containing:
   - A **page-by-page breakdown** of the document
   - A **long-form overall summary** integrating the key ideas
   - **5–10 key takeaways**
   - **Suggested next steps** for further exploration
5. The backend creates a new **Google Doc** via the Google Docs API, inserts the summary text, and moves it into a pre-configured Drive folder
6. The frontend receives the `documentId` and displays a direct link to open the Google Doc

## Key Features

- **Structured AI summaries** — Gemini is prompted to produce page-by-page, overall, takeaways, and next-steps sections in a consistent JSON schema enforced with Pydantic
- **Google Docs integration** — summaries are written directly into Google Docs via the Docs and Drive APIs, organized in a shared folder
- **Upload progress bar** — real-time upload percentage shown during PDF transmission
- **PDF-only validation** — both client and server enforce `.pdf` file type
- **Deployed on Vercel** — backend served via Vercel's serverless Python runtime (`backend/vercel.json`)

## Tech Stack

| Layer | Technology |
|---|---|
| Language (Backend) | Python 3.x |
| Web Framework | Flask + flask-cors |
| LLM | Google Gemini 2.0 Flash (via OpenAI-compatible API) |
| PDF Parsing | pypdf |
| Data Validation | Pydantic v2 |
| Google Integration | Google Docs API + Drive API (`google-api-python-client`) |
| Auth (Google) | `google-auth`, `google-auth-oauthlib` |
| Language (Frontend) | JavaScript (ES Modules) |
| UI Library | React |
| HTTP | Axios |
| Build Tool | Vite |
| Deployment | Vercel (backend + frontend) |

## Project Structure

```
├── backend/
│   ├── api/index.py        # Flask app: PDF upload, Gemini summarization, Google Docs creation
│   ├── requirements.txt
│   └── vercel.json         # Vercel serverless config
└── frontend/my-vite-app/
    └── src/
        ├── components/
        │   ├── Form.jsx    # Upload form with progress bar and result display
        │   ├── Header.jsx
        │   └── Footer.jsx
        ├── Home.jsx
        └── App.jsx
```

## Setup & Installation

**Prerequisites**: Python 3.x, Node.js 18+, a Google Cloud project with Docs and Drive APIs enabled, a Gemini API key, and OAuth 2.0 credentials.

### Backend

1. **Navigate to the backend directory**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up Google OAuth** — complete the OAuth flow locally once to generate `token.json`, then base64-encode it:
   ```bash
   python -c "import base64; print(base64.b64encode(open('token.json').read().encode()).decode())"
   ```

3. **Configure environment** — create a `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_TOKEN_JSON_BASE64=<base64_encoded_token_json>
   FOLDER_ID=your_google_drive_folder_id
   ```

4. **Run the Flask server**
   ```bash
   flask --app api/index run --port 5000
   ```

### Frontend

```bash
cd frontend/my-vite-app
npm install
# Create .env:
echo "VITE_API_BASE_URL=http://localhost:5000" > .env
npm run dev
```

## Usage

1. Open the app in your browser
2. Click **Choose File** and select a PDF
3. Click **Summarize** — a progress bar shows upload status
4. When complete, a link to the newly created Google Doc appears
5. Click **Open Google Doc** to view and share your structured summary
