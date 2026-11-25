"""Database module for League of Analytics.

This module provides functions for building and querying a DuckDB database.
"""

from .main import (
    get_connection,
    list_compressed_files,
    make_duckdb,
    read_compressed_json,
)

__all__ = ['get_connection', 'list_compressed_files', 'make_duckdb', 'read_compressed_json']
