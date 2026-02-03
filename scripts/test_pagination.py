#!/usr/bin/env python3
"""
Test script to verify we can get ALL products with pagination
"""

import json
import requests

def test_search_pagination():
    """Test if search API supports pagination"""
    url = "https://consumer-api.wolt.com/consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment/items/search"

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Test 1: Basic search
    print("Test 1: Basic search with limit=500")
    print("-" * 80)

    payload = {
        "search_phrase": "",
        "limit": 500
    }

    response = requests.post(url, json=payload, headers=headers, params={'language': 'en'}, timeout=30)
    data = response.json()

    items = data.get('items', [])
    print(f"Items returned: {len(items)}")
    print(f"Response keys: {list(data.keys())}")

    # Check for pagination indicators
    pagination_keys = [k for k in data.keys() if any(word in k.lower() for word in ['offset', 'next', 'page', 'cursor', 'skip', 'token', 'continuation'])]
    print(f"Pagination keys found: {pagination_keys}")

    if items:
        print(f"\nFirst item ID: {items[0].get('id')}")
        print(f"Last item ID: {items[-1].get('id')}")

    # Test 2: Try with offset parameter
    print("\n" + "="*80)
    print("Test 2: Try with offset parameter")
    print("-" * 80)

    payload_with_offset = {
        "search_phrase": "",
        "limit": 500,
        "offset": 500
    }

    response2 = requests.post(url, json=payload_with_offset, headers=headers, params={'language': 'en'}, timeout=30)
    data2 = response2.json()
    items2 = data2.get('items', [])

    print(f"Items returned with offset=500: {len(items2)}")

    if items2:
        print(f"First item ID: {items2[0].get('id')}")
        # Check if different from first batch
        first_batch_ids = {item.get('id') for item in items}
        second_batch_ids = {item.get('id') for item in items2}
        overlap = first_batch_ids & second_batch_ids
        print(f"Overlap with first batch: {len(overlap)} items")
        print(f"New items in second batch: {len(second_batch_ids - first_batch_ids)}")

    # Test 3: Try different limit values
    print("\n" + "="*80)
    print("Test 3: Try different limit values")
    print("-" * 80)

    for limit in [100, 500, 1000, 2000]:
        payload = {"search_phrase": "", "limit": limit}
        response = requests.post(url, json=payload, headers=headers, params={'language': 'en'}, timeout=30)
        data = response.json()
        items = data.get('items', [])
        print(f"Limit={limit:4}: {len(items)} items returned")

    # Test 4: Check category filtering
    print("\n" + "="*80)
    print("Test 4: Try with category filter")
    print("-" * 80)

    payload_with_category = {
        "search_phrase": "",
        "limit": 500,
        "category_id": "dbfe806ec1c2deda35f24e09"  # Fruits category
    }

    response3 = requests.post(url, json=payload_with_category, headers=headers, params={'language': 'en'}, timeout=30)
    data3 = response3.json()
    items3 = data3.get('items', [])
    print(f"Items with category filter: {len(items3)}")

    # Test 5: Check the full assortment to see if it lists item_ids
    print("\n" + "="*80)
    print("Test 5: Check assortment for item_ids")
    print("-" * 80)

    assortment_url = "https://consumer-api.wolt.com/consumer-api/consumer-assortment/v1/venues/slug/bravo-storefront/assortment"
    response4 = requests.get(assortment_url, headers=headers, timeout=30)
    assortment = response4.json()

    # Count total item_ids in categories
    def count_item_ids(categories):
        total = 0
        for cat in categories:
            item_ids = cat.get('item_ids', [])
            total += len(item_ids)
            if cat.get('subcategories'):
                total += count_item_ids(cat['subcategories'])
        return total

    total_item_ids = count_item_ids(assortment.get('categories', []))
    print(f"Total item_ids in category structure: {total_item_ids}")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS:")
    print("-" * 80)

    if total_item_ids > 0:
        print(f"✓ The assortment lists {total_item_ids} item IDs in categories")
        print("  BEST APPROACH: Extract all item_ids from categories, then fetch in batches")
    else:
        print("✗ Categories don't list item_ids directly")

    if len(items2) > 0 and len(second_batch_ids - first_batch_ids) > 0:
        print("✓ Offset pagination works! Use offset to get all products")
    else:
        print("✗ Offset pagination might not work or no more items")

    print(f"\nMax items per request: ~{max(len(items), 500)}")


if __name__ == "__main__":
    test_search_pagination()
