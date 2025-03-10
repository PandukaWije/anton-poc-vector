from bs4 import BeautifulSoup
from datetime import datetime
from nltk.tokenize import sent_tokenize
from urllib.parse import urlparse, urljoin
import os, re, uuid, json, pytz, requests, tiktoken, nltk
nltk.download('punkt')
 
# Timezone configuration
ist = pytz.timezone('Asia/Kolkata')
enc = tiktoken.encoding_for_model("gpt-4o")

def is_valid_url(
                url, 
                base_domain
                ):
    """Check if URL is valid and belongs to the same domain."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        skip_extensions = {
            '.css', '.js', '.jpg', '.jpeg', '.png', '.gif',
            '.pdf', '.zip', '.ico', '.woff', '.woff2',
            '.ttf', '.eot', '.svg', '.mp4', '.webp', '.mp3'
        }
        is_valid = (
            parsed.scheme in ('http', 'https') and
            len(parsed.path) < 255 and
            not any(parsed.path.lower().endswith(ext) for ext in skip_extensions)
        )
        # Allow same or sub-domains
        is_same_domain = (
            domain == base_domain or
            domain.endswith('.' + base_domain) or
            base_domain.endswith('.' + domain)
        )
        return is_same_domain and is_valid
    except Exception:
        return False
 
 
def parse_sitemap(base_url):
    """Parse sitemap.xml (or alternatives) to find additional URLs."""
    sitemap_urls = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/sitemap/sitemap.xml"
    ]
    found_urls = set()
    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                urls = soup.find_all(['loc', 'url'])
                for url in urls:
                    found_urls.add(url.text.strip())
        except Exception:
            continue
    return found_urls
 
 
def parse_robots_txt(base_url):
    """Parse robots.txt to find URLs (e.g., allowed paths)."""
    robots_url = f"{base_url}/robots.txt"
    found_urls = set()
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            lines = response.text.split('\n')
            for line in lines:
                line = line.strip().lower()
                if line.startswith('allow:'):
                    path = line.split(':', 1)[1].strip()
                    if path.startswith('/'):
                        found_urls.add(urljoin(base_url, path))
    except Exception:
        pass
    return found_urls
 
 
def extract_sub_urls(soup, base_url, base_domain):
    """Extract valid sub-URLs from the page content."""
    sub_urls = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Convert relative URL to absolute URL if necessary
        full_url = urljoin(base_url, href) if (href.startswith('/') or not href.startswith('http')) else href
        # Clean URL by removing fragments and queries
        cleaned_url = re.sub(r'[#?].*$', '', full_url).rstrip('/')
        if is_valid_url(cleaned_url, base_domain):
            sub_urls.add(cleaned_url)
    return sub_urls
 
 
def process_url_content(url, soup, base_domain):
    """
    Clean the HTML content by removing non-essential tags,
    and return a dictionary containing text content and metadata.
    """
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        element.decompose()

    # Extract and clean text
    text = soup.get_text(separator=' ')
    cleaned_text = " ".join(text.split())
    if not cleaned_text:
        return None
 
    title = soup.title.string if soup.title else ""
    content_length = len(enc.encode(cleaned_text))
    metadata = {
                "url": url,
                "domain": base_domain,
                "title": title,
                "fetch_time": datetime.now(ist).isoformat(),
                "content_length": content_length
                }
    return {"content": cleaned_text, "metadata": metadata}
 
 
def fetch_and_extract_url_data(
                                url, 
                                recursive=True, 
                                max_pages=100
                                ):
    """
    Given a URL, fetch its content, use sitemaps and robots.txt to gather additional URLs,
    extract text from each page, and return a list of extracted data.
    """
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    base_domain = parsed_url.netloc.replace('www.', '')
   
    processed_data = []
    visited_urls = set()
    urls_to_visit = {url}
 
    # Extend the list with sitemap and robots.txt discovered URLs
    urls_to_visit.update(parse_sitemap(base_url))
    urls_to_visit.update(parse_robots_txt(base_url))
 
    while urls_to_visit and len(processed_data) < max_pages:
        current_url = urls_to_visit.pop()
        if current_url in visited_urls:
            continue
        try:
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            data = process_url_content(current_url, soup, base_domain)
            if data:
                processed_data.append(data)
            visited_urls.add(current_url)
            if recursive:
                sub_urls = extract_sub_urls(soup, base_url, base_domain)
                urls_to_visit.update(sub_urls - visited_urls)
        except Exception:
            continue
    return processed_data
 
 
def save_extracted_data(data, filename):
    """
    Save the extracted data (list of dictionaries) to a JSON file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to file: {e}")