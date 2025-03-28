# Chatbot for documents using a socket connection
This is a test for chatting with uploaded document-files locally.  
Handles pdf, docx, rtf, txt files.

## Fatures
- Switch between a RAG search for input or use the whole text as llm context. 
- Drag n drop a document file to question it or delete the document and just chat. 
- Start a new conversation and delete the former conversation history.
- Switch audio reply to autoplay.

## Tools in use 
### backend
- llm interaction: Ollama 
- server: Fastapi
- stt: whisper
- tts: pyttsx3
- rag: Chroma DB 

### frontend
- Vue.js

## Usage
#### backend
source .venv/bin/activate
fastapi dev app.py

#### frontend
npm run dev



