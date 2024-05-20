## Here are the original dataset and notebooks for creating embeddings and vector indexes for the information retrieval system. 

1. `socialmaps-data.ipynb` explores the datasets provided by Social Map Berlin: `socialmaps-items.json` and `socialmaps-translations.json`.
2. `embeddings create.ipynb` preprocesses the `German Only Data.csv` (which is the german only csv form of the `socialmaps-items.json`), creates vector embeddings and creates jsons with relevant metadata and embeddings -> storing it in `docVectors_azure.json`.
3. `vector_store.ipynb` is used to create index and upload the data from `docVectors_azure.json` to a vector database in Azure. This data can be retrieved using Azure AI Search. 
