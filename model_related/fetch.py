import requests
import json

URL = "https://models.dev/api.json"
FIRST_PARTY = ["anthropic", "openai", "google", "mistral", "deepseek", "xai"]

def download(url:str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


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
    model_catalog = download(URL)
    print(len(model_catalog), type(model_catalog))

    for provider in FIRST_PARTY:
        provider_models = model_catalog.get(provider, {}).get('models', {})
        print(provider, len(provider_models))