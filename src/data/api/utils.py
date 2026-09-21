"""Utility functions for Riot API interactions."""

import os
import json
import zstandard as zstd
from typing import Optional, Dict, Any


def save_compressed_json(data: Dict[str, Any], filename: str, data_dir: str = "data") -> str:
    """
    Save data as compressed JSON file with .json.zst extension.

    Args:
        data: Data to save
        filename: Name of the file (without extension)
        data_dir: Directory to save files in

    Returns:
        Path to the saved file
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, f"{filename}.json.zst")
    
    # Serialize to JSON
    json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    
    # Compress with zstd
    cctx = zstd.ZstdCompressor(level=3)
    compressed_data = cctx.compress(json_data)
    
    # Save to file
    with open(filepath, 'wb') as f:
        f.write(compressed_data)
    
    return filepath


def read_compressed_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Read a compressed JSON file.

    Args:
        filepath: Path to the .json.zst file

    Returns:
        Parsed JSON data, or None if failed
    """
    try:
        dctx = zstd.ZstdDecompressor()
        with open(filepath, 'rb') as f:
            compressed_data = f.read()
        json_data = dctx.decompress(compressed_data)
        return json.loads(json_data)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def list_compressed_files(data_dir: str = "data") -> list:
    """
    List all .json.zst files in the data directory.

    Args:
        data_dir: Directory to search

    Returns:
        List of file paths
    """
    if not os.path.exists(data_dir):
        return []
    
    files = []
    for f in os.listdir(data_dir):
        if f.endswith('.json.zst'):
            files.append(os.path.join(data_dir, f))
    return files
