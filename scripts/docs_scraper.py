import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


def scrape_page(url, output_file):
    # Send a GET request to the URL
    response = requests.get(url)
    response.raise_for_status()

    # Create a BeautifulSoup object to parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Remove script and style tags
    for script in soup(["script", "style"]):
        script.extract()

    # Find all the HTML tags containing text
    tags = soup.find_all(text=True)

    # Extract and concatenate the textual content
    content = ' '.join(tag.strip() for tag in tags)

    # Remove extra whitespaces and newlines
    content = re.sub('\s+', ' ', content)

    # Append the content to the output file
    with open(output_file, 'a') as f:
        f.write(content)
        f.write(
            '\n')  # Add a new line to separate the content of different URLs


def scrape_pages_from_file(input_file, output_file):
    with open(input_file, 'r') as urls_file:
        urls = urls_file.readlines()

    print(urls)

    for url in urls:
        url = url.strip()
        scrape_page('https://docs.substrate.io' + url, output_file)
        print(f'Scraped URL: {url} -> Appended to {output_file}')


if __name__ == "__main__":
    # Modify these paths accordingly
    input_file_path = 'substrate_urls.txt'
    output_file_path = 'polkadocs.txt'

    scrape_pages_from_file(input_file_path, output_file_path)
