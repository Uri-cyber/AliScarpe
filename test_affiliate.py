#!/usr/bin/env python3
"""
Test script for affiliate link conversion functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from affiliate_converter import AffiliateConverter, AffiliatePresets, create_affiliate_converter_from_config
from excel_exporter import ExcelExporter
import json

def test_affiliate_converter_basic():
    """Test basic affiliate conversion"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Affiliate URL Conversion")
    print("=" * 60)

    # Test URL
    original_url = "https://www.aliexpress.com/item/1005001234567890.html"

    # Test with disabled converter
    converter_disabled = AffiliateConverter({'enabled': False})
    result = converter_disabled.convert_url(original_url)

    assert result == original_url, "Disabled converter should return original URL"
    print("✓ Disabled converter returns original URL")

    # Test with enabled converter and custom params
    config = {
        'enabled': True,
        'parameters': {
            'aff_trace_key': 'test_affiliate_id',
            'terminal_id': 'test_terminal'
        }
    }
    converter_enabled = AffiliateConverter(config)
    affiliate_url = converter_enabled.convert_url(original_url)

    # Check that parameters were added
    assert 'aff_trace_key=test_affiliate_id' in affiliate_url
    assert 'terminal_id=test_terminal' in affiliate_url
    assert original_url.split('?')[0] in affiliate_url  # Base URL preserved

    print(f"✓ Affiliate conversion works")
    print(f"  Original: {original_url}")
    print(f"  Affiliate: {affiliate_url}")

    return True


def test_affiliate_presets():
    """Test different affiliate presets"""
    print("\n" + "=" * 60)
    print("TEST 2: Affiliate Presets")
    print("=" * 60)

    test_url = "https://www.aliexpress.com/item/1005001234567890.html"

    # Test Standard AliExpress preset
    standard_config = AffiliatePresets.get_preset('aliexpress_standard', 'my_affiliate_id')
    converter_standard = AffiliateConverter(standard_config)
    standard_url = converter_standard.convert_url(test_url)

    assert 'aff_trace_key=my_affiliate_id' in standard_url
    assert 'aff_platform=portals-tool' in standard_url
    assert 'sk=my_affiliate_id' in standard_url
    print("✓ Standard AliExpress preset works")
    print(f"  Generated: {standard_url}")

    # Test Admitad preset
    admitad_config = AffiliatePresets.get_preset('admitad', 'admitad_uid_123')
    converter_admitad = AffiliateConverter(admitad_config)
    admitad_url = converter_admitad.convert_url(test_url)

    assert 'admitad_uid=admitad_uid_123' in admitad_url
    print("✓ Admitad preset works")
    print(f"  Generated: {admitad_url}")

    # Test Custom preset
    custom_config = AffiliatePresets.get_preset('custom', '', parameters={'custom_param': 'custom_value'})
    converter_custom = AffiliateConverter(custom_config)
    custom_url = converter_custom.convert_url(test_url)

    assert 'custom_param=custom_value' in custom_url
    print("✓ Custom preset works")
    print(f"  Generated: {custom_url}")

    return True


def test_batch_conversion():
    """Test converting multiple products"""
    print("\n" + "=" * 60)
    print("TEST 3: Batch Product Conversion")
    print("=" * 60)

    # Mock products
    products = [
        {
            'title': 'Product 1',
            'url': 'https://www.aliexpress.com/item/1001.html',
            'price': '99.99'
        },
        {
            'title': 'Product 2',
            'url': 'https://www.aliexpress.com/item/1002.html',
            'price': '149.99'
        },
        {
            'title': 'Product 3',
            'url': 'https://www.aliexpress.com/item/1003.html',
            'price': '199.99'
        }
    ]

    # Convert with affiliate
    config = {
        'enabled': True,
        'parameters': {
            'aff_trace_key': 'batch_test_id',
            'campaign': 'test_campaign'
        }
    }
    converter = AffiliateConverter(config)
    converted_products = converter.add_affiliate_to_products(products)

    # Verify all products have affiliate URLs
    for i, product in enumerate(converted_products, 1):
        assert 'affiliate_url' in product, f"Product {i} missing affiliate_url"
        assert 'aff_trace_key=batch_test_id' in product['affiliate_url']
        assert 'campaign=test_campaign' in product['affiliate_url']
        print(f"✓ Product {i} converted successfully")
        print(f"  Original URL: {product['url']}")
        print(f"  Affiliate URL: {product['affiliate_url']}")

    return True


def test_config_integration():
    """Test creating converter from config file"""
    print("\n" + "=" * 60)
    print("TEST 4: Config File Integration")
    print("=" * 60)

    # Test config structure (like in config.json)
    test_configs = [
        {
            'name': 'Standard AliExpress',
            'config': {
                'affiliate': {
                    'enabled': True,
                    'preset': 'aliexpress_standard',
                    'affiliate_id': 'test_id_123',
                    'parameters': {}
                }
            }
        },
        {
            'name': 'Custom Parameters',
            'config': {
                'affiliate': {
                    'enabled': True,
                    'preset': 'custom',
                    'parameters': {
                        'custom_key': 'custom_value',
                        'tracking_code': 'xyz789'
                    }
                }
            }
        },
        {
            'name': 'Disabled',
            'config': {
                'affiliate': {
                    'enabled': False,
                    'preset': 'aliexpress_standard',
                    'affiliate_id': '',
                    'parameters': {}
                }
            }
        }
    ]

    test_url = "https://www.aliexpress.com/item/9999999999.html"

    for test in test_configs:
        converter = create_affiliate_converter_from_config(test['config'])
        result_url = converter.convert_url(test_url)

        if test['config']['affiliate']['enabled']:
            assert result_url != test_url, f"{test['name']}: Should modify URL when enabled"
            print(f"✓ {test['name']}: URL converted")
        else:
            assert result_url == test_url, f"{test['name']}: Should not modify URL when disabled"
            print(f"✓ {test['name']}: URL unchanged (disabled)")

    return True


def test_excel_export_with_affiliate():
    """Test Excel export includes affiliate URLs"""
    print("\n" + "=" * 60)
    print("TEST 5: Excel Export with Affiliate URLs")
    print("=" * 60)

    # Mock products with affiliate URLs
    products = [
        {
            'product_id': '1001',
            'title': 'Test Product 1',
            'url': 'https://www.aliexpress.com/item/1001.html',
            'affiliate_url': 'https://www.aliexpress.com/item/1001.html?aff_trace_key=test123',
            'price': '99.99',
            'rating': '4.5',
            'orders': '1000+',
            'store_name': 'Test Store'
        },
        {
            'product_id': '1002',
            'title': 'Test Product 2',
            'url': 'https://www.aliexpress.com/item/1002.html',
            'affiliate_url': 'https://www.aliexpress.com/item/1002.html?aff_trace_key=test123',
            'price': '149.99',
            'rating': '4.8',
            'orders': '5000+',
            'store_name': 'Test Store 2'
        }
    ]

    # Export to Excel
    exporter = ExcelExporter(output_dir='test_output')
    filepath = exporter.export_to_excel(
        products=products,
        filename='test_affiliate_export.xlsx',
        search_query='test',
        auto_format=True
    )

    print(f"✓ Excel file created: {filepath}")

    # Read back and verify
    import pandas as pd
    df = pd.read_excel(filepath)

    # Check for affiliate URL column
    assert 'Affiliate URL' in df.columns, "Affiliate URL column missing"
    print("✓ 'Affiliate URL' column present")

    # Check both URLs are different columns
    assert 'Product URL' in df.columns, "Product URL column missing"
    print("✓ 'Product URL' column present")

    # Verify affiliate URLs are populated
    for idx, row in df.iterrows():
        assert pd.notna(row['Affiliate URL']), f"Row {idx} missing affiliate URL"
        assert 'aff_trace_key=test123' in str(row['Affiliate URL'])

    print(f"✓ All {len(df)} products have affiliate URLs")

    # Show column order
    print("\n  Column order:")
    for i, col in enumerate(df.columns[:10], 1):  # Show first 10
        print(f"    {i}. {col}")

    return True


def test_url_with_existing_params():
    """Test converting URLs that already have parameters"""
    print("\n" + "=" * 60)
    print("TEST 6: URL with Existing Parameters")
    print("=" * 60)

    # URL with existing parameters
    original_url = "https://www.aliexpress.com/item/1234.html?something=value&other=param"

    config = {
        'enabled': True,
        'parameters': {
            'aff_trace_key': 'new_affiliate_id',
            'campaign': 'summer_sale'
        }
    }
    converter = AffiliateConverter(config)
    result_url = converter.convert_url(original_url)

    # Should preserve existing params and add new ones
    assert 'something=value' in result_url
    assert 'other=param' in result_url
    assert 'aff_trace_key=new_affiliate_id' in result_url
    assert 'campaign=summer_sale' in result_url

    print("✓ Existing parameters preserved")
    print("✓ New affiliate parameters added")
    print(f"  Original: {original_url}")
    print(f"  Result: {result_url}")

    return True


def main():
    """Run all affiliate tests"""
    print("\n" + "=" * 60)
    print("AFFILIATE LINK CONVERSION - TEST SUITE")
    print("=" * 60)

    results = []

    try:
        results.append(("Basic Conversion", test_affiliate_converter_basic()))
        results.append(("Presets", test_affiliate_presets()))
        results.append(("Batch Conversion", test_batch_conversion()))
        results.append(("Config Integration", test_config_integration()))
        results.append(("Excel Export", test_excel_export_with_affiliate()))
        results.append(("Existing Parameters", test_url_with_existing_params()))
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:25} {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL AFFILIATE TESTS PASSED!")
        print("\nAffiliate link conversion is working perfectly!")
        print("\nTo use in production:")
        print("1. Edit config.json")
        print("2. Set 'enabled': true")
        print("3. Add your affiliate_id")
        print("4. Run the scraper normally")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
