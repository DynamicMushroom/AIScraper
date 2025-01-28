import requests
import json
import os
import re
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from langdetect import detect
from concurrent.futures import ThreadPoolExecutor
from textacy import preprocessing
import hashlib
from PIL import Image
from io import BytesIO
import pandas as pd
import logging
from datetime import datetime

# Configuration
CONFIG = {
    "output_dir": "ai_training_data",
    "max_workers": 5,
    "request_timeout": 15,
    "rate_limit_delay": 1,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ..."
    ],
    "content_filters": {
        "min_text_length": 500,
        "allowed_languages": ["en"],
        "blocklist_phrases": ["lorem ipsum", "test content"]
    },
    "storage_formats": ["jsonl", "parquet"]
}

class AIDataScraper:
    def __init__(self):
        self.session = requests.Session()
        self.setup_logging()
        self.setup_storage()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='scraper.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def setup_storage(self):
        os.makedirs(CONFIG["output_dir"], exist_ok=True)
        self.text_storage = []
        self.image_storage = []
        
    def get_robots_parser(self, domain):
        rp = RobotFileParser()
        rp.set_url(f"{domain}/robots.txt")
        try:
            rp.read()
        except Exception as e:
            logging.warning(f"Could not read robots.txt: {e}")
        return rp
        
    def clean_text(self, text):
        cleaner = preprocessing.make_pipeline(
            preprocessing.normalize.whitespace,
            preprocessing.remove.html_tags,
            preprocessing.replace.urls,
            preprocessing.replace.emails,
            preprocessing.replace.phone_numbers,
            preprocessing.normalize.unicode
        )
        cleaned = cleaner(text)
        return re.sub(r'\s+', ' ', cleaned).strip()
        
    def validate_content(self, text):
        if len(text) < CONFIG["content_filters"]["min_text_length"]:
            return False
        try:
            lang = detect(text)
            if lang not in CONFIG["content_filters"]["allowed_languages"]:
                return False
        except:
            return False
        return True
        
    def scrape_page(self, url):
        try:
            # Check robots.txt
            domain = url.split('/')[2]
            rp = self.get_robots_parser(domain)
            
            if not rp.can_fetch("*", url):
                logging.warning(f"Skipping {url} due to robots.txt")
                return
                
            # Make request with random user agent
            headers = {
                "User-Agent": random.choice(CONFIG["user_agents"]),
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            response = self.session.get(
                url,
                headers=headers,
                timeout=CONFIG["request_timeout"]
            )
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract main content
            main_content = self.extract_article_content(soup)
            cleaned_content = self.clean_text(main_content)
            
            if self.validate_content(cleaned_content):
                self.store_text_data({
                    "url": url,
                    "content": cleaned_content,
                    "timestamp": datetime.now().isoformat(),
                    "source_domain": domain
                })
                
            # Extract images
            self.scrape_images(soup, domain)
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            self.retry_url(url)
            
    def extract_article_content(self, soup):
        # Use advanced content extraction algorithm
        # (Can be replaced with trafilatura or readability-lxml)
        for selector in ['article', 'main', '[role="main"]']:
            element = soup.select_one(selector)
            if element:
                return element.get_text()
        return soup.get_text()
        
    def scrape_images(self, soup, domain):
        for img in soup.find_all('img'):
            img_url = img.get('src')
            if img_url and img_url.startswith('http'):
                self.download_image(img_url, domain)
                
    def download_image(self, url, domain):
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Validate image
            img = Image.open(BytesIO(response.content))
            img.verify()
            
            # Create unique filename
            content_hash = hashlib.sha256(response.content).hexdigest()
            filename = f"{domain}_{content_hash}.{img.format.lower()}"
            
            self.store_image_data({
                "url": url,
                "filename": filename,
                "dimensions": img.size,
                "format": img.format,
                "source_domain": domain
            })
            
            # Save image
            img.save(os.path.join(CONFIG["output_dir"], "images", filename))
            
        except Exception as e:
            logging.error(f"Error downloading image {url}: {e}")
            
    def store_text_data(self, data):
        self.text_storage.append(data)
        if len(self.text_storage) >= 1000:
            self.flush_storage()
            
    def store_image_data(self, data):
        self.image_storage.append(data)
            
    def flush_storage(self):
        # Save to multiple formats
        df = pd.DataFrame(self.text_storage)
        
        if "jsonl" in CONFIG["storage_formats"]:
            df.to_json(
                os.path.join(CONFIG["output_dir"], f"text_{datetime.now().timestamp()}.jsonl"),
                orient="records",
                lines=True
            )
            
        if "parquet" in CONFIG["storage_formats"]:
            df.to_parquet(
                os.path.join(CONFIG["output_dir"], f"text_{datetime.now().timestamp()}.parquet")
            )
            
        self.text_storage = []
        
    def retry_url(self, url):
        # Implement retry logic with exponential backoff
        pass
        
    def run(self, seed_urls):
        with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            future_to_url = {
                executor.submit(self.scrape_page, url): url
                for url in seed_urls
            }
            
if __name__ == "__main__":
    scraper = AIDataScraper()
    seed_urls = [
        # Add your target URLs here
        "https://example.com/article1",
        "https://example.com/article2"
    ]
    scraper.run(seed_urls)
    scraper.flush_storage()  # Ensure remaining data is saved