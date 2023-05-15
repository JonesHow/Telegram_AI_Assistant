import os

from langchain.callbacks import get_openai_callback
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

from key import *


def summarize_docs(docs, doc_url):
    print (f'You have {len(docs)} document(s) in your {doc_url} data')
    print (f'There are {len(docs[0].page_content)} characters in your document')

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

    split_docs = text_splitter.split_documents(docs)

    print (f'You have {len(split_docs)} split document(s)')

    os.environ["OPENAI_API_KEY"] = openai_api_key
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=1024)
    chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=False)

    with get_openai_callback() as cb:
        response = chain.run(input_documents=split_docs)
        print(f"Total Tokens: {cb.total_tokens}")
        print(f"Prompt Tokens: {cb.prompt_tokens}")
        print(f"Completion Tokens: {cb.completion_tokens}")
        print(f"Successful Requests: {cb.successful_requests}")
        print(f"Total Cost (USD): ${cb.total_cost}")

    return response