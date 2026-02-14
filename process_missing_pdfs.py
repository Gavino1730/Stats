#!/usr/bin/env python3
"""
Process Missing PDFs - Extracts text from missing PDF files and adds them to the database.
"""

import json
import fitz  # PyMuPDF
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None


def main():
    """Process all missing PDFs and add them to raw_pdfs.json."""
    print("=" * 70)
    print("PROCESSING MISSING PDF FILES")
    print("=" * 70)
    print()
    
    # Paths
    pdf_dir = Path('/home/runner/work/Stats/Stats/Stat Sheets/Stats')
    raw_pdfs_path = Path('/home/runner/work/Stats/Stats/data/raw_pdfs.json')
    backup_path = Path('/home/runner/work/Stats/Stats/data/raw_pdfs.json.backup')
    
    # Load existing raw PDF data
    print(f"Loading existing raw PDF data from: {raw_pdfs_path}")
    with open(raw_pdfs_path, 'r') as f:
        raw_pdfs = json.load(f)
    existing_count = len(raw_pdfs)
    print(f"✓ Loaded {existing_count} existing PDF entries")
    print()
    
    # Create backup
    print(f"Creating backup: {backup_path}")
    with open(backup_path, 'w') as f:
        json.dump(raw_pdfs, f, indent=2)
    print("✓ Backup created")
    print()
    
    # Find all PDF files
    pdf_files = sorted(pdf_dir.glob('*.pdf'))
    print(f"Found {len(pdf_files)} total PDF files in directory")
    print()
    
    # Find missing PDFs
    missing_pdfs = [f for f in pdf_files if f.name not in raw_pdfs]
    print(f"Found {len(missing_pdfs)} PDFs not yet processed:")
    for pdf in missing_pdfs:
        print(f"  - {pdf.name}")
    print()
    
    if not missing_pdfs:
        print("✓ All PDFs are already processed!")
        return
    
    # Process each missing PDF
    print("Processing missing PDFs...")
    print("-" * 70)
    
    processed_count = 0
    failed_count = 0
    
    for pdf_path in missing_pdfs:
        print(f"\nProcessing: {pdf_path.name}")
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        
        if text:
            # Add to raw_pdfs dictionary
            raw_pdfs[pdf_path.name] = text
            processed_count += 1
            
            # Show a preview
            preview = text[:150].replace('\n', ' ')
            print(f"  ✓ Extracted {len(text)} characters")
            print(f"  Preview: {preview}...")
        else:
            print(f"  ✗ Failed to extract text")
            failed_count += 1
    
    print()
    print("-" * 70)
    print(f"✓ Successfully processed {processed_count} new PDFs")
    if failed_count > 0:
        print(f"✗ Failed to process {failed_count} PDFs")
    print()
    
    # Save updated data
    print(f"Saving updated data to: {raw_pdfs_path}")
    with open(raw_pdfs_path, 'w') as f:
        json.dump(raw_pdfs, f, indent=2)
    print("✓ Data saved!")
    print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Before: {existing_count} PDFs in database")
    print(f"Added: {processed_count} new PDFs")
    print(f"After: {len(raw_pdfs)} PDFs in database")
    print(f"Remaining: {len(pdf_files) - len(raw_pdfs)} PDFs not processed")
    print()
    
    if processed_count > 0:
        print("✓ New PDFs have been added to raw_pdfs.json")
        print("→ Next step: Run fix_parsed_data.py to parse these new games")
    print()


if __name__ == '__main__':
    main()
