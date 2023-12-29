import os
import logging
import json
import requests
import azure.functions as func
from azure.core.credentials import AzureKeyCredential 
from azure.ai.textanalytics import TextAnalyticsClient, TextDocumentInput
from azure.cosmos import CosmosClient

# Send a HTTP request to Logic App
def send_http_request_logic_app(data):
    url = "https://prod-03.francecentral.logic.azure.com:443/workflows/33f0cc89aebe480698102e117d8d873b/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=KKsFooE1O7AiJ0mMaoB5Le5cfyuLASyRC5fsIdNZZSs"

    try:
        response = requests.post(url=url, json=data)
        logging.info(f"Request sent to Logic App")
    except Exception as e:
        logging.error(f"Failed to send request to logic app {str(e)}")


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
    key = os.environ.get('TEXT_ANALYTICS_KEY', 'd51e7a4cdbf04610bd9218cd0faf5a87')
    endpoint = os.environ.get('TEXT_ANALYTICS_ENDPOINT', 'https://mentalboysreviews.cognitiveservices.azure.com/')
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

        # Send request to logic app
        send_http_request_logic_app(item)
        logging.info(f"Review texts : {review_text}, \t Score : {sentiment}")