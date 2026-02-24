python

#!/usr/bin/env python3

"""

Enhanced auto_uid.py - Production-ready CLI for managing markdown with UIDs



Features:

- autoUID: Preserve and validate subject-based TR IDs

- hideUIDlocal: Move leading [ID] to HTML comments for clean reading

- autoNumbering: Ensure proper section numbering hierarchy

- autoTitle: Ensure YAML front-matter has title

- Dry-run mode: Preview changes safely

- Backup creation: Automatic .bak files for safety

- ID validation: Check for duplicates, format issues

- Statistics: Report processing details



Usage:

  python tools/auto_uid.py --file <markdown-file> [options]



Options:

  --hide-local-uids    Move leading [ID] to HTML comments

  --auto-numbering     Ensure numbered section headings

  --auto-title         Ensure YAML title exists

  --validate-ids       Check ID format and uniqueness

  --dry-run           Preview changes without modifying

  --backup            Create .bak file before changes

  --inplace           Modify file in place (default: create new file)

  --output, -o        Specify output file path

  --stats             Show processing statistics

"""

import argparse

import re

import sys

from collections import Counter

from pathlib import Path

from typing import Dict, List, Set, Tuple



# Enhanced regex patterns

ID_LEADING_RE = re.compile(r'^\s*\[(?P<id>[A-Z0-9\-]+)\]\s*(?P<content>.*)')

YAML_BOUNDARY = '---'

SECTION_HEADING_RE = re.compile(r'^(\d+(?:\.\d+)*)\s+(.+)$')

TR_ID_FORMAT_RE = re.compile(r'^TR-[A-Z]+(?:-[A-Z]+)*-\d+$')



class ProcessingStats:

    def __init__(self):

        self.ids_processed = 0

        self.ids_hidden = 0

        self.sections_numbered = 0

        self.title_added = False

        self.errors = []

        self.warnings = []

        self.duplicate_ids = []



    def report(self) -> str:

        lines = [

            f"Processing Statistics:",

            f"  IDs processed: {self.ids_processed}",

            f"  IDs hidden: {self.ids_hidden}",

            f"  Sections numbered: {self.sections_numbered}",

            f"  Title added: {'Yes' if self.title_added else 'No'}",

            f"  Errors: {len(self.errors)}",

            f"  Warnings: {len(self.warnings)}"

        ]

        if self.duplicate_ids:

            lines.append(f"  Duplicate IDs found: {', '.join(self.duplicate_ids)}")

        return '\n'.join(lines)



def validate_ids(text: str, stats: ProcessingStats) -> Dict[str, List[int]]:

    """Validate ID format and detect duplicates. Returns dict of id -> line_numbers."""

    id_locations = {}

    lines = text.splitlines()



    for line_num, line in enumerate(lines, 1):

        match = ID_LEADING_RE.match(line)

        if match:

            id_val = match.group('id')

            stats.ids_processed += 1



            # Track locations

            if id_val not in id_locations:

                id_locations[id_val] = []

            id_locations[id_val].append(line_num)



            # Validate format

            if not TR_ID_FORMAT_RE.match(id_val):

                stats.warnings.append(f"Line {line_num}: ID '{id_val}' doesn't match TR format")



    # Find duplicates

    for id_val, locations in id_locations.items():

        if len(locations) > 1:

            stats.duplicate_ids.append(id_val)

            stats.errors.append(f"Duplicate ID '{id_val}' found on lines: {', '.join(map(str, locations))}")



    return id_locations



def hide_local_uids(text: str, stats: ProcessingStats) -> str:

    """Enhanced version with better formatting preservation."""

    out_lines = []

    for line in text.splitlines():

        match = ID_LEADING_RE.match(line)

        if match:

            id_val = match.group('id')

            content = match.group('content')

            # Preserve original spacing in content

            out_lines.append(f'<!--{id_val}-->{content}')

            stats.ids_hidden += 1

        else:

            out_lines.append(line)

    return '\n'.join(out_lines) + ('\n' if text.endswith('\n') else '')



def ensure_yaml_title(text: str, stats: ProcessingStats) -> str:

    """Enhanced YAML parsing with better error handling."""

    lines = text.splitlines()

    if not lines:

        return text



    # Check for existing YAML front matter

    if lines[0].strip() == YAML_BOUNDARY:

        try:

            end_idx = lines[1:].index(YAML_BOUNDARY) + 1

        except ValueError:

            stats.errors.append("YAML front matter started but never closed")

            return text



        yaml_block = lines[1:end_idx]



        # Check if title already exists

        has_title = any(l.strip().lower().startswith('title:') for l in yaml_block)

        if has_title:

            return text



        # Extract potential title from content

        content_lines = lines[end_idx + 1:]

        title = extract_title_from_content(content_lines)



        # Insert title at the beginning of YAML block

        new_yaml = [f'title: "{title}"'] + yaml_block

        result_lines = [YAML_BOUNDARY] + new_yaml + [YAML_BOUNDARY] + content_lines

        stats.title_added = True

        return '\n'.join(result_lines) + ('\n' if text.endswith('\n') else '')



    else:

        # No YAML front matter - create one

        title = extract_title_from_content(lines)

        yaml_block = [

            YAML_BOUNDARY,

            f'title: "{title}"',

            YAML_BOUNDARY,

            ''

        ]

        result_lines = yaml_block + lines

        stats.title_added = True

        return '\n'.join(result_lines) + ('\n' if text.endswith('\n') else '')



def extract_title_from_content(lines: List[str]) -> str:

    """Extract a reasonable title from content lines."""

    for line in lines:

        line = line.strip()

        if not line:

            continue

        # Skip HTML comments

        if line.startswith('<!--'):

            continue

        # Look for first meaningful content

        if line.startswith('# '):

            return line[2:].strip()

        elif line and not line.startswith('['):

            # Take first non-ID line as title, truncate if too long

            clean_line = re.sub(r'^\[[\w\-]+\]\s*', '', line)

            return clean_line[:60] + ('...' if len(clean_line) > 60 else '')

    return "Untitled Document"



def auto_number_sections(text: str, stats: ProcessingStats) -> str:

    """Enhanced section numbering that preserves existing structure."""

    lines = text.splitlines()

    out_lines = []

    section_counter = 0

    in_yaml = False



    i = 0

    while i < len(lines):

        line = lines[i]



        # Track YAML boundaries

        if line.strip() == YAML_BOUNDARY:

            in_yaml = not in_yaml

            out_lines.append(line)

            i += 1

            continue



        if in_yaml:

            out_lines.append(line)

            i += 1

            continue



        # Skip empty lines, comments, and special markers

        if (not line.strip() or

            line.strip().startswith('<!--') or

            line.strip().startswith('#') or

            line.strip().startswith('::') or

            line.strip().startswith('.')):

            out_lines.append(line)

            i += 1

            continue



        # Check if this looks like a section heading

        # (non-empty line that's not an ID line and is followed by content)

        is_potential_section = (

            line.strip() and

            not ID_LEADING_RE.match(line) and

            i + 1 < len(lines)

        )



        if is_potential_section:

            # Check if already numbered

            if SECTION_HEADING_RE.match(line.strip()):

                out_lines.append(line)  # Already numbered

            else:

                # Add numbering

                section_counter += 1

                indented = line[:len(line) - len(line.lstrip())]  # Preserve indentation

                content = line.strip()

                out_lines.append(f"{indented}{section_counter} {content}")

                stats.sections_numbered += 1

        else:

            out_lines.append(line)



        i += 1



    return '\n'.join(out_lines) + ('\n' if text.endswith('\n') else '')



def create_backup(file_path: Path) -> Path:

    """Create a backup file with timestamp."""

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = file_path.with_suffix(f'.{timestamp}.bak')

    backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')

    return backup_path



def main():

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--file', '-f', required=True, help='Markdown file to process')

    parser.add_argument('--hide-local-uids', action='store_true', help='Move leading [ID] to HTML comments')

    parser.add_argument('--auto-numbering', action='store_true', help='Add section numbering')

    parser.add_argument('--auto-title', action='store_true', help='Ensure YAML title exists')

    parser.add_argument('--validate-ids', action='store_true', help='Validate ID format and uniqueness')

    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying')

    parser.add_argument('--backup', action='store_true', help='Create backup before changes')

    parser.add_argument('--inplace', action='store_true', help='Modify file in place')

    parser.add_argument('--output', '-o', help='Output file path')

    parser.add_argument('--stats', action='store_true', help='Show processing statistics')



    args = parser.parse_args()



    # Validate input file

    file_path = Path(args.file)

    if not file_path.exists():

        print(f"Error: File not found: {file_path}", file=sys.stderr)

        return 1



    try:

        text = file_path.read_text(encoding='utf-8')

    except Exception as e:

        print(f"Error reading file: {e}", file=sys.stderr)

        return 1



    stats = ProcessingStats()

    original_text = text



    # Always validate IDs if any processing is requested

    if any([args.hide_local_uids, args.auto_numbering, args.auto_title, args.validate_ids]):

        validate_ids(text, stats)



    # Apply transformations

    if args.auto_title:

        text = ensure_yaml_title(text, stats)



    if args.hide_local_uids:

        text = hide_local_uids(text, stats)



    if args.auto_numbering:

        text = auto_number_sections(text, stats)



    # Handle dry run

    if args.dry_run:

        print("=== DRY RUN MODE ===")

        if text != original_text:

            print("Changes would be made:")

            # Simple diff indication

            orig_lines = len(original_text.splitlines())

            new_lines = len(text.splitlines())

            print(f"  Lines: {orig_lines} -> {new_lines}")

        else:

            print("No changes would be made.")



        if args.stats:

            print("\n" + stats.report())

        return 0



    # Report errors

    if stats.errors:

        print("Errors found:", file=sys.stderr)

        for error in stats.errors:

            print(f"  {error}", file=sys.stderr)

        if not args.dry_run:

            print("Aborting due to errors. Use --dry-run to preview.", file=sys.stderr)

            return 1



    # Create backup if requested

    backup_path = None

    if args.backup and not args.dry_run:

        backup_path = create_backup(file_path)

        print(f"Backup created: {backup_path}")



    # Write output

    if not args.dry_run:

        try:

            if args.inplace:

                file_path.write_text(text, encoding='utf-8')

                print(f"File updated: {file_path}")

            else:

                output_path = Path(args.output) if args.output else file_path.with_name(f"{file_path.stem}-processed{file_path.suffix}")

                output_path.write_text(text, encoding='utf-8')

                print(f"Output written: {output_path}")

        except Exception as e:

            print(f"Error writing output: {e}", file=sys.stderr)

            return 1



    # Show statistics

    if args.stats:

        print("\n" + stats.report())



    # Show warnings

    if stats.warnings:

        print("\nWarnings:")

        for warning in stats.warnings:

            print(f"  {warning}")

    return 0



if __name__ == '__main__':
    sys.exit(main())
