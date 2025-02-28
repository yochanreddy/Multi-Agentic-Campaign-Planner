import json
import os
from openai import OpenAI
import chromadb
from chromadb import Client, Settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize chromadb client
client = chromadb.Client(Settings(
    persist_directory='./chroma_db',
    is_persistent=True
))

# Get or create the collection
collection = client.get_or_create_collection(
                name="category_description",
                metadata={"description": "Description of categories"}
            )
# Load categories from categories.json
with open('categories.json', 'r', encoding='utf-8') as f:
    categories_data = json.load(f)

categories = categories_data.get('categories', [])

descriptions = []
vectors = []
ids = []

for idx, category in enumerate(categories):
    prompt = f"Generate a brief description (less than 200 words) for the business category: '{category}'."
    response = openai_client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates brief, concise descriptions of business categories."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=100
    )
    description = response.choices[0].message.content
    with open('descriptions.txt', 'a', encoding='utf-8') as f:
        f.write(f"{category}: {description}\n")
    # Get the embedding vector for the description using OpenAI's embedding API
    embed_response = openai_client.embeddings.create(
        input=description,
        model='text-embedding-3-large'
    )
    vector = embed_response.data[0].embedding
    with open('vectors.txt', 'a', encoding='utf-8') as f:
        f.write(f"{vector}\n")

    descriptions.append(description)
    vectors.append(vector)
    ids.append(f"category_{idx}")

# Add the documents to the chromadb collection
collection.add(
    embeddings=vectors,
    metadatas=[{'category': cat} for cat in categories],
    ids=ids
)
#%%
import chromadb
from chromadb import Client, Settings
client = chromadb.Client(Settings(
    persist_directory='./chroma_db',
    is_persistent=True
))
collection = client.get_or_create_collection(
                name="category_description",
                metadata={"description": "Description of categories"}
            )

result = collection.get(
ids=["category_26"],
where={"category": "Education"},
include=["embeddings", "metadatas", "documents"]
)
print("Query result:", result)

print('Successfully added category descriptions to chromadb.') 
# %%
