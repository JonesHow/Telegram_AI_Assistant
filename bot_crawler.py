import os
import re

from langchain.indexes import VectorstoreIndexCreator
from langchain.schema import Document
from langchain.utilities import apify, ApifyWrapper

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
apify = ApifyWrapper()

def crawler(text):
    print("hahaha")
    # pattern = r"https?://[\w./]+"
    # urls = re.findall(pattern, text)
    pattern = r"(https?://\S+?)(?=[\u4e00-\u9fff]|$)"
    urls = re.search(pattern, text, re.UNICODE).group(1)
    # urls = re.search(r"(https?://\S+?)(?=[\u4e00-\u9fff]|$)", text, re.UNICODE).group(1)
    print(urls)
    print(str(urls))
    loader = apify.call_actor(
        actor_id="apify/website-content-crawler",
        run_input={"startUrls": [{"url": urls}]},
        dataset_mapping_function=lambda item: Document(
            page_content=item["text"] or "", metadata={"source": item["url"]}
        ),
    )
    # 從爬取的文檔中初始化向量索引：
    index = VectorstoreIndexCreator().from_loaders([loader])
    result = index.query_with_sources(text.replace(urls, "").strip())
    f"{result['answer']} \n {result['sources']}"

    return()