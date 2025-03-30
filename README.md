# Chatbot for documents 
This is a test for chatting with one uploaded document locally.  
Handles pdf, docx, rtf, txt files.


The socket connection is something I personally havent used a lot...



https://github.com/user-attachments/assets/79de14bd-73c2-4f25-b386-dc4061304108



## Fatures
- Takes user input in audio or text form
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

## Questions Arise
Should it be extendend to use multiple files? It easily can be


