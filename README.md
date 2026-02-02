# Contact Scraper v2.0

Extract emails and phone numbers from websites listed in Excel/CSV files.

## Features

✅ **Robust Phone Extraction**
- Extracts from `tel:` links (priority)
- Recognizes French formats: `+33 4 91 54 19 52`, `04 91 54 19 52`, `0491541952`
- Normalizes to E.164 format (`+33491541952`)
- **Filters GPS coordinates** and numeric IDs automatically
- Handles spaces, dots, parentheses, non-breaking spaces

✅ **Smart Crawling**
- Checks homepage first
- Follows contact/about/legal pages automatically
- **Early stopping** when email + phone found
- HTTP fallback if HTTPS fails
- Rate limiting to be polite

✅ **Email Extraction**
- Extracts from `mailto:` links
- Pattern matching in page text
- Deduplication

---

## Quick Start

### 1. Install Python
- Download from: https://www.python.org/downloads/
- ✅ **Check "Add Python to PATH"** during installation

### 2. Install Packages
Open Command Prompt and run:
```bash
pip install pandas openpyxl requests beautifulsoup4 lxml
```

### 3. Run the Scraper
**Option A (Easy):** Double-click `RUN_SCRAPER.bat`

**Option B (Manual):** 
```bash
python contact_scraper.py
```

Then follow the prompts:
1. Enter filename (e.g., `hotels.xlsx`)
2. Enter URL column name (e.g., `SITE INTERNET`)
3. Press Enter for automatic output filename

---

## Input Format

Your spreadsheet needs a column with URLs. They can be:
- `https://www.example.com` (full URL)
- `www.example.com` (auto-adds https://)
- `example.com` (auto-adds https://)

Example:
```
SITE INTERNET
https://www.hotel-aubrac.fr/
www.lemoulindemoisac.com
hotel-example.fr
```

---

## Output Format

The script creates a new file with **3 additional columns**:

| Column | Description | Example |
|--------|-------------|---------|
| **Emails** | Found email addresses | `contact@hotel.fr; info@hotel.fr` |
| **Phone_Numbers** | Normalized phones (E.164) | `+33491541952; +33612345678` |
| **Scrape_Status** | Result status | `Success`, `NoContactsFound`, `Timeout` |

### Status Values
- `Success` - At least 1 email or phone found
- `NoContactsFound` - No contacts found
- `ConnectionError` - Could not connect to site
- `HTTPError-404` - Page not found (or other HTTP error)
- `Timeout` - Site too slow to respond
- `ParseError` - Could not parse page
- `EmptyURL` - No URL provided

---

## Phone Number Filtering

### ✅ Valid Phones
```
+33 4 91 54 19 52  →  +33491541952
04 91 54 19 52     →  +33491541952
0491541952         →  +33491541952
06.12.34.56.78     →  +33612345678
```

### ❌ Filtered Out
```
43.296086          (GPS latitude)
5.378054           (GPS longitude)
12345              (too short)
00000000000        (all same digit)
12345678           (sequential)
```

The scraper intelligently detects:
- GPS coordinates (decimal numbers with 4+ decimals)
- Text near "latitude", "longitude", "coords", "GPS"
- Generic numeric IDs
- Invalid phone lengths

---

## Contact Page Keywords

The scraper looks for these keywords in links:
- `contact`, `nous-contacter`, `contactez-nous`
- `about`, `a-propos`, `qui-sommes-nous`
- `mentions-legales`, `legal`, `impressum`
- `privacy`, `politique`, `confidentialite`

---

## Configuration

Edit these values at the top of `contact_scraper.py`:

```python
TIMEOUT = 15              # Seconds to wait per page
DELAY = 2                 # Seconds between requests
MAX_CONTACT_PAGES = 3     # Max contact pages to check per site
```

---

## Testing

A test file `test_urls.csv` is included with 10 sample URLs covering:
- Sites with `tel:` links
- Sites with phone in text
- Sites with GPS coordinates (to test filtering)
- Major hotel chains (may block bots)

Run test:
```bash
python contact_scraper.py
# Enter: test_urls.csv
# Enter: SITE INTERNET
```

---

## Troubleshooting

**"Python is not recognized"**
- Reinstall Python with "Add to PATH" checked
- Or use full path: `C:\Python310\python.exe contact_scraper.py`

**"ModuleNotFoundError: No module named 'pandas'"**
- Run: `pip install pandas openpyxl requests beautifulsoup4 lxml`

**"Permission denied" when saving**
- Close Excel before running the script

**Many Timeout/ConnectionError results**
- Some sites block automated requests
- Increase `TIMEOUT` in the script
- Try again later (sites may be temporarily down)

**GPS coordinates appearing as phone numbers**
- This should be fixed in v2.0
- If you still see issues, report the URL

**No contacts found on sites you know have them**
- Contact info may be in images or JavaScript
- The scraper only reads visible HTML text
- Some sites load contacts dynamically (JavaScript)

---

## Performance

Approximate times (with 2-second delay):
- 10 URLs: ~1-2 minutes
- 50 URLs: ~5-8 minutes  
- 100 URLs: ~10-15 minutes
- 500 URLs: ~45-60 minutes

**Tip:** For 500+ URLs, split into multiple files and run in parallel.

---

## Legal Notice

**This tool is for legitimate business use only.**

✅ **Acceptable use:**
- Collecting publicly visible contact information
- Legitimate business outreach
- Market research with proper consent

❌ **Not acceptable:**
- Spam or harassment
- Violating website Terms of Service
- Collecting data for sale without permission
- Ignoring GDPR/privacy laws

**You are responsible for:**
- Complying with GDPR (Europe) and privacy laws
- Respecting website Terms of Service
- Only contacting businesses for legitimate purposes
- Maintaining ethical data collection practices

---

## Files Included

- `contact_scraper.py` - Main script
- `RUN_SCRAPER.bat` - Windows launcher
- `test_urls.csv` - Test data (10 URLs)
- `README.md` - This file

---

## Version History

**v2.0** (Current)
- Robust phone validation with GPS filtering
- E.164 normalization for French numbers
- Priority for `tel:` links
- Early stopping optimization
- Improved contact page detection
- HTTP fallback support

**v1.0**
- Initial release

---

## Support

For issues or questions:
1. Check this README thoroughly
2. Verify Python and packages are installed
3. Test with `test_urls.csv` first
4. Check your input file format

---

**Happy scraping! 🚀**
