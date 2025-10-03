from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess
import sys
import os
from datetime import datetime

def run_clean_and_dedupe():
    print(f"[{datetime.now()}] Running lead cleaning and deduplication...")
    # Run the cleaning script as a subprocess
    result = subprocess.run([sys.executable, os.path.join('scripts', 'clean_and_dedupe.py')])
    if result.returncode == 0:
        print(f"[{datetime.now()}] Cleaning and deduplication completed successfully.")
    else:
        print(f"[{datetime.now()}] Cleaning and deduplication failed with code {result.returncode}.")

def main():
    scheduler = BlockingScheduler()
    # Schedule to run every Sunday at 2am
    scheduler.add_job(run_clean_and_dedupe, 'cron', day_of_week='sun', hour=2, minute=0)
    print("Scheduled cleaning and deduplication every Sunday at 2am. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")

if __name__ == "__main__":
    main() 