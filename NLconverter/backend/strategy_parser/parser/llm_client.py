"""LLM client for communicating with Gemini API."""

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional, Union, Tuple


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    api_key: str
    model: str = "gemini-3.1-flash-lite"
    temperature: float = 0.2
    max_output_tokens: int = 8000
    timeout: int = 30


class LLMClient:
    """Client for interacting with Google's Gemini API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1/models"

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration. If None, uses environment variables.
            
        Raises:
            RuntimeError: If API key is not provided or found.
        """
        if config is None:
            api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "GOOGLE_GEMINI_API_KEY is not set. "
                    "Provide LLMConfig or set the environment variable."
                )
            self.config = LLMConfig(api_key=api_key)
        else:
            self.config = config

    def call(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        response_schema: Optional[dict] = None,
        return_metrics: bool = False
    ) -> Union[str, Tuple[str, dict]]:
        """
        Call Gemini API with system and user prompts.
        
        Args:
            user_prompt: The user's prompt/query
            system_prompt: Optional system prompt to guide the model
            response_schema: Optional JSON schema to enforce structured output
            return_metrics: If True, returns a tuple of (response_text, usage_metadata)
            
        Returns:
            The model's response as a string, or (string, dict) if return_metrics=True
            
        Raises:
            RuntimeError: If API request fails
        """
        contents = []

        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "I understand. I will follow these instructions."}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": user_prompt}]
        })

        generation_config = {
            "temperature": self.config.temperature,
            "maxOutputTokens": self.config.max_output_tokens,
            "candidateCount": 1,
        }
        
        if response_schema:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = response_schema

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        url = self._build_url()
        response = self._make_request(url, payload, return_metrics)
        return response

    def _build_url(self) -> str:
        """Build the API URL."""
        base_url = f"{self.BASE_URL}/{self.config.model}:generateContent"
        return f"{base_url}?{urllib.parse.urlencode({'key': self.config.api_key})}"

    def _make_request(self, url: str, payload: dict, return_metrics: bool = False) -> Union[str, Tuple[str, dict]]:
        """
        Make HTTP request to Gemini API.
        
        Args:
            url: The API endpoint URL
            payload: The request payload
            return_metrics: If True, returns token usage metrics alongside text
            
        Returns:
            The response text, or (text, metrics)
            
        Raises:
            RuntimeError: If request fails
        """
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
        }

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST"
        )

        if not url.startswith("https://generativelanguage.googleapis.com/"):
            raise ValueError("SSRF Prevention: URL must target the trusted Gemini API endpoint.")

        try:
            # URL is validated against the trusted generative language API endpoint to prevent SSRF
            with urllib.request.urlopen(request, timeout=self.config.timeout, context=ssl.create_default_context()) as response:
                response_data = json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"Gemini API request failed: {exc.code} {exc.reason}\n{body}"
            )
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error: {exc}")
        except Exception as exc:
            raise RuntimeError(f"Unexpected error: {exc}")

        return self._extract_response(response_data, return_metrics)

    def _extract_response(self, response_data: dict, return_metrics: bool = False) -> Union[str, Tuple[str, dict]]:
        """
        Extract text content from Gemini API response.
        
        Args:
            response_data: The JSON response from API
            return_metrics: If True, returns token usage metrics alongside text
            
        Returns:
            The extracted text, or (text, metrics)
            
        Raises:
            RuntimeError: If response format is unexpected
        """
        if "candidates" in response_data and response_data["candidates"]:
            candidate = response_data["candidates"][0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            if parts:
                text = "".join(part.get("text", "") for part in parts).strip()
                if return_metrics:
                    usage = response_data.get("usageMetadata", {})
                    return text, usage
                return text

        raise RuntimeError(f"Unexpected Gemini response format: {response_data}")



