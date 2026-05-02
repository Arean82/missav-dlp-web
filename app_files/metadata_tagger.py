# app_files/metadata_tagger.py - Scrapes and injects metadata into MP4 files

import os
import re
import logging
import cloudscraper
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    from mutagen.mp4 import MP4, MP4Cover
except ImportError:
    MP4 = None

# Logging setup
TAG_LOG = Path('logs') / 'tagger.log'
TAG_LOG.parent.mkdir(exist_ok=True)
logging.basicConfig(filename=str(TAG_LOG), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_jav_code(url_or_code):
    if not url_or_code: return ""
    if url_or_code.startswith('http'):
        # Extract from URL like .../en/ABP-123
        parts = url_or_code.rstrip('/').split('/')
        return parts[-1].upper()
    return url_or_code.upper()

def fetch_fallback_metadata(code):
    """
    Tries to get metadata from BestJavPorn and JavGuru if MissAV fails.
    """
    scraper = cloudscraper.create_scraper()
    
    # 1. Try BestJavPorn
    try:
        logger.info(f"Trying BestJavPorn for {code}...")
        search_url = f"https://www.bestjavporn.com/search/{code}/"
        res = scraper.get(search_url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        video_link = None
        for a in soup.find_all('a', href=True):
            if code.lower() in a['href'].lower() and "/video/" in a['href']:
                video_link = a['href']
                break
        
        if video_link:
            res = scraper.get(video_link, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            title = soup.find('h1').text.strip() if soup.find('h1') else ""
            
            def get_bjp_val(label):
                tag = soup.find(string=re.compile(label, re.I))
                if tag and tag.parent:
                    links = tag.parent.find_all('a')
                    valid = [l.text.strip() for l in links if l.text.strip() not in ['Home', 'Studios', 'Pornstars', 'Categories', 'Uncensored']]
                    if valid: return ", ".join(valid)
                return ""

            actors = get_bjp_val("Pornstars:")
            maker = get_bjp_val("Studio:")
            thumb = ""
            og_tag = soup.find('meta', property='og:image')
            if og_tag: thumb = og_tag.get('content', '')

            return {
                "title": title,
                "artist": actors,
                "maker": maker,
                "thumb_url": thumb,
                "source": "BestJavPorn"
            }
    except Exception as e:
        logger.warning(f"BestJavPorn fallback failed: {e}")

    # 2. Try Jav.Guru
    try:
        logger.info(f"Trying JavGuru for {code}...")
        search_url = f"https://jav.guru/?s={code}"
        res = scraper.get(search_url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        video_link = None
        for a in soup.find_all('a', href=True):
            if code.lower() in a['href'].lower() and "/tag/" not in a['href']:
                video_link = a['href']
                break
        
        if video_link:
            res = scraper.get(video_link, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            title = soup.find('h1').text.strip() if soup.find('h1') else ""
            
            # Simple metadata extraction for JavGuru
            actors = ""
            for strong in soup.find_all('strong'):
                if 'actress' in strong.text.lower():
                    actors = strong.next_sibling.strip() if strong.next_sibling else ""
                    break
            
            thumb = ""
            og_tag = soup.find('meta', property='og:image')
            if og_tag: thumb = og_tag.get('content', '')

            return {
                "title": title,
                "artist": actors,
                "thumb_url": thumb,
                "source": "JavGuru"
            }
    except Exception as e:
        logger.warning(f"JavGuru fallback failed: {e}")

    return None

def fetch_missav_metadata(url_or_code, mirrors=None):
    """
    Deep-scrapes metadata from MissAV for a specific URL or JAV code.
    Ported and optimized from the Video Analyse & Rename project.
    """
    scraper = cloudscraper.create_scraper()
    target_url = url_or_code
    
    # If it's just a code, build a URL using the first mirror
    if not url_or_code.startswith('http'):
        mirror = mirrors[0] if mirrors else 'missav.ai'
        target_url = f"https://{mirror}/en/{url_or_code.lower()}"

    try:
        res = scraper.get(target_url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        if not soup or not soup.find('h1'):
            return None

        # Basic Info
        title = soup.find('h1').text.strip()
        
        def get_sidebar_val(label_text):
            label_node = soup.find(['span', 'div', 'p'], string=re.compile(label_text, re.I))
            if label_node and label_node.parent:
                links = label_node.parent.find_all('a')
                if links:
                    return ", ".join([l.text.strip() for l in links])
                full_text = label_node.parent.get_text()
                return full_text.replace(label_node.get_text(), "").strip()
            return ""

        # Extended Metadata
        actors = get_sidebar_val("Actress")
        genres = get_sidebar_val("Genre")
        series = get_sidebar_val("Series")
        maker = get_sidebar_val("Maker")
        label = get_sidebar_val("Label")
        director = get_sidebar_val("Director")
        
        # Thumbnail (OpenGraph image is usually high res)
        thumb_url = ""
        og_tag = soup.find('meta', property='og:image')
        if og_tag and og_tag.has_attr('content'):
            thumb_url = og_tag['content']

        # Release Date / Year
        year = ""
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', soup.get_text())
        if date_match:
            year = date_match.group()[:4]

        # --- FALLBACK CHECK ---
        if not actors or not title:
            logger.info("MissAV metadata incomplete, trying fallbacks...")
            code = extract_jav_code(url_or_code)
            fallback = fetch_fallback_metadata(code)
            if fallback:
                logger.info(f"Using fallback metadata from {fallback['source']}")
                if not title: title = fallback.get('title', title)
                if not actors: actors = fallback.get('artist', actors)
                if not maker: maker = fallback.get('maker', maker)
                if not thumb_url: thumb_url = fallback.get('thumb_url', thumb_url)
        # --- END FALLBACK ---

        return {
            "title": title,
            "artist": actors,
            "genre": genres,
            "series": series,
            "maker": maker,
            "label": label,
            "director": director,
            "year": year,
            "thumb_url": thumb_url,
            "url": target_url
        }
    except Exception as e:
        logger.error(f"Error fetching metadata for {target_url}: {e}")
        # Try fallback even on exception
        code = extract_jav_code(url_or_code)
        return fetch_fallback_metadata(code)

def inject_metadata(filepath, metadata):
    """
    Injects the metadata dictionary into an MP4 file using Mutagen.
    """
    if MP4 is None:
        logger.error("Mutagen not found. Cannot inject metadata.")
        return False

    if not os.path.exists(filepath):
        logger.error(f"File not found for tagging: {filepath}")
        return False

    try:
        video = MP4(filepath)
        
        # Standard Tags (iTunes Atoms)
        video["\xa9nam"] = [metadata.get("title", "")]
        video["\xa9ART"] = [metadata.get("artist", "")]
        video["aART"] = [metadata.get("artist", "")]
        video["\xa9day"] = [metadata.get("year", "")]
        video["\xa9gen"] = [metadata.get("genre", "")]
        video["\xa9alb"] = [metadata.get("maker", "")]
        
        # Custom Tags
        def set_custom(name, value):
            if value:
                key = f"----:com.apple.iTunes:{name}"
                video[key] = [value.encode("utf-8")]

        set_custom("DIRECTOR", metadata.get("director", ""))
        set_custom("LABEL", metadata.get("label", ""))
        set_custom("SERIES", metadata.get("series", ""))

        # Thumbnail Embedding
        thumb_url = metadata.get("thumb_url")
        if thumb_url:
            try:
                img_res = requests.get(thumb_url, timeout=10)
                if img_res.status_code == 200:
                    fmt = MP4Cover.FORMAT_PNG if thumb_url.lower().endswith(".png") else MP4Cover.FORMAT_JPEG
                    video["covr"] = [MP4Cover(img_res.content, imageformat=fmt)]
                    logger.info(f"Embedded thumbnail from {thumb_url}")
            except Exception as e:
                logger.error(f"Failed to download/embed thumbnail: {e}")

        video.save()
        logger.info(f"Successfully tagged: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to tag {filepath}: {e}")
        return False
