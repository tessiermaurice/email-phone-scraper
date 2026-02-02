# Batch Scraper Setup Guide

## 🎯 What This Does

Process large CSV files (15,000+ rows) in manageable chunks with:
- Automatic splitting into 50-row chunks
- Progress tracking (survives restarts)
- Detailed statistics
- Manual control over how many chunks to process
- Merge results when complete

---

## 📁 Folder Structure

```
your_project/
├── input/                          ← PUT YOUR BIG CSV HERE
│   └── hotels_15000.csv
│
├── output/                         ← RESULTS GO HERE (auto-created)
│   ├── chunks/                     ← Split files (auto-created)
│   │   ├── chunk_001.csv
│   │   ├── chunk_002.csv
│   │   └── ...
│   ├── results/                    ← Completed chunks (auto-created)
│   │   ├── chunk_001_contacts.csv
│   │   ├── chunk_002_contacts.csv
│   │   └── ...
│   ├── final/                      ← Final merged file (when ready)
│   │   └── contacts_FINAL_20260202_143000.csv
│   └── progress.json               ← Memory file (auto-created)
│
├── contact_scraper.py              ← Core scraper
├── batch_scraper.py                ← NEW - Batch processor
└── RUN_BATCH_SCRAPER.bat           ← Easy launcher
```

---

## 🚀 Quick Start

### Step 1: Setup
1. Create `input` folder in your project directory
2. Put your big CSV file in the `input` folder
3. Make sure column with URLs is named `SITE INTERNET` (or edit code)

### Step 2: Run
**Windows:** Double-click `RUN_BATCH_SCRAPER.bat`

**Manual:** 
```bash
python batch_scraper.py
```

### Step 3: First Run (Auto-Split)
```
Script detects your CSV
Splits into 300 chunks (50 rows each)
Shows status screen
```

### Step 4: Process in Batches
```
Choose option 1: Process NEXT [X] chunks
Enter how many: 5
Wait ~10 minutes
Close laptop, go to sleep 😴
```

### Step 5: Next Day
```
Open laptop
Run script again
Shows: "✓ Completed: 5 chunks (250 hotels)"
Choose option 1 again
Enter how many: 10
Continue...
```

### Step 6: When All Done
```
Choose option 2: Merge results
Creates final combined CSV
Done! 🎉
```

---

## 📊 What You'll See

### Status Screen:
```
==========================================
BATCH CONTACT SCRAPER
==========================================

📊 STATUS REPORT:
------------------------------------------
Total chunks: 300 (50 rows each)

✓ Completed: 15 chunks (750 hotels)
⏳ Remaining: 285 chunks (14,250 hotels)

📈 RESULTS FROM COMPLETED CHUNKS:
------------------------------------------
Websites accessible (OK): 663/750 (88.4%)
Websites unavailable: 87/750 (11.6%)

Contacts found (Success): 572/750 (76.3%)
  → Hotels with emails: 558
  → Hotels with phones: 541

No contacts found: 91/750 (12.1%)

Failed to scrape: 87/750 (11.6%)
  → Timeout: 15
  → Connection Failed: 54
  → Does Not Exist: 18

📅 Last run: 2026-02-02 17:30:00
==========================================

What would you like to do?
1. Process NEXT [X] chunks
2. Merge results into final file
3. Exit

Your choice: _
```

---

## ⚙️ Configuration

Edit at top of `batch_scraper.py`:

```python
CHUNK_SIZE = 50      # Rows per chunk (recommended: 50)
DELAY = 2            # Seconds between sites (recommended: 2)
TIMEOUT = 15         # Seconds to wait per site
```

---

## 💡 Tips

### For 15,000 Hotels:
- **Total chunks:** 300
- **Recommended per session:** 10-20 chunks
- **Time per session:** 20-40 minutes
- **Total time:** ~10 hours spread over days

### Best Practice:
```
Day 1: Process 20 chunks (1 hour)
Day 2: Process 20 chunks (1 hour)
Day 3: Process 20 chunks (1 hour)
...
Day 15: Process last 20 chunks + merge
```

### If Something Goes Wrong:
- Script crashes? → Just run again, it remembers everything
- Laptop dies? → Files are saved, restart where you left off
- Want to stop? → Press Ctrl+C, progress is saved

---

## 🔧 Troubleshooting

**"No CSV file found in input/"**
- Create `input` folder
- Put your CSV file there
- Run script again

**"Module 'contact_scraper' not found"**
- Make sure `contact_scraper.py` is in the same folder
- Make sure you're running from the correct directory

**"Permission denied" when saving**
- Close Excel if you have result files open
- Make sure you have write permissions

**Want to start over?**
- Delete `output` folder
- Run script again
- It will re-split and start fresh

---

## 📈 Performance

**Time estimates (with 2 sec delay):**
- 1 chunk (50 hotels): ~2 minutes
- 10 chunks (500 hotels): ~20 minutes
- 50 chunks (2,500 hotels): ~2 hours
- 300 chunks (15,000 hotels): ~10 hours

**Actual time varies based on:**
- Your internet speed
- Website response times
- Number of contact pages checked
- Timeouts and errors

---

## 🎓 Understanding the Process

### What Happens Behind the Scenes:

1. **Split:** Big CSV → 300 small CSVs
2. **Process:** Each chunk → scrape websites → save results
3. **Track:** Update progress.json after each chunk
4. **Remember:** If you stop, progress.json knows what's done
5. **Resume:** Next run loads progress, continues from where you left off
6. **Merge:** When all done, combine all results into one file

### The Memory System:

**progress.json contains:**
```json
{
  "total_chunks": 300,
  "completed_chunks": [1, 2, 3, 4, 5, ...],
  "stats": {
    "total_processed": 750,
    "emails_found": 558,
    ...
  }
}
```

This file is how the script "remembers" everything!

---

## 📞 Support

**Common Questions:**

Q: Can I run multiple instances at once?
A: No, they would conflict. Run one at a time.

Q: Can I edit chunks manually?
A: Yes, but don't rename them. Keep the naming: chunk_001.csv

Q: What if I want to re-scrape failed chunks?
A: Delete the corresponding chunk_XXX_contacts.csv file, script will re-process it.

Q: How do I know which chunks failed?
A: Check the result files, look for high "Unavailable" counts.

---

**Happy scraping! 🚀**
