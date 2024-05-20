
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
from settings import rag_chain, mappings, write_settings_to_file, interface_langs, Language, reverse_mappings

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
credential = AzureKeyCredential(key)
tranlate_instance= translate()
value=""
current_lang= Language()

"""On chat start, initialize and set the llm chain as the runnable"""
@cl.on_chat_start
async def on_chat_start():
    choices= ["English", "German", "Spanish", "Arabic", "Turkish", "French"]
    
    text_content = interface_langs[current_lang]["Options"]
    image = cl.Image(path="public\logo_light.png", name="image1", display="inline")
    elements = [
        cl.Text(name=interface_langs[current_lang]["Instruct"], content=text_content, display="inline")
    ]

    settings = await cl.ChatSettings(
        [
            Select(
                id="Language",
                label="Language",
                values=choices,
                initial_index=choices.index(reverse_mappings[current_lang]),
            )
        ]
    ).send()
    value = settings["Language"]

    cl.user_session.set("runnable", rag_chain.rag_chain) 
    await cl.Avatar(
        name="SocialRobo",
        url="public\socialRobo.png",
    ).send()
    await cl.Message(
        content=interface_langs[current_lang]["Intro"],
        elements=elements,
        author="SocialRobo"
    ).send()
    await cl.Message(
        content=interface_langs[current_lang]["Acknowledge"],
        elements=[image],
        author="SocialRobo"
    ).send()
    

"""Update language if user updates the language setting"""
@cl.on_settings_update
async def setup_agent(settings: cl.ChatSettings):
    value= settings["Language"]
    write_settings_to_file(mappings[value])
    
@cl.step
async def Artificial_Intelligence(message):
    runnable = cl.user_session.get("runnable")  # type: Runnable
    _,translation=tranlate_instance.translate(message.content,detect_lang=False, language= current_lang)
    inputs = {"input": translation}
    result = await runnable.ainvoke(inputs)
    _, translated_answer= tranlate_instance.translate(result["answer"], target_lang=current_lang,detect_lang=False, language= 'de')
    return translated_answer


"""Translate user input into German, await response and get response translated back to user target language"""
@cl.on_message
async def on_message(message: cl.Message):
    

    msg = cl.Message(content="")
    
    translated_answer= await Artificial_Intelligence(message)
    msg = cl.Message(content=translated_answer, disable_feedback=True, author="SocialRobo")
    
    await msg.send()
    await cl.sleep(5)
    await msg.update()
