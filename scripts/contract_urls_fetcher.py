import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f'Bearer {os.getenv("GITHUB_TOKEN")}',
    "Accept": "application/vnd.github.v3+json"
}

query = "ink contract filename:lib.rs language:Rust"
query = requests.utils.quote(query)

for i in range(1, 9):
    url = f"https://api.github.com/search/code?q={query}&per_page=100&page={i}"
    response = requests.get(url, headers=headers)
    results = response.json()

    # dump all the results to a single text file
    for item in results['items']:
        with open("contract_urls.txt", "a") as f:
            f.write(item['html_url'] + "\n")