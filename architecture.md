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

1 file per API response, organized in sub folders according to the api endpoint it was retrieved from.

## Database

Concat files into a duckdb file. Each endpoint gets its own table. The content of json files should be a VARIANT type.

The database will be a duckdb file on disk and used with read only.

Queries should be done using duckdb Python API.

Frequently used queries such as filtering to only match ids where a specific account participated should be made as reusable functions.

## Apps



### Streamlit

This app should use pages and have a sidebar for selecting the account(s) to look at data for and navigation between pages.
