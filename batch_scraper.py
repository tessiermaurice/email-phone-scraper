"""
Batch Contact Scraper - Industrial Version
Processes large CSV files in chunks with progress tracking and statistics
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess

# Enable Windows terminal colors
if os.name == 'nt':  # Windows
    os.system('color 0A')  # Green on black

# Configuration
CHUNK_SIZE = 50
DELAY = 2
TIMEOUT = 15

# Paths
BASE_DIR = Path.cwd()
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
CHUNKS_DIR = OUTPUT_DIR / "chunks"
RESULTS_DIR = OUTPUT_DIR / "results"
FINAL_DIR = OUTPUT_DIR / "final"
PROGRESS_FILE = OUTPUT_DIR / "progress.json"

def ensure_directories():
    """Create necessary directories"""
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    CHUNKS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    FINAL_DIR.mkdir(exist_ok=True)

def load_progress():
    """Load progress from JSON file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_chunks": 0,
        "chunk_size": CHUNK_SIZE,
        "completed_chunks": [],
        "last_run": None,
        "stats": {
            "total_processed": 0,
            "websites_ok": 0,
            "websites_unavailable": 0,
            "success": 0,
            "no_contacts": 0,
            "emails_found": 0,
            "phones_found": 0,
            "timeout": 0,
            "connection_failed": 0,
            "does_not_exist": 0,
            "error": 0
        }
    }

def save_progress(progress):
    """Save progress to JSON file"""
    progress["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def split_csv(input_file):
    """Split large CSV into chunks"""
    print(f"\n📂 Splitting {input_file.name} into chunks...")
    
    df = pd.read_csv(input_file)
    total_rows = len(df)
    num_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    print(f"   Total rows: {total_rows}")
    print(f"   Chunk size: {CHUNK_SIZE} rows")
    print(f"   Total chunks: {num_chunks}")
    
    for i in range(num_chunks):
        start_idx = i * CHUNK_SIZE
        end_idx = min((i + 1) * CHUNK_SIZE, total_rows)
        chunk_df = df.iloc[start_idx:end_idx]
        
        chunk_filename = CHUNKS_DIR / f"chunk_{i+1:03d}.csv"
        chunk_df.to_csv(chunk_filename, index=False)
    
    print(f"✓ Created {num_chunks} chunks in: {CHUNKS_DIR}/")
    return num_chunks

def calculate_stats_from_results():
    """Calculate statistics from completed result files"""
    stats = {
        "total_processed": 0,
        "websites_ok": 0,
        "websites_unavailable": 0,
        "success": 0,
        "no_contacts": 0,
        "emails_found": 0,
        "phones_found": 0,
        "timeout": 0,
        "connection_failed": 0,
        "does_not_exist": 0,
        "error": 0
    }
    
    result_files = sorted(RESULTS_DIR.glob("chunk_*_contacts.csv"))
    
    for result_file in result_files:
        try:
            df = pd.read_csv(result_file)
            stats["total_processed"] += len(df)
            
            # Website status
            stats["websites_ok"] += len(df[df['Website_Status'] == 'OK'])
            stats["websites_unavailable"] += len(df[df['Website_Status'] == 'Unavailable'])
            
            # Scraping results
            stats["success"] += len(df[df['Scraping_Result'] == 'Success'])
            stats["no_contacts"] += len(df[df['Scraping_Result'] == 'No Contacts Found'])
            stats["timeout"] += len(df[df['Scraping_Result'] == 'Timeout'])
            stats["connection_failed"] += len(df[df['Scraping_Result'] == 'Connection Failed'])
            stats["does_not_exist"] += len(df[df['Scraping_Result'] == 'Does Not Exist'])
            stats["error"] += len(df[df['Scraping_Result'] == 'Error'])
            
            # Contacts found
            stats["emails_found"] += len(df[df['Email_Primary'].notna() & (df['Email_Primary'] != '')])
            stats["phones_found"] += len(df[df['Phone_Primary'].notna() & (df['Phone_Primary'] != '')])
        except Exception as e:
            print(f"Warning: Could not read {result_file.name}: {e}")
            continue
    
    return stats

def display_status(progress):
    """Display current status and statistics"""
    print("\n" + "="*70)
    print("BATCH CONTACT SCRAPER")
    print("="*70)
    
    total_chunks = progress.get("total_chunks", 0)
    completed = len(progress.get("completed_chunks", []))
    remaining = total_chunks - completed
    
    print(f"\n📊 STATUS REPORT:")
    print("-"*70)
    print(f"Total chunks: {total_chunks} ({CHUNK_SIZE} rows each)")
    print(f"\n✓ Completed: {completed} chunks ({completed * CHUNK_SIZE} hotels)")
    print(f"⏳ Remaining: {remaining} chunks ({remaining * CHUNK_SIZE} hotels)")
    
    if completed > 0:
        stats = progress["stats"]
        total = stats["total_processed"]
        
        if total > 0:  # Only show stats if we have actual data
            print(f"\n📈 RESULTS FROM COMPLETED CHUNKS:")
            print("-"*70)
            print(f"Websites accessible (OK): {stats['websites_ok']}/{total} ({stats['websites_ok']/total*100:.1f}%)")
            print(f"Websites unavailable: {stats['websites_unavailable']}/{total} ({stats['websites_unavailable']/total*100:.1f}%)")
            
            print(f"\nContacts found (Success): {stats['success']}/{total} ({stats['success']/total*100:.1f}%)")
            print(f"  → Hotels with emails: {stats['emails_found']}")
            print(f"  → Hotels with phones: {stats['phones_found']}")
            
            print(f"\nNo contacts found: {stats['no_contacts']}/{total} ({stats['no_contacts']/total*100:.1f}%)")
            
            failed_total = stats['timeout'] + stats['connection_failed'] + stats['does_not_exist'] + stats['error']
            if failed_total > 0:
                print(f"\nFailed to scrape: {failed_total}/{total} ({failed_total/total*100:.1f}%)")
                if stats['timeout'] > 0:
                    print(f"  → Timeout: {stats['timeout']}")
                if stats['connection_failed'] > 0:
                    print(f"  → Connection Failed: {stats['connection_failed']}")
                if stats['does_not_exist'] > 0:
                    print(f"  → Does Not Exist: {stats['does_not_exist']}")
                if stats['error'] > 0:
                    print(f"  → Error: {stats['error']}")
        else:
            print(f"\n⚠️  {completed} chunk(s) marked as complete but contain no data")
            print(f"   These will be re-processed on next run")
        
        if progress["last_run"]:
            print(f"\n📅 Last run: {progress['last_run']}")
    
    print("\n" + "="*70)

def is_chunk_completed(chunk_num):
    """Check if chunk is actually completed with data"""
    result_file = RESULTS_DIR / f"chunk_{chunk_num:03d}_contacts.csv"
    
    if not result_file.exists():
        return False
    
    # Check if file has actual data (more than just header row)
    try:
        df = pd.read_csv(result_file)
        return len(df) > 0  # Has at least 1 row of data
    except:
        return False

def process_chunks(num_chunks_to_process, progress):
    """Process specified number of chunks"""
    total_chunks = progress["total_chunks"]
    completed_chunks = set(progress["completed_chunks"])
    
    # Find next chunks to process
    chunks_to_process = []
    for i in range(1, total_chunks + 1):
        if i not in completed_chunks or not is_chunk_completed(i):
            chunks_to_process.append(i)
            if len(chunks_to_process) >= num_chunks_to_process:
                break
    
    if not chunks_to_process:
        print("\n✓ All chunks already processed!")
        return
    
    print(f"\n🌐 Processing {len(chunks_to_process)} chunks...")
    print(f"⏱ Estimated time: ~{len(chunks_to_process) * 2} minutes")
    print()
    
    for idx, chunk_num in enumerate(chunks_to_process, 1):
        chunk_file = CHUNKS_DIR / f"chunk_{chunk_num:03d}.csv"
        output_file = RESULTS_DIR / f"chunk_{chunk_num:03d}_contacts.csv"
        
        print(f"[Chunk {idx}/{len(chunks_to_process)}] Processing chunk {chunk_num}/{total_chunks}...")
        
        # Call contact_scraper.py with this chunk
        try:
            # Run contact_scraper programmatically with chunk info
            import contact_scraper as scraper
            scraper.process_spreadsheet(
                str(chunk_file), 
                "WEBSITE", 
                str(output_file),
                chunk_info=(chunk_num, total_chunks)  # Pass chunk context
            )
            
            # Mark as completed
            progress["completed_chunks"].append(chunk_num)
            progress["completed_chunks"].sort()
            
            # Update stats
            progress["stats"] = calculate_stats_from_results()
            save_progress(progress)
            
            print(f"✓ Saved: {output_file.name}\n")
            
        except Exception as e:
            print(f"✗ Error processing chunk {chunk_num}: {e}\n")
            continue
    
    print("="*70)
    print(f"{len(chunks_to_process)} CHUNKS COMPLETED!")
    print("="*70)
    
    # Show session summary
    stats = progress["stats"]
    session_hotels = len(chunks_to_process) * CHUNK_SIZE
    
    print(f"\n📊 SESSION SUMMARY:")
    print("-"*70)
    print(f"Processed: {len(chunks_to_process)} chunks ({session_hotels} hotels)")
    
    print(f"\n📊 OVERALL PROGRESS:")
    print("-"*70)
    completed = len(progress["completed_chunks"])
    print(f"Total completed: {completed}/{total_chunks} chunks ({completed/total_chunks*100:.1f}%)")
    print(f"Total hotels scraped: {stats['total_processed']}")
    
    if stats["total_processed"] > 0:
        print(f"\nTotal results:")
        print(f"  → Websites accessible: {stats['websites_ok']}/{stats['total_processed']} ({stats['websites_ok']/stats['total_processed']*100:.1f}%)")
        print(f"  → Contacts found: {stats['success']}/{stats['total_processed']} ({stats['success']/stats['total_processed']*100:.1f}%)")
        print(f"  → Emails found: {stats['emails_found']}")
        print(f"  → Phones found: {stats['phones_found']}")
    
    remaining = total_chunks - completed
    if remaining > 0:
        est_time_hours = (remaining * 2) / 60
        print(f"\nRemaining: {remaining} chunks")
        print(f"Estimated time to finish: ~{est_time_hours:.1f} hours")
    
    print("\n" + "="*70)

def merge_results(progress):
    """Merge all result chunks into final file"""
    print("\n📁 Merging all results into final file...")
    
    result_files = sorted(RESULTS_DIR.glob("chunk_*_contacts.csv"))
    
    if not result_files:
        print("✗ No result files found to merge!")
        return
    
    all_data = []
    for result_file in result_files:
        df = pd.read_csv(result_file)
        all_data.append(df)
    
    final_df = pd.concat(all_data, ignore_index=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_file = FINAL_DIR / f"contacts_FINAL_{timestamp}.csv"
    final_df.to_csv(final_file, index=False)
    
    print(f"✓ Merged {len(result_files)} files")
    print(f"✓ Total rows: {len(final_df)}")
    print(f"✓ Saved to: {final_file}")

def main_menu():
    """Main menu loop"""
    ensure_directories()
    
    # Check if we need to split the input file first
    progress = load_progress()
    
    if progress["total_chunks"] == 0:
        print("\n" + "="*70)
        print("INITIAL SETUP")
        print("="*70)
        
        # Look for CSV file in input folder
        csv_files = list(INPUT_DIR.glob("*.csv"))
        
        if not csv_files:
            print(f"\n✗ No CSV file found in {INPUT_DIR}/")
            print(f"   Please place your CSV file in the 'input' folder and run again.")
            return
        
        if len(csv_files) > 1:
            print(f"\n📂 Found multiple CSV files:")
            for i, f in enumerate(csv_files, 1):
                print(f"   {i}. {f.name}")
            choice = int(input("\nWhich file to process? ")) - 1
            input_file = csv_files[choice]
        else:
            input_file = csv_files[0]
            print(f"\n📂 Found: {input_file.name}")
        
        num_chunks = split_csv(input_file)
        progress["total_chunks"] = num_chunks
        save_progress(progress)
        print("\n✓ Setup complete! Ready to process.\n")
    
    # Main loop
    while True:
        progress = load_progress()
        progress["stats"] = calculate_stats_from_results()  # Recalculate from files
        save_progress(progress)
        
        display_status(progress)
        
        print("\nWhat would you like to do?")
        print("1. Process NEXT [X] chunks")
        print("2. Merge results into final file")
        print("3. Exit")
        
        try:
            choice = input("\nYour choice: ").strip()
            
            if choice == "1":
                num = int(input("How many chunks to process? "))
                process_chunks(num, progress)
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                merge_results(progress)
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                print("\n👋 Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\n✓ Progress saved. Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("BATCH CONTACT SCRAPER - Industrial Version")
    print("="*70)
    main_menu()
