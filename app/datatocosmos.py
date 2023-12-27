from azure.cosmos import CosmosClient
import os
import random
import faker
from datetime import datetime
import time
import uuid
from cryptography.fernet import Fernet

fake = faker.Faker()
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Cosmos DB settings
SETTINGS = {
    'host': os.environ.get('ACCOUNT_HOST', ''),
    'master_key': os.environ.get('ACCOUNT_KEY', ''),
    'database_id': os.environ.get('COSMOS_DATABASE', ''),
    'container_id': os.environ.get('COSMOS_CONTAINER', ''),
}

# Initialize Cosmos client
client = CosmosClient(SETTINGS['host'], credential=SETTINGS['master_key'])
database = client.get_database_client(SETTINGS['database_id'])
container = database.get_container_client(SETTINGS['container_id'])

# Function to encrypt fields
def encrypt_field(field):
    return cipher_suite.encrypt(field.encode()).decode()

# Function to insert data into Cosmos DB
def insert_into_cosmos(data):
    try:
        # Encrypt specific fields
        data['user']['name'] = encrypt_field(data['user']['name'])
        data['user']['email'] = encrypt_field(data['user']['email'])
        data['user']['location'] = encrypt_field(data['user']['location'])
        data['user']['dob'] = encrypt_field(data['user']['dob'])
        
        container.create_item(body=data)
        print("Inserted data into Cosmos DB.")
    except Exception as e:
        print(f"Failed to insert data into Cosmos DB: {str(e)}")

positive_reviews = {
    "Italian": ["Loved the authentic pizza!", "Pasta was divine.", "Best tiramisu I've ever had!", "Incredible risotto.", "The gelato was out of this world."],
    "Chinese": ["The dim sum was exceptional!", "Loved the Peking duck.", "Best hot pot experience.", "Amazing dumplings!", "Crispy sweet and sour pork."],
    "Mexican": ["Fantastic tacos!", "Delicious enchiladas.", "Great guacamole.", "Perfect burritos.", "Authentic quesadillas."],
    "Indian": ["Butter chicken was heavenly.", "Amazing biryani.", "Delicious naan bread.", "Tasty tandoori chicken.", "Incredible masala chai."],
    "Japanese": ["Sushi was top-notch.", "Great ramen, very authentic.", "Loved the tempura.", "Delicious teriyaki chicken.", "Best miso soup I've tasted."]
}

neutral_reviews = {
    "Italian": ["Pizza was okay, not great.", "Pasta was average.", "Tiramisu was alright.", "Risotto was mediocre.", "Gelato was decent."],
    "Chinese": ["Dim sum was just fine.", "Peking duck was okay.", "Hot pot was nothing special.", "Dumplings were average.", "Sweet and sour pork was standard."],
    "Mexican": ["Tacos were alright.", "Enchiladas were passable.", "Guacamole was average.", "Burritos were okay.", "Quesadillas were so-so."],
    "Indian": ["Butter chicken was decent.", "Biryani was unremarkable.", "Naan bread was okay.", "Tandoori chicken was average.", "Masala chai was fair."],
    "Japanese": ["Sushi was ordinary.", "Ramen was passable.", "Tempura was average.", "Teriyaki chicken was okay.", "Miso soup was standard."]
}

negative_reviews = {
    "Italian": ["Pizza was undercooked.", "Pasta was too salty.", "Tiramisu lacked flavor.", "Risotto was overcooked.", "Gelato tasted bland."],
    "Chinese": ["Dim sum was disappointing.", "Peking duck was dry.", "Hot pot was bland.", "Dumplings were greasy.", "Sweet and sour pork was soggy."],
    "Mexican": ["Tacos were too spicy.", "Enchiladas were dry.", "Guacamole was tasteless.", "Burritos were soggy.", "Quesadillas were burnt."],
    "Indian": ["Butter chicken was too creamy.", "Biryani was overcooked.", "Naan bread was stale.", "Tandoori chicken was dry.", "Masala chai was weak."],
    "Japanese": ["Sushi was not fresh.", "Ramen was too salty.", "Tempura was oily.", "Teriyaki chicken was burnt.", "Miso soup was watery."]
}
restaurants = [
    {"id": "restaurant_001", "name": "Gusto's Italian", "location": "123 Main St", "cuisine": "Italian", "operational_hours": "9 AM - 9 PM"},
    {"id": "restaurant_002", "name": "Beijing Bites", "location": "456 Oak Ave", "cuisine": "Chinese", "operational_hours": "9 AM - 9 PM"},
    {"id": "restaurant_003", "name": "Carlos Mexican", "location": "Sreet Wallet JT", "cuisine": "Mexican", "operational_hours": "9 AM - 9 PM"},
    {"id": "restaurant_004", "name": "Zanda BAHABI", "location": "Eve Ball St", "cuisine": "Indian", "operational_hours": "9 AM - 9 PM"},
    {"id": "restaurant_005", "name": "Chu Wawa", "location": "Santas Balmas", "cuisine": "Indian", "operational_hours": "9 AM - 9 PM"}
]

def generate_user():
    return {
        "id": fake.uuid4(),
        "name": fake.name(),
        "email": fake.email(),
        "location": fake.city(),
        "preferences": random.choice(["Vegan", "Seafood", "Spicy", "Desserts", "Vegetarian"]),
        "dob": fake.date_of_birth().strftime("%Y-%m-%d")
    }

def generate_unique_id():
    return str(uuid.uuid4())

def generate_review(user_id, restaurant):
    rating = random.randint(1, 5)
    cuisine = restaurant["cuisine"]

    review_id = generate_unique_id()  # Generate a review ID

    if rating >= 4:
        review_text = random.choice(positive_reviews[cuisine])
    elif rating == 3:
        review_text = random.choice(neutral_reviews[cuisine])
    else:
        review_text = random.choice(negative_reviews[cuisine])

    review_data = {
        "id": review_id,  # Set the review ID as the primary ID for the document
        "rating": rating,
        "review_text": review_text,
        "review_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": generate_user(),
        "restaurant": restaurant
    }

    return review_data


try:
    while True:
        user = generate_user()
        restaurant = random.choice(restaurants)
        review_data = generate_review(user["id"], restaurant)
        print(review_data)

        # Insert the review_data into Cosmos DB
        insert_into_cosmos(review_data)
        
        time.sleep(5)

except KeyboardInterrupt:
    print("Real-time data generation stopped.")
