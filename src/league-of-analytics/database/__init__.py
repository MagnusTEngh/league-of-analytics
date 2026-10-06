"""Database module for League of Analytics.

This module provides functions for building and querying a DuckDB database.
"""

from .main import (
    make_duckdb,
    get_connection,
    read_compressed_json,
    list_compressed_files,
)

__all__ = ['make_duckdb', 'get_connection', 'read_compressed_json', 'list_compressed_files']
