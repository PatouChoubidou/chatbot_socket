from fastapi import FastAPI, WebSocket, File, UploadFile
from datetime import datetime
import json
import os
import base64
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
import shutil
import subprocess
from . import tts
from . import stt
from . import read_in 
from . import chatbot
from . import my_rag


'''
my ping pong transporter object looks like:
{ 
    "type": ""          -> string or binary,
    "name": "",         -> empty if no binary    
    "mime-type": "",    -> empty if no binary 
    "data": "",         -> is str or base64 encoded binary   
}
'''

app = FastAPI()
rag = my_rag.MyRAG()
conversation = []

# config
doc_dir = "docs"

isFullTextSearch = True

allowedUploadFileMimeTypes = [
  "application/pdf",
  "text/plain",
  "text/rtf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.oasis.opendocument.text"
]

system_template = f"""
    You are a helpful assistant who calls himself Colonel Pubert. 
    You can receive documents and answer questions about it. 
    The user can upload a file via drag 'n drop. 
    Always only one document at a time. 
    """

# cors
origins = [
    "http://localhost:5173",   
    "http://0.0.0.0:8000/uploadpdf"
] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST'],
    allow_headers=["*"],
)

# init a few things
if os.path.isdir(doc_dir):
     shutil.rmtree(doc_dir)

os.mkdir(doc_dir)


def newMessage(role, content):
    """
    Create a new Message and add it to the chat message list
    Params:
        - role: str The role can be either system, user, assistant or function see ollama chat
        - content: str The content of the message
    """
    now = datetime.now()
    conversation.append({
        "role": role,
        "content": content,
        "created_at": now.strftime("%d.%m.%Y %H:%M:%S")
    })


def toggleIsFullTextSearch(status: str):
    global isFullTextSearch
    print(f"inside toggle the full text search value = {isFullTextSearch}")
    if status == "ON":
        isFullTextSearch = True
    if status == "OFF":
        isFullTextSearch = False
    print(f"full text search value after = {isFullTextSearch}")


def clear_messages():
    """
    Clear all messages and init new conversation
    """
    conversation.clear()
    
    # first message is system template
    newMessage("system", system_template)


async def convertWebmToWav(filename):
    """
    Convert the users question as webm to a wav
    """
    out_name = filename.split('.')[0]
    subprocess.run(f'ffmpeg -y -i {filename} {out_name}.wav', shell=True)


async def updateFrontend(socket, all_messages):
    """
    Sends the updated Message List to the client
    """

    transporterObj = {
        "type": "string",
        "name": "message_list",
        "mime-type": "",
        "data": json.dumps(all_messages),
    }
    await socket.send_json(transporterObj)


async def ask_llm(question):
    """
    Clear all messages and init new conversation
    """
    # create new user message
    newMessage("user", question)
            
    # generate ollama chat response
    response = await chatbot.answer_question(messages=conversation)
    print(response)
            
    # create new model answer
    newMessage(response['message']['role'], response['message']['content'])


async def ask_rag(question):
    """
    Clear all messages and init new conversation
    """
    # create new user message
    newMessage("user", question)
            
    # generate ollama chat response
    response = await chatbot.anwser_question_with_rag(question, conversation, rag)
    print(response.message.content)
            
    # create new model answer
    newMessage('assistant', response.message.content)


async def ask_full_text(question):
    """
    Clear all messages and init new conversation
    """
    # create new user message
    newMessage("user", question)
            
    # get the path of the first doc in doc directory
    path = os.listdir(doc_dir)[0]

    print("inside ask full_text func app.py")
    
    # generate ollama chat response
    response = await chatbot.answer_question_with_full_text(question, dir_name=doc_dir, in_path=path, messages=conversation)
    print(response.message.content)
            
    # create new model answer
    newMessage('assistant', response.message.content)

 
@app.get("/wav")
async def sendAudio():
    file_name = "output.wav"
    # return FileResponse(path=file_name, filename=file_name, media_type='audio/wav')
    return FileResponse(path=file_name, filename=file_name, media_type='application/octet-stream')


@app.get("/doc-list")
async def sendDocList():
    if os.path.isdir(doc_dir):
        list_of_files = os.listdir(doc_dir)
        return JSONResponse(content=list_of_files)


@app.websocket("/chat")
async def chat(mywebsocket: WebSocket):
    # client wants to connect
    await mywebsocket.accept()
    print("websocket accepted - handshake from server")

    # reset messages
    clear_messages()
    
    # start ollama if not running
    if not await chatbot.is_ollama_running():
        await chatbot.start_ollama_on_mac()
    
    # start listening for new messages
    while True:
        
        # receive json aka text whith json encode afterwards
        json = await mywebsocket.receive_json()
        print(f'received json: \n {json}')
        
        # ----- case data is a binary -----
        if json["type"] == 'binary':

            # --- and file is audio/webm
            if json["mime-type"] == 'audio/webm;codecs=opus':
                print("it is an webm file")
                
                newMessage("system", "received your audio...")
                await updateFrontend(mywebsocket, conversation)

                file_name = 'in.webm'
                try:
                    withoutPrefix = json["data"].removeprefix("data:audio/webm;codecs=opus;base64,")
                    print(withoutPrefix)
                    file_content = base64.b64decode(withoutPrefix)
                    with open(file_name,"wb") as f:
                            f.write(file_content)
                except Exception as e:
                    print(e)
                
                newMessage("system", "transcribing audio...")
                await updateFrontend(mywebsocket, conversation)
                await convertWebmToWav(file_name)
                in_txt = await stt.transcribe(file_name)
                print(f"stt text {in_txt}")
                newMessage("user", in_txt)
                await updateFrontend(mywebsocket, conversation)

                response = await chatbot.ask_ollama(in_txt, conversation, isFullTextSearch, doc_dir, rag)
                newMessage(response['message']['role'], response['message']['content'])
                await updateFrontend(mywebsocket, conversation)



            # --- or file is pdf,
            if json["mime-type"] in allowedUploadFileMimeTypes:
                
                print("Document Received!")
                newMessage("system", "received your doc")
                await updateFrontend(mywebsocket, conversation)

                # clear folder
                
                if os.path.isdir(doc_dir):
                    shutil.rmtree(doc_dir)
                # make new folder
                if not os.path.isdir(doc_dir):
                    print('creating dir')
                    os.mkdir(doc_dir)
                
                file_name = json["name"]
                file_save_path = os.path.join(os.getcwd(), doc_dir, file_name)
                # save the file
                try:
                    # withoutPrefix = json["data"].removeprefix("data:application/pdf;base64,")
                    file_content = base64.b64decode(json["data"])
                    
                    print(file_save_path)
                    
                    with open(file_save_path, "wb") as f:
                            f.write(file_content)
                except Exception as e:
                    print(e)

                # MISSING -> the whole rag thing
                # get content chunks from pdf
                txt_data = []
                if json['mime-type'] == allowedUploadFileMimeTypes[0]:
                    # txt_data = await read_in.getDataFromPDF(doc_dir+"/"+file_name)
                    txt_data = await read_in.getDataFromPDF(file_save_path)
                if json['mime-type'] == allowedUploadFileMimeTypes[1] or json['mime-type'] == allowedUploadFileMimeTypes[2]:
                    txt_data = await read_in.getTextFromTxt(file_save_path)
                if json['mime-type'] == allowedUploadFileMimeTypes[3]:
                    txt_data = await read_in.getTextFromDocx(file_save_path)
                
                print(f"pdf data: {txt_data}")
                # put em in chroma db
                await rag.add_data_to_collection(txt_data)

                newMessage("system", "You can now ask questions concerning your doc")
                await updateFrontend(mywebsocket, conversation)

            
        # ----- case data is just text -----
        if json['type'] == 'string':

            # --- and text is a special function call - delete docs 
            if json['data'] == '@clearDocuments':
                # clear folder
              
                if os.path.isdir(doc_dir):
                    shutil.rmtree(doc_dir)

                # clear rag
                if await rag.delete_all_items_in_collection():
                    newMessage("system", "All docs have been deleted.")
                    await updateFrontend(mywebsocket, conversation)
                else:
                    newMessage("system", "No docs there.")
                    await updateFrontend(mywebsocket, conversation)
            

            # --- and text is a special function call - clear chat history
            if json['data'] == '@resetChatHistory':
                
                clear_messages()
                newMessage("system", "Chat history resetted.")
                await updateFrontend(mywebsocket, all_messages=conversation)
                print("chat history cleared")

            
             # --- and text is a special function call - toggle full text search
            if json['data'].startswith('@isFullTextSearchToggle'):
                status = json['data'].split("-")[1]
                toggleIsFullTextSearch(status)
               
                if status == 'ON':
                    newMessage("system", "Full text search enabled")
                    await updateFrontend(mywebsocket, all_messages=conversation)
                if status == 'OFF':
                    newMessage("system", "Full text search disabled")
                    await updateFrontend(mywebsocket, all_messages=conversation)
                
                print("fullTextSearchToggled")


            # --- or data is a standard question 
            if json['name'] == 'question':

                q = json['data']
                print(q)
                
                # if no pdf folder there make one
                if not os.path.isdir(doc_dir):
                    os.makedirs(doc_dir)
                
                response = await chatbot.ask_ollama( q, conversation, isFullTextSearch, doc_dir, rag)
                print(response['message']['content'])
                newMessage(response['message']['role'], response['message']['content'])
                
                # tts an audio of the chatbot response aka last message
                # audio is then fetched through api endpoint /wav from the client
                await tts.generateAiff(conversation[-1]['content'])

                # send all messages as json back to client
                await updateFrontend(mywebsocket, all_messages=conversation)

 