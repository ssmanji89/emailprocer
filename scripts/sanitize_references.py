#!/usr/bin/env python3
"""
Repository Sanitization Script
Replaces company-specific references with generic placeholders for public release.
"""

import os
import re
import glob
import argparse
from pathlib import Path

# Replacement mappings
REPLACEMENTS = {
    # Company and domain references
    r'zgcompanies\.com': 'example.com',
    r'ZG Companies': 'Example Company',
    r'@zgcompanies\.com': '@example.com',
    
    # Personal email references
    r'smanji@zgcompanies\.com': 'admin@example.com',
    r'smanji@example\.com': 'admin@example.com',
    
    # Personal name references
    r'\bSuleman\b': 'User',
    r'suleman': 'user',
    
    # Specific tenant ID that appears in configs
    r'20989ce2-8d98-49ee-b545-5e5462d827cd': 'your-tenant-id-here',
    
    # Generic placeholders for other potential company references
    r'your-company\.com': 'example.com',
    r'@your-company\.com': '@example.com',
}

# File patterns to include
INCLUDE_PATTERNS = [
    '**/*.py',
    '**/*.md', 
    '**/*.json',
    '**/*.yml',
    '**/*.yaml',
    '**/*.ts',
    '**/*.tsx',
    '**/*.js',
    '**/*.jsx',
    '**/*.sh',
    '**/*.env.example',
    '**/*.env.template',
    '**/Dockerfile*',
    '**/docker-compose*.yml',
]

# File patterns to exclude
EXCLUDE_PATTERNS = [
    '.git/**',
    'node_modules/**',
    '__pycache__/**',
    '*.pyc',
    '.env',
    '*.env.local',
    'test.env',
    'test_local.env',
    '**/.env.*',
    '**/logs/**',
    '**/temp/**',
]

def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed based on include/exclude patterns."""
    file_str = str(file_path)
    
    # Check exclude patterns first
    for pattern in EXCLUDE_PATTERNS:
        if file_path.match(pattern) or file_str.find(pattern.replace('**/', '')) != -1:
            return False
    
    # Check include patterns
    for pattern in INCLUDE_PATTERNS:
        if file_path.match(pattern):
            return True
    
    return False

def sanitize_file(file_path: Path, dry_run: bool = False) -> tuple[int, list]:
    """Sanitize a single file."""
    changes = []
    replacement_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for pattern, replacement in REPLACEMENTS.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                replacement_count += len(matches)
                changes.append(f"  {pattern} → {replacement} ({len(matches)} times)")
        
        # Write back if changes were made and not dry run
        if content != original_content and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    except Exception as e:
        changes.append(f"  ERROR: {e}")
    
    return replacement_count, changes

def main():
    parser = argparse.ArgumentParser(description='Sanitize repository for public release')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--directory', '-d', default='.', help='Directory to process (default: current)')
    
    args = parser.parse_args()
    
    root_path = Path(args.directory).resolve()
    
    print(f"🧹 Repository Sanitization Tool")
    print(f"📁 Processing directory: {root_path}")
    print(f"🔍 Mode: {'DRY RUN' if args.dry_run else 'LIVE CHANGES'}")
    print("=" * 60)
    
    total_files = 0
    total_changes = 0
    processed_files = []
    
    # Find all files to process
    all_files = []
    for pattern in INCLUDE_PATTERNS:
        all_files.extend(root_path.glob(pattern))
    
    # Filter and process files
    for file_path in sorted(set(all_files)):
        if not file_path.is_file() or not should_process_file(file_path):
            continue
        
        rel_path = file_path.relative_to(root_path)
        replacement_count, changes = sanitize_file(file_path, args.dry_run)
        
        if replacement_count > 0:
            total_files += 1
            total_changes += replacement_count
            processed_files.append((rel_path, replacement_count, changes))
            
            print(f"📝 {rel_path} ({replacement_count} changes)")
            if args.verbose:
                for change in changes:
                    print(change)
                print()
    
    # Summary
    print("=" * 60)
    print(f"📊 SUMMARY")
    print(f"   Files processed: {total_files}")
    print(f"   Total changes: {total_changes}")
    
    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no files were actually modified")
        print("   Run without --dry-run to apply changes")
    else:
        print("\n✅ Sanitization complete!")
    
    # Show most changed files
    if processed_files:
        print("\n📋 Files with most changes:")
        for file_path, count, _ in sorted(processed_files, key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {file_path}: {count} changes")

if __name__ == "__main__":
    main() 