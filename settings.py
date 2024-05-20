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
import time
import re

APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT,'secrets.env')
load_dotenv(Path(dotenv_path))

""" Initialize LLM Chain with prompts and retreiver """
class Config:
    openai.api_type = "azure"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("azure_endpoint")
    openai.api_version = "2023-03-15-preview"
    chat_llm = AzureChatOpenAI(
            openai_api_version="2023-03-15-preview",
            openai_api_key=openai.api_key,
            azure_endpoint=openai.api_base,
            openai_api_type=openai.api_type,
            deployment_name="gpt-35-turbo")
    system_prompt = (
    "Du bist einen Assistenten mit guten Deutschkenntnissen namens SocialRobo, der Nutzern auf der Grundlage ihrer Eingaben und des gegebenen Kontextes soziale Einrichtungen empfiehlt"
    "Erzeugen Sie die Antwort in Form einer nummerierten Liste von Empfehlungen für die Frage, die den Titel wiedergibt, dem der 'Name der Organisation' vorangestellt ist."
    #"Wenn Sie Empfehlungen aussprechen, geben Sie neben dem Titel eine kurze Beschreibung der Organisation an. Es ist sehr wichtig."
    "Und achten Sie auf eine einheitliche Formatierung."
    "Achten Sie darauf, dass Sie nicht mehrmals dieselbe Organisation in einer Antwort empfehlen. Sie sollten Organisationen verwerfen, wenn sie nicht genau mit der Benutzereingabe übereinstimmen."
    "Wenn die Benutzeranfrage keine Frage, sondern eine Begrüßung ist, antworten Sie als Assistent mit einer korrekten Antwort."
    "Erfinden Sie nichts, wenn Sie sich nicht sicher sind. Wenn Sie die Antwort nicht wissen, sagen Sie: 'Tut mir leid, da kann ich Ihnen nicht helfen'."
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
     template= """ Geben Sie in Ihrer Antwort für jede Empfehlung die Website, den Google-Maps-Link und die unten genannte Adresse an. 
        Website: {website}
        Google maps link:{Maps}
        Adresse: {address}
        """)
    combine_docs_chain = create_stuff_documents_chain(chat_llm, prompt, document_prompt=document_combine_prompt)
    rag_chain = create_retrieval_chain(AzureRetriever(), combine_docs_chain)

rag_chain= Config()

""" Mappings to covert between the languages and their codes for the APIs """
mappings={"English": "en", 
          "German": "de",
          "Arabic": "ar",
          "French":	"fr",
          "Turkish": "tr", 
          "Spanish": "es"
          }
reverse_mappings={
    "en": "English",
    "de": "German",
    "ar": "Arabic",
    "fr": "French",
    "tr": "Turkish",
    "es": "Spanish"
}


""" Keep track of current user language here """
def Language():
    log_file= "config.toml"
    with open(log_file, 'r') as f:
        lines = f.readlines()
    try:
        if lines:
            current_lang=lines[-1].strip().split()[1]  # Remove trailing newline character
        else:
            current_lang='en'
    except:
        current_lang='en'
    return current_lang

""" Write to the toml file for chainlit to keep track of current language and restart app """
def write_settings_to_file(new_lang):
    current_settings = new_lang
    log_file= "config.toml"
    with open(log_file, "a") as f:
        f.write(f"\nLanguage: {current_settings}")

""" Store interface language for all 6 languages """
interface_langs={
    "en":{
        "Intro": "Hello, I am SocialRobo and I am here to help you! \n Do you have any questions about the Socialmap Berlin?",
        "Instruct": "You could ask me about:",
        "Options": "• healthcare institutions \n • places for children \n • Many things more! \n Please use the widget next to the message bar to change language.",
        "Acknowledge": "The chatbot is brought to you by the good folks at Paritätischer Wohlfahrtsverband and Team Multilang."
    },
    "ar":{
        "Intro": "مرحبًا، أنا سوشيال روبو وأحب أن أساعدك! \n هل لديك أي أسئلة حول الخريطة الاجتماعية في برلين؟",
        "Instruct": "يمكنك أن تسألني عن:",
        "Options":  "• منظمات الرعاية الصحية  \n • أماكن للأطفال  \n •  أكثر من ذلك بكثي!  \n  يُرجى استخدام الأداة الموجودة بجوار شريط الرسائل لتغيير اللغة.",
        "Acknowledge": "يتم تقديم روبوت الدردشة الآلي إليك من قبل الأشخاص الطيبين في Paritätischer Wohlfahrtsverband و Team Multilang"
    },
    "fr": {
        "Intro": "Bonjour, je suis SocialRobo et je suis là pour vous aider ! \n Vous avez des questions sur Socialmap Berlin?",
        "Instruct": "Vous pourriez m'interroger à ce sujet:",
        "Options": "• les établissements de soins de santé \n • lieux pour les enfants \n • Bien d'autres choses encore ! \n Veuillez utiliser le widget situé à côté de la barre de message pour changer de langue.",
        "Acknowledge": "Le chatbot vous est présenté par les bonnes gens de Paritätischer Wohlfahrtsverband et Team Multilang"
    },
    "de":{
        "Intro": "Hallo, ich bin SocialRobo und ich bin hier, um dir zu helfen! \n Haben Sie Fragen zur Socialmap Berlin?",
        "Instruct": "Sie könnten mich fragen:",
        "Options": "• Gesundheitseinrichtungen \n • Orte für Kinder \n • Viele weitere Dinge! \n Bitte benutzen Sie das Widget neben der Nachrichtenleiste, um die Sprache zu ändern.",
        "Acknowledge": "Der Chatbot wird Ihnen vom Paritätischen Wohlfahrtsverband und dem Team Multilang zur Verfügung gestellt"
    },
    "tr":{
        "Intro": "Merhaba, ben SocialRobo'yum ve yardım etmek için buradayım! \n Socialmap Berlin hakkında sorularınız mı var?",
        "Instruct": "Bana sorabilirsin:",
        "Options": "• sağlık kurumları \n • Çocuklar için yerler \n • Daha birçok şey! \n Dili değiştirmek için lütfen mesaj çubuğunun yanındaki widget'ı kullanın.",
        "Acknowledge": "Sohbet robotu size Paritätischer Wohlfahrtsverband ve Team Multilang'daki iyi insanlar tarafından getirilmiştir"
    },
    "es":{
        "Intro": "¡Hola, soy SocialRobo y estoy aquí para ayudarte! \n ¿Tiene alguna pregunta sobre Socialmap Berlín?",
        "Instruct": "Podrías preguntarme sobre:",
        "Options": "• instituciones sanitarias \n • plazas para niños \n • ¡Muchas cosas más! \n Utiliza el widget situado junto a la barra de mensajes para cambiar de idioma.",
        "Acknowledge": "El chatbot es obra de la buena gente de Paritätischer Wohlfahrtsverband y Team Multilang."
    },
}
