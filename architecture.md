# Project architecture

## Files and folders

```
league-of-analytics/
└── src/
    ├── sample-data/
        ├── match_v5/
        └── timelines/
    └── league-of-analytics/
        ├── app/           # contains the webapp
        └── database/      # everything before app
        └── api/           # API related code
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

Common pages should include:

- Home: Key stats such as amount of games played by queue and in total, winrates, games over time by patch and some fun stats like a high scores collection including highest amount of kills, deaths, assists, wards placed, dodged skillshots and missing pings.
- Champions: An overview of which Champions the player favors and a selector to pick a specific one for detailed stats. Selecting a champion should among other things show their splash art.
- Specific game viewer: just show all data associated with a selected match id.

Queries for this information should be functions that can be reused between apps.

### Streamlit

This app should use pages and have a sidebar for selecting the account(s) to look at data for and navigation between pages.
