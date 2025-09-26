#!/usr/bin/env python3
import csv, os

CSV_PATH = "data/signups.csv"
EXPORT_URL_PATH = ".secrets/newsletter-export.url"

def main():
    url = ""
    if os.path.exists(EXPORT_URL_PATH):
        url = open(EXPORT_URL_PATH, encoding="utf-8", errors="ignore").read().strip()

    emails = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            emails = [row for row in reader if row]

    with open(CSV_PATH, "w", encoding="utf-8", errors="ignore", newline="") as f:
        writer = csv.writer(f)
        for row in emails:
            writer.writerow(row)

    print("✅ signups.csv refreshed (UTF-8)")

if __name__ == "__main__":
    main()
