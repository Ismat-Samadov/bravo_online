#!/usr/bin/env python3
"""
Comprehensive Wolt Bravo Supermarket Scraper
Scrapes all categories, subcategories, and product data from Wolt API
"""

import json
import requests
import time
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class WoltBravoScraper:
    def __init__(self):
        self.base_url = "https://consumer-api.wolt.com"
        self.venue_slug = "bravo-storefront"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })

        self.all_categories = []
        self.all_products = []
        self.category_map = {}

    def get_assortment(self, language='en') -> Dict:
        """Fetch the full assortment structure"""
        url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment"

        params = {}
        if language:
            params['lang'] = language

        print(f"🔄 Fetching assortment from Wolt...")

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✓ Fetched assortment with {len(data.get('categories', []))} main categories")
            return data
        except Exception as e:
            print(f"❌ Error fetching assortment: {e}")
            return {}

    def extract_all_categories(self, categories: List[Dict], parent_path: str = "") -> List[Dict]:
        """Recursively extract all categories and subcategories"""
        all_cats = []

        for cat in categories:
            cat_info = {
                'id': cat.get('id'),
                'name': cat.get('name'),
                'slug': cat.get('slug'),
                'description': cat.get('description', ''),
                'path': f"{parent_path}/{cat.get('name')}" if parent_path else cat.get('name'),
                'level': parent_path.count('/'),
                'has_subcategories': len(cat.get('subcategories', [])) > 0,
                'item_ids': cat.get('item_ids', []),
                'image_url': cat.get('images', [{}])[0].get('url') if cat.get('images') else None
            }

            all_cats.append(cat_info)
            self.category_map[cat_info['id']] = cat_info

            # Recursively get subcategories
            if cat.get('subcategories'):
                subcats = self.extract_all_categories(
                    cat['subcategories'],
                    cat_info['path']
                )
                all_cats.extend(subcats)

        return all_cats

    def try_get_items_by_category(self, category_id: str, category_slug: str) -> List[Dict]:
        """Try various methods to get items for a category"""
        items = []

        # Method 1: Try category filter
        try:
            url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/assortment"
            params = {'category_id': category_id}
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    print(f"  ✓ Found {len(data['items'])} items via category_id")
                    return data['items']
        except:
            pass

        # Method 2: Try category slug
        try:
            url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/categories/{category_slug}"
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    print(f"  ✓ Found {len(data['items'])} items via category slug")
                    return data['items']
        except:
            pass

        # Method 3: Try items endpoint
        try:
            url = f"{self.base_url}/consumer-api/consumer-assortment/v1/venues/slug/{self.venue_slug}/items"
            params = {'category': category_slug}
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    print(f"  ✓ Found {len(data['items'])} items via items endpoint")
                    return data['items']
        except:
            pass

        return items

    def scrape_all_categories(self):
        """Scrape all categories and their structure"""
        assortment = self.get_assortment()

        if not assortment:
            print("❌ Failed to fetch assortment")
            return False

        # Extract all categories
        self.all_categories = self.extract_all_categories(assortment.get('categories', []))

        print(f"\n📊 Category Structure:")
        print(f"   Total categories: {len(self.all_categories)}")

        # Count by level
        by_level = defaultdict(int)
        for cat in self.all_categories:
            by_level[cat['level']] += 1

        for level in sorted(by_level.keys()):
            print(f"   Level {level}: {by_level[level]} categories")

        return True

    def display_category_tree(self, limit: int = 50):
        """Display category tree structure"""
        print(f"\n🌳 Category Tree (showing first {limit}):")
        print("-" * 80)

        for i, cat in enumerate(self.all_categories[:limit], 1):
            indent = "  " * cat['level']
            has_items = f"({len(cat['item_ids'])} items)" if cat['item_ids'] else "(no items yet)"
            print(f"{i:3}. {indent}{cat['name']} {has_items}")

    def save_categories(self, filename: str = "bravo_categories.json"):
        """Save all categories to file"""
        output = {
            'scraped_at': datetime.now().isoformat(),
            'total_categories': len(self.all_categories),
            'categories': self.all_categories
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved {len(self.all_categories)} categories to {filename}")

    def export_categories_csv(self, filename: str = "bravo_categories.csv"):
        """Export categories to CSV"""
        import csv

        if not self.all_categories:
            print("⚠️  No categories to export")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'name', 'slug', 'path', 'level', 'has_subcategories', 'item_count', 'image_url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for cat in self.all_categories:
                writer.writerow({
                    'id': cat['id'],
                    'name': cat['name'],
                    'slug': cat['slug'],
                    'path': cat['path'],
                    'level': cat['level'],
                    'has_subcategories': cat['has_subcategories'],
                    'item_count': len(cat['item_ids']),
                    'image_url': cat['image_url']
                })

        print(f"💾 Exported categories to {filename}")

    def scrape_with_mitmproxy_data(self, captured_file: str = "captured_requests.json"):
        """Use mitmproxy captured data to find items endpoint"""
        captured_path = Path(captured_file)

        if not captured_path.exists():
            print(f"\n⚠️  No captured data found: {captured_file}")
            print("\nTo capture the items endpoint:")
            print("1. Run: mitmdump -s wolt_capture.py")
            print("2. Open Wolt app and browse Bravo products")
            print("3. Run this script again")
            return []

        with open(captured_path, 'r') as f:
            captures = json.load(f)

        print(f"\n🔍 Analyzing {len(captures)} captured requests...")

        # Look for item endpoints
        item_requests = []
        for capture in captures:
            url = capture.get('url', '')
            if 'item' in url.lower() or 'product' in url.lower():
                item_requests.append(capture)
                print(f"   Found: {capture.get('method')} {url}")

        # Extract items from responses
        all_items = []
        for req in item_requests:
            response = req.get('response_body', {})

            if isinstance(response, dict):
                items = response.get('items', [])
                if items:
                    all_items.extend(items)
                    print(f"   ✓ Extracted {len(items)} items")

        return all_items

    def analyze_category_distribution(self):
        """Analyze category distribution for marketing insights"""
        print("\n📈 Category Analysis:")
        print("-" * 80)

        # Main categories
        main_cats = [c for c in self.all_categories if c['level'] == 0]
        print(f"\nMain Categories ({len(main_cats)}):")
        for cat in main_cats[:15]:
            subcats = [c for c in self.all_categories if c['path'].startswith(cat['path']) and c['level'] > 0]
            print(f"   • {cat['name']}: {len(subcats)} subcategories")

        # Categories with most items
        cats_with_items = [c for c in self.all_categories if c['item_ids']]
        if cats_with_items:
            print(f"\nCategories with items: {len(cats_with_items)}")
            sorted_cats = sorted(cats_with_items, key=lambda x: len(x['item_ids']), reverse=True)
            print("\nTop 10 categories by item count:")
            for i, cat in enumerate(sorted_cats[:10], 1):
                print(f"   {i}. {cat['name']}: {len(cat['item_ids'])} items")


def main():
    scraper = WoltBravoScraper()

    # Scrape all categories
    print("🚀 Wolt Bravo Comprehensive Scraper")
    print("=" * 80)

    if scraper.scrape_all_categories():
        scraper.display_category_tree(limit=30)
        scraper.analyze_category_distribution()
        scraper.save_categories()
        scraper.export_categories_csv()

        print("\n" + "=" * 80)
        print("📝 Next Steps:")
        print("-" * 80)
        print("The assortment API doesn't return items by default.")
        print("\nTo get product data, you need to:")
        print("1. Run: mitmdump -s wolt_capture.py")
        print("2. Open Wolt app and browse categories")
        print("3. The capture script will save the real items API endpoint")
        print("4. Run: python3 wolt_bravo_scraper.py --analyze-captures")

        # Try to load captured data if available
        scraper.scrape_with_mitmproxy_data()


if __name__ == "__main__":
    main()
