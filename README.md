# Welcome to Team MultiLang

This is the repository for a project about a multilingual conversational assistant which uses Retrieval Augmented Generation with GPT 3.5 Turbo to generate responses for user queries. 
The assistant has can respond in 6 different languages based on what the user has chosen in the chainlit webapp. 

The tech stack used: 
1. Azure OpenAI for embedding (text-ada_embedding) and the main model (GPT 3.5 Turbo).
2. Azure AI Search for retrieving the context from the data (given in the data folder). The data is the property of https://www.socialmap-berlin.de/.
3. Langchain for chaining the prompts, context, metadata, retreiver and the LLM together.
4. Chainlit for front end.
5. Azure AI Translation service for providing desired translations.

## To get started:
1. Install the dependencies from `requirements.txt` file.
2. Create a `secrets.env` file in the folder with keys and endpoints for Azure AI translator, Azure AI Search, the embedding and the chat completion models from OpenAI.
3. Run the webapp using `chainlit run --port 7990 app.py`.


This project is part of "AI for Impact: Civil Society and Public Life - Open Innovation Programme" hosted by Nextcoder Softwareentwicklungs GmbH supported by Microsoft, Capgemini. The data and usecase was provided by Paritätischer Wohlfahrtsverband Berlin. 
