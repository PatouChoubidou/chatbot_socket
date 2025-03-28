import ollama
import requests
import subprocess
from datetime import datetime
from . import my_rag
import os
from . import read_in

# https://github.com/ollama/ollama-python

async def answer_question(messages):
    """
    Takes a list of messages and returns an ollama response object
    Params:
        messages: list[message] - a list of ollama chat messages
    Returns:
        ollama ChatResponse 
    """
    response = await ollama.AsyncClient().chat(model='llama3.2', messages=messages)
    return response


async def answer_question_with_full_text(question_in: str, dir_name: str, in_path: os.path, messages):
    """
    Takes the users question, the conversation history and a os path obj returns an ollama response object
    Params:
        question_in: str - the users question
        in_path: os.path -  the path to the file
        messages: list[message] - a list of ollama chat messages
    Returns:
        ollama ChatResponse 
    """
    doc_text = ""

    filenameAndExtension = os.path.basename(in_path)
    filename = os.path.splitext(filenameAndExtension)[0]
    file_extension = os.path.splitext(filenameAndExtension)[1]

    print(f"filename is: {filename}")
    print(f"file_extension is: {file_extension}")

    path_with_dir = os.path.join(dir_name, in_path)

    if file_extension == ".pdf":
        doc_text = await read_in.getFullTextFromPDF(path_with_dir)
    if file_extension == ".docx" or file_extension == ".doc":
        doc_text = await read_in.getFullTextFromDoc(path_with_dir)
    if file_extension == ".txt" or file_extension == ".rtf":
        doc_text = await read_in.getFullTextFromTxt(path_with_dir)

    print(f"full text of doc: \n {doc_text}")

    prompt = f"""
        Answer the question in the language of the question below:

        Use the full text of this document {doc_text}.
        Use the metadata of this document search to explain your quotations. 
        Improve your anwser for follow up questions with the former conversation history: {messages}.
        Do not make anything up. 

        Question: {question_in}

        Answer:
    """

    message = {
        "role": 'user',
        "content": prompt,   
    }

    response = await ollama.AsyncClient().chat(model='llama3.2', messages=[message])
    return response



async def anwser_question_with_rag(question_in: str, messages: list, rag: my_rag.MyRAG):
    """
    Answer the user question usind the former message history and the RAG search output
    Params:
        question_in: str - the users question
        messages: list - former messages
        rag: - the Retrieval db
    Returns:
        ollama ChatResponse 
    """
    search_results = await rag.searchDocs(question_in, max_results=10)
    print(f"\ndocument search: \n{search_results['documents']}\n")
     
    prompt = f"""
        Answer the question in the language of the question below:

        Use the result of this document search {search_results}.
        Use the metadata of this document search to explain your quotations. 
        Improve your anwser for follow up questions with the former conversation history: {messages}.
        Do not make anything up. 

        Question: {question_in}

        Answer:
    """

    message = {
        "role": 'user',
        "content": prompt,   
    }
    
    response = await ollama.AsyncClient().chat(model='llama3.2', messages=[message])
    return response
   

async def is_ollama_running():
    """
    Pings the local ollama server and checks if it is running
    """
    ollama_url = "http://localhost:11434"
    try:
        req = requests.get(ollama_url)
        if req.status_code == 200:
            return True
    except:
        return False
    
      
async def start_ollama_on_mac():
    """
    Start the local ollama dev server via subprocess on mac osx
    """
    t_text = f'open -a "ollama"'
    proc = subprocess.run(t_text, shell=True)
    if proc.returncode == 0:
         print (f"ollama dev server started")
    else:
        print(f"ollama dev server could not be started")


async def stop_ollama_on_mac():
    """
    Stop the local ollama dev server via subprocess on mac osx
    """
    t_text = f"osascript -e 'quit app \"ollama\"'"
    proc = subprocess.run(t_text, shell=True)
    if proc.returncode == 0:
         print (f"ollama dev server stopped")
    else:
        print(f"ollama dev server could not be stopped")
   

  
    
