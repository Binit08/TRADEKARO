"""Helper for generating text embeddings using Google Gemini API."""

import os
import json
import ssl
import urllib.request
import urllib.parse
from typing import List

class GeminiEmbeddingClient:
    """Client for generating text embeddings using Google Gemini."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize the embedding client.
        """
        self.api_key = api_key or os.getenv("GOOGLE_GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_GEMINI_API_KEY is not set.")

    def load_model(self):
        # No-op since we use a remote API
        pass

    def unload_model(self):
        # No-op since we use a remote API
        pass

    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the provided text using Gemini API.
        """
        url = f"{self.BASE_URL}?key={self.api_key}"
        payload = {
            "model": "models/gemini-embedding-001",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(request, timeout=30, context=ssl.create_default_context()) as response:
                response_data = json.load(response)
                return response_data.get("embedding", {}).get("values", [])
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 768 # Return empty vector on failure to avoid crashes
