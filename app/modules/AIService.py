from flask import Flask, request,jsonify, g
from werkzeug.utils import secure_filename
from app.modules.PdfGeneration import PdfGeneration
import os
import requests
import sqlite3
import numpy as np

app = Flask(__name__)

DOC_UPLOAD_FOLDER = app.config['DOC_UPLOAD_FOLDER']
COMPANY_DOC_UPLOAD_FOLDER= app.config['COMPANY_DOC_UPLOAD_FOLDER']

class AIService:

    """
    Function to upload the file to server
    """
    @staticmethod
    def uploadFile():
        if request.method == 'POST':
            # Check if the POST request has the file part
            if 'file' not in request.files:
                return 'No file part'

            file = request.files['file']

            # If user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                return jsonify({'status': "failed", 'message' : "File Uploaded failed", "file_name" : ''}), 200
            if file:
                # Save the uploaded file
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['COMPANY_DOC_UPLOAD_FOLDER'], filename)
                print(f"Saving file to: {file_path}")  # Debugging line
                file.save(file_path)
                return jsonify({'status': "success", 'message' : "File Uploaded successfully", "file_name" : file_path}), 200
                
    """
    Function to Get Result based on given questions
    """
    @staticmethod
    def getFile():
        param = request.json    
        questions = list(param['question'].split(","))
        fileName = param['file_name']
        #Load PDF files from data directory that is present inside project folder
        documents = AIService.getPdfFile(fileName) 
        #split the data using RecursiveCharacterTextSplitter
        text = AIService.splitData(documents)
        #Embeddings the data using HuggingFaceEmbeddings
        db = AIService.DataEmbeddings(text, fileName)
        # db = AIService.DataEmbeddingsWithSqlite3(text)
        #LLM
        llm = AIService.loadOllamLLM()
        #Analysis the data using LLM
        data = AIService.AIAnalysisData(llm, db, questions)

        #PDF Creation 
        PdfGeneration.generate_pdf(data);
        print(data)
        return jsonify({'number_of_documents': "success"}), 200
    
    @staticmethod
     # Load PDF files from data directory that is present inside project folder
    def getPdfFile(fileName):
        from langchain_community.document_loaders.pdf import PyPDFLoader
        loader= PyPDFLoader(fileName)
        return loader.load()
    
    @staticmethod
    #split the data using RecursiveCharacterTextSplitter
    def splitData(documents):
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)        
        return text_splitter.split_documents(documents)
    
    @staticmethod
    def DataEmbeddings(texts, file_name):
        print(texts)
        fileName = file_name.split('/')
        # Embeddings
        from langchain_community.embeddings import HuggingFaceEmbeddings
        DB_FAISS_PATH = f'vectorstore/{fileName[len(fileName) - 1]}_faiss/db_faiss'
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})
            
        # Save Faiss vactor DB
        from langchain_community.vectorstores import FAISS
        db = FAISS.from_documents(texts, embeddings)
        db.save_local(DB_FAISS_PATH)
        return db
    
    @staticmethod
    def loadOllamLLM():
        from langchain_community.llms import Ollama
        #local lama2 llm
        return Ollama(model="llama3", temperature=0.1, base_url="http://ollama_service:11434")
    
    
    @staticmethod
    def AIAnalysisData(llm, db, questions):
        from langchain.chains import ConversationalRetrievalChain
        chat_history =  []
        data =[]

        legal_standards = """
                Consider the following as our legal standards:
                1. Invoice raised by Quess has to be paid within 30 days of invoice date.
                2. If the client would like to terminate the contract for any reason, the client should provide a 30 days notice period to Quess.
                """
        for item in questions:
            # prompt = f"Can you verify if the following statement is correct based on the document: {item}?"
            prompt = f"""
                        Quess is Our Company. Please verify if the following statements from the client's new PO align with our legal standards:
                        
                        {legal_standards}
                        
                        Statement: "{item}"
                        
                        For each statement, please provide:
                        1. A determination of whether it is in conflict with our standards (CONFLICT or Inline with Quess policy).
                        2. If there is a conflict, describe the conflict.
                        3. Suggested actions to resolve the conflict, such as requesting the client to update the PO or getting an internal approval from the CFO.
                        """
          # Set up the Conversational Retrieval Chain
            qa_chain = ConversationalRetrievalChain.from_llm(
                        llm,
                        db.as_retriever(search_kwargs={'k': 2}),
                        return_source_documents=True)
            result = qa_chain.invoke({'question': prompt, 'chat_history': chat_history, })
            print("Question : "+ item)
            print("Answets : "+ result['answer'])
            result['item']= item;
            chat_history.append((item, result['answer']))      
            data.append(result)
        return data
    

    # @staticmethod
    # def vector_to_blob(vector):
    #     return vector.tobytes()

    # @staticmethod
    # def blob_to_vector(blob, dtype=np.float64):
    #     return np.frombuffer(blob, dtype=dtype)

    # @staticmethod
    # def save_vector_to_db(vector):
    #     db = get_db()
    #     vector_blob = AIService.vector_to_blob(vector)
    #     cursor = db.cursor()
    #     cursor.execute('SELECT id FROM vectors WHERE vector=?', (vector_blob,))
    #     data = cursor.fetchone()

    #     if data is None:
    #         cursor.execute('INSERT INTO vectors (vector) VALUES (?)', (vector_blob,))
    #         db.commit()
    #         print("Vector saved.")
    #     else:
    #         print("Vector already exists in the database.")

    # @staticmethod
    # def retrieve_vectors_from_db():
    #     db = get_db()
    #     cursor = db.cursor()
    #     cursor.execute('SELECT vector FROM vectors') 
    #     rows = cursor.fetchall()
    #     return [AIService.blob_to_vector(row[0]) for row in rows]

    # @staticmethod 
    # def DataEmbeddingsWithSqlite3(texts):
    #     import numpy as np
    #     # Embeddings
    #     from langchain_community.embeddings import HuggingFaceEmbeddings
    #     embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})
    #     for text in texts:
    #         embedding = embeddings.embed_query(text.page_content)
    #         AIService.save_vector_to_db(np.array(embedding))
            
    #     return AIService.retrieve_vectors_from_db()



# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(DATABASE_PATH)
#         g.db.execute('''
#         CREATE TABLE IF NOT EXISTS vectors (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             vector BLOB
#         )
#         ''')
#     return g.db

# @app.teardown_appcontext
# def close_db(exception):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()
# DATABASE_PATH = 'vector_db.sqlite'
    