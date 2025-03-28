# Chatbot with socket  

## backend
source .venv/bin/activate
fastapi dev app.py

### 
https://fastapi.tiangolo.com/advanced/websockets/#in-production

## Issues & Questions
- All files and text extraction is handled by the server, but one could use the frontend send text to the server's RAG? But python is maybe easier in handling files? 
    - PRO: less to do for the server
    - PRO: why not simple just simple chatbot that takes string without sending files back and forth
    - CONTRA: Most docx and pdf readers dont work on clients on pure js. The client needs to have things installed which it might not have


- handle multiple files at onece instead of one at a time ? 



