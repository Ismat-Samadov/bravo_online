#!/usr/bin/env python3
"""
Complete Wolt Bravo Scraper - Fetches ALL products from ALL categories
Uses the correct category-based endpoint to ensure 100% coverage
"""

import json
import requests
import time
from typing import Dict, List, Set
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class WoltComprehensiveScraper:
    def __init__(self, language='az'):
        self.base_url = "https://consumer-api.wolt.com"
        self.venue_slug = "bravo-storefront"
        self.language = language
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
            'Accept-Language': f'{language},en;q=0.9'
        })

        self.all_categories = []
        self.all_products = {}  # Use dict to deduplicate by ID
        self.category_stats = {}

    def get_categories(self) -> List[Dict]:
        """Fetch all categories"""
        url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment"

        print("🔄 Fetching category structure...")

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
                'image_url': cat.get('images', [{}])[0].get('url') if cat.get('images') else None,
                'has_subcategories': len(cat.get('subcategories', [])) > 0
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

    def get_category_items(self, category_slug: str, category_name: str) -> List[Dict]:
        """Fetch all items for a specific category"""
        url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment/categories/slug/{category_slug}"

        params = {'language': self.language}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            items = data.get('items', [])

            # Annotate items with category info
            for item in items:
                item['_category_slug'] = category_slug
                item['_category_name'] = category_name

            return items

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Category might be empty or not exist
                return []
            print(f"  ❌ HTTP Error for {category_slug}: {e}")
            return []
        except Exception as e:
            print(f"  ❌ Error fetching {category_slug}: {e}")
            return []

    def scrape_all_products(self) -> Dict[str, Dict]:
        """Scrape ALL products by iterating through every category"""
        if not self.all_categories:
            print("❌ No categories loaded. Call get_categories() first")
            return {}

        print(f"\n🚀 Scraping products from {len(self.all_categories)} categories...")
        print("="*80)

        # Categories to scrape (leaf categories are most likely to have items)
        categories_to_scrape = self.all_categories

        total_requests = 0
        successful_requests = 0
        categories_with_items = 0

        for i, category in enumerate(categories_to_scrape, 1):
            slug = category['slug']
            name = category['name']
            level = category['level']
            indent = "  " * level

            print(f"[{i:3}/{len(categories_to_scrape)}] {indent}{name[:60]:60}", end=' ')

            total_requests += 1
            items = self.get_category_items(slug, name)

            if items:
                successful_requests += 1
                categories_with_items += 1

                # Add to products dict (deduplicates by ID)
                new_items = 0
                for item in items:
                    item_id = item.get('id')
                    if item_id:
                        if item_id not in self.all_products:
                            self.all_products[item_id] = item
                            new_items += 1

                # Track stats
                self.category_stats[slug] = {
                    'name': name,
                    'path': category['path'],
                    'item_count': len(items),
                    'new_items': new_items
                }

                print(f"✓ {len(items):3} items ({new_items} new) | Total: {len(self.all_products)}")
            else:
                print(f"  (empty)")

            # Rate limiting - be nice to the API
            time.sleep(0.3)

        print("\n" + "="*80)
        print(f"📊 SCRAPING SUMMARY")
        print("="*80)
        print(f"Categories scraped: {total_requests}")
        print(f"Categories with items: {categories_with_items}")
        print(f"Total API calls: {total_requests}")
        print(f"Successful calls: {successful_requests}")
        print(f"Total unique products: {len(self.all_products)}")

        # Show top categories by item count
        top_cats = sorted(self.category_stats.items(), key=lambda x: x[1]['item_count'], reverse=True)[:10]

        print(f"\n📈 Top 10 Categories by Product Count:")
        for i, (slug, stats) in enumerate(top_cats, 1):
            print(f"  {i:2}. {stats['name'][:50]:50} {stats['item_count']:4} items")

        return self.all_products

    def search_items(self, query: str = "", limit: int = 500) -> List[Dict]:
        """Alternative: Use search endpoint (returns max 500 items)"""
        url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment/items/search"

        params = {'language': self.language}
        payload = {"q": query}

        try:
            response = self.session.post(url, json=payload, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except Exception as e:
            print(f"  ❌ Search error: {e}")
            return []

    def supplement_with_search(self):
        """Use search to catch any items missed by category scraping"""
        print(f"\n🔍 Supplementing with search queries...")

        search_queries = [" ", "*", "a", "b", "c", "d", "e", "s", "m", "k"]

        initial_count = len(self.all_products)

        for query in search_queries:
            print(f"  Searching: '{query}'...", end=' ')
            items = self.search_items(query)

            new_items = 0
            for item in items:
                item_id = item.get('id')
                if item_id and item_id not in self.all_products:
                    self.all_products[item_id] = item
                    new_items += 1

            print(f"{new_items} new items")

            if new_items == 0:
                break  # No new items found, stop searching

            time.sleep(0.5)

        added = len(self.all_products) - initial_count
        if added > 0:
            print(f"✓ Added {added} items via search")
        else:
            print(f"✓ No additional items found via search")

    def save_all_data(self):
        """Save all scraped data"""
        timestamp = datetime.now()

        # Save categories
        if self.all_categories:
            cat_output = {
                'scraped_at': timestamp.isoformat(),
                'total': len(self.all_categories),
                'categories': self.all_categories,
                'category_stats': self.category_stats
            }

            with open('bravo_categories_complete.json', 'w', encoding='utf-8') as f:
                json.dump(cat_output, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Saved {len(self.all_categories)} categories → bravo_categories_complete.json")

        # Save products
        if self.all_products:
            products_list = list(self.all_products.values())

            prod_output = {
                'scraped_at': timestamp.isoformat(),
                'total_products': len(products_list),
                'total_categories': len(self.category_stats),
                'language': self.language,
                'products': products_list
            }

            with open('bravo_products_complete.json', 'w', encoding='utf-8') as f:
                json.dump(prod_output, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved {len(products_list)} products → bravo_products_complete.json")

            # Also save CSV
            self._save_products_csv(products_list)

    def _save_products_csv(self, products: List[Dict]):
        """Save products to CSV"""
        import csv

        if not products:
            return

        with open('bravo_products_complete.csv', 'w', newline='', encoding='utf-8') as f:
            # Define key fields for CSV
            csv_fields = ['id', 'name', 'description', 'baseprice', 'baseprice_cents',
                         'category_id', '_category_name', '_category_slug',
                         'image', 'available', 'in_stock']

            # Get all unique keys
            all_keys = set()
            for product in products:
                all_keys.update(product.keys())

            # Use defined fields plus any others that aren't nested
            fieldnames = []
            for field in csv_fields:
                if field in all_keys:
                    fieldnames.append(field)

            # Add remaining non-nested fields
            for key in sorted(all_keys):
                if key not in fieldnames and not isinstance(products[0].get(key), (dict, list)):
                    fieldnames.append(key)

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for product in products:
                row = {}
                for field in fieldnames:
                    value = product.get(field)
                    # Convert image dict to URL if needed
                    if field == 'image' and isinstance(value, dict):
                        value = value.get('url', '')
                    row[field] = value
                writer.writerow(row)

        print(f"💾 Exported to CSV → bravo_products_complete.csv")

    def display_sample(self, count: int = 5):
        """Display sample products"""
        if not self.all_products:
            return

        products = list(self.all_products.values())

        print(f"\n🛒 Sample Products (showing {min(count, len(products))} of {len(products)}):")
        print("-" * 80)

        for i, product in enumerate(products[:count], 1):
            name = product.get('name', 'Unknown')
            price = product.get('baseprice', 0)
            category = product.get('_category_name', 'N/A')

            print(f"{i}. {name[:70]}")
            print(f"   Price: {price} AZN")
            print(f"   Category: {category}")
            print(f"   ID: {product.get('id')}")
            print()

    def verify_completeness(self):
        """Verify we got all products"""
        print(f"\n✅ COMPLETENESS VERIFICATION")
        print("="*80)

        total_categories = len(self.all_categories)
        categories_with_items = len(self.category_stats)
        empty_categories = total_categories - categories_with_items

        print(f"Total categories: {total_categories}")
        print(f"Categories with items: {categories_with_items}")
        print(f"Empty categories: {empty_categories}")
        print(f"Total unique products: {len(self.all_products)}")

        # Estimate completeness
        if categories_with_items > 0:
            avg_items_per_cat = len(self.all_products) / categories_with_items
            print(f"Average items per category: {avg_items_per_cat:.1f}")

        # Check if any category hit the 500 limit (might indicate pagination needed)
        large_categories = {slug: stats for slug, stats in self.category_stats.items()
                           if stats['item_count'] >= 500}

        if large_categories:
            print(f"\n⚠️  WARNING: {len(large_categories)} categories have 500+ items:")
            for slug, stats in list(large_categories.items())[:5]:
                print(f"   • {stats['name']}: {stats['item_count']} items (might be capped)")
            print("   These categories might have more items than returned.")
        else:
            print(f"\n✓ No categories hit the 500 item limit - coverage appears complete")


def main():
    print("🚀 Wolt Bravo COMPREHENSIVE Scraper")
    print("="*80)
    print("This will scrape ALL products from ALL 223 categories")
    print()

    # Allow language selection
    import sys
    language = sys.argv[1] if len(sys.argv) > 1 else 'az'
    print(f"Language: {language} (use: python3 wolt_scraper_complete.py <az|en|ru>)")
    print()

    scraper = WoltComprehensiveScraper(language=language)

    # Step 1: Get all categories
    scraper.get_categories()

    if not scraper.all_categories:
        print("❌ Failed to fetch categories. Exiting.")
        return

    # Step 2: Scrape products from EVERY category
    scraper.scrape_all_products()

    # Step 3: Supplement with search (optional, catches edge cases)
    scraper.supplement_with_search()

    # Step 4: Verify completeness
    scraper.verify_completeness()

    # Step 5: Display sample
    scraper.display_sample(10)

    # Step 6: Save everything
    scraper.save_all_data()

    print("\n" + "="*80)
    print("✓ SCRAPING COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. python3 wolt_analyze.py    → Get marketing insights")
    print()
    print("Output files:")
    print("  • bravo_categories_complete.json")
    print("  • bravo_products_complete.json")
    print("  • bravo_products_complete.csv")


if __name__ == "__main__":
    main()
