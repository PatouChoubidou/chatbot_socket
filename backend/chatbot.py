import ollama
from ollama import ChatResponse
import requests
import subprocess
from datetime import datetime
from . import my_rag
import os
from . import read_in

# https://github.com/ollama/ollama-python


async def ask_ollama(user_question: str, messages: list, isFullText: bool, file_dir: str, rag: my_rag.MyRAG):
    """
    Generate an answer. If the full text search option is false 
    and a document is uploaded it uses a rag search. 
    If no document is uploaded it just chats away...
    Params:
        user_question: str - the users question
        messages: list[message] - the conversation history
        file_dir: str - the directory in which the uploaded documents are stored
        rag: MyRAG - an interface for chroma db 
    Returns: 
        response: Ollama ChatResponse - 
    """
    doc_txt = "empty"
    
    if isFullText:
        print("\n using full text search\n")
        
        for file_path in os.listdir(file_dir):
            
            filenameAndExtension = os.path.basename(file_path)
            filename = os.path.splitext(filenameAndExtension)[0]
            file_extension = os.path.splitext(filenameAndExtension)[1]
            
            print(f"filename is: {filename}")
            print(f"file_extension is: {file_extension}")
         
            path_with_dir = os.path.join(file_dir, file_path)

            doc_txt += f"\n{filenameAndExtension}:\n"

            if file_extension == ".pdf":
                doc_txt += await read_in.getFullTextFromPDF(path_with_dir)
            if file_extension == ".docx" or file_extension == ".doc":
                doc_txt += await read_in.getFullTextFromDoc(path_with_dir)
            if file_extension == ".txt" or file_extension == ".rtf":
                doc_txt += await read_in.getFullTextFromTxt(path_with_dir)
    
    else:
        print("\nusing rag search\n")
        doc_txt = await rag.searchDocs(user_question, max_results=10)

    prompt = f"""
        Answer the question in the language of the question below:

        If not empty, use the result of this document search: {doc_txt}.
        Use given metadata to refine your anwers quotations.
        
        If the document text is empty anwswer by your best knowlegde. 
        Improve your anwser for follow up questions with the former conversation history: {messages}.
        Do not make anything up. 

        Question: {user_question}

        Answer:
    """

    print(prompt)
    message = {
        "role": 'user',
        "content": prompt,   
    }

    response = await ollama.AsyncClient().chat(model='llama3.2', messages=[message])
    return response


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
   




'''
##### --------- Here come a few functions which were used before ---------#####

async def answer_question(messages):
    """
    Takes a list of messages and returns an ollama response object
    Use this Function if no other Function fits.
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



async def ask_ollama_func(user_q, messages):
    """
    Here the idea would be to let the model choose which search the user wants and call them as func.
    """
   
    avaiable_funcs = {
        'anwser_question_with_rag': anwser_question_with_rag,
        'answer_question': answer_question,
        'answer_question_with_full_text':answer_question_with_full_text,
    }

    response = await ollama.AsyncClient().chat(
            'llama3.2',
            messages=[{'role': 'user', 'content': user_q }],
            tools=[anwser_question_with_rag,
                   answer_question,
                   answer_question_with_full_text
                ],
        )

    print('the response: ', response, '\n\n')

    #check if tool call is initated
    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            if function_to_call := avaiable_funcs.get(tool.function.name):
                print('\nCalling function: ', tool.function.name)
                print('\nArguments: , \n', tool.function.arguments, "\n")
                print('\nFunction Output: \n', function_to_call(**tool.function.arguments), "\n")
                response = function_to_call(**tool.function.arguments)
            else: 
                print('\nFunction: ', tool.function.name, 'not found') 

      
    prompt2 = f"""
            Answer the question below:
            Use the result of this search {response}.
            Question: {user_q}  

            Answer:           
     """
        
    result = await ollama.AsyncClient().chat(
        'llama3',
        messages=[{'role': 'user', 'content': prompt2 }],
    )

'''
    
      


  
    
