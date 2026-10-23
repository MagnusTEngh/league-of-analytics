# league-of-analytics

The goal is to create a simple data storage to build analytical apps on.

## Usage

| Process | Command |
|---|---|
| Collect json files from api | uv run collect |
| Build database | uv run build_db |
| Run streamlit locally |  |
| Run streamlit in Docker |  |

## Requirements

Nix is used for providing the development environment.

## Instructions

1. Clone the repo
2. Create a .env file after the template in .env.example. Note, each account you want to collect data for needs to be in the ACCOUNTS list in ´.env´
3. Enter the repository with a terminal and run ´nix develop´, and install the python environment using ´uv sync´
4. Collect data by using ´uv run src/league_of_analytics/api/main.py´
5. Build the database using ´uv run src/league_of_analytics/database/main.py´

## Nice to know

### File sizes

| File type | 1 file (kB) | 1,000 files (mB) |
| --- | --- | --- |
| Match_v5 | 10kB | 10mB |
| Timelines   | 50-90kB | 50-90MiB |

Notes:
- Uncompressed files are larger by about 5-10x the space required.
- Size of timelines files vary be game lenght.