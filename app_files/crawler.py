# app_files/crawler.py
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def scrape_videos(base_url, selected_filter=None, pages_to_scrape=None):
    """
    Scrape videos from a MissAV series/maker page
    """
    scraper = cloudscraper.create_scraper()
    
    # Clean base URL
    clean_base_url = base_url.split("?")[0]
    
    # Detect current filter
    current_filter = None
    if "?filters=" in base_url:
        current_filter = base_url.split("?filters=")[-1].split("&")[0]
    
    # Determine filter
    if selected_filter is not None:
        use_filter = selected_filter
    elif current_filter is not None:
        use_filter = current_filter
    else:
        use_filter = None

    # Build target URL
    if use_filter is None:
        target_url = clean_base_url
    else:
        if "?" in clean_base_url:
            target_url = f"{clean_base_url}&filters={use_filter}"
        else:
            target_url = f"{clean_base_url}?filters={use_filter}"
    
    # Fetch initial page
    try:
        res = scraper.get(target_url)
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"Error fetching page: {e}")
        return {'videos': [], 'max_pages': 0}

    # Find max pages
    max_page = 1
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "page=" in href:
            try:
                num = int(href.split("page=")[-1].split("&")[0])
                if num > max_page:
                    max_page = num
            except:
                pass
    
    # If pages=0, return metadata only
    if pages_to_scrape == 0:
        return {'videos': [], 'max_pages': max_page}

    if pages_to_scrape is None or pages_to_scrape > max_page:
        pages_to_scrape = max_page
    
    all_videos = []
    
    # Scrape pages
    for page_num in range(1, pages_to_scrape + 1):
        sep = "&" if "?" in target_url else "?"
        url = f"{target_url}{sep}page={page_num}"
        
        if page_num == 1:
            current_soup = soup
        else:
            try:
                res = scraper.get(url)
                current_soup = BeautifulSoup(res.text, "html.parser")
            except:
                continue

        # --- IMPROVED EXTRACTION LOGIC ---
        for a in current_soup.find_all("a", href=True):
            href = a.get("href", "")
            full_url = urljoin("https://missav.ws", href)
            
            # Match video URL pattern
            if re.search(r'/en/[a-z]+-\d', full_url):
                
                # 1. Extract Code from URL (e.g., .../en/ABP-123 -> ABP-123)
                try:
                    code = full_url.split("/")[-1].upper()
                except:
                    code = "UNKNOWN"
                
                # 2. Extract Title (Priority: img alt tag > a tag text)
                title = ""
                img = a.find("img")
                if img and img.get("alt"):
                    # Use alt text if available (usually the full title)
                    title = img.get("alt").strip()
                else:
                    # Fallback to link text
                    title = a.get_text(strip=True)
                
                # Filter out timestamps or bad data
                if title and not re.match(r'\d+:\d+:\d+', title) and len(title) > 5:
                    all_videos.append({
                        'url': full_url,
                        'title': title,
                        'code': code
                    })
    
    # Remove duplicates
    seen = set()
    unique_videos = []
    for v in all_videos:
        if v['url'] not in seen:
            seen.add(v['url'])
            unique_videos.append(v)
    
    return {'videos': unique_videos, 'max_pages': max_page}

def get_filters(base_url):
    scraper = cloudscraper.create_scraper()
    try:
        res = scraper.get(base_url)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        return {'filters': {"All": None}, 'current_filter': None, 'clean_base_url': base_url.split("?")[0]}
    
    clean_base_url = base_url.split("?")[0]
    current_filter = None
    if "?filters=" in base_url:
        current_filter = base_url.split("?filters=")[-1].split("&")[0]
    
    filters = {"All": None}
    for a in soup.find_all("a", href=True):
        href = a['href']
        if '?filters=' in href:
            if '&sort=' not in href and '&page=' not in href:
                filter_name = a.text.strip()
                if filter_name:
                    filter_value = href.split("?filters=")[-1].split("&")[0]
                    filters[filter_name] = filter_value
    
    return {
        'filters': filters,
        'current_filter': current_filter,
        'clean_base_url': clean_base_url
    }