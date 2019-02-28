import requests
import json

base_url = 'https://alttpr.com/en/h/'

seed_url = 'https://alttpr.com/seed'

def generate_seed(params: dict) -> dict:
    payload = json.dumps(params)
    response = requests.post(url=seed_url, data=payload)
    return response.json()

def get_url(seed: str) -> str:
    return f'{base_url}{seed}'
