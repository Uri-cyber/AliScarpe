"""
Affiliate Link Converter for AliExpress URLs
Converts regular product URLs to affiliate tracking URLs
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AffiliateConverter:
    """
    Convert AliExpress product URLs to affiliate links
    """

    def __init__(self, affiliate_config: dict = None):
        """
        Initialize the affiliate converter

        Args:
            affiliate_config: Dictionary containing affiliate parameters
        """
        self.config = affiliate_config or {}
        self.enabled = self.config.get('enabled', False)
        self.affiliate_params = self.config.get('parameters', {})
        self.affiliate_id = self.config.get('affiliate_id', '')
        self.tracking_id = self.config.get('tracking_id', '')

        if self.enabled:
            logger.info("Affiliate link conversion enabled")
        else:
            logger.info("Affiliate link conversion disabled")

    def convert_url(self, original_url: str) -> str:
        """
        Convert a regular AliExpress URL to an affiliate URL

        Args:
            original_url: Original product URL

        Returns:
            Affiliate URL if conversion is enabled, otherwise original URL
        """
        if not self.enabled or not original_url:
            return original_url

        try:
            # Parse the URL
            parsed = urlparse(original_url)

            # Parse existing query parameters
            query_params = parse_qs(parsed.query)

            # Flatten query params (parse_qs returns lists)
            flat_params = {k: v[0] if isinstance(v, list) and len(v) > 0 else v
                          for k, v in query_params.items()}

            # Add affiliate parameters
            # Method 1: Direct affiliate parameters (most common)
            if self.affiliate_params:
                for key, value in self.affiliate_params.items():
                    flat_params[key] = value

            # Method 2: Standard AliExpress affiliate format
            if self.affiliate_id:
                flat_params['aff_trace_key'] = self.affiliate_id
                flat_params['aff_platform'] = flat_params.get('aff_platform', 'portals-tool')
                flat_params['sk'] = flat_params.get('sk', self.affiliate_id)

            # Method 3: Add tracking ID
            if self.tracking_id:
                flat_params['terminal_id'] = self.tracking_id

            # Rebuild the URL
            new_query = urlencode(flat_params)
            affiliate_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))

            logger.debug(f"Converted URL: {original_url[:50]}... -> {affiliate_url[:50]}...")
            return affiliate_url

        except Exception as e:
            logger.error(f"Error converting affiliate URL: {e}")
            return original_url

    def convert_multiple(self, urls: list) -> list:
        """
        Convert multiple URLs to affiliate links

        Args:
            urls: List of URLs

        Returns:
            List of converted URLs
        """
        return [self.convert_url(url) for url in urls]

    def add_affiliate_to_product(self, product: dict) -> dict:
        """
        Add affiliate URL to a product dictionary

        Args:
            product: Product dictionary with 'url' key

        Returns:
            Product dictionary with added 'affiliate_url' key
        """
        if not self.enabled:
            return product

        original_url = product.get('url', '')
        if original_url:
            affiliate_url = self.convert_url(original_url)
            product['affiliate_url'] = affiliate_url

        return product

    def add_affiliate_to_products(self, products: list) -> list:
        """
        Add affiliate URLs to a list of product dictionaries

        Args:
            products: List of product dictionaries

        Returns:
            List of products with affiliate URLs added
        """
        return [self.add_affiliate_to_product(product) for product in products]


class AffiliatePresets:
    """
    Pre-configured affiliate setups for common affiliate networks
    """

    @staticmethod
    def get_preset(preset_name: str, affiliate_id: str, **kwargs) -> dict:
        """
        Get a pre-configured affiliate setup

        Args:
            preset_name: Name of the preset ('aliexpress_standard', 'admitad', etc.)
            affiliate_id: Your affiliate ID
            **kwargs: Additional parameters

        Returns:
            Affiliate configuration dictionary
        """
        presets = {
            'aliexpress_standard': {
                'enabled': True,
                'affiliate_id': affiliate_id,
                'parameters': {
                    'aff_trace_key': affiliate_id,
                    'aff_platform': 'portals-tool',
                    'sk': affiliate_id,
                    'aff_request': 'yes'
                }
            },
            'admitad': {
                'enabled': True,
                'parameters': {
                    'admitad_uid': affiliate_id,
                }
            },
            'custom': {
                'enabled': True,
                'parameters': kwargs.get('parameters', {})
            }
        }

        preset = presets.get(preset_name, {})
        logger.info(f"Using affiliate preset: {preset_name}")
        return preset


# Example usage functions
def create_affiliate_converter_from_config(config: dict) -> AffiliateConverter:
    """
    Create an AffiliateConverter from a configuration dictionary

    Args:
        config: Configuration dictionary

    Returns:
        Configured AffiliateConverter instance
    """
    affiliate_config = config.get('affiliate', {})

    # Check if using a preset
    preset = affiliate_config.get('preset')
    if preset:
        affiliate_id = affiliate_config.get('affiliate_id', '')
        custom_params = affiliate_config.get('parameters', {})
        affiliate_config = AffiliatePresets.get_preset(preset, affiliate_id, parameters=custom_params)

    return AffiliateConverter(affiliate_config)
