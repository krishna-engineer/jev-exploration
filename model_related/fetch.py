import requests
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://models.dev/api.json"
FIRST_PARTY = ["anthropic", "openai", "google", "mistral", "deepseek", "xai"]


def download(url:str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_model_type(model_details: dict) -> str:
    if "embed" in model_details['id'].lower():
        # The embedding check comes first on purpose. Embedding models list their output as text
        # and checking the id first stops them being tagged chat
        return "embedding"

    if model_details['modalities']['output'] == ["text"]:
        return "chat"

    return "other"


def flatten(provider: str, model_details: dict) -> dict | None:
    if "cost" not in model_details:
        return None

    if "text" not in model_details.get("modalities", {}).get("output", []):
        return None

    if model_details.get("status") == "deprecated":
        return None

    model_details_flattened = {}
    model_details_flattened['provider'] = provider
    model_details_flattened['id'] = model_details['id']
    model_details_flattened['name'] = model_details['name']
    model_details_flattened['model_type'] = get_model_type(model_details)

    model_details_flattened['price_in'] = model_details['cost']['input']
    model_details_flattened['price_out'] = model_details['cost']['output']

    model_details_flattened['context'] = model_details['limit']['context']
    model_details_flattened['max_output'] = model_details['limit']['output']

    model_details_flattened['input_modalities'] = model_details['modalities']['input']

    model_details_flattened['tool_call'] = model_details.get('tool_call', False)
    model_details_flattened['structured_output'] = model_details.get('structured_output', False)
    model_details_flattened['reasoning'] = model_details.get('reasoning', False)
    model_details_flattened['open_weights'] = model_details.get('open_weights', False)

    model_details_flattened['knowledge'] = model_details.get('knowledge')
    model_details_flattened['release_date'] = model_details.get('release_date')

    return model_details_flattened


if __name__ == "__main__":

    list_valid_models = []
    model_catalog = download(URL)

    for provider in FIRST_PARTY:
        provider_models = model_catalog.get(provider, {}).get('models', {})

        total_models = len(provider_models)
        valid_models = 0
        for model, model_details in provider_models.items():
            model_details_flattened = flatten(provider, model_details)
            if model_details_flattened is not None:
                valid_models += 1
                list_valid_models.append(model_details_flattened)

    write_path = ROOT / "model_catalog.json"
    print(f"Count of valid models: {len(list_valid_models)}")
    with open(write_path, "w") as f:
        json.dump(list_valid_models, f, indent=2)