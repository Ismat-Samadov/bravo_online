#!/usr/bin/env python3
"""
Bravo Supermarket Business Intelligence Charts Generator
Creates executive-ready visualizations for strategic decision-making
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

# Set professional style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Color palette - professional and business-appropriate
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#06A77D',
    'warning': '#F18F01',
    'danger': '#C73E1D',
    'neutral': '#6C757D'
}


class BravoBusinessIntelligence:
    def __init__(self, data_file='data/bravo_products_complete.json'):
        self.data_file = Path(data_file)
        self.products = []
        self.charts_dir = Path('charts')
        self.charts_dir.mkdir(exist_ok=True)

        self.load_data()

    def load_data(self):
        """Load product data"""
        with open(self.data_file, 'r') as f:
            data = json.load(f)
            self.products = data.get('products', [])

        print(f"✓ Loaded {len(self.products)} products for analysis")

    def normalize_products(self):
        """Convert to analyzable format"""
        normalized = []

        for p in self.products:
            price_cents = p.get('price', 0)
            price = price_cents / 100 if price_cents else 0

            original_price_cents = p.get('original_price')
            original_price = original_price_cents / 100 if original_price_cents else None

            discount_pct = None
            if original_price and price and original_price > price:
                discount_pct = ((original_price - price) / original_price) * 100

            purchasable = p.get('purchasable_balance') or 0

            norm = {
                'price': price,
                'original_price': original_price,
                'discount_percent': discount_pct,
                'category': p.get('_category_name', 'Other'),
                'in_stock': purchasable > 0,
                'stock_qty': purchasable,
                'name': p.get('name', '')
            }

            normalized.append(norm)

        return pd.DataFrame(normalized)

    def chart1_category_portfolio_value(self, df):
        """Chart 1: Product Portfolio by Category (Top 15)"""
        plt.figure(figsize=(14, 8))

        category_counts = df['category'].value_counts().head(15)

        # Color bars by size
        colors = [COLORS['primary'] if i < 5 else COLORS['neutral']
                 for i in range(len(category_counts))]

        bars = plt.barh(range(len(category_counts)), category_counts.values, color=colors)
        plt.yticks(range(len(category_counts)), category_counts.index)
        plt.xlabel('Number of Products', fontweight='bold')
        plt.title('Product Portfolio Distribution - Top 15 Categories',
                 fontsize=16, fontweight='bold', pad=20)

        # Add value labels
        for i, (idx, val) in enumerate(category_counts.items()):
            plt.text(val + 1, i, str(val), va='center', fontweight='bold')

        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('charts/01_category_portfolio.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 1: Category Portfolio")

    def chart2_pricing_tiers(self, df):
        """Chart 2: Revenue Opportunity by Price Tier"""
        plt.figure(figsize=(14, 7))

        # Define business-relevant price tiers
        bins = [0, 1, 3, 5, 10, 20, 50, 1000]
        labels = ['Budget\n(<1 AZN)', 'Economy\n(1-3 AZN)', 'Standard\n(3-5 AZN)',
                 'Premium\n(5-10 AZN)', 'Specialty\n(10-20 AZN)',
                 'Luxury\n(20-50 AZN)', 'Ultra-Premium\n(>50 AZN)']

        df['price_tier'] = pd.cut(df['price'], bins=bins, labels=labels, include_lowest=True)
        tier_counts = df['price_tier'].value_counts().sort_index()

        colors_gradient = [COLORS['success'], COLORS['primary'], COLORS['primary'],
                          COLORS['warning'], COLORS['warning'],
                          COLORS['secondary'], COLORS['danger']]

        bars = plt.bar(range(len(tier_counts)), tier_counts.values,
                      color=colors_gradient[:len(tier_counts)])
        plt.xticks(range(len(tier_counts)), tier_counts.index, rotation=0)
        plt.ylabel('Number of Products', fontweight='bold')
        plt.title('Revenue Opportunity Analysis - Product Distribution by Price Tier',
                 fontsize=16, fontweight='bold', pad=20)

        # Add value labels
        for i, val in enumerate(tier_counts.values):
            plt.text(i, val + 50, str(val), ha='center', fontweight='bold')

        plt.tight_layout()
        plt.savefig('charts/02_pricing_tiers.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 2: Pricing Tiers")

    def chart3_premium_categories(self, df):
        """Chart 3: High-Value Categories (Top 12 by Average Price)"""
        plt.figure(figsize=(14, 8))

        category_avg = df[df['price'] > 0].groupby('category')['price'].agg(['mean', 'count'])
        category_avg = category_avg[category_avg['count'] >= 5]  # Min 5 products
        category_avg = category_avg.sort_values('mean', ascending=True).tail(12)

        bars = plt.barh(range(len(category_avg)), category_avg['mean'], color=COLORS['secondary'])
        plt.yticks(range(len(category_avg)), category_avg.index)
        plt.xlabel('Average Price (AZN)', fontweight='bold')
        plt.title('Premium Category Opportunities - Highest Average Prices',
                 fontsize=16, fontweight='bold', pad=20)

        # Add value labels
        for i, val in enumerate(category_avg['mean']):
            plt.text(val + 1, i, f'{val:.2f} AZN', va='center', fontweight='bold')

        plt.tight_layout()
        plt.savefig('charts/03_premium_categories.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 3: Premium Categories")

    def chart4_discount_strategy(self, df):
        """Chart 4: Discount Strategy Effectiveness"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

        # Left: Discount distribution
        discounted = df[df['discount_percent'].notna()]
        discount_ranges = pd.cut(discounted['discount_percent'],
                                bins=[0, 10, 20, 30, 40, 100],
                                labels=['<10%', '10-20%', '20-30%', '30-40%', '>40%'])
        discount_counts = discount_ranges.value_counts().sort_index()

        bars1 = ax1.bar(range(len(discount_counts)), discount_counts.values,
                       color=COLORS['warning'])
        ax1.set_xticks(range(len(discount_counts)))
        ax1.set_xticklabels(discount_counts.index)
        ax1.set_ylabel('Number of Products', fontweight='bold')
        ax1.set_title('Discount Distribution', fontsize=14, fontweight='bold')

        for i, val in enumerate(discount_counts.values):
            ax1.text(i, val + 10, str(val), ha='center', fontweight='bold')

        # Right: Products on sale vs regular price
        on_sale = len(discounted)
        regular_price = len(df) - on_sale

        bars2 = ax2.bar(['Products on Sale', 'Regular Price'],
                       [on_sale, regular_price],
                       color=[COLORS['warning'], COLORS['neutral']])
        ax2.set_ylabel('Number of Products', fontweight='bold')
        ax2.set_title('Promotional Coverage', fontsize=14, fontweight='bold')

        for i, (label, val) in enumerate(zip(['Products on Sale', 'Regular Price'],
                                             [on_sale, regular_price])):
            pct = (val / len(df)) * 100
            ax2.text(i, val + 50, f'{val}\n({pct:.1f}%)', ha='center', fontweight='bold')

        plt.suptitle('Promotional Strategy Analysis', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig('charts/04_discount_strategy.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 4: Discount Strategy")

    def chart5_stock_risk_assessment(self, df):
        """Chart 5: Inventory Risk Assessment"""
        plt.figure(figsize=(14, 7))

        # Stock status categories
        out_of_stock = len(df[~df['in_stock']])
        low_stock = len(df[(df['in_stock']) & (df['stock_qty'] < 10)])
        medium_stock = len(df[(df['stock_qty'] >= 10) & (df['stock_qty'] < 50)])
        healthy_stock = len(df[df['stock_qty'] >= 50])

        categories = ['Out of Stock\n(CRITICAL)', 'Low Stock\n(<10 units)',
                     'Medium Stock\n(10-50 units)', 'Healthy Stock\n(>50 units)']
        values = [out_of_stock, low_stock, medium_stock, healthy_stock]
        colors_risk = [COLORS['danger'], COLORS['warning'], COLORS['primary'], COLORS['success']]

        bars = plt.bar(range(len(categories)), values, color=colors_risk)
        plt.xticks(range(len(categories)), categories)
        plt.ylabel('Number of Products', fontweight='bold')
        plt.title('Inventory Risk Assessment - Stock Availability Status',
                 fontsize=16, fontweight='bold', pad=20)

        # Add value labels with percentages
        for i, val in enumerate(values):
            pct = (val / len(df)) * 100
            plt.text(i, val + 50, f'{val}\n({pct:.1f}%)', ha='center', fontweight='bold')

        plt.tight_layout()
        plt.savefig('charts/05_stock_risk.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 5: Stock Risk Assessment")

    def chart6_category_performance_matrix(self, df):
        """Chart 6: Category Performance - Volume vs Value"""
        plt.figure(figsize=(14, 9))

        # Calculate metrics per category
        category_metrics = df[df['price'] > 0].groupby('category').agg({
            'price': 'mean',
            'category': 'count'
        }).rename(columns={'category': 'product_count'})

        # Filter categories with at least 10 products for meaningful analysis
        category_metrics = category_metrics[category_metrics['product_count'] >= 10]

        # Top 20 by product count
        top_categories = category_metrics.nlargest(20, 'product_count')

        # Create scatter plot
        scatter = plt.scatter(top_categories['product_count'],
                            top_categories['price'],
                            s=top_categories['product_count'] * 10,
                            c=top_categories['price'],
                            cmap='RdYlGn_r',
                            alpha=0.6,
                            edgecolors='black',
                            linewidth=1.5)

        plt.xlabel('Product Volume (Number of Products)', fontweight='bold', fontsize=12)
        plt.ylabel('Average Price (AZN)', fontweight='bold', fontsize=12)
        plt.title('Category Performance Matrix - Volume vs. Value Opportunity',
                 fontsize=16, fontweight='bold', pad=20)

        # Add category labels for top performers
        for idx, row in top_categories.head(10).iterrows():
            plt.annotate(idx[:25],
                        xy=(row['product_count'], row['price']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, alpha=0.8)

        plt.colorbar(scatter, label='Avg Price (AZN)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('charts/06_category_performance_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 6: Category Performance Matrix")

    def chart7_competitive_positioning(self, df):
        """Chart 7: Competitive Price Positioning"""
        plt.figure(figsize=(14, 8))

        # Compare budget vs premium categories
        category_avg = df[df['price'] > 0].groupby('category')['price'].agg(['mean', 'count'])
        category_avg = category_avg[category_avg['count'] >= 8]

        # Get top 10 cheapest and top 10 most expensive
        cheapest = category_avg.nsmallest(10, 'mean')
        expensive = category_avg.nlargest(10, 'mean')

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # Cheapest categories
        bars1 = ax1.barh(range(len(cheapest)), cheapest['mean'], color=COLORS['success'])
        ax1.set_yticks(range(len(cheapest)))
        ax1.set_yticklabels(cheapest.index)
        ax1.set_xlabel('Average Price (AZN)', fontweight='bold')
        ax1.set_title('Budget-Friendly Categories', fontsize=14, fontweight='bold')
        ax1.invert_yaxis()

        for i, val in enumerate(cheapest['mean']):
            ax1.text(val + 0.05, i, f'{val:.2f}', va='center', fontsize=9)

        # Most expensive categories
        bars2 = ax2.barh(range(len(expensive)), expensive['mean'], color=COLORS['secondary'])
        ax2.set_yticks(range(len(expensive)))
        ax2.set_yticklabels(expensive.index)
        ax2.set_xlabel('Average Price (AZN)', fontweight='bold')
        ax2.set_title('Premium Categories', fontsize=14, fontweight='bold')
        ax2.invert_yaxis()

        for i, val in enumerate(expensive['mean']):
            ax2.text(val + 1, i, f'{val:.2f}', va='center', fontsize=9)

        plt.suptitle('Competitive Price Positioning - Market Segmentation',
                    fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        plt.savefig('charts/07_competitive_positioning.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 7: Competitive Positioning")

    def chart8_revenue_concentration(self, df):
        """Chart 8: Revenue Concentration Analysis"""
        plt.figure(figsize=(14, 7))

        # Calculate potential revenue per category (product count × avg price)
        category_metrics = df[df['price'] > 0].groupby('category').agg({
            'price': ['mean', 'count']
        })
        category_metrics.columns = ['avg_price', 'product_count']
        category_metrics['revenue_potential'] = (
            category_metrics['avg_price'] * category_metrics['product_count']
        )

        # Top 15 by revenue potential
        top_revenue = category_metrics.nlargest(15, 'revenue_potential').sort_values(
            'revenue_potential', ascending=True
        )

        bars = plt.barh(range(len(top_revenue)), top_revenue['revenue_potential'],
                       color=COLORS['primary'])
        plt.yticks(range(len(top_revenue)), top_revenue.index)
        plt.xlabel('Revenue Potential Index (Avg Price × Product Count)', fontweight='bold')
        plt.title('Revenue Concentration - Top 15 Categories by Market Opportunity',
                 fontsize=16, fontweight='bold', pad=20)

        # Add value labels
        for i, val in enumerate(top_revenue['revenue_potential']):
            plt.text(val + 5, i, f'{val:.0f}', va='center', fontweight='bold', fontsize=9)

        plt.tight_layout()
        plt.savefig('charts/08_revenue_concentration.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 8: Revenue Concentration")

    def chart9_discount_impact(self, df):
        """Chart 9: Discount Impact on Average Savings"""
        plt.figure(figsize=(14, 7))

        discounted = df[df['discount_percent'].notna()].copy()
        discounted['savings'] = discounted['original_price'] - discounted['price']

        # Group by category and calculate average savings
        category_savings = discounted.groupby('category').agg({
            'savings': 'mean',
            'discount_percent': 'mean',
            'category': 'count'
        }).rename(columns={'category': 'count'})

        # Filter categories with at least 5 discounted products
        category_savings = category_savings[category_savings['count'] >= 5]
        category_savings = category_savings.nlargest(15, 'savings')

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))

        x = range(len(category_savings))
        bars = ax.barh(x, category_savings['savings'], color=COLORS['warning'])

        ax.set_yticks(x)
        ax.set_yticklabels(category_savings.index)
        ax.set_xlabel('Average Savings per Product (AZN)', fontweight='bold')
        ax.set_title('Promotional Impact - Categories with Highest Average Savings',
                    fontsize=16, fontweight='bold', pad=20)
        ax.invert_yaxis()

        # Add value labels with discount percentage
        for i, (idx, row) in enumerate(category_savings.iterrows()):
            label = f'{row["savings"]:.2f} AZN ({row["discount_percent"]:.0f}% off)'
            ax.text(row['savings'] + 0.1, i, label, va='center', fontsize=9, fontweight='bold')

        plt.tight_layout()
        plt.savefig('charts/09_discount_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 9: Discount Impact")

    def chart10_market_segmentation(self, df):
        """Chart 10: Market Segmentation Overview"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Top-left: Product count by price tier
        bins = [0, 1, 3, 5, 10, 20, 50, 1000]
        labels = ['<1', '1-3', '3-5', '5-10', '10-20', '20-50', '>50']
        df['price_tier'] = pd.cut(df['price'], bins=bins, labels=labels)
        tier_counts = df['price_tier'].value_counts().sort_index()

        axes[0, 0].bar(range(len(tier_counts)), tier_counts.values, color=COLORS['primary'])
        axes[0, 0].set_xticks(range(len(tier_counts)))
        axes[0, 0].set_xticklabels(tier_counts.index)
        axes[0, 0].set_ylabel('Product Count', fontweight='bold')
        axes[0, 0].set_title('Distribution by Price Range (AZN)', fontweight='bold')

        # Top-right: Discount penetration
        discounted_count = df['discount_percent'].notna().sum()
        regular_count = len(df) - discounted_count

        axes[0, 1].bar(['On Promotion', 'Regular Price'],
                      [discounted_count, regular_count],
                      color=[COLORS['warning'], COLORS['neutral']])
        axes[0, 1].set_ylabel('Product Count', fontweight='bold')
        axes[0, 1].set_title('Promotional Penetration', fontweight='bold')

        for i, val in enumerate([discounted_count, regular_count]):
            pct = (val / len(df)) * 100
            axes[0, 1].text(i, val + 50, f'{pct:.1f}%', ha='center', fontweight='bold')

        # Bottom-left: Stock status
        stock_status = {
            'Healthy': len(df[df['stock_qty'] >= 50]),
            'Medium': len(df[(df['stock_qty'] >= 10) & (df['stock_qty'] < 50)]),
            'Low': len(df[(df['in_stock']) & (df['stock_qty'] < 10)]),
            'Out': len(df[~df['in_stock']])
        }

        axes[1, 0].bar(stock_status.keys(), stock_status.values(),
                      color=[COLORS['success'], COLORS['primary'],
                            COLORS['warning'], COLORS['danger']])
        axes[1, 0].set_ylabel('Product Count', fontweight='bold')
        axes[1, 0].set_title('Inventory Health', fontweight='bold')

        # Bottom-right: Top 5 categories
        top5 = df['category'].value_counts().head(5)
        axes[1, 1].barh(range(len(top5)), top5.values, color=COLORS['secondary'])
        axes[1, 1].set_yticks(range(len(top5)))
        axes[1, 1].set_yticklabels(top5.index)
        axes[1, 1].set_xlabel('Product Count', fontweight='bold')
        axes[1, 1].set_title('Top 5 Categories by Volume', fontweight='bold')
        axes[1, 1].invert_yaxis()

        plt.suptitle('Market Segmentation Dashboard', fontsize=18, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig('charts/10_market_segmentation.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Chart 10: Market Segmentation")

    def generate_all_charts(self):
        """Generate all business intelligence charts"""
        print("\n" + "="*80)
        print("GENERATING BUSINESS INTELLIGENCE CHARTS")
        print("="*80 + "\n")

        df = self.normalize_products()

        self.chart1_category_portfolio_value(df)
        self.chart2_pricing_tiers(df)
        self.chart3_premium_categories(df)
        self.chart4_discount_strategy(df)
        self.chart5_stock_risk_assessment(df)
        self.chart6_category_performance_matrix(df)
        self.chart7_competitive_positioning(df)
        self.chart8_revenue_concentration(df)
        self.chart9_discount_impact(df)
        self.chart10_market_segmentation(df)

        print("\n" + "="*80)
        print(f"✓ All charts generated successfully in '{self.charts_dir}/' directory")
        print("="*80)


if __name__ == "__main__":
    bi = BravoBusinessIntelligence()
    bi.generate_all_charts()
