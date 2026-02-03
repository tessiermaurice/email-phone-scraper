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
from html import unescape
import sys

# Configuration
TIMEOUT = 15
DELAY = 2
MAX_CONTACT_PAGES = 3

# Comprehensive country code to ISO mapping with territories (200+ countries)
COUNTRY_CODES = {
    # Europe
    '33': 'FR', '32': 'BE', '41': 'CH', '49': 'DE', '44': 'GB', '34': 'ES', '39': 'IT', 
    '351': 'PT', '31': 'NL', '43': 'AT', '45': 'DK', '46': 'SE', '47': 'NO', '358': 'FI',
    '353': 'IE', '30': 'GR', '48': 'PL', '420': 'CZ', '36': 'HU', '40': 'RO', '421': 'SK',
    '386': 'SI', '385': 'HR', '359': 'BG', '370': 'LT', '371': 'LV', '372': 'EE', '354': 'IS',
    '356': 'MT', '357': 'CY', '352': 'LU', '377': 'MC', '378': 'SM', '423': 'LI', '376': 'AD',
    '382': 'ME', '381': 'RS', '383': 'XK', '387': 'BA', '389': 'MK', '355': 'AL', '373': 'MD',
    '380': 'UA', '375': 'BY', '7': 'RU/KZ',  # Russia or Kazakhstan (ambiguous)
    
    # French Territories (DOM-TOM)
    '262': 'FR-RE',  # Réunion
    '590': 'FR-GP',  # Guadeloupe
    '594': 'FR-GF',  # French Guiana
    '596': 'FR-MQ',  # Martinique
    '508': 'FR-PM',  # Saint Pierre and Miquelon
    '681': 'FR-WF',  # Wallis and Futuna
    '687': 'FR-NC',  # New Caledonia
    '689': 'FR-PF',  # French Polynesia
    
    # UK Territories
    '500': 'GB-FK',  # Falkland Islands
    '350': 'GB-GI',  # Gibraltar
    '290': 'GB-SH',  # Saint Helena
    '247': 'GB-AC',  # Ascension Island
    '1284': 'GB-VG', # British Virgin Islands
    '1345': 'GB-KY', # Cayman Islands
    '1441': 'GB-BM', # Bermuda
    '1664': 'GB-MS', # Montserrat
    '1649': 'GB-TC', # Turks and Caicos
    '1264': 'GB-AI', # Anguilla
    
    # Spanish Territories
    # Note: Ceuta, Melilla, Canary Islands use regular +34 (same as mainland Spain)
    # But we can note them in comments for awareness
    
    # Netherlands Territories
    '297': 'NL-AW',  # Aruba
    '599': 'NL-CW',  # Curaçao
    '5999': 'NL-CW', # Curaçao (alternative)
    '721': 'NL-SX',  # Sint Maarten
    
    # US Territories
    '1340': 'US-VI', # US Virgin Islands
    '1670': 'US-MP', # Northern Mariana Islands
    '1671': 'US-GU', # Guam
    '1684': 'US-AS', # American Samoa
    '1787': 'US-PR', # Puerto Rico
    '1939': 'US-PR', # Puerto Rico
    
    # Danish Territories
    '299': 'DK-GL',  # Greenland
    '298': 'DK-FO',  # Faroe Islands
    
    # Australian Territories
    '672': 'AU-NF',  # Norfolk Island
    '6189164': 'AU-CX', # Christmas Island (uses AU +61)
    
    # New Zealand Territories
    '682': 'NZ-CK',  # Cook Islands
    '683': 'NZ-NU',  # Niue
    '690': 'NZ-TK',  # Tokelau
    
    # Portuguese Territories
    '351': 'PT',     # Mainland + Azores + Madeira (all use same code)
    
    # Americas
    '1': 'US/CA',    # USA/Canada (ambiguous without area code analysis)
    '52': 'MX', '54': 'AR', '55': 'BR', '56': 'CL', '57': 'CO', '51': 'PE',
    '58': 'VE', '593': 'EC', '591': 'BO', '595': 'PY', '598': 'UY', '506': 'CR', '507': 'PA',
    '53': 'CU', '509': 'HT', '1809': 'DO', '1829': 'DO', '1849': 'DO', '502': 'GT', '503': 'SV',
    '504': 'HN', '505': 'NI', '501': 'BZ',
    
    # Caribbean (independent nations)
    '1242': 'BS', '1246': 'BB', '1268': 'AG', '1473': 'GD', '1758': 'LC', 
    '1767': 'DM', '1784': 'VC', '1868': 'TT', '1869': 'KN', '1876': 'JM',
    
    # Asia
    '86': 'CN', '91': 'IN', '81': 'JP', '82': 'KR', '886': 'TW', '852': 'HK', '853': 'MO',
    '65': 'SG', '60': 'MY', '66': 'TH', '84': 'VN', '62': 'ID', '63': 'PH', '95': 'MM',
    '855': 'KH', '856': 'LA', '673': 'BN', '670': 'TL', '92': 'PK', '880': 'BD', '94': 'LK',
    '977': 'NP', '975': 'BT', '960': 'MV', '93': 'AF', '98': 'IR', '964': 'IQ', '962': 'JO',
    '961': 'LB', '963': 'SY', '972': 'IL', '970': 'PS', '971': 'AE', '966': 'SA', '968': 'OM',
    '965': 'KW', '973': 'BH', '974': 'QA', '967': 'YE', '90': 'TR', '994': 'AZ', '995': 'GE',
    '374': 'AM', '992': 'TJ', '993': 'TM', '998': 'UZ', '996': 'KG',
    
    # Middle East & North Africa
    '20': 'EG', '212': 'MA', '213': 'DZ', '216': 'TN', '218': 'LY', '249': 'SD',
    
    # Sub-Saharan Africa
    '27': 'ZA', '254': 'KE', '255': 'TZ', '256': 'UG', '234': 'NG', '233': 'GH', '225': 'CI',
    '221': 'SN', '223': 'ML', '226': 'BF', '227': 'NE', '228': 'TG', '229': 'BJ', '230': 'MU',
    '231': 'LR', '232': 'SL', '235': 'TD', '236': 'CF', '237': 'CM', '238': 'CV', '239': 'ST',
    '240': 'GQ', '241': 'GA', '242': 'CG', '243': 'CD', '244': 'AO', '245': 'GW', '246': 'IO',
    '248': 'SC', '250': 'RW', '251': 'ET', '252': 'SO', '253': 'DJ', '257': 'BI', '258': 'MZ',
    '260': 'ZM', '261': 'MG', '263': 'ZW', '264': 'NA', '265': 'MW', '266': 'LS', '267': 'BW',
    '268': 'SZ', '269': 'KM',
    
    # Oceania
    '61': 'AU', '64': 'NZ', '679': 'FJ', '675': 'PG', '676': 'TO', '677': 'SB', '678': 'VU',
    '685': 'WS', '686': 'KI', '688': 'TV', '691': 'FM', '692': 'MH', '680': 'PW',
}

def detect_country_from_phone(phone_e164):
    """Detect country ISO code from E.164 phone number"""
    if not phone_e164 or not phone_e164.startswith('+'):
        return 'UNK'
    
    # Remove + and try to match country codes (try longest first)
    digits = phone_e164[1:]
    
    # Try 4-digit codes first (like 1242, 1787, 1670, etc.)
    for length in [7, 6, 5, 4, 3, 2, 1]:
        code = digits[:length]
        if code in COUNTRY_CODES:
            return COUNTRY_CODES[code]
    
    return 'UNK'

def detect_country_from_domain(url):
    """Detect country from website domain TLD"""
    if not url:
        return None
    
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        # TLD to country mapping
        tld_map = {
            '.fr': 'FR', '.es': 'ES', '.it': 'IT', '.de': 'DE', '.pt': 'PT',
            '.be': 'BE', '.nl': 'NL', '.ch': 'CH', '.at': 'AT', '.lu': 'LU',
            '.uk': 'GB', '.co.uk': 'GB', '.ie': 'IE', '.se': 'SE', '.no': 'NO',
            '.dk': 'DK', '.fi': 'FI', '.pl': 'PL', '.cz': 'CZ', '.gr': 'GR',
            '.ru': 'RU', '.ua': 'UA', '.ro': 'RO', '.hu': 'HU', '.hr': 'HR',
            '.rs': 'RS', '.bg': 'BG', '.si': 'SI', '.sk': 'SK', '.lt': 'LT',
            '.lv': 'LV', '.ee': 'EE', '.is': 'IS', '.tr': 'TR',
            '.us': 'US', '.ca': 'CA', '.mx': 'MX', '.br': 'BR', '.ar': 'AR',
            '.cl': 'CL', '.co': 'CO', '.pe': 'PE', '.ve': 'VE', '.ec': 'EC',
            '.cn': 'CN', '.jp': 'JP', '.kr': 'KR', '.in': 'IN', '.au': 'AU',
            '.nz': 'NZ', '.sg': 'SG', '.my': 'MY', '.th': 'TH', '.vn': 'VN',
            '.id': 'ID', '.ph': 'PH', '.hk': 'HK', '.tw': 'TW',
            '.za': 'ZA', '.eg': 'EG', '.ma': 'MA', '.ng': 'NG', '.ke': 'KE',
            '.ae': 'AE', '.sa': 'SA', '.il': 'IL', '.iq': 'IQ', '.ir': 'IR',
        }
        
        # Check for TLD match
        for tld, country in tld_map.items():
            if domain.endswith(tld):
                return country
        
        return None
    except:
        return None

def normalize_url(url):
    """Add https:// scheme, fallback to http:// if needed"""
    url = str(url).strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def extract_emails_from_html(soup, text):
    """Extract emails from mailto links and text"""
    emails = set()
    
    # Extract from links with various prefixes
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith(('mailto:', 'goto:', 'email:', 'e-mail:', 'mail:')):
            # Remove prefix and clean
            for prefix in ['mailto:', 'goto:', 'email:', 'e-mail:', 'mail:']:
                if href.startswith(prefix):
                    email = href.replace(prefix, '').split('?')[0].strip()
                    break
            
            # Remove whitespace and validate
            email = re.sub(r'\s+', '', email)
            if '@' in email and '.' in email:
                emails.add(email.lower())
    
    # Extract from text using regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    found = re.findall(email_pattern, text)
    # Normalize whitespace
    emails.update([re.sub(r'\s+', '', e).lower() for e in found])
    
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
    """Normalize phone to E.164 format - ONLY if international format is explicit
    
    Rules:
    - 00XXXXXXXXXXX → +XXXXXXXXXXX (European international prefix)
    - +XXXXXXXXXXX → Keep as-is (already international)
    - 33XXXXXXXXX (11+ digits, starts with country code) → +33XXXXXXXXX
    - 0XXXXXXXXX (10 digits, local) → KEEP AS-IS (don't know country!)
    """
    if not phone:
        return None
    
    original_phone = phone
    
    # Remove (0) patterns: (0), ( 0 ), [0], [ 0 ]
    phone = re.sub(r'[\(\[]\s*0\s*[\)\]]', '', phone)
    
    # Check if phone starts with 00 (European international prefix)
    if phone.strip().startswith('00'):
        # This is INTERNATIONAL - convert 00 to +
        phone = '+' + phone.strip()[2:]
        has_international_indicator = True
    # Check if phone starts with +
    elif phone.strip().startswith('+'):
        has_international_indicator = True
    else:
        has_international_indicator = False
    
    # Remove all non-digit characters except leading +
    if phone.startswith('+'):
        digits = '+' + re.sub(r'\D', '', phone[1:])
        digits = digits.lstrip('+')  # Remove + for processing
    else:
        digits = re.sub(r'\D', '', phone)
    
    # Too short or too long
    if len(digits) < 9 or len(digits) > 15:
        return None
    
    # CRITICAL RULE: Local numbers (0XXXXXXXXX with 10 digits) stay unchanged!
    if digits.startswith('0') and len(digits) == 10 and not has_international_indicator:
        # This is a LOCAL number - keep as-is!
        return digits
    
    # Check if it looks like it has a country code (11+ digits, starts with known code)
    if not has_international_indicator and len(digits) >= 11:
        # Check if starts with known country code
        for code_len in [3, 2, 1]:
            potential_code = digits[:code_len]
            if potential_code in COUNTRY_CODES:
                has_international_indicator = True
                break
    
    # Only normalize if we detected international format
    if has_international_indicator:
        # Fix: Handle "+3304..." where country code has extra 0
        if digits.startswith('330') and len(digits) == 12:
            digits = '33' + digits[3:]
        
        # Fix: Handle any country code followed by extra 0
        country_code_match = re.match(r'^(\d{2,3})0(\d{9})$', digits)
        if country_code_match:
            country_code = country_code_match.group(1)
            rest = country_code_match.group(2)
            if country_code in COUNTRY_CODES:
                digits = country_code + rest
        
        # Return with + prefix
        if len(digits) >= 10:
            return '+' + digits
    else:
        # NO international indicator - keep as-is (cleaned)
        return digits
    
    return None

def extract_phones_from_html(soup, text):
    """Extract and validate phone numbers with GPS filtering"""
    phones = set()
    
    # Priority: tel and call links
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith(('tel:', 'call:', 'callto:', 'phone:')):
            # Remove prefix
            for prefix in ['tel:', 'call:', 'callto:', 'phone:']:
                if href.startswith(prefix):
                    phone = href.replace(prefix, '').strip()
                    break
            
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
    """Scrape website for emails and phones with early stopping - returns (emails, phones, website_status, scraping_result)"""
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
        text = unescape(soup.get_text(separator='\n'))
        
        emails = extract_emails_from_html(soup, text)
        phones = extract_phones_from_html(soup, text)
        
        all_emails.update(emails)
        all_phones.update(phones)
        pages_checked += 1
        
        print(f"    ↳ Homepage: {len(emails)} email(s), {len(phones)} phone(s)")
        
        # Early stop if we have both email and phone
        if all_emails and all_phones:
            print(f"    ✓ Found email + phone, stopping early")
            return list(all_emails), list(all_phones), "OK", "Success"
        
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
                contact_text = unescape(contact_soup.get_text(separator='\n'))
                
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
            return list(all_emails), list(all_phones), "OK", "Success"
        else:
            print(f"    ✗ No contacts found on {pages_checked} page(s)")
            return [], [], "OK", "No Contacts Found"
        
    except requests.Timeout:
        print(f"    ✗ Timeout")
        return list(all_emails), list(all_phones), "Unavailable", "Timeout"
    except requests.ConnectionError:
        print(f"    ✗ Connection failed")
        return list(all_emails), list(all_phones), "Unavailable", "Connection Failed"
    except requests.HTTPError as e:
        status_code = e.response.status_code
        print(f"    ✗ HTTP {status_code}")
        return list(all_emails), list(all_phones), "Unavailable", "Does Not Exist"
    except Exception as e:
        print(f"    ✗ Error: {type(e).__name__}")
        return list(all_emails), list(all_phones), "Unavailable", "Error"

def deduplicate_phones(phone_list):
    """Remove duplicate phone numbers that are the same number in different formats
    
    Compares last 9 digits to catch duplicates like:
    - +33479059522 and 0479059522 (same number, different format)
    - +33479059522 and +33479059522 (exact duplicate)
    """
    if not phone_list:
        return []
    
    # Normalize all phones
    normalized = []
    for phone in phone_list:
        norm = normalize_phone_to_e164(phone)
        if norm:
            normalized.append(norm)
    
    # Deduplicate by last 9 digits
    seen_cores = set()
    result = []
    
    for phone in normalized:
        # Get last 9 digits for comparison
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) >= 9:
            core = digits_only[-9:]  # Last 9 digits
        else:
            core = digits_only  # Use all digits if less than 9
        
        # Check if we've seen this core before
        if core not in seen_cores:
            seen_cores.add(core)
            result.append(phone)
        # else: duplicate detected, skip it
    
    return result

def process_spreadsheet(input_file, url_column, output_file=None, chunk_info=None):
    """Process the spreadsheet
    
    Args:
        input_file: Path to input CSV/Excel
        url_column: Name of column containing URLs
        output_file: Optional output filename
        chunk_info: Optional tuple (current_chunk, total_chunks) for batch processing display
    """
    
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
    df['Email_Primary'] = ''
    df['Email_Additional'] = ''
    df['Country'] = ''
    df['Phone_Primary'] = ''
    df['Phone_Additional'] = ''
    df['Website_Status'] = ''
    df['Scraping_Result'] = ''
    
    # Process each URL
    print(f"🌐 Scraping {len(df)} websites...\n")
    
    for idx, row in df.iterrows():
        url = row[url_column]
        
        # Build progress string with optional chunk info
        if chunk_info:
            current_chunk, total_chunks = chunk_info
            progress = f"[Chunk {current_chunk}/{total_chunks}] [{idx+1}/{len(df)}] "
        else:
            progress = f"[{idx+1}/{len(df)}] "
        
        if pd.isna(url) or str(url).strip() == '':
            print(f"{progress}Skipping empty URL")
            df.at[idx, 'Website_Status'] = 'Unavailable'
            df.at[idx, 'Scraping_Result'] = 'No URL'
            continue
        
        emails, phones, website_status, scraping_result = scrape_website(str(url), progress)
        
        # Deduplicate phones (removes duplicates by comparing last 9 digits)
        phones = deduplicate_phones(phones)
        
        # Final safety check: remove any remaining duplicates by last 9 digits
        seen_cores = set()
        final_phones = []
        for phone in phones:
            if phone:
                # Get last 9 digits
                digits_only = re.sub(r'\D', '', phone)
                core = digits_only[-9:] if len(digits_only) >= 9 else digits_only
                
                if core not in seen_cores:
                    seen_cores.add(core)
                    final_phones.append(phone)
        
        phones = final_phones
        
        # Assign emails
        df.at[idx, 'Email_Primary'] = emails[0] if emails else ''
        df.at[idx, 'Email_Additional'] = '; '.join(sorted(emails[1:])) if len(emails) > 1 else ''
        
        # Determine country: First from phone (if international), then from domain
        country = 'UNK'
        if phones:
            # Primary phone
            primary_phone = phones[0]
            df.at[idx, 'Phone_Primary'] = "'" + primary_phone
            
            # Try to get country from phone first
            country = detect_country_from_phone(primary_phone)
            
            # If phone didn't give us country (local number), try domain
            if country == 'UNK':
                domain_country = detect_country_from_domain(str(url))
                if domain_country:
                    country = domain_country
            
            df.at[idx, 'Country'] = country
            
            # Additional phones (also with ' prefix to protect + sign in Excel)
            if len(phones) > 1:
                protected_additional = ["'" + p for p in sorted(phones[1:])]
                df.at[idx, 'Phone_Additional'] = '; '.join(protected_additional)
        else:
            # No phones found - try to get country from domain anyway
            domain_country = detect_country_from_domain(str(url))
            if domain_country:
                country = domain_country
            df.at[idx, 'Country'] = country
        
        df.at[idx, 'Website_Status'] = website_status
        df.at[idx, 'Scraping_Result'] = scraping_result
        
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
    success = len(df[df['Scraping_Result'] == 'Success'])
    websites_ok = len(df[df['Website_Status'] == 'OK'])
    with_email = len(df[df['Email_Primary'] != ''])
    with_phone = len(df[df['Phone_Primary'] != ''])
    
    print(f"✓ Websites accessible: {websites_ok}/{len(df)} sites")
    print(f"✓ Scraping success: {success}/{len(df)} sites")
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
