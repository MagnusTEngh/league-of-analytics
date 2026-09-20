Process for getting data:


1. Retrieve list of downloaded match histories.
2. Find all matches for summonername
   First find puuid for gamename#tag using https://developer.riotgames.com/apis#accountv1/GET_getByRiotId
   Then find all matches using https://developer.riotgames.com/apis#match-v5/GET_getMatchIdsByPUUID
3. Exclude already downloaded matches.
4. Download missing matches.
    both match info https://developer.riotgames.com/apis#match-v5/GET_getMatch
and timeline https://developer.riotgames.com/apis#match-v5/GET_getTimeline

Rate limit for Riot games API is:
- 20 requests every 1 second
- 100 requests every 2 minutes