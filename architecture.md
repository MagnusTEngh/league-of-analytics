# Project architecture

## Files and folders

app/
data/


## Data collection

### 1. Get data from Riot API

Using these APIs
- https://developer.riotgames.com/apis

### 2. Save data as retrieved in .json.zst format

1 file per API response.

### 3. Read data using duckdb

Concat files into a duckdb file.

## App 
