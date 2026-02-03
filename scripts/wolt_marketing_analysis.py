#!/usr/bin/env python3
"""
Wolt Bravo Marketing Analysis Tool
Analyzes the complete scraped product data for marketing insights
"""

import json
import csv
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime


class BravoMarketingAnalyzer:
    def __init__(self, products_file='bravo_products_complete.json'):
        self.products_file = Path(products_file)
        self.products = []
        self.load_data()

    def load_data(self):
        """Load scraped product data"""
        if not self.products_file.exists():
            print(f"❌ File not found: {self.products_file}")
            print("\nRun first: python3 wolt_scraper_complete.py")
            return

        with open(self.products_file, 'r') as f:
            data = json.load(f)
            self.products = data.get('products', [])

        print(f"✓ Loaded {len(self.products)} products")
        print(f"  Scraped: {data.get('scraped_at', 'Unknown')}")
        print(f"  Language: {data.get('language', 'Unknown')}")

    def normalize_products(self):
        """Normalize products to easier format"""
        normalized = []

        for p in self.products:
            # Get price in AZN
            price_cents = p.get('price', 0)
            price = price_cents / 100 if price_cents else 0

            # Get original price if discounted
            original_price_cents = p.get('original_price')
            original_price = original_price_cents / 100 if original_price_cents else None

            # Calculate discount
            discount_pct = None
            if original_price and price and original_price > price:
                discount_pct = ((original_price - price) / original_price) * 100

            # Get image URL
            image_url = None
            if p.get('images') and len(p['images']) > 0:
                image_url = p['images'][0].get('url')

            # Handle None values
            purchasable_balance = p.get('purchasable_balance') or 0

            norm = {
                'id': p.get('id'),
                'name': p.get('name', ''),
                'description': p.get('description', ''),
                'price': price,
                'original_price': original_price,
                'discount_percent': discount_pct,
                'currency': 'AZN',
                'category': p.get('_category_name', 'Unknown'),
                'category_slug': p.get('_category_slug', ''),
                'image_url': image_url,
                'in_stock': purchasable_balance > 0,
                'stock_qty': purchasable_balance,
                'barcode': p.get('barcode_gtin'),
                'unit': p.get('sell_by_weight_config', {}).get('unit', 'piece') if p.get('sell_by_weight_config') else 'piece',
                'alcohol_permille': p.get('alcohol_permille') or 0,
                'is_wolt_plus_only': p.get('is_wolt_plus_only', False),
                'tags': p.get('product_hierarchy_tags') or [],
                'dietary_preferences': p.get('dietary_preferences') or []
            }

            normalized.append(norm)

        return normalized

    def pricing_analysis(self, products):
        """Analyze pricing"""
        print("\n" + "="*80)
        print("💰 PRICING ANALYSIS")
        print("="*80)

        prices = [p['price'] for p in products if p['price'] > 0]

        if not prices:
            print("❌ No pricing data available")
            return

        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        median_price = sorted(prices)[len(prices) // 2]

        print(f"\nOverall Pricing:")
        print(f"  Products with prices: {len(prices)}/{len(products)}")
        print(f"  Average Price: {avg_price:.2f} AZN")
        print(f"  Median Price: {median_price:.2f} AZN")
        print(f"  Min Price: {min_price:.2f} AZN")
        print(f"  Max Price: {max_price:.2f} AZN")

        # Price distribution
        ranges = {
            'Under 0.50 AZN': 0,
            '0.50-1 AZN': 0,
            '1-3 AZN': 0,
            '3-5 AZN': 0,
            '5-10 AZN': 0,
            '10-20 AZN': 0,
            '20-50 AZN': 0,
            'Over 50 AZN': 0
        }

        for price in prices:
            if price < 0.5:
                ranges['Under 0.50 AZN'] += 1
            elif price < 1:
                ranges['0.50-1 AZN'] += 1
            elif price < 3:
                ranges['1-3 AZN'] += 1
            elif price < 5:
                ranges['3-5 AZN'] += 1
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
            if count > 0:
                pct = (count / len(prices)) * 100
                bar = '█' * int(pct / 2)
                print(f"  {range_name:15} {count:5} ({pct:5.1f}%) {bar}")

        # Discounted products
        discounted = [p for p in products if p['discount_percent']]
        if discounted:
            avg_discount = sum(p['discount_percent'] for p in discounted) / len(discounted)
            print(f"\nDiscounts:")
            print(f"  Products on sale: {len(discounted)} ({len(discounted)/len(products)*100:.1f}%)")
            print(f"  Average discount: {avg_discount:.1f}%")

            top_discounts = sorted(discounted, key=lambda x: x['discount_percent'], reverse=True)[:10]
            print(f"\n  Top 10 Discounts:")
            for i, p in enumerate(top_discounts, 1):
                savings = p['original_price'] - p['price']
                print(f"    {i:2}. {p['discount_percent']:5.1f}% off - Save {savings:.2f} AZN - {p['name'][:50]}")

    def category_analysis(self, products):
        """Analyze categories"""
        print("\n" + "="*80)
        print("📊 CATEGORY ANALYSIS")
        print("="*80)

        # Count by category
        category_counts = Counter(p['category'] for p in products)

        print(f"\nTop 20 Categories by Product Count:")
        for i, (cat, count) in enumerate(category_counts.most_common(20), 1):
            pct = (count / len(products)) * 100
            print(f"  {i:2}. {cat[:55]:55} {count:4} ({pct:5.1f}%)")

        # Average price by category
        category_prices = defaultdict(list)
        for p in products:
            if p['price'] > 0:
                category_prices[p['category']].append(p['price'])

        if category_prices:
            print(f"\nTop 15 Most Expensive Categories (by avg price):")
            cat_avg = {cat: sum(prices)/len(prices) for cat, prices in category_prices.items()}
            for i, (cat, avg) in enumerate(sorted(cat_avg.items(), key=lambda x: -x[1])[:15], 1):
                count = len(category_prices[cat])
                print(f"  {i:2}. {cat[:50]:50} {avg:7.2f} AZN (n={count})")

        # Cheapest categories
        print(f"\nTop 15 Cheapest Categories (by avg price):")
        for i, (cat, avg) in enumerate(sorted(cat_avg.items(), key=lambda x: x[1])[:15], 1):
            count = len(category_prices[cat])
            print(f"  {i:2}. {cat[:50]:50} {avg:7.2f} AZN (n={count})")

    def stock_analysis(self, products):
        """Analyze stock availability"""
        print("\n" + "="*80)
        print("📦 STOCK AVAILABILITY ANALYSIS")
        print("="*80)

        in_stock = [p for p in products if p['in_stock']]
        out_of_stock = [p for p in products if not p['in_stock']]

        print(f"\nStock Status:")
        print(f"  In stock: {len(in_stock)} ({len(in_stock)/len(products)*100:.1f}%)")
        print(f"  Out of stock: {len(out_of_stock)} ({len(out_of_stock)/len(products)*100:.1f}%)")

        # Stock by category
        if out_of_stock:
            cat_oos = Counter(p['category'] for p in out_of_stock)
            print(f"\nTop 10 Categories with Most Out-of-Stock Items:")
            for i, (cat, count) in enumerate(cat_oos.most_common(10), 1):
                total_in_cat = sum(1 for p in products if p['category'] == cat)
                pct = (count / total_in_cat) * 100
                print(f"  {i:2}. {cat[:50]:50} {count:3}/{total_in_cat:3} ({pct:5.1f}%)")

        # Low stock warnings
        low_stock = [p for p in products if p['in_stock'] and p['stock_qty'] < 10]
        if low_stock:
            print(f"\nLow Stock Warnings (< 10 units):")
            print(f"  {len(low_stock)} products running low")

    def special_products_analysis(self, products):
        """Analyze special product types"""
        print("\n" + "="*80)
        print("🌟 SPECIAL PRODUCTS ANALYSIS")
        print("="*80)

        # Wolt Plus exclusives
        wolt_plus = [p for p in products if p['is_wolt_plus_only']]
        if wolt_plus:
            print(f"\nWolt Plus Exclusive Products: {len(wolt_plus)}")

        # Alcoholic products
        alcoholic = [p for p in products if p['alcohol_permille'] > 0]
        if alcoholic:
            print(f"Alcoholic Products: {len(alcoholic)}")
            avg_alcohol_price = sum(p['price'] for p in alcoholic if p['price'] > 0) / len([p for p in alcoholic if p['price'] > 0])
            print(f"  Average alcoholic product price: {avg_alcohol_price:.2f} AZN")

        # Products with dietary preferences
        dietary = [p for p in products if p['dietary_preferences']]
        if dietary:
            print(f"\nProducts with Dietary Preferences: {len(dietary)}")
            all_prefs = []
            for p in dietary:
                all_prefs.extend(p['dietary_preferences'])
            pref_counts = Counter(all_prefs)
            for pref, count in pref_counts.most_common():
                print(f"  {pref}: {count}")

        # Products by tags
        all_tags = []
        for p in products:
            all_tags.extend(p['tags'])

        if all_tags:
            print(f"\nProduct Tags Distribution:")
            tag_counts = Counter(all_tags)
            for tag, count in tag_counts.most_common():
                print(f"  {tag}: {count} ({count/len(products)*100:.1f}%)")

    def marketing_insights(self, products):
        """Generate actionable marketing insights"""
        print("\n" + "="*80)
        print("🎯 MARKETING INSIGHTS & RECOMMENDATIONS")
        print("="*80)

        # 1. High-value opportunities
        high_value = [p for p in products if p['price'] > 20]
        print(f"\n1. HIGH-VALUE PRODUCT OPPORTUNITIES:")
        print(f"   • {len(high_value)} premium products (>20 AZN)")
        if high_value:
            avg_high = sum(p['price'] for p in high_value) / len(high_value)
            print(f"   • Average premium price: {avg_high:.2f} AZN")
            print(f"   • Recommendation: Create luxury product bundles and targeted campaigns")

        # 2. Price sweet spots
        prices = [p['price'] for p in products if p['price'] > 0]
        if prices:
            median = sorted(prices)[len(prices) // 2]
            mode_range = None
            for range_name, (min_p, max_p) in [
                ('1-3 AZN', (1, 3)),
                ('3-5 AZN', (3, 5)),
                ('5-10 AZN', (5, 10))
            ]:
                count = len([p for p in prices if min_p <= p < max_p])
                if not mode_range or count > mode_range[1]:
                    mode_range = (range_name, count)

            print(f"\n2. OPTIMAL PRICE POINTS:")
            print(f"   • Median price: {median:.2f} AZN")
            print(f"   • Most common range: {mode_range[0]} ({mode_range[1]} products)")
            print(f"   • Recommendation: Focus promotions around {median:.0f} AZN products")

        # 3. Category opportunities
        category_counts = Counter(p['category'] for p in products)
        top_cat = category_counts.most_common(1)[0] if category_counts else None
        if top_cat:
            print(f"\n3. TOP PERFORMING CATEGORY:")
            print(f"   • {top_cat[0]}: {top_cat[1]} products")
            print(f"   • Recommendation: Feature this category in homepage banners")

        # 4. Out of stock opportunities
        oos = [p for p in products if not p['in_stock']]
        if oos:
            print(f"\n4. RESTOCK MARKETING OPPORTUNITIES:")
            print(f"   • {len(oos)} out-of-stock products")
            print(f"   • Recommendation: Set up 'Back in Stock' email notifications")

        # 5. Discount strategy
        discounted = [p for p in products if p['discount_percent']]
        if discounted:
            avg_disc = sum(p['discount_percent'] for p in discounted) / len(discounted)
            print(f"\n5. DISCOUNT OPTIMIZATION:")
            print(f"   • Current discount rate: {len(discounted)/len(products)*100:.1f}% of products")
            print(f"   • Average discount: {avg_disc:.1f}%")
            print(f"   • Recommendation: Test {avg_disc-5:.0f}%-{avg_disc+5:.0f}% discount range for conversions")

        # 6. Seasonal/trending
        print(f"\n6. PRODUCT ASSORTMENT:")
        print(f"   • Total unique products: {len(products)}")
        print(f"   • Average products per category: {len(products)/len(category_counts):.1f}")
        print(f"   • Recommendation: Monitor top 20 products weekly for trend analysis")

    def save_analysis_report(self, products, filename='bravo_marketing_report.txt'):
        """Save comprehensive report"""
        import sys
        from io import StringIO

        # Capture all output
        old_stdout = sys.stdout
        sys.stdout = report = StringIO()

        print("WOLT BRAVO SUPERMARKET - COMPREHENSIVE MARKETING ANALYSIS")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Products Analyzed: {len(products)}")
        print("\n")

        self.pricing_analysis(products)
        self.category_analysis(products)
        self.stock_analysis(products)
        self.special_products_analysis(products)
        self.marketing_insights(products)

        sys.stdout = old_stdout

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report.getvalue())

        print(f"\n📄 Detailed report saved → {filename}")

    def export_analysis_csv(self, products, filename='bravo_products_analyzed.csv'):
        """Export analyzed products to CSV"""
        if not products:
            return

        fieldnames = list(products[0].keys())

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)

        print(f"💾 Analyzed products exported → {filename}")


def main():
    print("🚀 Wolt Bravo Marketing Analysis")
    print("="*80)

    analyzer = BravoMarketingAnalyzer()

    if not analyzer.products:
        return

    # Normalize products
    print("\n📊 Normalizing product data...")
    products = analyzer.normalize_products()
    print(f"✓ Normalized {len(products)} products")

    # Run all analyses
    analyzer.pricing_analysis(products)
    analyzer.category_analysis(products)
    analyzer.stock_analysis(products)
    analyzer.special_products_analysis(products)
    analyzer.marketing_insights(products)

    # Save outputs
    analyzer.save_analysis_report(products)
    analyzer.export_analysis_csv(products)

    print("\n" + "="*80)
    print("✓ ANALYSIS COMPLETE!")
    print("="*80)
    print("\nOutput files:")
    print("  • bravo_marketing_report.txt - Full analysis report")
    print("  • bravo_products_analyzed.csv - Normalized product data")


if __name__ == "__main__":
    main()
