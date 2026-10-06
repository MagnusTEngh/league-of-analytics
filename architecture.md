# Project architecture

```
league-of-analytics/
└── src/
    ├── sample-data/.      # contains sample data for endpoints
        ├── match_v5/
        └── timelines/
    └── league-of-analytics/
        ├── app/           # contains the webapp(s)
        └── database/      # everything before app
        └── api/           # API related code
```

## Data collection

Using these APIs
- https://developer.riotgames.com/apis
- datadragon

There should be one class called RequestHandler at api/main.py. It will be responsible for rate limiting and running requests for each endpoint and storing the data. The storage path is an attribute set in its init method.

It will have a method that takes a summonername#tag as input, that finds all existing data per endpoint, sets self.current_account and then runs the requests necessary for gathering all missing data for the account.

Each endpoint is its own method with a shared request method which handles errors and such.

Note: list of match ids is not saved as it is just temporarily used for finding matches, not of analytical interest.

API responses are saved as they are received in the .json.zst format.

1 file per API response, organized in sub folders according to the api endpoint it was retrieved from.

File names are {region}_{id}.json.zst. Where id is either match_id, account-tag or similar.

## Database

A function concats files into a duckdb file, over writing if it already exists.

Each endpoint gets its own table. The content of json files should be a VARIANT type.

The database will be a duckdb file on disk and used with read only.

Queries should be done using duckdb Python API.

Frequently used queries such as filtering to only match ids where a specific account participated should be made as reusable functions. These are placed under database/utilS/

## Apps

Common pages should include:

- Home: Key stats such as amount of games played by queue and in total, winrates, games over time by patch and some fun stats like a high scores collection including highest amount of kills, deaths, assists, wards placed, dodged skillshots and missing pings.
- Champions: An overview of which Champions the player favors and a selector to pick a specific one for detailed stats. Selecting a champion should among other things show their splash art.
- Specific game viewer: just show all data associated with a selected match id.

Queries for this information should be functions that can be reused between apps. These are stored in apps/queries/ and can be grouped in the same file when it makes logical sense.

### Streamlit

This app should use pages and have a sidebar for selecting the account(s) to look at data for and navigation between pages.
