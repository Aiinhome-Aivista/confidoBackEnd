import requests

# api url
MISTRAL_API_URL = "http://localhost:11434/api/generate"

# mistral api call
def call_mistral(prompt: str) -> str:
    try:
        response = requests.post(
            MISTRAL_API_URL,
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.RequestException as e:
        raise RuntimeError(f"Error calling Mistral API: {e}")