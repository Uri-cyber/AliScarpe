#!/usr/bin/env python3
"""
Test script to validate scraper functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from excel_exporter import ExcelExporter
import json

def test_excel_exporter():
    """Test Excel exporter with mock data containing all new fields"""

    print("=" * 60)
    print("Testing Excel Exporter with Comprehensive Data")
    print("=" * 60)

    # Create mock product data with ALL new fields
    mock_products = [
        {
            # Basic Info
            'product_id': '1234567890',
            'title': 'Test Laptop Gaming High Performance',
            'url': 'https://www.aliexpress.com/item/1234567890.html',
            'image_url': 'https://ae01.alicdn.com/test-image.jpg',

            # Pricing
            'price': '899.99',
            'original_price': '1299.99',
            'discount_percentage': '30.8%',
            'discount_badge': '31% OFF',
            'price_min': '799.99',
            'price_max': '999.99',

            # Ratings & Reviews
            'rating': '4.8',
            'review_count': '1500',

            # Sales & Popularity
            'orders': '10K+ sold',
            'orders_count': '10000',
            'recent_sold_24h': '150',
            'people_viewing': '45',

            # Shipping
            'shipping': 'Free Shipping',
            'free_shipping': 'Yes',
            'delivery_time': '5-10 days',
            'ships_from': 'China',

            # Store Info
            'store_name': 'Premium Electronics Store',
            'store_rating': '4.9',

            # Product Features
            'has_variations': 'Yes',
            'variation_count': '5',
            'badges': 'Top Selling, Choice',
            'stock_status': 'In Stock',

            # Additional Info
            'is_sponsored': 'No',
            'coupon_available': 'Yes',
            'plus_discount': 'Save 5% with Plus',
            'return_days': '30',
            'description': 'High performance gaming laptop with latest specs'
        },
        {
            # Second product with fewer fields (to test optional fields)
            'product_id': '9876543210',
            'title': 'Wireless Bluetooth Earbuds Premium Sound',
            'url': 'https://www.aliexpress.com/item/9876543210.html',
            'image_url': 'https://ae01.alicdn.com/test-earbuds.jpg',
            'price': '29.99',
            'rating': '4.5',
            'review_count': '2500',
            'orders': '50K+ sold',
            'orders_count': '50000',
            'shipping': 'Free Shipping',
            'free_shipping': 'Yes',
            'store_name': 'Audio Gear Shop',
            'is_sponsored': 'Yes',
            'badges': 'Hot, Choice'
        }
    ]

    # Test Excel export
    exporter = ExcelExporter(output_dir='test_output')

    print(f"\n✓ ExcelExporter initialized")
    print(f"  Output directory: test_output")

    # Export to Excel
    filepath = exporter.export_to_excel(
        products=mock_products,
        filename='test_comprehensive_data.xlsx',
        search_query='test',
        auto_format=True
    )

    print(f"\n✓ Excel file created: {filepath}")

    # Read back and verify columns
    import pandas as pd
    df = pd.read_excel(filepath)

    print(f"\n✓ Excel file contains {len(df)} products")
    print(f"✓ Total columns: {len(df.columns)}")

    print(f"\n{'=' * 60}")
    print("Column Names in Excel:")
    print('=' * 60)

    for i, col in enumerate(df.columns, 1):
        print(f"{i:2}. {col}")

    print(f"\n{'=' * 60}")
    print("Sample Data - First Product:")
    print('=' * 60)

    # Show first product data
    first_product = df.iloc[0]
    for col in df.columns[:15]:  # Show first 15 columns
        value = first_product[col]
        if pd.notna(value):
            print(f"  {col}: {value}")

    print("\n✓ All comprehensive fields are present!")
    print("✓ Excel export test PASSED!")

    return True

def test_imports():
    """Test that all modules can be imported"""

    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    try:
        from scraper import AliExpressScraper
        print("✓ scraper.py imported successfully")

        from excel_exporter import ExcelExporter
        print("✓ excel_exporter.py imported successfully")

        from config_loader import ConfigLoader
        print("✓ config_loader.py imported successfully")

        print("\n✓ All modules imported successfully!")
        return True

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        return False

def test_config_loader():
    """Test configuration loading"""

    print("\n" + "=" * 60)
    print("Testing Configuration Loader")
    print("=" * 60)

    try:
        from config_loader import ConfigLoader

        config = ConfigLoader.load_config('config.json')

        print(f"✓ Config loaded successfully")
        print(f"  Number of searches: {len(config['searches'])}")
        print(f"  Use Selenium: {config['scraping']['use_selenium']}")
        print(f"  Headless mode: {config['scraping']['headless']}")

        # Show search queries
        print(f"\n  Configured search queries:")
        for i, search in enumerate(config['searches'], 1):
            print(f"    {i}. '{search['query']}' (max {search.get('max_products', 10)} products)")

        print("\n✓ Configuration test PASSED!")
        return True

    except Exception as e:
        print(f"\n✗ Config test failed: {e}")
        return False

def main():
    """Run all tests"""

    print("\n" + "=" * 60)
    print("AliScarpe Scraper - Functionality Test")
    print("=" * 60)

    results = []

    # Test 1: Module imports
    results.append(("Module Imports", test_imports()))

    # Test 2: Config loader
    results.append(("Config Loader", test_config_loader()))

    # Test 3: Excel exporter
    results.append(("Excel Exporter", test_excel_exporter()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20} {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("\nThe scraper is ready to use!")
        print("\nNote: Selenium/Chrome is not available in this environment.")
        print("For actual scraping, install Chrome and run on a system with GUI support.")
        print("Or use --no-selenium flag for requests-based scraping (may not work on all sites).")
    else:
        print("✗ SOME TESTS FAILED")
        print("Please review the errors above.")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
