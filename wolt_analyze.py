#!/usr/bin/env python3
"""
Wolt Bravo Data Analyzer
Extracts products from captured data and performs marketing analysis
"""

import json
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List
from datetime import datetime
import re


class WoltAnalyzer:
    def __init__(self, captured_file: str = "wolt_captured.json"):
        self.captured_file = Path(captured_file)
        self.captures = []
        self.products = []
        self.categories_data = {}

        self.load_data()

    def load_data(self):
        """Load captured data"""
        if self.captured_file.exists():
            with open(self.captured_file, 'r', encoding='utf-8') as f:
                self.captures = json.load(f)
            print(f"✓ Loaded {len(self.captures)} captured requests")
        else:
            print(f"❌ No captured data found: {self.captured_file}")
            print("\nRun: mitmdump -s wolt_capture.py")
            print("Then browse products in the Wolt app")

        # Load categories if available
        cat_file = Path("bravo_categories.json")
        if cat_file.exists():
            with open(cat_file, 'r') as f:
                data = json.load(f)
                self.categories_data = {c['id']: c for c in data.get('categories', [])}
            print(f"✓ Loaded {len(self.categories_data)} categories")

    def extract_products(self) -> List[Dict]:
        """Extract all products from captured responses"""
        all_products = []
        product_ids = set()

        for capture in self.captures:
            if not capture.get('has_items'):
                continue

            response = capture.get('response_body', {})
            products = self._extract_products_recursive(response)

            for product in products:
                # Add source metadata
                product['_source_url'] = capture.get('url')
                product['_captured_at'] = capture.get('timestamp')

                # Deduplicate by ID
                if product.get('id') and product['id'] not in product_ids:
                    product_ids.add(product['id'])
                    all_products.append(product)

        self.products = all_products
        print(f"\n✓ Extracted {len(all_products)} unique products")
        return all_products

    def _extract_products_recursive(self, data: any, depth=0) -> List[Dict]:
        """Recursively extract products from nested JSON"""
        products = []

        if depth > 10:  # Prevent infinite recursion
            return products

        if isinstance(data, dict):
            # Check if this looks like a product
            if self._is_product(data):
                products.append(data)

            # Check for items array
            if 'items' in data and isinstance(data['items'], list):
                for item in data['items']:
                    if isinstance(item, dict) and self._is_product(item):
                        products.append(item)

            # Recursively search nested dicts
            for value in data.values():
                products.extend(self._extract_products_recursive(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                products.extend(self._extract_products_recursive(item, depth + 1))

        return products

    def _is_product(self, item: Dict) -> bool:
        """Check if a dict looks like a product"""
        if not isinstance(item, dict):
            return False

        # Must have ID and name
        if not item.get('id') or not item.get('name'):
            return False

        # Should have price-related fields
        has_price = any(k in item for k in ['price', 'baseprice', 'baseprice_cents'])

        return has_price

    def normalize_products(self) -> List[Dict]:
        """Normalize products to standard format"""
        normalized = []

        for product in self.products:
            # Extract price
            price = None
            if 'baseprice_cents' in product:
                price = product['baseprice_cents'] / 100
            elif 'baseprice' in product:
                price = product['baseprice']
            elif 'price' in product:
                price = product['price']

            # Get category info
            category_id = product.get('category_id')
            category_info = self.categories_data.get(category_id, {})

            norm = {
                'id': product.get('id'),
                'name': product.get('name'),
                'description': product.get('description', ''),
                'price': price,
                'currency': 'AZN',  # Azerbaijan Manat
                'original_price': product.get('original_price_cents', 0) / 100 if product.get('original_price_cents') else None,
                'discount': None,
                'category_id': category_id,
                'category_name': category_info.get('name'),
                'category_path': category_info.get('path'),
                'image_url': product.get('image', {}).get('url') if isinstance(product.get('image'), dict) else product.get('image'),
                'unit': product.get('unit'),
                'weight': product.get('weight'),
                'available': product.get('available', True),
                'in_stock': product.get('in_stock', True),
                'sku': product.get('sku'),
                'barcode': product.get('barcode'),
                'tags': product.get('tags', []),
                'raw_data': product
            }

            # Calculate discount
            if norm['original_price'] and norm['price']:
                if norm['original_price'] > norm['price']:
                    norm['discount'] = ((norm['original_price'] - norm['price']) / norm['original_price']) * 100

            normalized.append(norm)

        print(f"✓ Normalized {len(normalized)} products")
        return normalized

    def analyze_pricing(self):
        """Analyze pricing for marketing insights"""
        if not self.products:
            return

        normalized = self.normalize_products()

        prices = [p['price'] for p in normalized if p['price']]

        if not prices:
            print("⚠️  No pricing data available")
            return

        print("\n" + "=" * 80)
        print("💰 PRICING ANALYSIS")
        print("=" * 80)

        # Basic stats
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        median_price = sorted(prices)[len(prices) // 2]

        print(f"\nOverall Pricing:")
        print(f"  Average Price: {avg_price:.2f} AZN")
        print(f"  Median Price: {median_price:.2f} AZN")
        print(f"  Min Price: {min_price:.2f} AZN")
        print(f"  Max Price: {max_price:.2f} AZN")

        # Price ranges
        ranges = {
            'Under 1 AZN': 0,
            '1-5 AZN': 0,
            '5-10 AZN': 0,
            '10-20 AZN': 0,
            '20-50 AZN': 0,
            'Over 50 AZN': 0
        }

        for price in prices:
            if price < 1:
                ranges['Under 1 AZN'] += 1
            elif price < 5:
                ranges['1-5 AZN'] += 1
            elif price < 10:
                ranges['5-10 AZN'] += 1
            elif price < 20:
                ranges['10-20 AZN'] += 1
            elif price < 50:
                ranges['20-50 AZN'] += 1
            else:
                ranges['Over 50 AZN'] += 1

        print(f"\nPrice Distribution:")
        for range_name, count in ranges.items():
            pct = (count / len(prices)) * 100
            bar = '█' * int(pct / 2)
            print(f"  {range_name:15} {count:4} ({pct:5.1f}%) {bar}")

        # Products with discounts
        discounted = [p for p in normalized if p['discount']]
        if discounted:
            avg_discount = sum(p['discount'] for p in discounted) / len(discounted)
            print(f"\nDiscounts:")
            print(f"  Products on sale: {len(discounted)} ({len(discounted)/len(normalized)*100:.1f}%)")
            print(f"  Average discount: {avg_discount:.1f}%")

            print(f"\n  Top 10 Discounts:")
            top_discounts = sorted(discounted, key=lambda x: x['discount'], reverse=True)[:10]
            for i, p in enumerate(top_discounts, 1):
                print(f"    {i}. {p['name'][:50]:50} {p['discount']:5.1f}% off")

    def analyze_categories(self):
        """Analyze category distribution"""
        if not self.products:
            return

        normalized = self.normalize_products()

        print("\n" + "=" * 80)
        print("📊 CATEGORY ANALYSIS")
        print("=" * 80)

        # Count by category
        category_counts = Counter(p['category_name'] for p in normalized if p['category_name'])

        print(f"\nTop 20 Categories by Product Count:")
        for i, (cat, count) in enumerate(category_counts.most_common(20), 1):
            print(f"  {i:2}. {cat[:50]:50} {count:4} products")

        # Average price by category
        category_prices = defaultdict(list)
        for p in normalized:
            if p['category_name'] and p['price']:
                category_prices[p['category_name']].append(p['price'])

        if category_prices:
            print(f"\nTop 10 Most Expensive Categories (by avg price):")
            cat_avg = {cat: sum(prices)/len(prices) for cat, prices in category_prices.items()}
            for i, (cat, avg) in enumerate(sorted(cat_avg.items(), key=lambda x: -x[1])[:10], 1):
                print(f"  {i:2}. {cat[:50]:50} {avg:7.2f} AZN")

    def analyze_availability(self):
        """Analyze product availability"""
        if not self.products:
            return

        normalized = self.normalize_products()

        print("\n" + "=" * 80)
        print("📦 AVAILABILITY ANALYSIS")
        print("=" * 80)

        available_count = sum(1 for p in normalized if p['available'])
        in_stock_count = sum(1 for p in normalized if p['in_stock'])

        print(f"\nStock Status:")
        print(f"  Available products: {available_count}/{len(normalized)} ({available_count/len(normalized)*100:.1f}%)")
        print(f"  In stock: {in_stock_count}/{len(normalized)} ({in_stock_count/len(normalized)*100:.1f}%)")

        # Out of stock by category
        out_of_stock = [p for p in normalized if not p['in_stock']]
        if out_of_stock:
            cat_oos = Counter(p['category_name'] for p in out_of_stock if p['category_name'])
            print(f"\nTop 10 Categories with Most Out-of-Stock Items:")
            for i, (cat, count) in enumerate(cat_oos.most_common(10), 1):
                total_in_cat = sum(1 for p in normalized if p['category_name'] == cat)
                pct = (count / total_in_cat) * 100
                print(f"  {i:2}. {cat[:45]:45} {count:3}/{total_in_cat:3} ({pct:5.1f}%)")

    def generate_marketing_insights(self):
        """Generate actionable marketing insights"""
        if not self.products:
            return

        normalized = self.normalize_products()

        print("\n" + "=" * 80)
        print("🎯 MARKETING INSIGHTS")
        print("=" * 80)

        # 1. Best selling potential
        print("\n1. HIGH-VALUE OPPORTUNITIES:")
        high_value = [p for p in normalized if p['price'] and p['price'] > 20]
        print(f"   • {len(high_value)} high-value products (>20 AZN)")
        print(f"   • Opportunity for premium marketing campaigns")

        # 2. Discount strategy
        discounted = [p for p in normalized if p['discount']]
        if discounted:
            print(f"\n2. DISCOUNT OPTIMIZATION:")
            print(f"   • {len(discounted)} products currently on sale")
            avg_disc = sum(p['discount'] for p in discounted) / len(discounted)
            print(f"   • Average discount: {avg_disc:.1f}%")
            print(f"   • Recommendation: Analyze conversion rates for different discount tiers")

        # 3. Category focus
        category_counts = Counter(p['category_name'] for p in normalized if p['category_name'])
        top_cat = category_counts.most_common(1)[0] if category_counts else None
        if top_cat:
            print(f"\n3. TOP CATEGORY:")
            print(f"   • {top_cat[0]}: {top_cat[1]} products")
            print(f"   • Recommendation: Focus marketing efforts on this category")

        # 4. Price points
        prices = [p['price'] for p in normalized if p['price']]
        if prices:
            median = sorted(prices)[len(prices) // 2]
            print(f"\n4. OPTIMAL PRICE POINT:")
            print(f"   • Median price: {median:.2f} AZN")
            print(f"   • Recommendation: Target promotions around {median:.0f} AZN products")

        # 5. Stock alerts
        out_of_stock = [p for p in normalized if not p['in_stock']]
        if out_of_stock:
            print(f"\n5. STOCK ALERTS:")
            print(f"   • {len(out_of_stock)} out-of-stock items")
            print(f"   • Recommendation: Set up restock notifications for marketing")

    def save_products(self, filename: str = "bravo_products_full.json"):
        """Save all products to JSON"""
        normalized = self.normalize_products()

        output = {
            'scraped_at': datetime.now().isoformat(),
            'total_products': len(normalized),
            'source': 'Wolt Bravo Supermarket',
            'products': normalized
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved {len(normalized)} products to {filename}")

    def export_csv(self, filename: str = "bravo_products.csv"):
        """Export products to CSV"""
        normalized = self.normalize_products()

        if not normalized:
            print("⚠️  No products to export")
            return

        fieldnames = ['id', 'name', 'price', 'original_price', 'discount',
                     'category_name', 'category_path', 'available', 'in_stock',
                     'description', 'image_url']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for product in normalized:
                writer.writerow(product)

        print(f"💾 Exported to {filename}")

    def create_marketing_report(self, filename: str = "marketing_report.txt"):
        """Create a comprehensive marketing report"""
        with open(filename, 'w', encoding='utf-8') as f:
            import sys
            old_stdout = sys.stdout
            sys.stdout = f

            print("WOLT BRAVO SUPERMARKET - MARKETING ANALYSIS REPORT")
            print("=" * 80)
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total Products Analyzed: {len(self.products)}")
            print("\n")

            self.analyze_pricing()
            self.analyze_categories()
            self.analyze_availability()
            self.generate_marketing_insights()

            sys.stdout = old_stdout

        print(f"\n📄 Marketing report saved to {filename}")


def main():
    print("🚀 Wolt Bravo Data Analyzer")
    print("=" * 80)

    analyzer = WoltAnalyzer()

    if not analyzer.captures:
        print("\n⚠️  No captured data. Please run:")
        print("   mitmdump -s wolt_capture.py")
        print("\nThen browse products in the Wolt app.")
        return

    # Extract products
    analyzer.extract_products()

    if not analyzer.products:
        print("\n⚠️  No products found in captured data.")
        print("\nMake sure to:")
        print("1. Browse different categories in the app")
        print("2. Scroll through product listings")
        print("3. View individual product details")
        return

    # Run all analyses
    analyzer.analyze_pricing()
    analyzer.analyze_categories()
    analyzer.analyze_availability()
    analyzer.generate_marketing_insights()

    # Save data
    analyzer.save_products()
    analyzer.export_csv()
    analyzer.create_marketing_report()

    print("\n" + "=" * 80)
    print("✓ Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
