import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ExtractionError(Exception):
    """Custom exception for extraction errors"""
    pass

def extract_from_web(base_url, max_pages=50, max_items=1000):
    """
    Extract data from web with error handling
    
    Args:
        base_url (str): The base URL to scrape
        max_pages (int): Maximum number of pages to scrape
        max_items (int): Maximum number of items to collect
        
    Returns:
        pd.DataFrame: Extracted data
        
    Raises:
        ExtractionError: If there are critical errors during extraction
        ValueError: If input parameters are invalid
    """
    try:
        # Validate input parameters
        if not isinstance(base_url, str) or not base_url.startswith('http'):
            raise ValueError("Invalid base URL provided")
        if not isinstance(max_pages, int) or max_pages <= 0:
            raise ValueError("max_pages must be a positive integer")
        if not isinstance(max_items, int) or max_items <= 0:
            raise ValueError("max_items must be a positive integer")

        all_data = []
        extraction_time = datetime.now()
        failed_pages = []

        for page in range(1, max_pages + 1):
            try:
                # Adjust URL for page 1
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url}/page{page}"

                logging.info(f"Scraping page {page}: {url}")
                
                # Add timeout to prevent hanging
                response = requests.get(url, timeout=30)
                response.raise_for_status()  # Raise an exception for bad status codes

                soup = BeautifulSoup(response.content, "html.parser")
                cards = soup.find_all("div", class_="collection-card")

                if not cards:
                    logging.warning(f"No product cards found on page {page}")
                    continue

                for card in cards:
                    try:
                        title = card.find("h3", class_="product-title")
                        if not title:
                            raise ValueError("Product title not found")
                        title = title.text.strip()

                        price = card.find("span", class_="price")
                        if not price:
                            raise ValueError("Price not found")
                        price_text = price.text.strip().replace("$", "")
                        price_usd = float(price_text)

                        details = card.find("div", class_="product-details")
                        if not details:
                            raise ValueError("Product details not found")
                        details = details.find_all("p")

                        rating_text = details[0].text.strip()
                        rating = float(rating_text.split("⭐")[1].split("/")[0].strip()) if "⭐" in rating_text else None

                        colors = int(details[1].text.strip().split()[0])
                        size = details[2].text.strip().split(":")[1].strip()
                        gender = details[3].text.strip().split(":")[1].strip()

                        all_data.append({
                            "Title": title,
                            "Price": price_usd,
                            "Rating": rating,
                            "Colors": colors,
                            "Size": size,
                            "Gender": gender,
                            "Timestamp": extraction_time
                        })

                        if len(all_data) >= max_items:
                            logging.info(f"Reached maximum items limit: {max_items}")
                            return pd.DataFrame(all_data)

                    except (ValueError, IndexError) as e:
                        logging.error(f"Error processing product card: {str(e)}")
                        continue

            except requests.RequestException as e:
                logging.error(f"Failed to fetch page {page}: {str(e)}")
                failed_pages.append(page)
                continue

        if not all_data:
            raise ExtractionError("No data was extracted from any page")

        if failed_pages:
            logging.warning(f"Failed to extract from pages: {failed_pages}")

        return pd.DataFrame(all_data)

    except Exception as e:
        logging.error(f"Critical error during extraction: {str(e)}")
        raise ExtractionError(f"Extraction failed: {str(e)}")
