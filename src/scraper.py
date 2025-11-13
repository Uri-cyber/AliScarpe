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
        """Extract comprehensive information from a single product element"""
        try:
            product = {}

            # ========== BASIC INFO ==========
            # Title
            title_selectors = ['h1', 'h2', 'h3', 'span[class*="title"]', 'a[title]', 'div[class*="title"]']
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    product['title'] = title_elem.get_text(strip=True) or title_elem.get('title', '')
                    break

            if not product.get('title'):
                return None

            # URL
            link_elem = element.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://www.aliexpress.com' + href
                product['url'] = href

                # Extract product ID from URL
                product_id_match = re.search(r'/(\d{10,})', href)
                if product_id_match:
                    product['product_id'] = product_id_match.group(1)

            # Image URL
            img_elem = element.find('img', src=True)
            if not img_elem:
                img_elem = element.find('img', attrs={'data-src': True})
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src', '')
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                product['image_url'] = img_src

            # ========== PRICING ==========
            # Current Price
            price_selectors = ['span[class*="price"]', 'div[class*="price"]', 'strong[class*="price"]',
                             'span[class*="Price"]', 'div[class*="snow-price"]']
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    if price_match:
                        product['price'] = price_match.group().replace(',', '')
                    break

            # Original Price (before discount)
            original_price_selectors = ['span[class*="original"]', 'span[class*="was"]',
                                       'del', 's', 'span[class*="old-price"]']
            for selector in original_price_selectors:
                orig_elem = element.select_one(selector)
                if orig_elem:
                    orig_text = orig_elem.get_text(strip=True)
                    orig_match = re.search(r'[\d,]+\.?\d*', orig_text)
                    if orig_match:
                        product['original_price'] = orig_match.group().replace(',', '')
                        # Calculate discount percentage
                        if product.get('price') and product.get('original_price'):
                            try:
                                current = float(product['price'])
                                original = float(product['original_price'])
                                discount = ((original - current) / original) * 100
                                product['discount_percentage'] = f"{discount:.1f}%"
                            except:
                                pass
                    break

            # Price Range (for products with variations)
            price_range_match = re.search(r'([\d,]+\.?\d*)\s*-\s*([\d,]+\.?\d*)', element.get_text())
            if price_range_match:
                product['price_min'] = price_range_match.group(1).replace(',', '')
                product['price_max'] = price_range_match.group(2).replace(',', '')

            # Discount/Sale badge
            discount_selectors = ['span[class*="discount"]', 'span[class*="sale"]', 'div[class*="off"]']
            for selector in discount_selectors:
                discount_elem = element.select_one(selector)
                if discount_elem:
                    product['discount_badge'] = discount_elem.get_text(strip=True)
                    break

            # ========== RATINGS & REVIEWS ==========
            # Rating
            rating_selectors = ['span[class*="rating"]', 'div[class*="rating"]', 'span[class*="star"]',
                              'span[class*="Star"]', 'div[class*="rate"]']
            for selector in rating_selectors:
                rating_elem = element.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'[\d.]+', rating_text)
                    if rating_match:
                        product['rating'] = rating_match.group()
                    break

            # Number of reviews
            review_count_selectors = ['span[class*="review"]', 'span[class*="evaluation"]',
                                     'a[class*="review"]', 'span[class*="Review"]']
            for selector in review_count_selectors:
                review_elem = element.select_one(selector)
                if review_elem:
                    review_text = review_elem.get_text(strip=True)
                    # Extract number (handle K notation: 1.2K = 1200)
                    review_match = re.search(r'([\d.]+)\s*([KkMm])?', review_text)
                    if review_match:
                        num = review_match.group(1)
                        multiplier = review_match.group(2)
                        if multiplier:
                            if multiplier.upper() == 'K':
                                num = str(float(num) * 1000)
                            elif multiplier.upper() == 'M':
                                num = str(float(num) * 1000000)
                        product['review_count'] = num
                    break

            # ========== ORDERS/SALES ==========
            orders_selectors = ['span[class*="order"]', 'span[class*="sale"]', 'span[class*="sold"]',
                              'em[title*="sold"]', 'span[class*="Sales"]']
            for selector in orders_selectors:
                orders_elem = element.select_one(selector)
                if orders_elem:
                    orders_text = orders_elem.get_text(strip=True)
                    product['orders'] = orders_text
                    # Extract numeric value
                    orders_match = re.search(r'([\d,]+\.?\d*)\s*([KkMm+])?', orders_text)
                    if orders_match:
                        num = orders_match.group(1).replace(',', '')
                        multiplier = orders_match.group(2)
                        if multiplier:
                            if 'K' in multiplier.upper():
                                num = str(float(num) * 1000)
                            elif 'M' in multiplier.upper():
                                num = str(float(num) * 1000000)
                        product['orders_count'] = num
                    break

            # ========== SHIPPING ==========
            # Shipping info (free/cost)
            shipping_elem = element.select_one('span[class*="shipping"]')
            if not shipping_elem:
                shipping_elem = element.select_one('div[class*="shipping"]')
            if not shipping_elem:
                shipping_elem = element.select_one('span[class*="Shipping"]')
            if shipping_elem:
                product['shipping'] = shipping_elem.get_text(strip=True)
                # Determine if free shipping
                if 'free' in product['shipping'].lower():
                    product['free_shipping'] = 'Yes'
                else:
                    product['free_shipping'] = 'No'

            # Delivery time
            delivery_selectors = ['span[class*="delivery"]', 'span[class*="arrive"]', 'div[class*="delivery"]']
            for selector in delivery_selectors:
                delivery_elem = element.select_one(selector)
                if delivery_elem:
                    product['delivery_time'] = delivery_elem.get_text(strip=True)
                    break

            # Ships from
            ships_from_selectors = ['span[class*="from"]', 'span[class*="warehouse"]', 'div[class*="ships"]']
            for selector in ships_from_selectors:
                ships_elem = element.select_one(selector)
                if ships_elem:
                    product['ships_from'] = ships_elem.get_text(strip=True)
                    break

            # ========== STORE INFO ==========
            # Store name
            store_selectors = ['a[class*="store"]', 'span[class*="store"]', 'div[class*="shop"]',
                             'a[class*="Shop"]', 'span[class*="seller"]']
            for selector in store_selectors:
                store_elem = element.select_one(selector)
                if store_elem:
                    product['store_name'] = store_elem.get_text(strip=True)
                    break

            # Store rating
            store_rating_selectors = ['span[class*="store"][class*="rating"]', 'div[class*="shop"][class*="rating"]']
            for selector in store_rating_selectors:
                store_rating_elem = element.select_one(selector)
                if store_rating_elem:
                    product['store_rating'] = store_rating_elem.get_text(strip=True)
                    break

            # ========== BADGES & INDICATORS ==========
            # Top selling / Choice / Hot badges
            badge_selectors = ['span[class*="badge"]', 'span[class*="tag"]', 'div[class*="badge"]',
                             'span[class*="choice"]', 'span[class*="hot"]', 'span[class*="top"]']
            badges = []
            for selector in badge_selectors:
                badge_elems = element.select(selector)
                for badge_elem in badge_elems:
                    badge_text = badge_elem.get_text(strip=True)
                    if badge_text and len(badge_text) < 30:  # Avoid long text
                        badges.append(badge_text)
            if badges:
                product['badges'] = ', '.join(badges)

            # "Almost gone" / "Limited stock"
            limited_stock_keywords = ['almost gone', 'limited', 'only.*left', 'low stock']
            element_text = element.get_text().lower()
            for keyword in limited_stock_keywords:
                if re.search(keyword, element_text):
                    product['stock_status'] = 'Limited Stock'
                    break

            # ========== POPULARITY INDICATORS ==========
            # Recently sold count
            recent_sold_match = re.search(r'(\d+)\s*sold.*?(24|hour|recently)', element.get_text(), re.IGNORECASE)
            if recent_sold_match:
                product['recent_sold_24h'] = recent_sold_match.group(1)

            # People viewing
            viewing_match = re.search(r'(\d+)\s*people.*?viewing', element.get_text(), re.IGNORECASE)
            if viewing_match:
                product['people_viewing'] = viewing_match.group(1)

            # ========== ADDITIONAL INFO ==========
            # Ad indicator
            ad_indicators = element.select('span[class*="ad"]')
            if ad_indicators or 'sponsored' in element.get_text().lower():
                product['is_sponsored'] = 'Yes'
            else:
                product['is_sponsored'] = 'No'

            # Variations available (colors, sizes, etc.)
            variation_selectors = ['span[class*="variation"]', 'div[class*="option"]', 'span[class*="color"]']
            for selector in variation_selectors:
                var_elem = element.select_one(selector)
                if var_elem:
                    product['has_variations'] = 'Yes'
                    variation_text = var_elem.get_text(strip=True)
                    # Try to extract number of options
                    var_match = re.search(r'(\d+)\s*(color|option|size)', variation_text, re.IGNORECASE)
                    if var_match:
                        product['variation_count'] = var_match.group(1)
                    break

            # Plus/Premium membership discount
            plus_match = re.search(r'plus.*?(save|off|\d+%)', element.get_text(), re.IGNORECASE)
            if plus_match:
                product['plus_discount'] = plus_match.group(0)

            # Coupon available
            coupon_keywords = ['coupon', 'code', 'voucher']
            for keyword in coupon_keywords:
                if keyword in element.get_text().lower():
                    product['coupon_available'] = 'Yes'
                    break

            # Return policy
            return_match = re.search(r'(\d+)\s*day.*?return', element.get_text(), re.IGNORECASE)
            if return_match:
                product['return_days'] = return_match.group(1)

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
