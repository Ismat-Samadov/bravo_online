#!/usr/bin/env python3
"""
Mitmproxy addon script to capture and analyze supermarket app API requests.
This script will automatically save food-related API requests to a JSON file.
"""

import json
import re
from datetime import datetime
from mitmproxy import http
from pathlib import Path


class SupermarketCapture:
    def __init__(self):
        self.captured_data = []
        self.output_file = Path("captured_requests.json")
        self.food_keywords = [
            'product', 'item', 'food', 'grocery', 'price',
            'catalog', 'search', 'menu', 'inventory'
        ]

    def request(self, flow: http.HTTPFlow) -> None:
        """Called when a request is made"""
        pass

    def response(self, flow: http.HTTPFlow) -> None:
        """Called when a response is received"""
        # Check if this is a potential food/product API endpoint
        url = flow.request.pretty_url

        # Check if URL contains food-related keywords
        is_food_related = any(keyword in url.lower() for keyword in self.food_keywords)

        # Also check if response is JSON
        content_type = flow.response.headers.get("content-type", "")
        is_json = "json" in content_type.lower()

        if is_food_related or (is_json and flow.response.status_code == 200):
            try:
                # Try to parse response as JSON
                response_data = flow.response.text
                json_data = json.loads(response_data)

                # Capture request details
                capture = {
                    "timestamp": datetime.now().isoformat(),
                    "method": flow.request.method,
                    "url": url,
                    "host": flow.request.host,
                    "path": flow.request.path,
                    "status_code": flow.response.status_code,
                    "request_headers": dict(flow.request.headers),
                    "response_headers": dict(flow.response.headers),
                    "request_body": flow.request.text if flow.request.text else None,
                    "response_body": json_data,
                    "size": len(response_data)
                }

                self.captured_data.append(capture)

                # Save to file after each capture
                self._save_data()

                print(f"✓ Captured: {flow.request.method} {url}")

            except json.JSONDecodeError:
                # Not JSON, skip
                pass
            except Exception as e:
                print(f"Error capturing request: {e}")

    def _save_data(self):
        """Save captured data to JSON file"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.captured_data, f, indent=2, ensure_ascii=False)

    def done(self):
        """Called when mitmproxy shuts down"""
        print(f"\n📊 Total requests captured: {len(self.captured_data)}")
        print(f"💾 Data saved to: {self.output_file}")


addons = [SupermarketCapture()]
