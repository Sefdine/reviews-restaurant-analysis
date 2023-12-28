import os
import logging
import json
import requests
import azure.functions as func
from azure.core.credentials import AzureKeyCredential 
from azure.ai.textanalytics import TextAnalyticsClient, TextDocumentInput
from azure.cosmos import CosmosClient

# CosmosDB configuration
SETTINGS = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://mentallboys.documents.azure.com:443/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'bE4xRSJNgkVGjDiMLv0o0svZ9DzQ188fgv1wuYhNSwKVfyGTFR1hQY9hlkV1BqnnvfGtZqddWpiTACDbvxZlog=='),
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

# functions to send message into slack
def send_message_to_slack(message):
    headers = {
        "Content-type": "application/json"
    }

    data = {
        "text": message
    }

    url = "https://hooks.slack.com/services/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"

    try:
        response = requests.post(url, headers=headers, json=data)
        logging.info("Message sent to slack")
    except Exception as e:
        logging.error(f"Failed to send message to slack {str(e)}")

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

        sentiment = result.sentiment

        if sentiment == 'negative':
            message = f'''Hi, the user with id {item['user']['id']} send a negative review to the restaurant with id {item['restaurant']['id']}.\n
                    The review is "{item['review_text']}" 
            '''
            send_message_to_slack(message)

        item['sentiment'] = sentiment

        # Update the data in cosmos db
        logging.info(f"Item:  {item}")
        insert_into_cosmos(item)
        logging.info(f"Review texts : {review_text}, \t Score : {sentiment}")