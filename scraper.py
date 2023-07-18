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

    # Find all the links on the page
    links = soup.find_all('a')

    # Recursively scrape the content of the links
    for link in links:
        href = link.get('href')
        if not href or href.startswith('#'):
            continue

        if href.startswith('/'):
            href = urljoin(url, href)

        scrape_page(href, output_file)


# Start scraping from the given URL and save the content in a single file
scrape_page('https://polkadot.network/development/docs/', 'output_text.txt')
