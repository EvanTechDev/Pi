#!/usr/bin/env python3

import os
import sys
import mmap
import time
import argparse
from pathlib import Path

def count_digits_optimized(filename):
    filepath = Path(filename)
    if not filepath.exists():
        raise FileNotFoundError(f"File {filename} not found")
    
    file_size = filepath.stat().st_size
    print(f"File size: {file_size:,} bytes")
    
    digit_count = 0
    processed = 0
    chunk_size = 1024 * 1024 * 50
    
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            digit_count += (chunk.count(b'0') + chunk.count(b'1') + chunk.count(b'2') +
                            chunk.count(b'3') + chunk.count(b'4') + chunk.count(b'5') +
                            chunk.count(b'6') + chunk.count(b'7') + chunk.count(b'8') + chunk.count(b'9'))
            
            processed += len(chunk)
            if processed % (1024 * 1024 * 50) == 0 or processed == file_size:
                progress = (processed / file_size) * 100
                print(f"Progress: {progress:.1f}% ({processed:,} bytes, {digit_count:,} digits found)", end='\r')
    
    print()
    return digit_count

def verify_file(short_file, long_file):
    short_path = Path(short_file)
    long_path = Path(long_file)
    
    if not short_path.exists():
        print(f"Error: Short file '{short_file}' not found")
        return False
    if not long_path.exists():
        print(f"Error: Long file '{long_file}' not found")
        return False
    
    short_size = short_path.stat().st_size
    print(f"Short file size: {short_size:,} bytes")
    print(f"Long file size: {long_path.stat().st_size:,} bytes")
    
    with open(short_path, 'rb') as f_short:
        short_data = f_short.read()
    
    with open(long_path, 'rb') as f_long:
        long_start = f_long.read(short_size)
    
    if len(long_start) < short_size:
        print(f"Error: Long file is shorter than short file ({len(long_start)} < {short_size})")
        return False
    
    match = (short_data == long_start)
    if match:
        print("✓ The short file content matches the beginning of the long file.")
    else:
        print("✗ Mismatch! The short file content does NOT match the beginning of the long file.")
        # Show first differing byte
        for i, (a, b) in enumerate(zip(short_data, long_start)):
            if a != b:
                print(f"First difference at offset {i}: short={a:02x} ('{chr(a)}'), long={b:02x} ('{chr(b)}')")
                break
    return match

def main():
    parser = argparse.ArgumentParser(description='Pi digits counter and verifier')
    parser.add_argument('files', nargs='*', help='File(s) to process. If two files given, verify short vs long.')
    parser.add_argument('--verify', action='store_true', help='Enable verification mode (requires two files)')
    parser.add_argument('--real', help='Short file with expected content')
    parser.add_argument('--check', help='Long file to check against')
    
    args = parser.parse_args()
    
    # Verification mode
    if args.verify or args.real or args.check:
        if not args.real or not args.check:
            print("Error: Both --real and --check are required for verification.")
            sys.exit(1)
        print("=" * 60)
        print("Verification Mode")
        print("=" * 60)
        start = time.time()
        result = verify_file(args.real, args.check)
        elapsed = time.time() - start
        print(f"Time: {elapsed:.2f} seconds")
        sys.exit(0 if result else 1)
    
    # If two positional files are given, treat as verify (short, long)
    if len(args.files) == 2:
        print("=" * 60)
        print("Verification Mode (from positional arguments)")
        print("=" * 60)
        start = time.time()
        result = verify_file(args.files[0], args.files[1])
        elapsed = time.time() - start
        print(f"Time: {elapsed:.2f} seconds")
        sys.exit(0 if result else 1)
    
    # Counting mode
    filename = args.files[0] if args.files else 'output.txt'
    print("=" * 60)
    print("Pi Digits Counter")
    print("=" * 60)
    
    start = time.time()
    try:
        digit_count = count_digits_optimized(filename)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    elapsed = time.time() - start
    print("=" * 60)
    print(f"Total digits: {digit_count:,}")
    if elapsed > 0:
        print(f"Speed: {digit_count/elapsed:,.0f} digits/second")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    print("=" * 60)
    
    # Show preview
    try:
        with open(filename, 'rb') as f:
            first = f.read(50)
            if first:
                preview = first.decode('ascii', errors='ignore')
                print(f"\nFile preview: {preview[:50]}...")
    except:
        pass

if __name__ == "__main__":
    main()