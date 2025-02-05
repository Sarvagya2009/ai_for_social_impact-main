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



"""Class for the hybrid search information retrieval"""
class AzureRetriever(BaseRetriever):

    def __int__(self):
        pass

    def get_embedding(self, text, model="text-embedding-ada-002"):
        openai.api_type = "azure"
        openai.api_key = os.getenv("embedding_key")
        openai.api_base = os.getenv("embedding_url")
        openai.api_version = "2023-05-15" 
        credential = AzureKeyCredential(key)
        #text= text['input'] #for dictionary in chainlit
        text = text.replace("\n", " ")
        return openai.Embedding.create(input = [text], engine=model).data[0].embedding
    
    def _get_relevant_documents(self, query: str) -> List[Document]:

        relevant_result=[]
        query_vector= self.get_embedding(query)
        search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))  
        vector_query = VectorizedQuery(vector=query_vector, 
                                    k_nearest_neighbors=3, 
                                    fields="embeddings")

        results = search_client.search(  
            search_text=query,  
            vector_queries=[vector_query],
            select=["title", "website", "full_text", "latitude", "longitude", "address"],
            top=3
            )     
        for result in results:
            context= result['full_text'].split('\n    ')
            context= context[:4]
            
            context= [i.strip() for i in context]
            context= ("\t   ").join(context)
            relevant_result.append(Document(page_content=context,
            metadata={"title": result["title"], "website": result["website"], 
                      "Maps": f"http://maps.google.com/?q={result["latitude"]},{result['longitude']}", "address":result["address"]}))
        return relevant_result
    
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """async native implementation."""
        relevant_result=[]
        query_vector= self.get_embedding(query)
        search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))  
        vector_query = VectorizedQuery(vector=query_vector, 
                                    k_nearest_neighbors=3, 
                                    fields="embeddings")

        results = search_client.search(  
            search_text=query,  
            vector_queries=[vector_query],
            select=["title", "website", "full_text", "latitude", "longitude", "address"],
            top=3
            )     
        for result in results:
            context= result['full_text'].split('\n    ')
            context= context[:4]
            
            context= [i.strip() for i in context]
            context= ("\t   ").join(context)
            relevant_result.append(Document(page_content=context,
            metadata={"title": result["title"], "website": result["website"], 
                      "Maps": f"http://maps.google.com/?q={result["latitude"]},{result['longitude']}", "address":result["address"]}))
        return relevant_result

"""Translate text to and fro between German and target language"""  
class translate():
    def translate(self, text, target_lang='de', detect_lang=True, language= ""):
        headers = {
                'Ocp-Apim-Subscription-Key': translation_key,
                # location required if you're using a multi-service or regional (not global) resource.
                'Ocp-Apim-Subscription-Region': location,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }
        text_json= [{'text':text}]
        if detect_lang:
            path_detect = '/detect'
            constructed_url_detect = translation_url + path_detect
            params_detect = {
                'api-version': '3.0'
            }
            try:
                request = requests.post(constructed_url_detect, params=params_detect, headers=headers, json=text_json)
                response = request.json()
                language= (response[0]['language'])
            except Exception as e:
                print(e)
                return "", ""
        
        path = '/translate'
        constructed_url = translation_url + path

        params = {
            'api-version': '3.0',
            'from': language,
            'to': target_lang
        }
        
        try:
            request = requests.post(constructed_url, params=params, headers=headers, json=text_json)
            response = request.json()
            translation= (response[0]['translations'][0]['text'])
        except Exception as e:
            print(e)
            return language, ""
        
        return language, translation



