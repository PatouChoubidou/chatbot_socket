# Chatbot with socket  

## backend
source .venv/bin/activate
fastapi dev app.py

### 
https://fastapi.tiangolo.com/advanced/websockets/#in-production

## Issues & Questions
- All files and text extraction is handled by the server, but one could use the frontend send text only to the server's RAG? On the other hand python has probably better possibilities to cope with files? 
    - PRO: less to do for the server
    - PRO: using a simple chatbot that takes string without all that sending files back and forth
    - CONTRA: Most docx and pdf readers dont work on clients on pure js. The client needs to have things installed which it might not have...

- What about handling multiple files at once instead of only one at a time? 
- Change the seperator while reading in pdf so that one chunk of text has more context?



