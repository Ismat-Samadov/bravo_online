#!/bin/bash

# Supermarket App Traffic Capture Script

echo "🚀 Supermarket Food Data Scraper"
echo "================================"
echo ""

# Get local IP address
echo "📱 iOS Device Setup:"
echo "-------------------"
echo "1. On your iOS device, go to Settings > Wi-Fi"
echo "2. Tap (i) next to your network"
echo "3. Configure HTTP Proxy:"
echo ""
echo "   Server: $(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')"
echo "   Port: 8080"
echo ""
echo "4. Install certificate from: http://mitm.it"
echo ""
echo "Press Enter when ready to start capturing..."
read

echo ""
echo "🔄 Starting mitmproxy capture..."
echo "Open the supermarket app and browse products"
echo "Press Ctrl+C when done capturing"
echo ""

mitmdump -s mitm_capture.py
