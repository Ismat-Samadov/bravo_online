#!/bin/bash

# Bravo Supermarket Data Update Script
# This script runs the complete data collection and analysis workflow

echo "=========================================="
echo "Bravo Supermarket Data Update"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check and install dependencies
echo "🔄 Checking dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies ready"
echo ""

# Step 1: Scrape data
echo "=========================================="
echo "Step 1: Scraping Latest Product Data"
echo "=========================================="
python3 scripts/wolt_scraper_complete.py
echo ""

# Check if scraping was successful
if [ ! -f "data/bravo_products_complete.json" ]; then
    echo "❌ Error: Scraping failed - no data file created"
    exit 1
fi

# Step 2: Generate charts
echo "=========================================="
echo "Step 2: Generating Business Charts"
echo "=========================================="
python3 generate_charts.py
echo ""

# Step 3: Generate marketing report (optional)
echo "=========================================="
echo "Step 3: Generating Marketing Analysis"
echo "=========================================="
python3 scripts/wolt_marketing_analysis.py
echo ""

# Summary
echo "=========================================="
echo "✓ Update Complete!"
echo "=========================================="
echo ""
echo "Generated files:"
echo "  📊 data/bravo_products_complete.json"
echo "  📊 data/bravo_categories_complete.json"
echo "  📈 charts/*.png (10 charts)"
echo "  📄 data/bravo_marketing_report.txt"
echo ""
echo "View the business report: README.md"
echo "View the charts: charts/ directory"
echo ""
