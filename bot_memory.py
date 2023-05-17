import os
from dotenv import load_dotenv
from langchain.schema import Document

load_dotenv()
from datetime import datetime
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

# from langchain.vectorstores import Pinecone
from langchain.vectorstores import Pinecone
import pinecone


# initialize pinecone
pinecone.init(
    api_key = os.getenv("PINECONE_API_KEY"),  # find at app.pinecone.io
    environment = os.getenv("PINECONE_ENV")  # next to api key in console
)


# persist_directory = "qa_memory_storage"
# current_path = os.getcwd()
# if not os.path.isdir(current_path + "/qa_memory_storage/"):
#     loader = TextLoader(current_path + "\\memory_init.txt", encoding="utf-8")
#     documents = loader.load()
#     text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
#     docs = text_splitter.split_documents(documents)
#     vectorstore = Chroma.from_documents(docs, embeddings, persist_directory=persist_directory)
#     vectorstore.persist()


def qa_memory(ask_question, llm):

    # Load the vectorstore from disk
    # vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    #
    # query = ask_question
    # docs = vectordb.similarity_search(query)
    docs = [Document(page_content="qwerytpuiohnas", metadata={"url": "None"})]
    embeddings = OpenAIEmbeddings()
    index_name = "telegram-chat-bot"
    vectorstore = Pinecone.from_documents(documents=docs, embedding=embeddings, index_name=index_name)
    # the vector lookup still returns the semantically relevant information
    retriever = vectorstore.as_retriever(search_kwargs=dict(k=4))
    memory = VectorStoreRetrieverMemory(retriever=retriever)

    _DEFAULT_TEMPLATE = """下面是一段人類與 AI 的友好對話。AI 很健談，並根據其上下文提供了許多具體細節。
    如果 AI 不知道問題的答案，AI 會如實說不知道，不會編造不存在的資訊。
    
    歷史對話:
    {history}

    (如果和當前對話内容不相關，就不需要使用歷史對話的信息。)

    當前對話:
    人類: {input}
    AI:"""

    PROMPT = PromptTemplate(
        input_variables=["history", "input"], template=_DEFAULT_TEMPLATE
    )

    conversation_with_summary = ConversationChain(
        llm=llm,
        prompt=PROMPT,
        memory=memory,
        verbose=True
    )

    ai_answer = conversation_with_summary.predict(input=ask_question)

    return ai_answer