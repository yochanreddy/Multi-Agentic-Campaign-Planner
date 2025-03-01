from typing import Any, Dict, List
from langchain_chroma import Chroma
from utils import get_module_logger
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from utils.generator import Generator
import json
from pathlib import Path
from tqdm import tqdm

logger = get_module_logger()


class Retriever:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.generator = Generator(config)

        self.embeddings = OpenAIEmbeddings(
            model=config["OPENAI"]["EMBEDDINGS"]["MODEL_NAME"]
        )

        self.vector_store = Chroma(
            collection_name="industry_description",
            embedding_function=self.embeddings,
            persist_directory=config["DATASTORE"]["PATH"],
        )

        self.retriever = self.vector_store.as_retriever(
            search_type=config["DATASTORE"]["RETRIEVAL"]["SEARCH_TYPE"],
            search_kwargs=config["DATASTORE"]["RETRIEVAL"]["SEARCH_KWARGS"],
        )

    def _load_categories(self) -> List[str]:
        """Load categories from JSON file."""
        try:
            categories_path = Path(self.config["DATA"]["CATEGORIES_PATH"])
            with open(categories_path, "r") as f:
                data = json.load(f)
                return data["categories"]
        except Exception as e:
            logger.error(f"Error loading categories: {str(e)}")
            raise

    def generate_category_description(self, category: str) -> str:
        """Generate a description for a given category using LangChain ChatModel."""
        prompt = ChatPromptTemplate.from_template(
            """Generate a concise description (<250 words) for the industry category: {category}.
            The description should help identify brands and products that belong to this category.
            Include key characteristics, typical products/services, and common business models."""
        )

        try:
            chat_model = self.generator.get_model()
            messages = prompt.format_messages(category=category)
            response = chat_model.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating description for {category}: {str(e)}")
            return ""

    def embed_and_store_categories(self):
        """Generate descriptions, embed them, and store in Chroma."""
        texts = []
        metadatas = []

        logger.debug("Generating descriptions and storing embeddings...")
        for category in tqdm(self.categories):
            description = self.generate_category_description(category)
            if description:
                texts.append(description)
                metadatas.append({"category": category, "description": description})

        try:
            # Add texts to the vector store
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            self.vector_store.persist()
            logger.debug(f"Successfully stored {len(texts)} category descriptions")
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")

    def get_retriever(self):
        return self.retriever

    def initialize_database(self):
        """Initialize the vector database with category descriptions."""
        self.categories = self._load_categories()
        # Check if database already contains embeddings
        if len(self.vector_store.get()["ids"]) == 0:
            logger.debug("Initializing database with category descriptions...")
            self.embed_and_store_categories()
        else:
            logger.debug("Database already contains embeddings")
