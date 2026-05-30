"""Recursively scan directories and group support files by parent folder."""

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from utils import is_supported


def scan_and_group(root_dir: str) -> Dict[str, List[str]]:
    """
    Recursively scan root_dir for supported files, group by direct parent folder.
    Files in root_dir itself are grouped under '.'.
    Returns {folder_path: [file_paths]}.
    """
    groups: Dict[str, List[str]] = defaultdict(list)

    for dirpath, _dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            if is_supported(fpath):
                # Group key is the direct parent directory
                groups[dirpath].append(fpath)

    # Sort files within each group for consistency
    for key in groups:
        groups[key].sort()

    return dict(groups)


def get_group_name(folder_path: str, root_dir: str) -> str:
    """Return a human-readable name for a folder group."""
    if folder_path == root_dir:
        return os.path.basename(root_dir) or "课程资料"
    return os.path.basename(folder_path)
