import streamlit as st
import requests
import fitz  # PyMuPDF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
 
# Database API details (replace with actual values)
DATABASE_API_URL = "http://localhost:8080/api/v1/user/get-user?id=1"
DATABASE_API_URL2 = "http://localhost:8080/api/v1/requirement/list-requirement"
 
# List of PDF file paths
PDF_FILE_PATHS = [
    r"/usr/app/app/data/24_karuppu_selva.pdf",
    r"/usr/app/app/data/26_akka_only.pdf"
]
 
def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
        return None
 
def extract_texts_from_pdfs(pdf_paths):
    combined_text = ""
    for path in pdf_paths:
        text = extract_text_from_pdf(path)
        if text:
            combined_text += text + "\n"
    return combined_text.strip()
 
pdf_texts = extract_texts_from_pdfs(PDF_FILE_PATHS)
 
def get_relevant_pdf_text(user_question, pdf_text):
    sentences = pdf_text.split('\n')
    vectorizer = TfidfVectorizer().fit_transform([user_question] + sentences)
    vectors = vectorizer.toarray()
    cosine_similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    relevant_sentences = [sentences[i] for i in cosine_similarities.argsort()[-5:][::-1]]
    return " ".join(relevant_sentences)
 
def connect_to_database_api():
    return requests.Session()
 
def get_answer_from_api(db_url, question, connection, method):
    query = {"q": question}
    try:
        response = connection.request(method, db_url, params=query if method.lower() == "get" else None, json=query if method.lower() == "post" else None)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error getting answer from API {db_url}: {e}")
        return None
 
def generate_response_with_ollama(prompt):
    # try:
    import ollama
    ollama_client = ollama(model="llama3", temperature=0.1, base_url="http://ollama_service:11434")
    print(ollama_client)
    response = ollama_client.chat(
        messages=[{'role': 'user', 'content': prompt}],
    )
    return response['message']['content']
    # except Exception as e:
    #     print(f"Error generating response with Ollama: {e}")
    #     return None
 
st.title("HR Chatbot")
user_question = st.text_input("Ask your question:")
 
if user_question:
    # connection = connect_to_database_api()
    api_1_answer = ''
    api_2_answer = ''
   
    # Convert dictionaries to strings before concatenating
    context_1 = str(api_1_answer) if api_1_answer else ""
    context_2 = str(api_2_answer) if api_2_answer else ""
    context_3 = get_relevant_pdf_text(user_question, pdf_texts) if pdf_texts else ""
    print(context_3)
    context = context_1 + " " + context_2 + " " + context_3
 
    prompt = f"""
    The user has asked the question: '{user_question}'
    Only include information that directly answers the question.
    Provide a concise and relevant answer within two lines without additional information:
    {context}
    """
    with st.spinner("Thinking..."):
        response = generate_response_with_ollama(prompt)
        if response:
            st.write(response)
        else:
            st.write("Sorry, I couldn't generate a response.")
else:
    st.write("Please enter a question.")