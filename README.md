# Supermarket Food Data Scraper

A complete solution for scraping food price and product data from supermarket mobile apps using mitmproxy and iOS device.

## Quick Links

- **[Wolt Bravo Scraper Guide](WOLT_BRAVO_GUIDE.md)** - Complete guide for scraping Bravo supermarket on Wolt
- **General scraping tools** - Works with any supermarket app (see below)

## Setup

### 1. Install Requirements

```bash
pip install mitmproxy requests
```

### 2. Configure iOS Device

1. Start mitmproxy to get your computer's IP address:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. On your iOS device:
   - Go to Settings > Wi-Fi
   - Tap the (i) icon next to your connected network
   - Scroll down to "HTTP Proxy"
   - Select "Manual"
   - Server: Your computer's IP address
   - Port: 8080

3. Install mitmproxy certificate:
   - Open Safari on iOS and go to: http://mitm.it
   - Tap on the Apple icon to download the certificate
   - Go to Settings > General > VPN & Device Management
   - Install the mitmproxy certificate
   - Go to Settings > General > About > Certificate Trust Settings
   - Enable full trust for mitmproxy certificate

## Usage

### Step 1: Capture API Traffic

Start mitmproxy with the capture script:

```bash
mitmdump -s mitm_capture.py
```

Now open the supermarket app on your iOS device and:
- Browse products
- Search for items
- View categories
- Check prices

The script will automatically capture and save all food-related API requests to `captured_requests.json`.

Press Ctrl+C to stop capturing.

### Step 2: Analyze Captured Data

Analyze the captured API calls to understand the data structure:

```bash
python3 analyze_data.py
```

This will:
- Show all API endpoints found
- Display response structures
- Extract and save products to `products.json`

### Step 3: Automated Scraping

Once you understand the API patterns, use the scraper for automated data collection:

```bash
python3 scraper.py
```

The scraper will:
- Generate a configuration from captured requests
- Automatically call all discovered endpoints
- Extract and normalize product data
- Save results to:
  - `scraped_products.json` (full data)
  - `products.csv` (spreadsheet format)

## Files

- `mitm_capture.py` - Mitmproxy addon to capture API requests
- `analyze_data.py` - Analyze and extract data from captures
- `scraper.py` - Automated scraper using discovered APIs
- `captured_requests.json` - Raw captured API calls
- `products.json` - Extracted products from captures
- `scraper_config.json` - Generated scraper configuration
- `scraped_products.json` - Final scraped data
- `products.csv` - Products in CSV format

## Customization

### Modify Capture Keywords

Edit `mitm_capture.py` and update the `food_keywords` list:

```python
self.food_keywords = [
    'product', 'item', 'food', 'grocery', 'price',
    'catalog', 'search', 'menu', 'inventory'
]
```

### Adjust Product Extraction

Edit `scraper.py` in the `_normalize_product()` method to match your API's field names.

## Tips

1. **Start small**: Capture just a few products first to understand the API structure
2. **Check rate limits**: Some APIs may rate limit requests
3. **Authentication**: If the app requires login, make sure to authenticate in the app before capturing
4. **Headers**: The scraper copies headers from captured requests, including auth tokens
5. **Offline mode**: Once configured, the scraper works without the iOS device

## Troubleshooting

### No requests captured
- Verify iOS proxy settings
- Ensure certificate is trusted
- Check if app uses certificate pinning (this blocks mitmproxy)

### Empty product data
- Run `analyze_data.py` to inspect response structures
- Adjust extraction logic in `scraper.py`

### API requires authentication
- Login in the app while capturing
- The auth tokens will be saved in headers

### Certificate pinning
If the app uses certificate pinning, mitmproxy won't work. Alternative approaches:
- Use a jailbroken device with SSL Kill Switch
- Decompile and patch the app
- Contact the supermarket for official API access
