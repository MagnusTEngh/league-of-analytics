# Project architecture

## Files and folders

```
league-of-analytics/
├── app/.          # contains the webapp
└── data/          # everything before app
    ├── storage.py # data management
    └── api/       # API related code
```

## Data collection

### 1. Get data from Riot API

Using these APIs
- https://developer.riotgames.com/apis

### 2. Save data as retrieved in .json.zst format

1 file per API response.

### 3. Read data using duckdb

Concat files into a duckdb file.

## App 
