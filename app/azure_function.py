import os
import logging
import json
import azure.functions as func
from azure.core.credentials import AzureKeyCredential 
from azure.ai.textanalytics import TextAnalyticsClient, TextDocumentInput
from azure.cosmos import CosmosClient

# CosmosDB configuration
SETTINGS = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://mentalboys.documents.azure.com/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'xl24TZdLTNo7lmOEasPUxUnVqr3zIhiNSm4kvGe5Uhsdc0zRV9FtuIOROnZZHykEBP3WiSHgSOn1ACDbYiD1SA=='),
    'database_id': os.environ.get('COSMOS_DATABASE', 'Reviews'),
    'container_id': os.environ.get('COSMOS_CONTAINER', 'ItemsUpdated'),
}

# Initialize Cosmos client
client = CosmosClient(SETTINGS['host'], credential=SETTINGS['master_key'])
database = client.get_database_client(SETTINGS['database_id'])
container = database.get_container_client(SETTINGS['container_id'])

# Function to insert data into Cosmos DB
def insert_into_cosmos(data):
    try:
        container.create_item(body=data)
        logging.info("Inserted data into Cosmos DB.")
    except Exception as e:
        logging.error(f"Failed to insert data into Cosmos DB: {str(e)}")

# Function to analyze sentiment 
def analyse_sentiment(review_text):
    # Connect to Azure Language Analysis service
    key = os.environ.get('TEXT_ANALYTICS_KEY', '83f7f2fbcace4636b37c488c05cc9570')
    endpoint = os.environ.get('TEXT_ANALYTICS_ENDPOINT', 'https://mentallboys.cognitiveservices.azure.com/')
    credentials = AzureKeyCredential(key)
    client = TextAnalyticsClient(endpoint=endpoint, credential=credentials)

    # Analyse the review text sentiment
    documents = [TextDocumentInput(id="1", text=review_text)]
    response = client.analyze_sentiment(documents=documents)

    return response

def main(documents: func.DocumentList) -> str:
    if documents:

        # Retrieve document
        item_azure = documents[0]
        # Convert Azure Document to JSON
        item_data = json.dumps(item_azure, default=lambda o: o.__dict__)
        item = json.loads(item_data)['data']

        review_text = item["review_text"]

        result = analyse_sentiment(review_text)[0]
        item['sentiment'] = result.sentiment

        # Update the data in cosmos db
        logging.info(f"Item:  {item}")
        insert_into_cosmos(item)
        logging.info(f"Review texts : {review_text}, \t Score : {result.sentiment}")


