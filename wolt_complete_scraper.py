#!/usr/bin/env python3
"""
Complete Wolt Bravo Scraper
Uses discovered POST endpoint to scrape all products efficiently
"""

import json
import requests
import time
from typing import Dict, List
from pathlib import Path
from datetime import datetime


class WoltCompleteScraper:
    def __init__(self):
        self.base_url = "https://consumer-api.wolt.com"
        self.venue_slug = "bravo-storefront"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })

        self.all_categories = []
        self.all_products = []

    def get_categories(self) -> List[Dict]:
        """Fetch all categories"""
        url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment"

        print("🔄 Fetching categories...")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            categories = self._flatten_categories(data.get('categories', []))
            self.all_categories = categories

            print(f"✓ Found {len(categories)} total categories")
            return categories

        except Exception as e:
            print(f"❌ Error fetching categories: {e}")
            return []

    def _flatten_categories(self, categories: List[Dict], parent_path: str = "", level: int = 0) -> List[Dict]:
        """Recursively flatten category tree"""
        result = []

        for cat in categories:
            cat_info = {
                'id': cat.get('id'),
                'name': cat.get('name'),
                'slug': cat.get('slug'),
                'description': cat.get('description', ''),
                'path': f"{parent_path}/{cat.get('name')}" if parent_path else cat.get('name'),
                'level': level,
                'parent_path': parent_path,
                'image_url': cat.get('images', [{}])[0].get('url') if cat.get('images') else None
            }

            result.append(cat_info)

            # Process subcategories
            if cat.get('subcategories'):
                result.extend(self._flatten_categories(
                    cat['subcategories'],
                    cat_info['path'],
                    level + 1
                ))

        return result

    def get_items_batch(self, item_ids: List[str], language: str = 'en') -> List[Dict]:
        """Fetch items in batch using POST endpoint"""
        if not item_ids:
            return []

        url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment/items"

        payload = {
            "item_ids": item_ids,
            "language": language
        }

        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            items = data.get('items', [])
            return items

        except Exception as e:
            print(f"  ❌ Error fetching items batch: {e}")
            return []

    def search_items(self, query: str = "", limit: int = 500, language: str = 'en') -> List[Dict]:
        """Search for items - use empty query to get all items"""
        url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment/items/search"

        params = {'language': language}

        payload = {
            "search_phrase": query,
            "limit": limit
        }

        try:
            response = self.session.post(url, json=payload, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            items = data.get('items', [])
            return items

        except Exception as e:
            print(f"  ❌ Error searching items: {e}")
            return []

    def scrape_all_products(self) -> List[Dict]:
        """Scrape all products using search endpoint"""
        print("\n🔄 Scraping all products...")

        all_products = []
        product_ids = set()

        # Strategy 1: Search with empty query to get batches
        print("  Method 1: Search endpoint (empty query)...")
        batch_num = 0

        while True:
            batch_num += 1
            print(f"    Batch {batch_num}...", end=' ')

            items = self.search_items(query="", limit=500)

            if not items:
                print("Done")
                break

            # Filter duplicates
            new_items = []
            for item in items:
                item_id = item.get('id')
                if item_id and item_id not in product_ids:
                    product_ids.add(item_id)
                    new_items.append(item)

            all_products.extend(new_items)
            print(f"{len(new_items)} new items ({len(all_products)} total)")

            # If we got less than requested, we're done
            if len(items) < 500:
                break

            # Avoid rate limiting
            time.sleep(0.5)

        # Strategy 2: Search by category if we have categories
        if self.all_categories:
            print("\n  Method 2: Category-based search...")

            # Get main categories
            main_categories = [c for c in self.all_categories if c['level'] == 0]

            for i, cat in enumerate(main_categories, 1):
                # Use category name as search query
                category_query = cat['name'].split()[0]  # First word of category

                print(f"    [{i}/{len(main_categories)}] {cat['name'][:40]:40}...", end=' ')

                items = self.search_items(query=category_query, limit=100)

                new_count = 0
                for item in items:
                    item_id = item.get('id')
                    if item_id and item_id not in product_ids:
                        product_ids.add(item_id)
                        all_products.append(item)
                        new_count += 1

                print(f"{new_count} new ({len(all_products)} total)")

                time.sleep(0.3)  # Rate limiting

        self.all_products = all_products
        print(f"\n✓ Total unique products scraped: {len(all_products)}")

        return all_products

    def save_all_data(self):
        """Save all scraped data"""
        timestamp = datetime.now()

        # Save categories
        if self.all_categories:
            cat_output = {
                'scraped_at': timestamp.isoformat(),
                'total': len(self.all_categories),
                'categories': self.all_categories
            }

            with open('bravo_categories_complete.json', 'w', encoding='utf-8') as f:
                json.dump(cat_output, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved {len(self.all_categories)} categories")

        # Save products
        if self.all_products:
            prod_output = {
                'scraped_at': timestamp.isoformat(),
                'total': len(self.all_products),
                'products': self.all_products
            }

            with open('bravo_products_raw.json', 'w', encoding='utf-8') as f:
                json.dump(prod_output, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved {len(self.all_products)} products")

            # Also save CSV
            self._save_products_csv()

    def _save_products_csv(self):
        """Save products to CSV"""
        import csv

        if not self.all_products:
            return

        with open('bravo_products_raw.csv', 'w', newline='', encoding='utf-8') as f:
            # Get all unique keys
            all_keys = set()
            for product in self.all_products:
                all_keys.update(product.keys())

            # Remove nested objects
            csv_keys = [k for k in all_keys if not isinstance(self.all_products[0].get(k), (dict, list))]

            writer = csv.DictWriter(f, fieldnames=sorted(csv_keys))
            writer.writeheader()

            for product in self.all_products:
                row = {k: product.get(k) for k in csv_keys}
                writer.writerow(row)

        print(f"💾 Exported to bravo_products_raw.csv")

    def display_sample(self, count: int = 5):
        """Display sample products"""
        if not self.all_products:
            return

        print(f"\n🛒 Sample Products (showing {min(count, len(self.all_products))} of {len(self.all_products)}):")
        print("-" * 80)

        for i, product in enumerate(self.all_products[:count], 1):
            name = product.get('name', 'Unknown')
            price = product.get('baseprice', 0)
            category = product.get('category_id', 'N/A')

            print(f"{i}. {name[:60]}")
            print(f"   Price: {price} AZN")
            print(f"   Category ID: {category}")
            print(f"   ID: {product.get('id')}")
            print()


def main():
    print("🚀 Wolt Bravo Complete Scraper")
    print("=" * 80)
    print("This will scrape ALL categories and products from Wolt Bravo")
    print()

    scraper = WoltCompleteScraper()

    # Step 1: Get categories
    scraper.get_categories()

    # Step 2: Get all products
    scraper.scrape_all_products()

    # Step 3: Display sample
    scraper.display_sample()

    # Step 4: Save everything
    scraper.save_all_data()

    print("\n" + "=" * 80)
    print("✓ Scraping complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python3 wolt_analyze.py")
    print("   → Get marketing insights and analysis")
    print()
    print("Output files:")
    print("  • bravo_categories_complete.json - All categories")
    print("  • bravo_products_raw.json - All products (raw)")
    print("  • bravo_products_raw.csv - Products in CSV format")


if __name__ == "__main__":
    main()
