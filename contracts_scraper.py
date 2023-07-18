import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f'Bearer {os.getenv("GITHUB_TOKEN")}',
    "Accept": "application/vnd.github.v3+json"
}
# path:**/lib.rs+language:Rust
query = "ink+contract+language:Rust"
url = f"https://api.github.com/search/code?q={query}"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    results = response.json()
    for item in results['items']:
        print(item['html_url'])
else:
    print(f"Request failed with status code {response.status_code}")
