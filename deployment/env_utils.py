#!/usr/bin/env python3
"""
Environment file utilities for Phase 1 deployment scripts.

Provides section-based ownership of .env file where each script
can safely update only its own section without affecting others.
"""

from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Dict, Optional


def update_env_section(file_path: Path, section_name: str, section_content: List[str],
                       create_backup: bool = True) -> None:
    """
    Update a specific section in an environment file while preserving all other sections.

    Args:
        file_path: Path to the .env file
        section_name: Name of the section (e.g., "AUTHENTICATION")
        section_content: List of lines to write in the section (without section header)
        create_backup: Whether to create a backup before modifying
    """

    start_marker = f"# === {section_name} ==="

    # Create backup if requested and file exists
    if create_backup and file_path.exists():
        backup_name = file_path.parent / f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_name)
        print(f"📁 Created backup: {backup_name.name}")

    # Read existing content
    existing_lines = []
    if file_path.exists():
        with open(file_path, 'r') as f:
            existing_lines = f.readlines()

    # Find section boundaries
    start_idx = None
    end_idx = len(existing_lines)

    for i, line in enumerate(existing_lines):
        line_stripped = line.strip()
        if line_stripped == start_marker:
            start_idx = i
        elif start_idx is not None and line_stripped.startswith("# === ") and line_stripped != start_marker:
            end_idx = i
            break

    # Build new file content
    new_lines = []

    # Keep everything before our section
    if start_idx is not None:
        new_lines.extend(existing_lines[:start_idx])
    else:
        new_lines.extend(existing_lines)
        # Add separator if file has content but no sections yet
        if existing_lines and not existing_lines[-1].strip() == "":
            new_lines.append("\n")

    # Add our section
    new_lines.append(f"{start_marker}\n")
    for line in section_content:
        if not line.endswith('\n'):
            line += '\n'
        new_lines.append(line)

    # Add separator after our section
    if section_content:  # Only add separator if we have content
        new_lines.append("\n")

    # Keep everything after our section
    if start_idx is not None and end_idx < len(existing_lines):
        new_lines.extend(existing_lines[end_idx:])

    # Write atomically (write to temp file, then move)
    temp_file = file_path.with_suffix('.tmp')
    try:
        with open(temp_file, 'w') as f:
            f.writelines(new_lines)

        # Atomic move
        temp_file.replace(file_path)

    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise e


def read_env_section(file_path: Path, section_name: str) -> Dict[str, str]:
    """
    Read variables from a specific section of an environment file.

    Args:
        file_path: Path to the .env file
        section_name: Name of the section to read

    Returns:
        Dictionary of environment variables from that section
    """

    if not file_path.exists():
        return {}

    start_marker = f"# === {section_name} ==="
    variables = {}
    in_section = False

    with open(file_path, 'r') as f:
        for line in f:
            line_stripped = line.strip()

            if line_stripped == start_marker:
                in_section = True
                continue
            elif in_section and line_stripped.startswith("# === "):
                # Hit next section, stop reading
                break
            elif in_section and line_stripped and not line_stripped.startswith('#'):
                # Parse environment variable
                if '=' in line_stripped:
                    if line_stripped.startswith('export '):
                        _, rest = line_stripped.split('export ', 1)
                        key, value = rest.split('=', 1)
                    else:
                        key, value = line_stripped.split('=', 1)
                    variables[key] = value

    return variables


def get_all_env_vars(file_path: Path) -> Dict[str, str]:
    """
    Read all environment variables from the file, regardless of section.

    Args:
        file_path: Path to the .env file

    Returns:
        Dictionary of all environment variables
    """

    if not file_path.exists():
        return {}

    variables = {}

    with open(file_path, 'r') as f:
        for line in f:
            line_stripped = line.strip()

            if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                if line_stripped.startswith('export '):
                    _, rest = line_stripped.split('export ', 1)
                    key, value = rest.split('=', 1)
                else:
                    key, value = line_stripped.split('=', 1)
                variables[key] = value

    return variables
