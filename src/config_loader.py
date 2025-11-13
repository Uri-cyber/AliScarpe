"""
Configuration Loader
Loads and validates configuration from JSON files
"""

import json
import os
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load and validate configuration for the scraper
    """

    DEFAULT_CONFIG = {
        "scraping": {
            "use_selenium": True,
            "headless": True,
            "timeout": 30
        },
        "searches": [
            {
                "query": "laptop",
                "max_products": 10,
                "min_price": None,
                "max_price": None,
                "sort_by": "default"
            }
        ],
        "export": {
            "output_dir": "output",
            "auto_format": True,
            "separate_files": False
        }
    }

    @staticmethod
    def load_config(config_path: str = "config.json") -> Dict:
        """
        Load configuration from JSON file

        Args:
            config_path: Path to the configuration file

        Returns:
            Configuration dictionary
        """
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found: {config_path}")
            logger.info("Using default configuration")
            return ConfigLoader.DEFAULT_CONFIG

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate configuration
            ConfigLoader._validate_config(config)

            logger.info(f"Configuration loaded from: {config_path}")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.info("Using default configuration")
            return ConfigLoader.DEFAULT_CONFIG

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return ConfigLoader.DEFAULT_CONFIG

    @staticmethod
    def _validate_config(config: Dict):
        """
        Validate configuration structure

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required sections
        required_sections = ['scraping', 'searches', 'export']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")

        # Validate searches
        if not isinstance(config['searches'], list) or not config['searches']:
            raise ValueError("'searches' must be a non-empty list")

        for i, search in enumerate(config['searches']):
            if 'query' not in search:
                raise ValueError(f"Search #{i+1} missing required 'query' field")

            if 'max_products' not in search:
                search['max_products'] = 10  # Default value

            # Validate sort_by values
            valid_sort_options = ['default', 'price_asc', 'price_desc', 'orders']
            if 'sort_by' in search and search['sort_by'] not in valid_sort_options:
                logger.warning(f"Invalid sort_by value in search #{i+1}. Using 'default'")
                search['sort_by'] = 'default'

        logger.info("Configuration validated successfully")

    @staticmethod
    def save_config(config: Dict, config_path: str = "config.json"):
        """
        Save configuration to JSON file

        Args:
            config: Configuration dictionary
            config_path: Path to save the configuration file
        """
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to: {config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    @staticmethod
    def create_example_config(config_path: str = "config_example.json"):
        """
        Create an example configuration file

        Args:
            config_path: Path to save the example configuration
        """
        example_config = {
            "scraping": {
                "use_selenium": True,
                "headless": True,
                "timeout": 30
            },
            "searches": [
                {
                    "query": "smartphone",
                    "max_products": 20,
                    "min_price": 100,
                    "max_price": 500,
                    "sort_by": "orders"
                },
                {
                    "query": "laptop gaming",
                    "max_products": 15,
                    "min_price": None,
                    "max_price": None,
                    "sort_by": "price_desc"
                },
                {
                    "query": "bluetooth speaker",
                    "max_products": 10,
                    "min_price": 20,
                    "max_price": 100,
                    "sort_by": "default"
                }
            ],
            "export": {
                "output_dir": "output",
                "auto_format": True,
                "separate_files": False
            }
        }

        ConfigLoader.save_config(example_config, config_path)
        logger.info(f"Example configuration created: {config_path}")
