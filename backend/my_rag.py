import ollama
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings, Settings
from dotenv import dotenv_values
from . import read_in
from datetime import datetime


'''
# one text object looks like this:
{
    newTextObj["filename"] = fileName
    newTextObj["content"] = paragraph or peace of txt
    newTextObj["page"] = pageNum from the pdf 
    newTextObj["paragraph"] = paraIndex + 1 or id
}
'''

class MyEmbeddingFunction(EmbeddingFunction):
    """
    Takes a peace of text and returns an embedding vector
    Depends:
        - ollama 
        - some embedding model
    """
    def __call__(self, docs: Documents) -> Embeddings:
        config = dotenv_values(".env")
        embeddings = []
        # embed the documents somehow
        for i, doc in enumerate(docs):
            response = ollama.embeddings(model=config['EMBEDDING_MODEL'], prompt=doc)
            embedding = response["embedding"]
            embeddings.append(embedding)
            
        return embeddings


class MyRAG():
    """
    Initialize a chroma db (sqlite type db specialized for vectors) with the data from an env file
    """
    def __init__(self, my_documents=[], collection_name="my_collection", persist_dir="/db",  embedding_model="nomic-embed-text"):
            config = dotenv_values(".env")
            self.id_num = 0
            self.documents = my_documents
            self.collection_name =  config['CHROMA_COLLECTION_NAME'] or collection_name 
            self.persist_dir = config['CHROMA_DB_DIR'] or persist_dir  
            self.embedding_model = config['EMBEDDING_MODEL'] or embedding_model  
            self.chroma_client = chromadb.PersistentClient(path=self.persist_dir, settings=Settings(anonymized_telemetry=False))
            '''metadata valid options for the distance algorithmn hnsw:space are: "l2", "ip, "or "cosine", 
            meaning squred l2, Inner Product, Cosine Similarity'''
            # self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name, metadata={"hnsw:space": config['CHROMA_DISTANCE_ALGO']}, embedding_function=MyEmbeddingFunction())
            self.collection = chromadb.Client().create_collection(name=self.collection_name, embedding_function=MyEmbeddingFunction())
            
   
    async def add_all_docs_to_collection(self):
        """
        Take peaces of text-objects from read_in.py and insert them in the db
        """
        # print('\ninside documents size is:', len(self.documents), self.documents)
        # ---- ADD TO COLLECTION -----
        for i, docObj in enumerate(self.documents):
            print(docObj)
             
            fileName = docObj["filename"]
            page = str(docObj["page"])
            paragraph = str(docObj["paragraph"])
            content = docObj["content"]
             
            metaData = f'file: {fileName} - page: {page} - paragraph: {paragraph}'
             
            if(content):
                self.collection.add(
                    ids = [str(i+1)],
                    documents = [content],
                    metadatas = [{"source": metaData}]
                )
     
             
    async def searchDocs(self, question: str, max_results: int=1):
        """
        Question the chroma db  with a text query
        Params: 
            question: str - the query
            max_results: number - the maximum number of results
        Returns:
            results: type unknown

            https://docs.trychroma.com/docs/querying-collections/full-text-search
        """
        print(self.collection)
        
        return self.collection.query(
                query_texts=question,
                n_results=max_results,
                # include=["embeddings", "documents", "metadatas", "distances"],
                include=["documents", "metadatas"],
                )
        
    
    async def delete_all_items_in_collection(self):
        """
        Delete all items in collection 
        client.list_collections() not working right now
        """
        # if collection is not empty
        if self.collection.get()["ids"]: 
            print(f"List of items/ids in collection before deletion: {self.collection.get()["ids"]}")
            self.collection.delete(self.collection.get()["ids"])
            print(f"List of items in collection after deletion: {self.collection.get()["ids"]}")
            return True
        else:
            print('collection already empty')
            return False
            


    def add_all_pdfs_to_docs(self, dirname="/pdfs"):
        """
        Using read_in.py to add all documents of a given directory to the rags docs
        Params:
            dirname: str - name of the directory
        """
        data=[]
        data = read_in.readAllPDFs(dirname)
        self.documents = data


    async def add_pdf_to_docs(self, file_name, dir_name="/pdfs", ):
        """
        Add one pdf to the self documents
        Params:
            file_name: str - name of file e.g. test.pdf
            dir_name: str - name of the directory the file is in 
        """
        pdf_data = []
        pdf_data  = await read_in.getDataFromPDF(dir_name+"/"+file_name)
        self.documents.extend(pdf_data)


    async def add_data_to_collection(self, data):
        """
        Take list of text-objects data from read_in.py and inserts them in the db
        Params:
            data: list[myTextObj] - list of the text obj with keys: filename, page, paragaph, content
        """
        for i, docObj in enumerate(data):
            try:
                print(docObj)
                
                fileName = docObj["filename"]
                page = str(docObj["page"])
                paragraph = str(docObj["paragraph"])
                content = docObj["content"]
                
                metaData = f'file: {fileName} - page: {page} - paragraph: {paragraph}'
                this_id = f"id{self.id_num + 1}"
                
                if(content and content != ''):
                    self.collection.add(
                        ids = [this_id],
                        documents = [content],
                        metadatas = [{"source": metaData}]
                    )
                self.id_num = self.id_num + 1
            except Exception as e: 
                print(e)








