#!/usr/bin/env python3
"""
Analyze captured supermarket API data and extract food information.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


class DataAnalyzer:
    def __init__(self, data_file: str = "captured_requests.json"):
        self.data_file = Path(data_file)
        self.data = []
        self.load_data()

    def load_data(self):
        """Load captured data from JSON file"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✓ Loaded {len(self.data)} captured requests")
        else:
            print(f"❌ No data file found: {self.data_file}")

    def analyze_endpoints(self):
        """Analyze all unique endpoints"""
        endpoints = defaultdict(int)
        for item in self.data:
            path = item.get('path', '')
            method = item.get('method', '')
            key = f"{method} {path}"
            endpoints[key] += 1

        print("\n📍 API Endpoints Found:")
        print("-" * 80)
        for endpoint, count in sorted(endpoints.items(), key=lambda x: -x[1]):
            print(f"{endpoint:60} ({count} calls)")

    def find_product_data(self) -> List[Dict]:
        """Extract product/food data from responses"""
        products = []

        for item in self.data:
            response = item.get('response_body', {})
            url = item.get('url', '')

            # Try to find product data in the response
            extracted = self._extract_products(response)
            if extracted:
                for product in extracted:
                    product['source_url'] = url
                    product['timestamp'] = item.get('timestamp')
                    products.append(product)

        return products

    def _extract_products(self, data: Any, depth=0) -> List[Dict]:
        """Recursively search for product data in JSON"""
        products = []
        max_depth = 10

        if depth > max_depth:
            return products

        # Look for common product fields
        product_keys = {'name', 'title', 'product', 'item'}
        price_keys = {'price', 'cost', 'amount', 'value'}

        if isinstance(data, dict):
            # Check if this dict looks like a product
            has_name = any(key in data for key in product_keys)
            has_price = any(key in data for key in price_keys)

            if has_name or has_price:
                product = {}

                # Extract relevant fields
                for key, value in data.items():
                    if not isinstance(value, (dict, list)) or key in product_keys:
                        product[key] = value

                if product:
                    products.append(product)

            # Recursively search nested dicts
            for value in data.values():
                products.extend(self._extract_products(value, depth + 1))

        elif isinstance(data, list):
            # Search each item in list
            for item in data:
                products.extend(self._extract_products(item, depth + 1))

        return products

    def save_products(self, products: List[Dict], output_file: str = "products.json"):
        """Save extracted products to file"""
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved {len(products)} products to {output_path}")

    def display_sample_products(self, products: List[Dict], limit: int = 5):
        """Display sample products"""
        print(f"\n🛒 Sample Products (showing {min(limit, len(products))} of {len(products)}):")
        print("-" * 80)

        for i, product in enumerate(products[:limit], 1):
            print(f"\n{i}. Product:")
            for key, value in product.items():
                if key not in ['source_url', 'timestamp']:
                    print(f"   {key}: {value}")

    def analyze_response_structure(self):
        """Analyze the structure of API responses"""
        print("\n🔍 Response Structure Analysis:")
        print("-" * 80)

        for i, item in enumerate(self.data[:3], 1):  # Show first 3
            print(f"\n{i}. {item.get('method')} {item.get('path')}")
            response = item.get('response_body', {})
            self._print_structure(response, indent=2)

    def _print_structure(self, data: Any, indent: int = 0, max_depth: int = 3):
        """Print the structure of nested data"""
        if indent > max_depth * 2:
            return

        prefix = " " * indent

        if isinstance(data, dict):
            for key, value in list(data.items())[:5]:  # Show first 5 keys
                if isinstance(value, (dict, list)):
                    print(f"{prefix}{key}: {type(value).__name__}")
                    self._print_structure(value, indent + 2, max_depth)
                else:
                    print(f"{prefix}{key}: {type(value).__name__} = {str(value)[:50]}")

            if len(data) > 5:
                print(f"{prefix}... ({len(data) - 5} more keys)")

        elif isinstance(data, list):
            print(f"{prefix}Array length: {len(data)}")
            if data and len(data) > 0:
                print(f"{prefix}First item:")
                self._print_structure(data[0], indent + 2, max_depth)


def main():
    analyzer = DataAnalyzer()

    if not analyzer.data:
        print("\n⚠️  No data captured yet. Please:")
        print("1. Run: mitmdump -s mitm_capture.py")
        print("2. Configure your iOS device to use the proxy")
        print("3. Open the supermarket app and browse products")
        return

    # Analyze endpoints
    analyzer.analyze_endpoints()

    # Analyze response structures
    analyzer.analyze_response_structure()

    # Extract and save products
    products = analyzer.find_product_data()
    if products:
        analyzer.display_sample_products(products)
        analyzer.save_products(products)
    else:
        print("\n⚠️  No products found. The response structure might be different.")
        print("Check the response structure above and adjust the extraction logic.")


if __name__ == "__main__":
    main()
