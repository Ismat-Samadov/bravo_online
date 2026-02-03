#!/usr/bin/env python3
"""
Supermarket Food Data Scraper
Uses captured API patterns to scrape product data programmatically.
"""

import json
import requests
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class SupermarketScraper:
    def __init__(self, config_file: str = "scraper_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.session = requests.Session()
        self.products = []

    def load_config(self) -> Dict:
        """Load scraper configuration from captured data"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            "base_url": "",
            "endpoints": {},
            "headers": {},
            "auth": {}
        }

    def save_config(self):
        """Save scraper configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def generate_config_from_captures(self, captured_file: str = "captured_requests.json"):
        """Generate scraper config from captured requests"""
        captures_path = Path(captured_file)

        if not captures_path.exists():
            print(f"❌ No captured data found: {captured_file}")
            return

        with open(captures_path, 'r') as f:
            captures = json.load(f)

        if not captures:
            print("⚠️  No captured requests found")
            return

        # Analyze captures to build config
        hosts = {}
        endpoints = {}

        for capture in captures:
            host = capture.get('host', '')
            path = capture.get('path', '')
            method = capture.get('method', 'GET')

            # Count host occurrences
            hosts[host] = hosts.get(host, 0) + 1

            # Store endpoint details
            endpoint_key = f"{method} {path}"
            if endpoint_key not in endpoints:
                endpoints[endpoint_key] = {
                    "method": method,
                    "path": path,
                    "url": capture.get('url', ''),
                    "headers": capture.get('request_headers', {}),
                    "sample_response": capture.get('response_body', {}),
                    "count": 0
                }
            endpoints[endpoint_key]['count'] += 1

        # Pick most common host as base
        if hosts:
            most_common_host = max(hosts.items(), key=lambda x: x[1])[0]
            self.config['base_url'] = f"https://{most_common_host}"

        # Store endpoints sorted by frequency
        self.config['endpoints'] = dict(
            sorted(endpoints.items(), key=lambda x: -x[1]['count'])
        )

        # Extract common headers
        if captures:
            sample_headers = captures[0].get('request_headers', {})
            self.config['headers'] = {
                k: v for k, v in sample_headers.items()
                if k.lower() in ['user-agent', 'accept', 'accept-language', 'authorization']
            }

        self.save_config()
        print(f"✓ Generated config with {len(endpoints)} endpoints")
        print(f"✓ Base URL: {self.config['base_url']}")

    def fetch_products(self, endpoint_name: str, params: Optional[Dict] = None) -> List[Dict]:
        """Fetch products from a specific endpoint"""
        if endpoint_name not in self.config['endpoints']:
            print(f"❌ Endpoint not found: {endpoint_name}")
            return []

        endpoint = self.config['endpoints'][endpoint_name]
        method = endpoint['method']
        url = endpoint['url'] if endpoint['url'] else f"{self.config['base_url']}{endpoint['path']}"
        headers = self.config.get('headers', {})

        try:
            print(f"🔄 Fetching: {method} {url}")

            if method == 'GET':
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, headers=headers, json=params, timeout=30)
            else:
                print(f"⚠️  Unsupported method: {method}")
                return []

            response.raise_for_status()

            data = response.json()
            print(f"✓ Status: {response.status_code}")

            return self._extract_products_from_response(data)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching data: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return []

    def _extract_products_from_response(self, data: any) -> List[Dict]:
        """Extract product data from API response"""
        products = []

        # Common patterns for product data in responses
        if isinstance(data, dict):
            # Check for common list keys
            for key in ['products', 'items', 'data', 'results', 'content']:
                if key in data and isinstance(data[key], list):
                    products.extend(self._process_product_list(data[key]))

            # If no list found, might be a single product
            if not products and ('name' in data or 'title' in data or 'price' in data):
                products.append(self._normalize_product(data))

        elif isinstance(data, list):
            products.extend(self._process_product_list(data))

        return products

    def _process_product_list(self, items: List) -> List[Dict]:
        """Process a list of potential product items"""
        products = []
        for item in items:
            if isinstance(item, dict):
                normalized = self._normalize_product(item)
                if normalized:
                    products.append(normalized)
        return products

    def _normalize_product(self, product: Dict) -> Optional[Dict]:
        """Normalize product data to a standard format"""
        # Skip if doesn't look like a product
        if not any(key in product for key in ['name', 'title', 'product_name', 'item_name']):
            return None

        normalized = {
            'id': product.get('id') or product.get('product_id') or product.get('item_id'),
            'name': (
                product.get('name') or
                product.get('title') or
                product.get('product_name') or
                product.get('item_name')
            ),
            'price': (
                product.get('price') or
                product.get('cost') or
                product.get('amount') or
                product.get('price_value')
            ),
            'currency': product.get('currency') or product.get('price_currency'),
            'description': product.get('description') or product.get('desc'),
            'category': product.get('category') or product.get('category_name'),
            'brand': product.get('brand') or product.get('manufacturer'),
            'image': product.get('image') or product.get('image_url') or product.get('thumbnail'),
            'unit': product.get('unit') or product.get('unit_type'),
            'quantity': product.get('quantity') or product.get('stock'),
            'raw_data': product  # Keep original data
        }

        return normalized

    def scrape_all_endpoints(self):
        """Scrape all available endpoints"""
        all_products = []

        print(f"\n🚀 Starting scrape of {len(self.config['endpoints'])} endpoints...")

        for i, (name, endpoint) in enumerate(self.config['endpoints'].items(), 1):
            print(f"\n[{i}/{len(self.config['endpoints'])}] {name}")
            products = self.fetch_products(name)
            all_products.extend(products)
            print(f"   Found {len(products)} products")

        self.products = all_products
        return all_products

    def save_products(self, filename: str = "scraped_products.json"):
        """Save scraped products to file"""
        output = {
            'scraped_at': datetime.now().isoformat(),
            'total_products': len(self.products),
            'products': self.products
        }

        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved {len(self.products)} products to {output_path}")

    def export_csv(self, filename: str = "products.csv"):
        """Export products to CSV"""
        import csv

        if not self.products:
            print("⚠️  No products to export")
            return

        # Get all unique keys
        keys = set()
        for product in self.products:
            keys.update(k for k in product.keys() if k != 'raw_data')

        keys = sorted(keys)

        output_path = Path(filename)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for product in self.products:
                row = {k: product.get(k) for k in keys}
                writer.writerow(row)

        print(f"💾 Exported {len(self.products)} products to {output_path}")


def main():
    scraper = SupermarketScraper()

    # Check if config exists
    if not scraper.config.get('base_url'):
        print("⚠️  No scraper config found. Generating from captured data...")
        scraper.generate_config_from_captures()

        if not scraper.config.get('base_url'):
            print("\n❌ Could not generate config. Please:")
            print("1. Run: mitmdump -s mitm_capture.py")
            print("2. Use the supermarket app to browse products")
            print("3. Run this script again")
            return

    # Display available endpoints
    print("\n📍 Available Endpoints:")
    for i, (name, endpoint) in enumerate(scraper.config['endpoints'].items(), 1):
        print(f"{i}. {name} ({endpoint['count']} captured)")

    # Scrape all endpoints
    products = scraper.scrape_all_endpoints()

    if products:
        # Display sample
        print(f"\n🛒 Sample Products (showing 3 of {len(products)}):")
        for i, product in enumerate(products[:3], 1):
            print(f"\n{i}. {product.get('name', 'Unknown')}")
            print(f"   Price: {product.get('price', 'N/A')} {product.get('currency', '')}")
            print(f"   Category: {product.get('category', 'N/A')}")

        # Save results
        scraper.save_products()
        scraper.export_csv()
    else:
        print("\n⚠️  No products found. You may need to:")
        print("1. Capture more requests from the app")
        print("2. Adjust the extraction logic in _extract_products_from_response()")


if __name__ == "__main__":
    main()
