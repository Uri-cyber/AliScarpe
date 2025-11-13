# AliScarpe - AliExpress Product Scraper

A powerful and configurable Python scraper for extracting product information from AliExpress and exporting it to beautifully formatted Excel files.

## Features

- **Flexible Scraping**: Scrape products by search query with customizable parameters
- **Price Filtering**: Set minimum and maximum price ranges
- **Sorting Options**: Sort by default, price (ascending/descending), or popularity (orders)
- **Excel Export**: Automatic export to Excel with professional formatting
- **Multiple Search Support**: Scrape multiple product categories in one run
- **Two Usage Modes**:
  - Configuration file for complex scraping jobs
  - Command-line arguments for quick searches
- **Selenium Support**: Uses Selenium for reliable scraping of JavaScript-rendered content
- **Headless Mode**: Run browser in background for faster scraping

## Installation

### Prerequisites

- Python 3.7 or higher
- Google Chrome browser (for Selenium)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd AliScarpe
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Method 1: Configuration File (Recommended for multiple searches)

1. Edit `config.json` to specify your scraping parameters:

```json
{
  "scraping": {
    "use_selenium": true,
    "headless": true,
    "timeout": 30
  },
  "searches": [
    {
      "query": "laptop",
      "max_products": 20,
      "min_price": null,
      "max_price": null,
      "sort_by": "default"
    },
    {
      "query": "wireless earbuds",
      "max_products": 15,
      "min_price": 10,
      "max_price": 100,
      "sort_by": "orders"
    }
  ],
  "export": {
    "output_dir": "output",
    "auto_format": true,
    "separate_files": false
  }
}
```

2. Run the scraper:
```bash
python main.py
```

Or specify a custom config file:
```bash
python main.py --config my_config.json
```

### Method 2: Command Line Arguments (Quick searches)

#### Single Search
```bash
python main.py --query "laptop" --max 20
```

#### Multiple Searches
```bash
python main.py --query "laptop" --query "phone" --max 15
```

#### With Price Filters
```bash
python main.py --query "headphones" --max 10 --min-price 20 --max-price 100
```

#### Sort by Popularity
```bash
python main.py --query "wireless mouse" --max 15 --sort orders
```

#### Custom Output Filename
```bash
python main.py --query "gaming keyboard" --max 10 --output my_products.xlsx
```

#### Show Browser Window (Non-headless)
```bash
python main.py --query "laptop" --max 10 --no-headless
```

## Command Line Options

```
usage: main.py [-h] [--config CONFIG] [--query QUERY] [--max MAX]
               [--min-price MIN_PRICE] [--max-price MAX_PRICE]
               [--sort {default,price_asc,price_desc,orders}]
               [--output OUTPUT] [--no-selenium] [--no-headless]

Options:
  -h, --help            Show help message
  --config, -c          Path to configuration file (default: config.json)
  --query, -q           Search query (can be used multiple times)
  --max, -m             Maximum number of products (default: 10)
  --min-price           Minimum price filter
  --max-price           Maximum price filter
  --sort                Sort order: default, price_asc, price_desc, orders
  --output, -o          Custom output filename
  --no-selenium         Use requests instead of Selenium (faster but may fail)
  --no-headless         Show browser window
```

## Configuration Parameters

### Scraping Settings
- `use_selenium`: Use Selenium WebDriver (recommended: true)
- `headless`: Run browser in background (recommended: true)
- `timeout`: Request timeout in seconds

### Search Parameters
- `query`: Search term (e.g., "laptop", "phone case")
- `max_products`: Number of products to scrape
- `min_price`: Minimum price filter (optional)
- `max_price`: Maximum price filter (optional)
- `sort_by`: Sorting option
  - `default`: AliExpress default sorting
  - `price_asc`: Price low to high
  - `price_desc`: Price high to low
  - `orders`: Most orders (popularity)

### Export Settings
- `output_dir`: Directory for Excel files
- `auto_format`: Apply formatting to Excel (recommended: true)
- `separate_files`: Create separate files for each search vs. one file with multiple sheets

## Output

### Excel File Contents

The scraper extracts the following information for each product:

- **#**: Row number
- **Export Date**: When the data was scraped
- **Product Title**: Full product name
- **Price (USD)**: Product price in USD
- **Rating**: Customer rating (if available)
- **Orders/Sales**: Number of orders/sales
- **Store Name**: Seller's store name
- **Shipping Info**: Shipping details
- **Product URL**: Direct link to product page
- **Image URL**: Product image link
- **Description**: Product description (if available)
- **Specifications**: Product specifications (if available)

### Output Files

Files are saved in the `output/` directory with automatic timestamped filenames:
- Single search: `aliexpress_laptop_20250113_143022.xlsx`
- Multiple searches: `aliexpress_multiple_queries_20250113_143022.xlsx`

## Project Structure

```
AliScarpe/
├── main.py                 # Main entry point
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── src/
│   ├── __init__.py
│   ├── scraper.py        # AliExpress scraper logic
│   ├── excel_exporter.py # Excel export functionality
│   └── config_loader.py  # Configuration loader
└── output/               # Excel output files (auto-created)
```

## Examples

### Example 1: Basic Search
```bash
python main.py --query "bluetooth speaker" --max 20
```

### Example 2: Price Range Search
```bash
python main.py --query "smartphone" --max 15 --min-price 200 --max-price 500 --sort price_asc
```

### Example 3: Multiple Categories
```bash
python main.py --query "laptop" --query "tablet" --query "monitor" --max 10
```

### Example 4: Using Config File
Create a `my_searches.json`:
```json
{
  "scraping": {
    "use_selenium": true,
    "headless": true,
    "timeout": 30
  },
  "searches": [
    {
      "query": "gaming laptop",
      "max_products": 25,
      "min_price": 500,
      "max_price": 2000,
      "sort_by": "orders"
    },
    {
      "query": "mechanical keyboard",
      "max_products": 20,
      "sort_by": "orders"
    }
  ],
  "export": {
    "output_dir": "my_output",
    "auto_format": true,
    "separate_files": false
  }
}
```

Run with:
```bash
python main.py --config my_searches.json
```

## Troubleshooting

### Chrome Driver Issues
If you encounter Chrome driver errors:
- Ensure Google Chrome is installed
- The `webdriver-manager` package will auto-download the correct driver
- Try running with `--no-headless` to see what's happening

### No Products Found
- AliExpress may be blocking automated requests
- Try reducing the number of products
- Check if the search query is valid on AliExpress website
- Some regions may have restricted access

### Selenium Timeout
- Increase the timeout in config: `"timeout": 60`
- Check your internet connection
- AliExpress servers may be slow or temporarily unavailable

## Legal Disclaimer

This tool is for educational and personal use only. When using this scraper:

- Respect AliExpress's Terms of Service
- Use reasonable rate limiting to avoid overwhelming servers
- Don't use scraped data for commercial purposes without permission
- Be aware that web scraping may violate terms of service

The authors are not responsible for misuse of this tool.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Happy Scraping!** 🚀
