
import chainlit as cl
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from chainlit.input_widget import Select

from langchain import hub
from dotenv import load_dotenv,dotenv_values
import warnings
warnings.filterwarnings("ignore")
import json
import os
from pathlib import Path
import openai
import requests, uuid, json
from azure.core.credentials import AzureKeyCredential  
from azure.search.documents import SearchClient, SearchIndexingBufferedSender  
from azure.search.documents.indexes import SearchIndexClient  
from azure.search.documents.models import (
    QueryAnswerType,
    QueryCaptionType,
    VectorizedQuery,
    VectorQuery,
    VectorFilterMode,    
)
from langchain.chat_models import AzureChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.retriever import BaseRetriever
from langchain.schema.document import Document
from typing import List
from langchain_community.document_loaders.telegram import text_to_docs
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from chatbot import AzureRetriever, translate
from config import rag_chain, mappings, update_language

"""Import environmental variables"""
APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT,'secrets.env')
load_dotenv(Path(dotenv_path))

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT") 
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME") 
key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
translation_url= os.getenv("url")
translation_key= os.getenv("KEY")
location= os.getenv("location")
openai.api_type = "azure"
openai.api_key = os.getenv("embedding_key")
openai.api_base = os.getenv("embedding_url")
openai.api_version = "2023-05-15" 
credential = AzureKeyCredential(key)
tranlate_instance= translate()
value=""

"""On chat start, initialize and set the llm chain as the runnable"""
@cl.on_chat_start
async def on_chat_start():

    settings = await cl.ChatSettings(
        [
            Select(
                id="Language",
                label="Language",
                values=["English", "German", "Spanish", "Arabic", "Turkish", "French"],
                initial_index=0,
            )
        ]
    ).send()
    value = settings["Language"]

    cl.user_session.set("runnable", rag_chain.rag_chain) 
    await cl.Avatar(
        name="SocialRobo",
        url="ai_for_social_impact-main\public\socialRobo.png",
    ).send()

"""Update language if user updates the language setting"""
@cl.on_settings_update
async def setup_agent(settings: cl.ChatSettings):
    value= settings["Language"]
    update_language.update(mappings[value])
   
    
"""Translate user input into German, await response and get response translated back to user target language"""
@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")
    _,translation=tranlate_instance.translate(message.content,detect_lang=False, language= update_language.current_lang)
    inputs = {"input": translation}
    result = await runnable.ainvoke(inputs)
    _, translated_answer= tranlate_instance.translate(result["answer"], target_lang=update_language.current_lang,detect_lang=False, language= 'de')
    msg = cl.Message(content=translated_answer, disable_feedback=True)
    print(result["answer"], "##########")

    await msg.send()
    await msg.update()
