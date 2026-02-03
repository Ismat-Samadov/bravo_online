# Wolt Bravo Supermarket Scraper - Complete Guide

## Overview

This is a comprehensive solution for scraping **all food data** from Bravo Supermarket on Wolt platform for **marketing analysis**. The system includes:

1. **Category scraping** - All 223 categories and subcategories
2. **Product scraping** - All products with prices, images, availability
3. **Marketing analysis** - Pricing insights, category distribution, recommendations

## Quick Start (3 Methods)

### Method 1: Direct API Scraping (Recommended)

Use the complete scraper that directly calls Wolt's API:

```bash
python3 wolt_complete_scraper.py
```

This will:
- Scrape all 223 categories
- Scrape all products (using search API)
- Save everything to JSON and CSV
- No iOS device needed!

**Time:** ~2-5 minutes depending on product count

### Method 2: Using Captured Data

If you already captured data with mitmproxy:

```bash
# Analyze captured requests
python3 wolt_analyze.py
```

This extracts products from previously captured traffic.

### Method 3: Live Traffic Capture

Capture traffic from iOS Wolt app:

```bash
# Start capture
mitmdump -s wolt_capture.py

# Browse products in Wolt app
# Then analyze
python3 wolt_analyze.py
```

## Detailed Instructions

### Step 1: Scrape All Data

```bash
python3 wolt_complete_scraper.py
```

**What it does:**
- Fetches category structure from: `/consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment`
- Scrapes products using: `/consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment/items/search`
- Uses two strategies:
  1. Empty search query to get products in batches of 500
  2. Category-based search to ensure complete coverage
- Deduplicates all products
- Saves to JSON and CSV

**Output:**
- `bravo_categories_complete.json` - All 223 categories
- `bravo_products_raw.json` - All products (raw API format)
- `bravo_products_raw.csv` - Products in CSV

### Step 2: Marketing Analysis

```bash
python3 wolt_analyze.py
```

**What it analyzes:**

#### 1. Pricing Analysis
- Average, median, min, max prices
- Price distribution (under 1 AZN, 1-5 AZN, etc.)
- Discount statistics
- Top discounted products

#### 2. Category Analysis
- Top 20 categories by product count
- Average price by category
- Most expensive categories
- Category hierarchy

#### 3. Availability Analysis
- Stock status overview
- Out-of-stock items by category
- Availability percentages

#### 4. Marketing Insights
- High-value opportunities (premium products)
- Discount optimization recommendations
- Category focus suggestions
- Optimal price point analysis
- Stock alerts for marketing

**Output:**
- `bravo_products_full.json` - Normalized product data
- `bravo_products.csv` - Clean CSV export
- `marketing_report.txt` - Complete analysis report
- Console output with visualizations

### Step 3: Use the Data

The scraped data includes:

**For each product:**
```json
{
  "id": "product_id",
  "name": "Product Name",
  "price": 5.99,
  "original_price": 7.99,
  "discount": 25.0,
  "category_name": "Meyvələr",
  "category_path": "Meyvə və Tərəvəz Məhsulları/Meyvələr",
  "description": "Product description",
  "image_url": "https://...",
  "available": true,
  "in_stock": true,
  "unit": "kg",
  "weight": "1 kg"
}
```

**For each category:**
```json
{
  "id": "category_id",
  "name": "Category Name",
  "slug": "category-slug",
  "path": "Parent/Child",
  "level": 1,
  "image_url": "https://..."
}
```

## API Endpoints Discovery

### Main Endpoints

1. **Assortment (Categories)**
   ```
   GET /consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment
   ```
   Returns: Category tree, metadata

2. **Items Search**
   ```
   POST /consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment/items/search?language=az
   Body: {"search_phrase": "", "limit": 500}
   ```
   Returns: Products (500 per request)

3. **Items by ID**
   ```
   POST /consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment/items
   Body: {"item_ids": ["id1", "id2", ...], "language": "en"}
   ```
   Returns: Specific products

## Marketing Use Cases

### 1. Price Monitoring

Track competitor prices and market trends:

```bash
# Run daily
python3 wolt_complete_scraper.py
mv bravo_products_raw.json "products_$(date +%Y%m%d).json"
```

Compare prices over time to identify:
- Price changes
- New discounts
- Stock changes
- New products

### 2. Category Analysis

Identify top-performing categories:

```python
# Load data
import json
with open('bravo_products_full.json') as f:
    data = json.load(f)
    products = data['products']

# Count by category
from collections import Counter
categories = Counter(p['category_name'] for p in products if p['category_name'])
top_categories = categories.most_common(10)
```

### 3. Discount Opportunities

Find products on sale for promotion:

```python
# Get discounted products
discounted = [p for p in products if p['discount'] and p['discount'] > 20]
top_deals = sorted(discounted, key=lambda x: x['discount'], reverse=True)[:20]
```

### 4. Stock Monitoring

Track availability for inventory management:

```python
# Out of stock items
oos = [p for p in products if not p['in_stock']]
print(f"Out of stock: {len(oos)} items")

# By category
from collections import defaultdict
oos_by_cat = defaultdict(list)
for p in oos:
    oos_by_cat[p['category_name']].append(p['name'])
```

### 5. Price Positioning

Compare your prices with Bravo:

```python
# Average price by category
category_prices = defaultdict(list)
for p in products:
    if p['price'] and p['category_name']:
        category_prices[p['category_name']].append(p['price'])

avg_prices = {cat: sum(prices)/len(prices)
              for cat, prices in category_prices.items()}
```

## Advanced Features

### Custom Search Queries

Search for specific products:

```python
from wolt_complete_scraper import WoltCompleteScraper

scraper = WoltCompleteScraper()
dairy_products = scraper.search_items(query="süd", limit=100)
print(f"Found {len(dairy_products)} dairy products")
```

### Category-Specific Scraping

Scrape only certain categories:

```python
scraper = WoltCompleteScraper()
scraper.get_categories()

# Get fruit category
fruits = [c for c in scraper.all_categories if 'Meyvə' in c['name']]
print(f"Found {len(fruits)} fruit-related categories")
```

### Language Options

Available languages: `az` (Azerbaijani), `en` (English), `ru` (Russian)

```python
# Get products in English
items = scraper.search_items(query="", language="en")
```

## File Structure

```
bravo_online/
├── wolt_complete_scraper.py     # Complete scraper (recommended)
├── wolt_bravo_scraper.py        # Category-focused scraper
├── wolt_capture.py              # Mitmproxy capture addon
├── wolt_analyze.py              # Marketing analysis tool
├── WOLT_BRAVO_GUIDE.md          # This guide
│
├── bravo_categories_complete.json  # All categories
├── bravo_products_raw.json        # Raw product data
├── bravo_products_full.json       # Normalized products
├── bravo_products.csv             # CSV export
└── marketing_report.txt           # Analysis report
```

## API Rate Limiting

Wolt's API is generally permissive but follow these guidelines:

- Add delays between requests: `time.sleep(0.5)`
- Don't hammer the API (we use batches of 500)
- If you get rate limited (429), increase delays
- The complete scraper includes built-in rate limiting

## Troubleshooting

### Issue: No products returned

**Solution:**
```bash
# Try with captured data instead
mitmdump -s wolt_capture.py
# Browse products in app
python3 wolt_analyze.py
```

### Issue: SSL/Certificate errors

**Solution:**
```python
# Disable SSL verification (not recommended for production)
import urllib3
urllib3.disable_warnings()
```

### Issue: Empty categories

**Possible causes:**
- API structure changed
- Network issues
- Rate limiting

**Solution:**
```bash
# Check API directly
curl "https://consumer-api.wolt.com/consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment"
```

## Data Schema

### Product Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique product ID |
| `name` | string | Product name |
| `price` | float | Current price (AZN) |
| `original_price` | float | Original price before discount |
| `discount` | float | Discount percentage |
| `category_name` | string | Category name |
| `category_path` | string | Full category path |
| `description` | string | Product description |
| `image_url` | string | Product image URL |
| `available` | boolean | Is product available |
| `in_stock` | boolean | Is product in stock |
| `unit` | string | Unit of measurement |
| `weight` | string | Product weight |

### Category Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Category ID |
| `name` | string | Category name |
| `slug` | string | URL-friendly slug |
| `path` | string | Full category path |
| `level` | int | Hierarchy level (0=main) |
| `image_url` | string | Category image |

## Integration Examples

### Export to Google Sheets

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load data
with open('bravo_products.csv') as f:
    # Upload to Google Sheets
    # (requires Google API credentials)
```

### Power BI / Tableau

Import the CSV files directly:
- `bravo_products.csv` - Main product table
- `bravo_categories.csv` - Category lookup

### Database Import

PostgreSQL example:
```sql
CREATE TABLE products (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    price DECIMAL(10,2),
    category_name VARCHAR,
    ...
);

COPY products FROM 'bravo_products.csv' CSV HEADER;
```

## Best Practices

1. **Schedule regular scrapes**
   - Daily for price monitoring
   - Weekly for inventory analysis
   - Monthly for trend analysis

2. **Store historical data**
   - Keep timestamped snapshots
   - Track price changes over time
   - Identify seasonal patterns

3. **Respect the API**
   - Add delays between requests
   - Don't scrape more often than needed
   - Cache results locally

4. **Validate data**
   - Check for missing prices
   - Verify category mappings
   - Monitor data quality

## Marketing Insights

The analysis tool provides actionable insights:

1. **High-Value Opportunities**
   - Premium products (>20 AZN)
   - Perfect for targeted marketing
   - Higher profit margins

2. **Discount Optimization**
   - Current discount strategies
   - Average discount percentages
   - Most discounted categories

3. **Category Focus**
   - Top categories by product count
   - Customer interest indicators
   - Cross-selling opportunities

4. **Price Positioning**
   - Median price points
   - Competitive pricing data
   - Sweet spot identification

5. **Stock Alerts**
   - Out-of-stock items
   - Restock marketing opportunities
   - Back-in-stock notifications

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the code comments
3. Test with small samples first
4. Check API responses directly with `curl`

## Updates

The API structure may change. If scrapers stop working:
1. Use mitmproxy to capture current API calls
2. Update endpoint URLs in scrapers
3. Adjust data extraction logic if needed

---

**Last Updated:** 2026-02-03
**API Version:** Wolt Consumer API v1
**Data Source:** Bravo Supermarket via Wolt Platform
