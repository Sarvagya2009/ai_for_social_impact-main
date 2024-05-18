
import chainlit as cl
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from chainlit.input_widget import Select
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
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
    print(value, "lang")

    chat_llm = AzureChatOpenAI(
        openai_api_version=openai.api_version,
        openai_api_key=openai.api_key,
        azure_endpoint=openai.api_base,
        openai_api_type=openai.api_type,
        deployment_name="gpt-4")

    """ 
    system_prompt = (
    "Sie sind ein Deutsch-verstehender Assistent, der die Fragen des Benutzers auf der Grundlage des unten angegebenen Kontexts beantwortet. "
    "Erzeugen Sie die Antwort in Form einer Empfehlungsliste für die Frage, die nur den Titel zurückgibt, dem im Kontext der 'Name der Organisation' vorangestellt ist. "
    "Wenn es sich bei der Benutzeranfrage nicht um eine Frage, sondern um eine Begrüßung handelt, antworten Sie als Assistent mit einer korrekten Antwort. "
    "Wenn Sie die Antwort nicht wissen, sagen Sie: 'Da kann ich Ihnen leider nicht helfen'. "
    "Kontext: {context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )
    """ 
    
    prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    print(prompt)

    combine_docs_chain = create_stuff_documents_chain(chat_llm, prompt)
    rag_chain = create_retrieval_chain(AzureRetriever(), combine_docs_chain)
    
    cl.user_session.set("runnable", rag_chain)
    
    
    await cl.Avatar(
        name="SocialRobo",
        url="ai_for_social_impact-main\public\socialRobo.png",
    ).send()



@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")
    lang, translation=tranlate_instance.translate(message.content)
    inputs = {"input": translation}
    result = await runnable.ainvoke(inputs)
    msg = cl.Message(content=result["answer"], disable_feedback=True)

    await msg.send()

    await msg.update()
