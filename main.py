import os
import json
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import typer
import time

app = typer.Typer()


class Crawler:
    def __init__(self, url: str, output_dir: str, prefix: str):
        self.url = url
        self.output_dir = output_dir
        self.prefix = prefix

    def content_2_json(self, sou, post_url, title, published_time):
        if type(sou) != str:
            content = sou.text.strip()
        else:
            content = sou

        post_data = {
            'page_link': post_url,
            'title': title,
            'published_time': published_time,
            'content': content
        }

        file_name = f"{self.prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        file_path = os.path.join(self.output_dir, file_name)

        with open(file_path, 'w') as file:
            json.dump(post_data, file, indent=4)
        print(f"Saved {file_path}")

        time.sleep(3)

    def fetch_and_save_post(self, post_url: str):
        response = requests.get(post_url, headers={"User-Agent": "XY"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').text.strip()
            published_time = datetime.now().isoformat()
            only_once = False

            try:
                content = soup.find('description').text.strip()
                self.content_2_json(content, post_url, title, published_time)
            except Exception:
                if not only_once:
                    for sou in soup.find_all('div', class_='wpforo-topic-title'):
                        self.content_2_json(sou, post_url, title, published_time)
                    only_once = True

    def crawl(self):
        response = requests.get(self.url, headers={"User-Agent": "XY"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            post_links = [link['href'] for link in soup.find_all('link')]

            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.map(self.fetch_and_save_post, post_links[:len(post_links)//2])

            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.map(self.fetch_and_save_post, post_links[len(post_links)//2:])


@app.command()
def run_crawler(url: str = 'https://foreternia.com/community/announcement-forum',
                output_dir: str = './data/', prefix: str = 'thread'):
    """
    Crawl and save posts from the given URL with a 3-second delay between retrievals, a user-agent header, and cookie handling.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    crawler = Crawler(url, output_dir, prefix)
    crawler.crawl()


if __name__ == "__main__":
    # TODO: add logger
    # TODO: add error handling
    app()
