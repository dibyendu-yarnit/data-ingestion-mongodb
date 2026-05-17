from dotenv import load_dotenv
from openai import OpenAI
import os


# Load environment variables from .env file
load_dotenv()

# Load the Secret Key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAPI_EMBEDDING_MODEL = os.getenv("OPENAPI_EMBEDDING_MODEL", "text-embedding-3-small")


class OpenAIHandler:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def get_embedding(self, text):
        """
            Get the embedding for a given text using OpenAI's API.
        """
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=OPENAPI_EMBEDDING_MODEL
            )

            # Return the embedding vector from the response
            return response.data[0].embedding
        
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None
        


# Global instance of OpenAIHandler
openai_handler = OpenAIHandler()