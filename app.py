import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceInstructEmbeddings , HuggingFaceEmbeddings
from langchain.vectorstores import faiss ,chroma
from langchain.llms import  HuggingFaceHub , huggingface_hub
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from  HTMLtemp import css, bot_template, user_template

from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings


def get_pdf_text(Pdf_docs):
    text=''
    for pdf in Pdf_docs:
        pdf_reader=PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    return text

def get_text_chunks(raw_text):

    text_splitter=CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks=text_splitter.split_text(raw_text)
    return chunks


def get_vectorstores(text_chunks):

    # embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    #embeddings=HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore= chroma.from_texts(texts=text_chunks,embedding=embeddings)
    return vectorstore


def get_conversation_chain(vectorstore):
    #
    llm = huggingface_hub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})
    #llm = HuggingFaceHub(repo_id="HuggingFaceH4/zephyr-7b-alpha",model_kwargs={'temperature':0.1,'max-length':1024})
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)



def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with Documents", page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with multiple documents :books:")
    st.text_input("Ask a Question about your Document")
    with st.sidebar:
        st.subheader("Your documents")
        
        Pdf_docs = st.file_uploader("Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                #get pdf text        #completed
                raw_text=get_pdf_text(Pdf_docs)
                

                #get the text chunks      #completed
                text_chunks=get_text_chunks(raw_text) 
          
                #store in vector          #completed

                vectorstore=get_vectorstores(text_chunks)

                 
                st.session_state.conversation = get_conversation_chain(vectorstore)


if __name__ == '__main__':
    main()