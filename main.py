#!/usr/bin/env python3
"""
AliExpress Scraper - Main Entry Point
Scrapes product information from AliExpress and exports to Excel
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper import AliExpressScraper
from excel_exporter import ExcelExporter
from config_loader import ConfigLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the scraper"""

    parser = argparse.ArgumentParser(
        description='AliExpress Product Scraper - Extract product data to Excel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use configuration file
  python main.py --config config.json

  # Quick scrape with command line arguments
  python main.py --query "laptop" --max 20

  # Multiple queries with command line
  python main.py --query "laptop" --query "phone" --max 15

  # With price filters
  python main.py --query "headphones" --max 10 --min-price 20 --max-price 100

  # Sort by orders (popularity)
  python main.py --query "wireless mouse" --max 15 --sort orders
        """
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )

    parser.add_argument(
        '--query', '-q',
        type=str,
        action='append',
        help='Search query (can be used multiple times for multiple searches)'
    )

    parser.add_argument(
        '--max', '-m',
        type=int,
        default=10,
        help='Maximum number of products to scrape (default: 10)'
    )

    parser.add_argument(
        '--min-price',
        type=float,
        help='Minimum price filter'
    )

    parser.add_argument(
        '--max-price',
        type=float,
        help='Maximum price filter'
    )

    parser.add_argument(
        '--sort',
        type=str,
        choices=['default', 'price_asc', 'price_desc', 'orders'],
        default='default',
        help='Sort order (default: default)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output filename (optional)'
    )

    parser.add_argument(
        '--no-selenium',
        action='store_true',
        help='Use requests instead of Selenium (faster but may not work)'
    )

    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Show browser window (only with Selenium)'
    )

    args = parser.parse_args()

    try:
        # Determine if using config file or command line arguments
        if args.query:
            # Command line mode
            logger.info("Running in command-line mode")
            run_from_command_line(args)
        else:
            # Config file mode
            logger.info("Running in config file mode")
            run_from_config(args.config)

    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


def run_from_config(config_path: str):
    """
    Run scraper using configuration file

    Args:
        config_path: Path to configuration file
    """
    # Load configuration
    config = ConfigLoader.load_config(config_path)

    # Extract settings
    scraping_config = config['scraping']
    searches = config['searches']
    export_config = config['export']

    # Initialize scraper
    logger.info("Initializing scraper...")
    with AliExpressScraper(
        use_selenium=scraping_config['use_selenium'],
        headless=scraping_config['headless']
    ) as scraper:

        # Initialize exporter
        exporter = ExcelExporter(output_dir=export_config['output_dir'])

        # Determine if we need multiple sheets
        if export_config.get('separate_files', False) or len(searches) == 1:
            # Separate files or single search
            for search in searches:
                logger.info(f"\n{'='*60}")
                logger.info(f"Scraping: {search['query']}")
                logger.info(f"{'='*60}")

                products = scraper.scrape_search_results(
                    search_query=search['query'],
                    max_products=search.get('max_products', 10),
                    min_price=search.get('min_price'),
                    max_price=search.get('max_price'),
                    sort_by=search.get('sort_by', 'default')
                )

                if products:
                    filepath = exporter.export_to_excel(
                        products=products,
                        search_query=search['query'],
                        auto_format=export_config['auto_format']
                    )
                    logger.info(f"✓ Exported {len(products)} products to: {filepath}")
                else:
                    logger.warning(f"✗ No products found for: {search['query']}")

        else:
            # Multiple searches in one file with multiple sheets
            logger.info(f"\nScraping {len(searches)} queries...")
            results_dict = {}

            for search in searches:
                logger.info(f"\n{'='*60}")
                logger.info(f"Scraping: {search['query']}")
                logger.info(f"{'='*60}")

                products = scraper.scrape_search_results(
                    search_query=search['query'],
                    max_products=search.get('max_products', 10),
                    min_price=search.get('min_price'),
                    max_price=search.get('max_price'),
                    sort_by=search.get('sort_by', 'default')
                )

                if products:
                    results_dict[search['query']] = products
                    logger.info(f"✓ Found {len(products)} products")
                else:
                    logger.warning(f"✗ No products found")

            # Export all results to one file
            if results_dict:
                filepath = exporter.export_multiple_queries(results_dict)
                total_products = sum(len(products) for products in results_dict.values())
                logger.info(f"\n✓ Exported {total_products} total products to: {filepath}")
            else:
                logger.warning("\n✗ No products found for any query")

    logger.info("\n" + "="*60)
    logger.info("Scraping completed!")
    logger.info("="*60)


def run_from_command_line(args):
    """
    Run scraper using command line arguments

    Args:
        args: Parsed command line arguments
    """
    # Initialize scraper
    logger.info("Initializing scraper...")
    with AliExpressScraper(
        use_selenium=not args.no_selenium,
        headless=not args.no_headless
    ) as scraper:

        # Initialize exporter
        exporter = ExcelExporter(output_dir='output')

        # Multiple queries
        if len(args.query) > 1:
            results_dict = {}

            for query in args.query:
                logger.info(f"\n{'='*60}")
                logger.info(f"Scraping: {query}")
                logger.info(f"{'='*60}")

                products = scraper.scrape_search_results(
                    search_query=query,
                    max_products=args.max,
                    min_price=args.min_price,
                    max_price=args.max_price,
                    sort_by=args.sort
                )

                if products:
                    results_dict[query] = products
                    logger.info(f"✓ Found {len(products)} products")
                else:
                    logger.warning(f"✗ No products found")

            # Export all results
            if results_dict:
                filepath = exporter.export_multiple_queries(
                    results_dict,
                    filename=args.output
                )
                total_products = sum(len(products) for products in results_dict.values())
                logger.info(f"\n✓ Exported {total_products} total products to: {filepath}")

        # Single query
        else:
            query = args.query[0]
            logger.info(f"\n{'='*60}")
            logger.info(f"Scraping: {query}")
            logger.info(f"{'='*60}")

            products = scraper.scrape_search_results(
                search_query=query,
                max_products=args.max,
                min_price=args.min_price,
                max_price=args.max_price,
                sort_by=args.sort
            )

            if products:
                filepath = exporter.export_to_excel(
                    products=products,
                    filename=args.output,
                    search_query=query
                )
                logger.info(f"\n✓ Exported {len(products)} products to: {filepath}")
            else:
                logger.warning(f"\n✗ No products found for: {query}")

    logger.info("\n" + "="*60)
    logger.info("Scraping completed!")
    logger.info("="*60)


if __name__ == '__main__':
    main()
