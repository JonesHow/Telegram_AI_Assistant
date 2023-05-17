import os
from dotenv import load_dotenv
from langchain import OpenAI, FAISS, PromptTemplate
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import VectorStoreRetrieverMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import Document

load_dotenv()

from langchain.callbacks import get_openai_callback
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter

# from langchain.vectorstores import Chroma
from langchain.vectorstores import Pinecone
import pinecone

# initialize pinecone
pinecone.init(
    api_key = os.getenv("PINECONE_API_KEY"),  # find at app.pinecone.io
    environment = os.getenv("PINECONE_ENV")  # next to api key in console
)

def importing_pdf(docs, doc_url):
    print (f'You have {len(docs)} characters in your {doc_url} data')
    # print (f'There are {len(docs[0].page_content)} characters in your document')

    # 切割文檔
    text_splitter = CharacterTextSplitter(separator="\n",
                                          chunk_size=700,
                                          chunk_overlap=30,
                                          length_function = len)

    # 加載切割後的文檔
    split_docs = text_splitter.split_text(docs)

    print (f'You have {len(split_docs)} split document(s)')

    embeddings = OpenAIEmbeddings()
    # index_name = "telegram-chat-bot"
    # Pinecone.from_documents(documents=docs, embedding=embeddings, index_name=index_name)
    db = FAISS.from_texts(split_docs, embeddings)
    db.save_local("save_pdf_index")

    response = "我已經讀取了 PDF，可以開始提問了！"

    return response

def chat_pdf(text):
    # docs = [Document(page_content="qwerytpuiohnas", metadata={"url": "None"})]
    embeddings = OpenAIEmbeddings()
    # index_name = "telegram-chat-bot"
    # docsearch = Pinecone.from_documents(documents=docs, embedding=embeddings, index_name=index_name)
    new_db  = FAISS.load_local("save_pdf_index", embeddings)
    docsearch = new_db.similarity_search(text)


    # system_template = """下面是一段人類與 AI 的友好對話。AI 很健談，並根據其上下文提供了許多具體細節。
    # 如果 AI 不知道問題的答案，AI 會如實說:"不知道"，不會編造不存在的資訊。
    #
    # 資料庫:
    # {vector_stores}
    #
    # (如果和當前對話内容不相關，就不需要使用歷史對話的信息。)
    #
    # 當前對話:
    # 人類: {question}
    # AI:
    #
    # """
    #
    # PROMPT = PromptTemplate(
    #     input_variables=[docsearch[:3000], "question"], template=system_template
    # )
    #
    # def get_chain(store):
    #     chain_type_kwargs = {"prompt": PROMPT}
    #     chain = RetrievalQAWithSourcesChain.from_chain_type(
    #         ChatOpenAI(temperature=0),
    #         chain_type="stuff",
    #         retriever=store.as_retriever(),
    #         chain_type_kwargs=chain_type_kwargs,
    #         reduce_k_below_max_tokens=True
    #     )
    #     return chain

    chain = load_qa_chain(OpenAI(), chain_type="stuff")

    response = chain.run(input_documents=docsearch[:3], question=text)

    return response