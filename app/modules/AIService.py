from flask import Flask, request,jsonify
from werkzeug.utils import secure_filename
from app.modules.PdfGeneration import PdfGeneration
import os
import requests

app = Flask(__name__)

UPLOAD_FOLDER = '/usr/app/app/data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
   os.makedirs(UPLOAD_FOLDER)

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
                return 'No selected file'

            if file:
                # Save the uploaded file
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"Saving file to: {file_path}")  # Debugging line
                file.save(file_path)
                return 'File uploaded successfully'
    """
    Function to Get Result based on given questions
    """
    @staticmethod
    def getFile():
        param = request.json    
        questions = list(param['question'].split(","))
        #Load PDF files from data directory that is present inside project folder
        documents = AIService.getPdfFile() 
        #split the data using RecursiveCharacterTextSplitter
        text = AIService.splitData(documents)
        db = AIService.DataEmbeddings(text)
        llm = AIService.loadOllamLLM()
        data = AIService.AIAnalysisData(llm, db, questions)
        PdfGeneration.generate_pdf(data);
        print(data)
        return jsonify({'number_of_documents': "success"}), 200
    

    @staticmethod
     # Load PDF files from data directory that is present inside project folder
    def getPdfFile():
        from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
        loader= PyPDFDirectoryLoader(app.config['UPLOAD_FOLDER'])
        return loader.load()
    
    @staticmethod
    #split the data using RecursiveCharacterTextSplitter
    def splitData(documents):
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)        
        return text_splitter.split_documents(documents)
    
    @staticmethod
    def DataEmbeddings(texts):
        
        # Embeddings
        from langchain_community.embeddings import HuggingFaceEmbeddings
        DB_FAISS_PATH = 'vectorstore/db_faiss'
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
        for item in questions:
            # Set up the Conversational Retrieval Chain
            qa_chain = ConversationalRetrievalChain.from_llm(
                        llm,
                        db.as_retriever(search_kwargs={'k': 2}),
                        return_source_documents=True)
            result = qa_chain.invoke({'question': item, 'chat_history': [], })
            print("Question : "+ item)
            print("Answets : "+ result['answer'])
            chat_history.append((item, result['answer']))      
            data.append(result)
        return data