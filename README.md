AI Data Scraper
A flexible and straightforward Python script for scraping textual and image data from web pages. Designed for collecting large volumes of data that can be used to train AI models or for more general data extraction tasks, while respecting robots.txt rules. The script filters, cleans, and stores text data and images in user-defined formats, providing a robust foundation for building AI training datasets.

Table of Contents
Key Features
Requirements
Installation
Usage
Configuration
How It Works
Logging and Output
Potential Customizations
License
Key Features
Automated Text Scraping

Extracts text from common “main content” HTML elements (<article>, <main>, [role="main"]).
Cleans and normalizes text using textacy.preprocessing.
Language Detection and Filtering

Utilizes langdetect to verify language (e.g., English).
Allows filtering out pages that do not meet a minimum text length or contain certain blocklist phrases (expandable).
Image Scraping

Automatically locates img tags in the HTML and downloads them.
Verifies image format and dimensions before storing.
Robust to Errors and Limitations

Respects robots.txt rules.
Logs issues to scraper.log for easy debugging.
Includes a placeholder for retry logic with backoff.
Flexible Output

Stores text data in both JSONL and Parquet (user-configurable).
Maintains separate image metadata for each downloaded image.
Automatically flushes data to disk once a threshold is reached (configurable).
Requirements
Make sure to install the following Python packages (ideally in a dedicated virtual environment):

bash
Copy
Edit
pip install requests beautifulsoup4 langdetect textacy pandas lxml pillow
Dependency	Purpose
requests	Handling HTTP requests
beautifulsoup4	Parsing HTML content
langdetect	Detecting the language of the text
textacy	Text cleaning and normalization
pandas	Storing and exporting the scraped text data
lxml	High-performance XML and HTML parsing
pillow	Image handling and verification
Note: Python 3.7+ is recommended for compatibility.

Installation
Clone or download this repository to your local environment.
Create a virtual environment (optional but recommended):
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
Install required packages:
bash
Copy
Edit
pip install -r requirements.txt
(Or individually as noted in Requirements)
Usage
Add your target URLs in the seed_urls list near the bottom of the script ("__main__" section).

python
Copy
Edit
seed_urls = [
    "https://example.com/article1",
    "https://example.com/article2"
]
Run the script directly:

bash
Copy
Edit
python ai_data_scraper.py
Monitor the output:

Scraping logs are saved to scraper.log.
Text data is stored in ai_training_data/ as JSONL and/or Parquet files.
Images are saved in ai_training_data/images.
Configuration
A global CONFIG dictionary at the top of the script controls how scraping is performed:

python
Copy
Edit
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
Parameter	Description
output_dir	Directory for saving data
max_workers	Number of threads to use for concurrent scraping
request_timeout	Timeout (in seconds) for each HTTP request
rate_limit_delay	Delay (in seconds) between requests to avoid overloading a server (not fully implemented in the sample code)
user_agents	A list of user agent strings to randomize requests
content_filters	Settings to filter out insufficient or undesired content
storage_formats	Output file formats (options: jsonl, parquet)
Feel free to modify the configuration to suit your needs.

How It Works
Initialization

The AIDataScraper class creates a requests.Session and a logging system.
Two storage lists (text_storage and image_storage) hold data in memory until it’s time to flush to disk.
Scraping

scrape_page(url) is called for each URL:
Robots.txt Check: A RobotFileParser checks if the page can be scraped.
Fetch Page: A GET request is made using a random User-Agent from CONFIG["user_agents"].
Parse HTML: Beautiful Soup extracts the main content from <article>, <main>, or [role="main"].
Clean & Validate: Text is cleaned, normalized, and then checked for language (langdetect) and length.
Store Text: If valid, the text is appended to self.text_storage.
Scrape Images: All <img> tags with src attributes are downloaded. Images are verified, hashed, and saved.
Storage & Output

Text data is flushed to disk in JSONL and/or Parquet format once text_storage hits a certain size (here, 1000 items).
Image files are saved immediately in ai_training_data/images.
Concurrency

ThreadPoolExecutor from the concurrent.futures module allows multiple pages to be scraped in parallel.
Logging and Output
Logs: All major operations, warnings, and errors are written to scraper.log with timestamps.
Text Data: By default, stored in ai_training_data/ as:
JSON Lines (*.jsonl)
Parquet (*.parquet)
Images: Stored in ai_training_data/images with filenames containing the domain name and a SHA-256 hash of the file contents.
Potential Customizations
Retry Logic:
Implement exponential backoff in retry_url(url) for more robust error handling when requests fail.

More Advanced Text Extraction:
Swap out the simple main-element search with libraries like trafilatura or readability-lxml for better article extraction.

Stricter Content Filtering:
Add checks for blocklisted phrases or terms in the text before saving.
Expand language detection to multiple target languages.

Rate Limiting:
Incorporate a throttle or delay in each request to respect server load constraints, beyond just robots.txt.

Image Dimension Filters:
Filter out certain image sizes (e.g., too small or too large) before saving.

License
This script is distributed under the MIT License, meaning you can freely modify, distribute, and use it for both commercial and personal projects.

