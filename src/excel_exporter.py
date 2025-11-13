"""
Excel Exporter for AliExpress Product Data
Exports scraped product information to Excel files with formatting
"""

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from typing import List, Dict
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Export product data to Excel files with formatting
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize the Excel exporter

        Args:
            output_dir: Directory to save Excel files
        """
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")

    def export_to_excel(self, products: List[Dict], filename: str = None,
                       search_query: str = "", auto_format: bool = True) -> str:
        """
        Export products to Excel file

        Args:
            products: List of product dictionaries
            filename: Custom filename (optional)
            search_query: The search query used (for default filename)
            auto_format: Whether to apply automatic formatting

        Returns:
            Path to the created Excel file
        """
        if not products:
            logger.warning("No products to export")
            return None

        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c for c in search_query if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_query = safe_query.replace(' ', '_')[:30]  # Limit length
            filename = f"aliexpress_{safe_query}_{timestamp}.xlsx"

        filepath = os.path.join(self.output_dir, filename)

        # Convert to DataFrame
        df = self._create_dataframe(products)

        # Export to Excel
        logger.info(f"Exporting {len(products)} products to {filepath}")
        df.to_excel(filepath, index=False, sheet_name='Products')

        # Apply formatting if requested
        if auto_format:
            self._apply_formatting(filepath)

        logger.info(f"Export completed: {filepath}")
        return filepath

    def _create_dataframe(self, products: List[Dict]) -> pd.DataFrame:
        """
        Create a pandas DataFrame from product data

        Args:
            products: List of product dictionaries

        Returns:
            Formatted DataFrame
        """
        # Define column order and names - Comprehensive mapping for all fields
        column_mapping = {
            # Basic Info
            'product_id': 'Product ID',
            'title': 'Product Title',
            'url': 'Product URL',
            'affiliate_url': 'Affiliate URL',
            'image_url': 'Image URL',

            # Pricing
            'price': 'Current Price (USD)',
            'original_price': 'Original Price (USD)',
            'discount_percentage': 'Discount %',
            'discount_badge': 'Discount Badge',
            'price_min': 'Price Min (Range)',
            'price_max': 'Price Max (Range)',

            # Ratings & Reviews
            'rating': 'Rating',
            'review_count': 'Number of Reviews',

            # Sales & Popularity
            'orders': 'Orders/Sales Text',
            'orders_count': 'Orders Count',
            'recent_sold_24h': 'Sold in 24h',
            'people_viewing': 'People Viewing',

            # Shipping
            'shipping': 'Shipping Info',
            'free_shipping': 'Free Shipping',
            'delivery_time': 'Delivery Time',
            'ships_from': 'Ships From',

            # Store Info
            'store_name': 'Store Name',
            'store_rating': 'Store Rating',

            # Product Features
            'has_variations': 'Has Variations',
            'variation_count': 'Number of Variations',
            'badges': 'Badges',
            'stock_status': 'Stock Status',

            # Additional Info
            'is_sponsored': 'Is Sponsored',
            'coupon_available': 'Coupon Available',
            'plus_discount': 'Plus Member Discount',
            'return_days': 'Return Policy (Days)',

            # Detailed (from product page)
            'description': 'Description',
            'specifications': 'Specifications'
        }

        # Create DataFrame
        df = pd.DataFrame(products)

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Reorder columns (only include columns that exist)
        desired_order = list(column_mapping.values())
        existing_columns = [col for col in desired_order if col in df.columns]
        df = df[existing_columns]

        # Clean price columns (remove currency symbols, convert to float)
        price_columns = ['Current Price (USD)', 'Original Price (USD)', 'Price Min (Range)', 'Price Max (Range)']
        for col in price_columns:
            if col in df.columns:
                df[col] = df[col].apply(self._clean_price)

        # Clean rating column
        if 'Rating' in df.columns:
            df['Rating'] = df['Rating'].apply(self._clean_rating)

        # Add export timestamp
        df.insert(0, 'Export Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Add row numbers
        df.insert(0, '#', range(1, len(df) + 1))

        return df

    def _clean_price(self, price_str) -> float:
        """Clean and convert price string to float"""
        if pd.isna(price_str):
            return None
        try:
            # Remove currency symbols and convert to float
            import re
            price_cleaned = re.sub(r'[^\d.]', '', str(price_str))
            return float(price_cleaned) if price_cleaned else None
        except:
            return None

    def _clean_rating(self, rating_str) -> float:
        """Clean and convert rating string to float"""
        if pd.isna(rating_str):
            return None
        try:
            import re
            rating_cleaned = re.search(r'[\d.]+', str(rating_str))
            return float(rating_cleaned.group()) if rating_cleaned else None
        except:
            return None

    def _apply_formatting(self, filepath: str):
        """
        Apply formatting to the Excel file

        Args:
            filepath: Path to the Excel file
        """
        try:
            # Load workbook
            wb = load_workbook(filepath)
            ws = wb.active

            # Header formatting
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Apply header formatting
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment

            # Border style
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Apply borders and alignment to all cells
            for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
                for cell in row:
                    cell.border = thin_border
                    if cell.row > 1:  # Data rows
                        cell.alignment = Alignment(vertical="top", wrap_text=True)

            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)

                for cell in column:
                    try:
                        if cell.value:
                            # Special handling for URL columns
                            if 'URL' in str(ws.cell(1, cell.column).value):
                                max_length = 15  # Fixed width for URLs
                                break
                            else:
                                cell_length = len(str(cell.value))
                                if cell_length > max_length:
                                    max_length = cell_length
                    except:
                        pass

                # Set column width (with limits)
                adjusted_width = min(max_length + 2, 50)
                adjusted_width = max(adjusted_width, 10)
                ws.column_dimensions[column_letter].width = adjusted_width

            # Set row height for header
            ws.row_dimensions[1].height = 30

            # Freeze header row
            ws.freeze_panes = 'A2'

            # Save formatted workbook
            wb.save(filepath)
            logger.info("Formatting applied successfully")

        except Exception as e:
            logger.error(f"Error applying formatting: {e}")

    def export_multiple_queries(self, results_dict: Dict[str, List[Dict]],
                               filename: str = None) -> str:
        """
        Export results from multiple search queries to a single Excel file with multiple sheets

        Args:
            results_dict: Dictionary where keys are search queries and values are product lists
            filename: Custom filename (optional)

        Returns:
            Path to the created Excel file
        """
        if not results_dict:
            logger.warning("No results to export")
            return None

        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aliexpress_multiple_queries_{timestamp}.xlsx"

        filepath = os.path.join(self.output_dir, filename)

        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for query, products in results_dict.items():
                if products:
                    # Create DataFrame
                    df = self._create_dataframe(products)

                    # Create safe sheet name
                    sheet_name = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()
                    sheet_name = sheet_name.replace(' ', '_')[:31]  # Excel sheet name limit

                    # Write to sheet
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
                    logger.info(f"Added sheet '{sheet_name}' with {len(products)} products")

        # Apply formatting to all sheets
        self._apply_formatting_multiple_sheets(filepath)

        logger.info(f"Multi-sheet export completed: {filepath}")
        return filepath

    def _apply_formatting_multiple_sheets(self, filepath: str):
        """Apply formatting to all sheets in a workbook"""
        try:
            wb = load_workbook(filepath)

            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]

                # Apply same formatting as single sheet
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_font = Font(bold=True, color="FFFFFF", size=11)
                header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment

                ws.freeze_panes = 'A2'

            wb.save(filepath)
            logger.info("Multi-sheet formatting applied successfully")

        except Exception as e:
            logger.error(f"Error applying multi-sheet formatting: {e}")
