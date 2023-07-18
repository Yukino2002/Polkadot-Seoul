import requests
import os

# Create the "contracts" directory if it doesn't exist
if not os.path.exists("contracts"):
    os.makedirs("contracts")

# load all the urls from the text file
with open("contract_urls.txt", "r") as f:
    urls = f.readlines()

# replace github.com with raw.githubusercontent.com
urls = [url.replace("github.com", "raw.githubusercontent.com") for url in urls]

# remove the blob part
urls = [url.replace("/blob/", "/") for url in urls]

# remove the new line character
urls = [url.replace("\n", "") for url in urls]

# download all the contracts and put them in a contrcts folder as text files
count = 0
for url in urls:
    url = url.strip()
    reponse = requests.get(url)
    # hast the url to get the file name
    file_name = str(count + 1)
    count += 1
    with open(f"contracts/{file_name}.txt", "w") as f:
        f.write(reponse.text)
