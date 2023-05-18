# 引入必要的模組
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader

from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredURLLoader, PyPDFLoader
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain import GoogleSerperAPIWrapper
from langchain.tools import Tool

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters

from bot_crawler import crawler
from bot_summarize import summarize_docs
from bot_memory import qa_memory
from bot_import_pdf import importing_pdf, chat_pdf

# 設定你的 token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", streaming=True, callbacks=[StreamingStdOutCallbackHandler()])

# 建立 Google 搜尋物件
search = GoogleSerperAPIWrapper()
tools = [
    Tool(
        name="Intermediate Answer",
        func=search.run,
        description="useful for when you need to ask with search"
    )
]
# 初始化搜尋工具，verbose=True 會打印全部執行詳情
self_ask_with_search = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# 建立 Telegram 的 updater 和 dispatcher 物件
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# 創建必要文件夾
current_path = os.getcwd()
if not os.path.isdir(current_path + "/pdfs/"):
    os.makedirs(current_path + "/pdfs/")

# 定義 /start command 的處理函數
def start(update: Update, context: CallbackContext) -> None:
    # 發送一個歡迎訊息
    update.message.reply_text("歡迎使用，我是 Gin 智慧助理！")
    # 初始化特殊屬性
    context.user_data["chat_with_pdf"] = False


# 定義 /help command 的處理函數
def help(update: Update, context: CallbackContext) -> None:
    # 初始化特殊屬性
    context.user_data["chat_with_pdf"] = False
    # 發送一個說明訊息
    update.message.reply_text("你可以使用以下的 command：\n"
                              "/start - 開始使用 bot\n"
                              "/help - 查看說明\n"
                              "/summarize - 對一個 URL 或 PDF 進行摘要\n"
                              "/importpdf - 將 PDF 存儲進向量資料庫")


# 定義 /summarize command 的處理函數
def summarize(update: Update, context: CallbackContext) -> None:
    # 建立兩個按鈕叫“URL”和“PDF”
    keyboard = [
        [
            InlineKeyboardButton("URL", callback_data="url"),
            InlineKeyboardButton("PDF", callback_data="pdf"),
        ]
    ]
    # 建立一個按鈕選單
    reply_markup = InlineKeyboardMarkup(keyboard)
    # 發送一個訊息並附上按鈕選單
    update.message.reply_text("請選擇你想要摘要的類型：", reply_markup=reply_markup)


# 定義 /importpdf command 的處理函數
def importpdf(update: Update, context: CallbackContext) -> None:
    # 發送一個訊息要求用戶給一個 PDF
    update.message.reply_text("請給我一個 PDF 檔案，我會讀取並儲存它。")
    # 設定用戶資料中的 summarize_type 為 pdf，以便後續處理
    context.user_data["importpdf"] = True


# 定義按鈕回調的處理函數
def button(update: Update, context: CallbackContext) -> None:
    # 獲取按鈕的資料
    query = update.callback_query
    data = query.data

    # 根據不同的資料執行不同的動作
    if data == "url":
        # 發送一個訊息要求用戶給一個 URL 網址
        query.message.reply_text("請給我一個 URL 網址，我會對它進行摘要。")
        # 設定用戶資料中的 summarize_type 為 url，以便後續處理
        context.user_data["summarize_type"] = "url"
    elif data == "pdf":
        # 發送一個訊息要求用戶給一個 PDF 檔案
        query.message.reply_text("請給我一個 PDF 檔案，我會對它進行摘要。")
        # 設定用戶資料中的 summarize_type 為 pdf，以便後續處理
        context.user_data["summarize_type"] = "pdf"


# 定義用戶文字的處理函數
def text(update: Update, context: CallbackContext) -> None:
    # 獲取用戶發送的文字
    text = update.message.text

    # 根據不同的文字執行不同的動作
    if "哈嘍" in text:
        update.message.reply_text("你好！有什麽可以幫助你的嗎？")
    elif "搜尋網頁" in text:
        update.message.reply_text(self_ask_with_search.run(text))
    elif "幫我爬蟲" in text:
        update.message.reply_text("好的，請給我網址和爬蟲要求。\n(為了更好地識別，請在網址前後空一格)")
        context.user_data["crawler"] = True
    elif "查看sql" in text:
        # update.message.reply_text(search_sql(text, llm))
        update.message.reply_text("抱歉，SQL 功能還在開發中。")
    elif "關閉pdf" in text:
        context.user_data["chat_with_pdf"] = False
        update.message.reply_text("好的，不談 pdf 的内容了，我們來聊些別的吧！")
    elif "查看pdf" in text or context.user_data["chat_with_pdf"] == True:
        update.message.reply_text(chat_pdf(text))
        context.user_data["chat_with_pdf"] = True
    else:
        # update.message.reply_text("你說了：" + text) # Testing
        update.message.reply_text(qa_memory(text, llm))


# 定義用戶 URL 的處理函數
def url(update: Update, context: CallbackContext) -> None:
    # 獲取用戶發送的 URL 網址
    text_url = str(update.message.text)

    # 判斷用戶資料中是否有 summarize_type 或 crawler 的標記，以便執行不同的動作
    if "summarize_type" in context.user_data and context.user_data["summarize_type"] == "url":
        # 如果是 /summarize command 的 URL 摘要，則執行以下動作：
        summary = summarize_docs(UnstructuredURLLoader(urls = [text_url]).load(), text_url, llm)

        # 發送摘要結果給用戶（這裡假設摘要結果不超過 4096 個字元）
        update.message.reply_text(summary[:4096])

        # 清除用戶資料中的 summarize_type 標記，以免影響後續處理
        del context.user_data["summarize_type"]

    elif "crawler" in context.user_data and context.user_data["crawler"] == True:
        # 如果是爬蟲功能，則執行以下動作：

        # 發送內容給用戶（這裡假設內容不超過 4096 個字元）
        update.message.reply_text(crawler(text_url, llm))

        # 清除用戶資料中的 crawler 標記，以免影響後續處理
        del context.user_data["crawler"]


# 定義用戶 PDF 的處理函數
def pdf(update: Update, context: CallbackContext) -> None:
    # 獲取用戶發送的 PDF 檔案 ID（這裡假設只有 PDF 檔案會觸發此函數）
    file_id = update.message.document.file_id

    # 使用 bot 物件下載 PDF 檔案到本地（這裡假設下載路徑為 "./pdfs/"）
    bot = context.bot
    file_path = f"./pdfs/{file_id}.pdf"
    bot.getFile(file_id).download(file_path)

    # 判斷用戶資料中是否有 summarize_type 的標記，以便執行不同的動作
    if "summarize_type" in context.user_data and context.user_data["summarize_type"] == "pdf":

        try:
            # 如果是 /summarize command 的 PDF 摘要，則執行以下動作：
            # 使用某種摘要演算法對文字進行摘要
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            summary = summarize_docs(pages, file_path, llm)
            # 發送摘要結果給用戶（這裡假設摘要結果不超過 4096 個字元）
            update.message.reply_text(summary[:4096])
        except telegram.error.BadRequest as e:
            # 如果出現 BadRequest 錯誤，並且錯誤訊息是 Message text is empty
            if str(e) == "Message text is empty":
                context.bot.send_message(chat_id=update.effective_chat.id, text="PDF 裡都是圖片，沒有字元可讀喔！")

        # 清除用戶資料中的 summarize_type 標記，以免影響後續處理
        del context.user_data["summarize_type"]

    elif "importpdf" in context.user_data and context.user_data["importpdf"] == True:
        # 如果是 /importpdf command 的 PDF 讀取，則執行以下動作：
        # 發送文字給用戶（這裡假設文字不超過 4096 個字元）

        reader = PdfReader(file_path)
        raw_text = ''
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                raw_text += text

        import_done = importing_pdf(raw_text, file_path)
        print(import_done)

        update.message.reply_text(import_done)

        # 清除用戶資料中的 importpdf 標記，以免影響後續處理
        del context.user_data["importpdf"]


# Run the program
if __name__ == '__main__':
    # 將各種處理函數與對應的 handler 物件關聯
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    summarize_handler = CommandHandler("summarize", summarize)
    importpdf_handler = CommandHandler("importpdf", importpdf)
    button_handler = CallbackQueryHandler(button)
    url_handler = MessageHandler(Filters.entity("url"), url)
    pdf_handler = MessageHandler(Filters.document.mime_type("application/pdf"), pdf)
    text_handler = MessageHandler(Filters.text, text)

    # 將各種 handler 物件添加到 dispatcher 物件中
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(summarize_handler)
    dispatcher.add_handler(importpdf_handler)
    dispatcher.add_handler(button_handler)
    dispatcher.add_handler(url_handler)
    dispatcher.add_handler(pdf_handler)
    dispatcher.add_handler(text_handler)

    # 開始 bot 的運行
    updater.start_polling()
    print('Polling...')
    updater.idle()
