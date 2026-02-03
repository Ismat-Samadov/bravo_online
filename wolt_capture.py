#!/usr/bin/env python3
"""
Specialized Mitmproxy addon for capturing Wolt Bravo API requests
Focuses on finding product/item endpoints
"""

import json
import re
from datetime import datetime
from mitmproxy import http
from pathlib import Path


class WoltCapture:
    def __init__(self):
        self.captured_data = []
        self.output_file = Path("wolt_captured.json")
        self.items_found = 0

    def request(self, flow: http.HTTPFlow) -> None:
        """Called when a request is made"""
        pass

    def response(self, flow: http.HTTPFlow) -> None:
        """Called when a response is received"""
        url = flow.request.pretty_url
        host = flow.request.host

        # Only capture Wolt API requests
        if 'wolt.com' not in host:
            return

        # Check if response is JSON
        content_type = flow.response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            return

        try:
            response_data = flow.response.text
            json_data = json.loads(response_data)

            # Check if this response contains items/products
            has_items = self._contains_items(json_data)

            # Capture request details
            capture = {
                "timestamp": datetime.now().isoformat(),
                "method": flow.request.method,
                "url": url,
                "host": host,
                "path": flow.request.path,
                "status_code": flow.response.status_code,
                "has_items": has_items,
                "request_headers": dict(flow.request.headers),
                "request_query": dict(flow.request.query),
                "request_body": flow.request.text if flow.request.text else None,
                "response_body": json_data,
                "response_size": len(response_data)
            }

            self.captured_data.append(capture)

            # Special logging for items
            if has_items:
                items_count = self._count_items(json_data)
                self.items_found += items_count
                print(f"🎯 ITEMS FOUND: {flow.request.method} {url}")
                print(f"   └─ {items_count} products")
            else:
                print(f"✓ Captured: {flow.request.method} {flow.request.path}")

            # Save after each capture
            self._save_data()

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error capturing request: {e}")

    def _contains_items(self, data: any) -> bool:
        """Check if response contains product items"""
        if isinstance(data, dict):
            # Check for common item keys
            if 'items' in data and isinstance(data['items'], list) and len(data['items']) > 0:
                # Verify items look like products
                first_item = data['items'][0] if data['items'] else {}
                if isinstance(first_item, dict):
                    # Check if item has product-like fields
                    product_fields = {'name', 'price', 'baseprice', 'id', 'description'}
                    if any(field in first_item for field in product_fields):
                        return True

            # Check nested structures
            for value in data.values():
                if self._contains_items(value):
                    return True

        elif isinstance(data, list):
            for item in data:
                if self._contains_items(item):
                    return True

        return False

    def _count_items(self, data: any, counted=None) -> int:
        """Count the number of product items in response"""
        if counted is None:
            counted = set()

        count = 0

        if isinstance(data, dict):
            if 'items' in data and isinstance(data['items'], list):
                for item in data['items']:
                    if isinstance(item, dict) and 'id' in item:
                        item_id = item['id']
                        if item_id not in counted:
                            counted.add(item_id)
                            count += 1

            # Check nested structures
            for value in data.values():
                count += self._count_items(value, counted)

        elif isinstance(data, list):
            for item in data:
                count += self._count_items(item, counted)

        return count

    def _save_data(self):
        """Save captured data to JSON file"""
        # Sort by has_items (items first)
        sorted_data = sorted(self.captured_data, key=lambda x: x['has_items'], reverse=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=2, ensure_ascii=False)

    def done(self):
        """Called when mitmproxy shuts down"""
        print(f"\n{'='*80}")
        print(f"📊 Capture Summary")
        print(f"{'='*80}")
        print(f"Total requests captured: {len(self.captured_data)}")
        print(f"Total items found: {self.items_found}")

        # Show requests with items
        requests_with_items = [c for c in self.captured_data if c['has_items']]
        if requests_with_items:
            print(f"\n🎯 Requests with items ({len(requests_with_items)}):")
            for req in requests_with_items:
                items_count = self._count_items(req['response_body'])
                print(f"   • {req['method']} {req['path']}")
                print(f"     └─ {items_count} items")

        print(f"\n💾 Data saved to: {self.output_file}")
        print(f"\nNext steps:")
        print(f"1. Run: python3 wolt_analyze.py")
        print(f"2. This will extract all products and create marketing reports")


addons = [WoltCapture()]
