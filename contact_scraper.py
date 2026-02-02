"""
Website Email & Phone Number Scraper
Extracts contact information from websites with robust phone validation
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
import sys

# Configuration
TIMEOUT = 15
DELAY = 2
MAX_CONTACT_PAGES = 3

def normalize_url(url):
    """Add https:// scheme, fallback to http:// if needed"""
    url = str(url).strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def extract_emails_from_html(soup, text):
    """Extract emails from mailto links and text"""
    emails = set()
    
    # Extract from mailto links
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0].strip()
            if '@' in email:
                emails.add(email.lower())
    
    # Extract from text using regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    found = re.findall(email_pattern, text)
    emails.update([e.lower() for e in found])
    
    return list(emails)

def is_gps_coordinate(text):
    """Check if text looks like GPS coordinates"""
    # Match patterns like: 43.296086, 5.378054 or (43.296, 5.378)
    gps_pattern = r'[-+]?\d{1,3}\.\d{4,}'
    matches = re.findall(gps_pattern, text)
    
    if len(matches) >= 2:
        return True
    
    # Check for lat/lon keywords nearby
    if re.search(r'(latitude|longitude|lat|lon|coords?|gps)', text.lower()):
        return True
    
    return False

def normalize_phone_to_e164(phone):
    """Normalize French phone to E.164 format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Too short or too long
    if len(digits) < 9 or len(digits) > 15:
        return None
    
    # French number starting with 0 (10 digits)
    if len(digits) == 10 and digits.startswith('0'):
        return '+33' + digits[1:]
    
    # Already has country code
    if digits.startswith('33') and len(digits) == 11:
        return '+' + digits
    
    # International format
    if len(digits) >= 10 and (digits.startswith('1') or digits.startswith('2') or 
                               digits.startswith('3') or digits.startswith('4') or
                               digits.startswith('5') or digits.startswith('6') or
                               digits.startswith('7') or digits.startswith('8') or
                               digits.startswith('9')):
        if not digits.startswith('33'):
            return '+' + digits
    
    return '+' + digits if len(digits) >= 10 else None

def extract_phones_from_html(soup, text):
    """Extract and validate phone numbers with GPS filtering"""
    phones = set()
    
    # Priority: tel links
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('tel:'):
            phone = href.replace('tel:', '').strip()
            normalized = normalize_phone_to_e164(phone)
            if normalized:
                phones.add(normalized)
    
    # If we found tel links, prefer those
    if phones:
        return list(phones)
    
    # Extract from text - multiple French formats
    # Split text into chunks to avoid GPS coordinates
    chunks = text.split('\n')
    
    patterns = [
        r'\+33\s*[1-9](?:[\s.-]*\d{2}){4}',  # +33 4 91 54 19 52
        r'0[1-9](?:[\s.-]*\d{2}){4}',        # 04 91 54 19 52
        r'\b0[1-9]\d{8}\b',                   # 0491541952
    ]
    
    for chunk in chunks:
        # Skip chunks that look like GPS coordinates
        if is_gps_coordinate(chunk):
            continue
        
        # Skip chunks with typical GPS markers
        if re.search(r'(°|latitude|longitude|coords)', chunk.lower()):
            continue
        
        for pattern in patterns:
            matches = re.findall(pattern, chunk)
            for match in matches:
                # Additional validation
                clean_match = re.sub(r'\D', '', match)
                
                # Reject if it looks like a decimal number
                if '.' in match or ',' in match:
                    # Check if it's like "5.378054" (GPS)
                    if re.match(r'\d+\.\d{4,}', match.replace(',', '.')):
                        continue
                
                # Reject short numbers (likely IDs)
                if len(clean_match) < 9:
                    continue
                
                # Must start with 0 or + for French
                if not match.strip().startswith(('+', '0')):
                    continue
                
                normalized = normalize_phone_to_e164(match)
                if normalized:
                    phones.add(normalized)
    
    # Filter out numbers that are too similar to each other (likely IDs)
    filtered_phones = []
    for phone in phones:
        digits = re.sub(r'\D', '', phone)
        # Reject if all digits are the same (11111111)
        if len(set(digits)) == 1:
            continue
        # Reject if it's a sequence (12345678)
        if digits in '0123456789' * 2:
            continue
        filtered_phones.append(phone)
    
    return filtered_phones

def find_contact_page_links(soup, base_url):
    """Find links to contact-type pages"""
    contact_keywords = [
        'contact', 'nous-contacter', 'contactez', 'contactez-nous',
        'about', 'a-propos', 'qui-sommes-nous',
        'mentions-legales', 'mentions', 'legal', 'impressum',
        'privacy', 'politique', 'confidentialite'
    ]
    
    contact_urls = []
    base_domain = urlparse(base_url).netloc
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').lower()
        text = link.get_text().lower()
        
        # Check URL and link text
        for keyword in contact_keywords:
            if keyword in href or keyword in text.replace(' ', '-'):
                full_url = urljoin(base_url, link['href'])
                link_domain = urlparse(full_url).netloc
                
                # Must be same domain
                if link_domain == base_domain:
                    contact_urls.append(full_url)
                    break
    
    # Deduplicate and limit
    return list(set(contact_urls))[:MAX_CONTACT_PAGES]

def scrape_website(url, progress_info=""):
    """Scrape website for emails and phones with early stopping"""
    all_emails = set()
    all_phones = set()
    pages_checked = 0
    
    try:
        # Normalize URL
        url = normalize_url(url)
        print(f"  {progress_info}Checking {url}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # Try HTTPS first
        try:
            response = requests.get(url, timeout=TIMEOUT, headers=headers, allow_redirects=True)
            response.raise_for_status()
        except (requests.RequestException, Exception):
            # Fallback to HTTP
            if url.startswith('https://'):
                url = url.replace('https://', 'http://')
                print(f"    ↳ Trying HTTP fallback...")
                response = requests.get(url, timeout=TIMEOUT, headers=headers, allow_redirects=True)
                response.raise_for_status()
            else:
                raise
        
        # Parse homepage
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n')
        
        emails = extract_emails_from_html(soup, text)
        phones = extract_phones_from_html(soup, text)
        
        all_emails.update(emails)
        all_phones.update(phones)
        pages_checked += 1
        
        print(f"    ↳ Homepage: {len(emails)} email(s), {len(phones)} phone(s)")
        
        # Early stop if we have both email and phone
        if all_emails and all_phones:
            print(f"    ✓ Found email + phone, stopping early")
            return list(all_emails), list(all_phones), "Success"
        
        # Check contact pages
        contact_pages = find_contact_page_links(soup, url)
        
        for contact_url in contact_pages:
            # Early stop check
            if all_emails and all_phones:
                break
            
            try:
                time.sleep(DELAY)
                print(f"    ↳ Checking: {contact_url.split('/')[-1][:40]}...")
                
                contact_resp = requests.get(contact_url, timeout=TIMEOUT, headers=headers)
                contact_resp.raise_for_status()
                contact_soup = BeautifulSoup(contact_resp.text, 'html.parser')
                contact_text = contact_soup.get_text(separator='\n')
                
                contact_emails = extract_emails_from_html(contact_soup, contact_text)
                contact_phones = extract_phones_from_html(contact_soup, contact_text)
                
                all_emails.update(contact_emails)
                all_phones.update(contact_phones)
                pages_checked += 1
                
                if contact_emails or contact_phones:
                    print(f"      → {len(contact_emails)} email(s), {len(contact_phones)} phone(s)")
                
            except Exception as e:
                continue
        
        # Determine status
        if all_emails or all_phones:
            print(f"    ✓ Total: {len(all_emails)} email(s), {len(all_phones)} phone(s) from {pages_checked} page(s)")
            return list(all_emails), list(all_phones), "Success"
        else:
            print(f"    ✗ No contacts found on {pages_checked} page(s)")
            return [], [], "NoContactsFound"
        
    except requests.Timeout:
        print(f"    ✗ Timeout")
        return list(all_emails), list(all_phones), "Timeout"
    except requests.ConnectionError:
        print(f"    ✗ Connection failed")
        return list(all_emails), list(all_phones), "ConnectionError"
    except requests.HTTPError as e:
        print(f"    ✗ HTTP {e.response.status_code}")
        return list(all_emails), list(all_phones), f"HTTPError-{e.response.status_code}"
    except Exception as e:
        print(f"    ✗ Error: {type(e).__name__}")
        return list(all_emails), list(all_phones), f"ParseError"

def process_spreadsheet(input_file, url_column, output_file=None):
    """Process the spreadsheet"""
    
    print(f"\n{'='*70}")
    print(f"EMAIL & PHONE NUMBER SCRAPER v2.0")
    print(f"{'='*70}\n")
    
    # Read file
    print(f"📂 Reading: {input_file}")
    try:
        if input_file.lower().endswith('.csv'):
            df = pd.read_csv(input_file)
        else:
            df = pd.read_excel(input_file)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"   Found {len(df)} rows\n")
    
    # Validate column
    if url_column not in df.columns:
        print(f"❌ Column '{url_column}' not found!")
        print(f"   Available columns: {', '.join(df.columns)}")
        return
    
    # Add result columns
    df['Emails'] = ''
    df['Phone_Numbers'] = ''
    df['Scrape_Status'] = ''
    
    # Process each URL
    print(f"🌐 Scraping {len(df)} websites...\n")
    
    for idx, row in df.iterrows():
        url = row[url_column]
        progress = f"[{idx+1}/{len(df)}] "
        
        if pd.isna(url) or str(url).strip() == '':
            print(f"{progress}Skipping empty URL")
            df.at[idx, 'Scrape_Status'] = 'EmptyURL'
            continue
        
        emails, phones, status = scrape_website(str(url), progress)
        
        df.at[idx, 'Emails'] = '; '.join(sorted(emails)) if emails else ''
        df.at[idx, 'Phone_Numbers'] = '; '.join(sorted(phones)) if phones else ''
        df.at[idx, 'Scrape_Status'] = status
        
        if idx < len(df) - 1:
            time.sleep(DELAY)
        print()
    
    # Save
    if output_file is None:
        base = input_file.rsplit('.', 1)[0]
        ext = input_file.rsplit('.', 1)[1] if '.' in input_file else 'xlsx'
        output_file = f"{base}_contacts.{ext}"
    
    print(f"💾 Saving to: {output_file}")
    try:
        if output_file.lower().endswith('.csv'):
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
        else:
            df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✅ Saved!\n")
    except Exception as e:
        print(f"❌ Error saving: {e}")
        return
    
    # Summary
    print(f"{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    success = len(df[df['Scrape_Status'] == 'Success'])
    with_email = len(df[df['Emails'] != ''])
    with_phone = len(df[df['Phone_Numbers'] != ''])
    
    print(f"✓ Success: {success}/{len(df)} sites")
    print(f"✓ Found emails: {with_email} sites")
    print(f"✓ Found phones: {with_phone} sites")
    print(f"\n📁 Output: {output_file}\n")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("WEBSITE CONTACT SCRAPER")
    print("="*70 + "\n")
    
    input_file = input("Excel/CSV filename (e.g., hotels.xlsx): ").strip()
    if not input_file:
        print("❌ No file specified")
        sys.exit(1)
    
    url_column = input("URL column name (default: SITE INTERNET): ").strip()
    if not url_column:
        url_column = "SITE INTERNET"
    
    output_file = input("Output filename (Enter for auto): ").strip() or None
    
    process_spreadsheet(input_file, url_column, output_file)
    
    input("\nPress Enter to exit...")
