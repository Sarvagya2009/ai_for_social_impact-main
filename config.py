from pathlib import Path
import os
from dotenv import load_dotenv
from langchain.chat_models import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from chatbot import AzureRetriever, translate
from langchain_core.prompts import PromptTemplate
import openai

APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT,'secrets.env')
load_dotenv(Path(dotenv_path))

"""Initialize LLM Chain with prompts and retreiver"""
class Config:
    openai.api_type = "azure"
    openai.api_key = os.getenv("embedding_key")
    openai.api_base = os.getenv("embedding_url")
    openai.api_version = "2023-05-15" 
    chat_llm = AzureChatOpenAI(
            openai_api_version=openai.api_version,
            openai_api_key=openai.api_key,
            azure_endpoint=openai.api_base,
            openai_api_type=openai.api_type,
            deployment_name="gpt-4")
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
    document_combine_prompt = PromptTemplate(
     input_variables=["website","Maps", "address"],
     template= """ Geben Sie in Ihrer Antwort für jede Empfehlung die Website, den Google Maps-Link und die unten stehende Adresse an. 
     Diese drei waren die Metadaten, die zusammen mit dem Kontext abgerufen wurden. 
        Website: {website}
        Google maps link:{Maps}
        Adresse: {address}
        """)
    combine_docs_chain = create_stuff_documents_chain(chat_llm, prompt, document_prompt=document_combine_prompt)
    rag_chain = create_retrieval_chain(AzureRetriever(), combine_docs_chain)

rag_chain= Config()


mappings={"English": "en", 
          "German": "de",
          "Arabic": "ar",
          "French":	"fr",
          "Turkish": "tr", 
          "Spanish": "es"
          }


"""Keep track of current user language here"""
class Language:
    current_lang='en'
    def update(self, lang= 'en'):
        self.current_lang=lang

update_language= Language()
