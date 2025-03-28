# Chatbot with socket
This is test for chatting with uploaded pdf-files locally.
Personally used socket the first time.  

## backend
source .venv/bin/activate
fastapi dev app.py

## frontend
npm run dev

### 
https://fastapi.tiangolo.com/advanced/websockets/#in-production

## Issues & Questions
- All files are handled on the server, but maybe use frontend to handle files and just send text to servers RAG? But python is maybe easier in handling files? 

- what about text files

- question multiple files ? or always just one ? 

- maybe use python docx to extract data from docs
```python
import docx

def getText(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)
```
