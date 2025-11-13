"""
AliExpress Product Scraper
Extracts product information from AliExpress search results
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time
import json
import re
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AliExpressScraper:
    """
    Scraper for extracting product information from AliExpress
    """

    def __init__(self, use_selenium: bool = True, headless: bool = True):
        """
        Initialize the scraper

        Args:
            use_selenium: Whether to use Selenium for scraping (recommended for AliExpress)
            headless: Whether to run browser in headless mode
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.ua = UserAgent()
        self.driver = None

        if self.use_selenium:
            self._setup_selenium()

    def _setup_selenium(self):
        """Setup Selenium WebDriver"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'user-agent={self.ua.random}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            raise

    def scrape_search_results(self, search_query: str, max_products: int = 10,
                             min_price: Optional[float] = None,
                             max_price: Optional[float] = None,
                             sort_by: str = "default") -> List[Dict]:
        """
        Scrape product information from AliExpress search results

        Args:
            search_query: The search term (e.g., "laptop", "phone case")
            max_products: Maximum number of products to scrape
            min_price: Minimum price filter (optional)
            max_price: Maximum price filter (optional)
            sort_by: Sorting option (default, price_asc, price_desc, orders)

        Returns:
            List of product dictionaries containing scraped data
        """
        logger.info(f"Starting scrape for '{search_query}' - Max products: {max_products}")

        # Build search URL
        base_url = "https://www.aliexpress.com/wholesale"
        params = {
            'SearchText': search_query,
        }

        # Add price filters if specified
        if min_price:
            params['minPrice'] = min_price
        if max_price:
            params['maxPrice'] = max_price

        # Add sorting
        if sort_by == "price_asc":
            params['SortType'] = 'price_asc'
        elif sort_by == "price_desc":
            params['SortType'] = 'price_desc'
        elif sort_by == "orders":
            params['SortType'] = 'total_tranpro_desc'

        search_url = base_url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()])

        products = []

        if self.use_selenium:
            products = self._scrape_with_selenium(search_url, max_products)
        else:
            products = self._scrape_with_requests(search_url, max_products)

        logger.info(f"Scraping completed. Total products found: {len(products)}")
        return products

    def _scrape_with_selenium(self, url: str, max_products: int) -> List[Dict]:
        """Scrape using Selenium WebDriver"""
        products = []

        try:
            self.driver.get(url)
            logger.info(f"Navigating to: {url}")

            # Wait for products to load
            time.sleep(5)  # Initial wait for page load

            # Scroll to load more products
            scroll_pause_time = 2
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while len(products) < max_products:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)

                # Get page source and parse
                soup = BeautifulSoup(self.driver.page_source, 'lxml')

                # Extract products from current page state
                current_products = self._extract_products_from_html(soup)

                # Add new products
                for product in current_products:
                    if product not in products and len(products) < max_products:
                        products.append(product)

                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height or len(products) >= max_products:
                    break
                last_height = new_height

                logger.info(f"Products found so far: {len(products)}")

        except Exception as e:
            logger.error(f"Error during Selenium scraping: {e}")

        return products[:max_products]

    def _scrape_with_requests(self, url: str, max_products: int) -> List[Dict]:
        """Scrape using requests library (faster but may not work if JS is required)"""
        products = []

        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            products = self._extract_products_from_html(soup)

        except Exception as e:
            logger.error(f"Error during requests scraping: {e}")

        return products[:max_products]

    def _extract_products_from_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract product information from HTML soup"""
        products = []

        # Try multiple selectors as AliExpress structure may vary
        product_selectors = [
            'div[class*="product-item"]',
            'div[class*="list-item"]',
            'a[class*="search-card-item"]',
            'div.search-item-card-wrapper',
        ]

        product_elements = []
        for selector in product_selectors:
            product_elements = soup.select(selector)
            if product_elements:
                logger.info(f"Found {len(product_elements)} products using selector: {selector}")
                break

        for element in product_elements:
            try:
                product = self._extract_product_info(element)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error extracting product info: {e}")
                continue

        return products

    def _extract_product_info(self, element) -> Optional[Dict]:
        """Extract information from a single product element"""
        try:
            product = {}

            # Title
            title_selectors = ['h1', 'h2', 'h3', 'span[class*="title"]', 'a[title]']
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    product['title'] = title_elem.get_text(strip=True) or title_elem.get('title', '')
                    break

            if not product.get('title'):
                return None

            # Price
            price_selectors = ['span[class*="price"]', 'div[class*="price"]', 'strong[class*="price"]']
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    if price_match:
                        product['price'] = price_match.group().replace(',', '')
                    break

            # URL
            link_elem = element.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://www.aliexpress.com' + href
                product['url'] = href

            # Image URL
            img_elem = element.find('img', src=True)
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src', '')
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                product['image_url'] = img_src

            # Rating
            rating_selectors = ['span[class*="rating"]', 'div[class*="rating"]', 'span[class*="star"]']
            for selector in rating_selectors:
                rating_elem = element.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'[\d.]+', rating_text)
                    if rating_match:
                        product['rating'] = rating_match.group()
                    break

            # Orders/Sales
            orders_selectors = ['span[class*="order"]', 'span[class*="sale"]', 'em[title*="sold"]']
            for selector in orders_selectors:
                orders_elem = element.select_one(selector)
                if orders_elem:
                    orders_text = orders_elem.get_text(strip=True)
                    product['orders'] = orders_text
                    break

            # Shipping info
            shipping_elem = element.select_one('span[class*="shipping"]')
            if shipping_elem:
                product['shipping'] = shipping_elem.get_text(strip=True)

            # Store name
            store_selectors = ['a[class*="store"]', 'span[class*="store"]', 'div[class*="shop"]']
            for selector in store_selectors:
                store_elem = element.select_one(selector)
                if store_elem:
                    product['store_name'] = store_elem.get_text(strip=True)
                    break

            return product if product.get('title') else None

        except Exception as e:
            logger.debug(f"Error extracting product info: {e}")
            return None

    def scrape_product_details(self, product_url: str) -> Dict:
        """
        Scrape detailed information from a specific product page

        Args:
            product_url: URL of the product page

        Returns:
            Dictionary containing detailed product information
        """
        logger.info(f"Scraping product details from: {product_url}")

        product = {}

        try:
            if self.use_selenium:
                self.driver.get(product_url)
                time.sleep(3)
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
            else:
                headers = {'User-Agent': self.ua.random}
                response = requests.get(product_url, headers=headers, timeout=30)
                soup = BeautifulSoup(response.content, 'lxml')

            # Extract detailed information
            # Title
            title_elem = soup.select_one('h1[class*="title"]')
            if title_elem:
                product['title'] = title_elem.get_text(strip=True)

            # Price
            price_elem = soup.select_one('span[class*="price"]')
            if price_elem:
                product['price'] = price_elem.get_text(strip=True)

            # Description
            desc_elem = soup.select_one('div[class*="description"]')
            if desc_elem:
                product['description'] = desc_elem.get_text(strip=True)[:500]  # Limit length

            # Specifications
            spec_elems = soup.select('li[class*="specification"]')
            if spec_elems:
                product['specifications'] = [elem.get_text(strip=True) for elem in spec_elems]

            product['url'] = product_url

        except Exception as e:
            logger.error(f"Error scraping product details: {e}")

        return product

    def close(self):
        """Close the browser and clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
