### things to do:

Get a s3 credential (ideally gitcoin official) so we can connect to https://github.com/activeloopai/Hub  

API - can we get access to Gitcoin user data - either API, data table,

### Feature hierarchy:


[feature_source].[feature_set].[feature_name]

examples:

"[gitcoin.co](http://gitcoin.co/)"."user_sybil"."sybil_likelihood"

"[api.github.com](http://api.github.com/)"."reputation"."followers"

"manual_googlesheets"."joe"."favouriteicons_count"


### Selection criteria:


1. Coverage: data fields  covering a significant amount of users are prefered

sparse features require more preparation effort to be useful, it is possible to include, maybe sometimes consider to derive/pca/merge sparse ones

2. Battle-tested: Used in previous GR rounds

3. Subject Matter Experts

4. Industry anti-spam resources (curated list, blacklist, IP addresses)

5. based on data source list (asked for it from dao members)

### V0.1.1 feature name and datatype

[api.github.com]
- Number of repos, int
- Number of repos where fork=false, int
- Followers, int
- Followed, int
- watchers, int

   \#derived or row level
- total issues (summary from all repos), int
- highest open_issues_count of rep, int
- total forks (summary from all repos), int
- highest forks of rep, int
- total stars (summary from all repos), int
- highest stars of rep, int
- language, size, created_at, pushed_at date of each repo
-  Is the user followed by an authenticated github account - and history
- Most number of folders created across all repos, int
- Most number of files created across all reposts, int

[onchain][]
- wallet address 
- previous behaviour /# make use of http://tokenomics.io/gitcoin by tjayrush https://github.com/TrueBlocks/tokenomics.io

[gitcoin.co][behaviour]

- Registration, Date/Time
- Last Activity, Date/Time
- kudos collected, int
- quest started, int
- Quest finished, int
- donation row level data (Address, grant, quantity, token, time)
- hackathon started count, int
- bounty started count, int
- bounty finished count,int
- IP Address row level/summary data (IP, date or first/last date range)
- browsing row level data (type of url, date)
- changed_default_preference, boolean
- count of activities in each GR round
  data source TBD

[gitcoin.co][attributes]

- Email domain (Inherit from Github), string
- Feedback row level/summary
- Built avatar, boolean
- Job status, string
- Location, string


Other potential:

[gov.gitcoin.co]

/#Some data rules already on  [https://www.daostewards.xyz/](https://www.daostewards.xyz/))
[Discord activity raw data]

[user][self_defined_rules]



### Ref
[GR10 antifraud report blockscience] (https://medium.com/block-science/evaluating-the-anti-fraud-results-for-gitcoin-round-10-cec9277ce5b2)
combined dialog with Omnianalytics, Disruption

[internal Notion page of Anti-sybil workstream](https://www.notion.so/gitcoin/06fad27dbd2d49468aa810c92f1f28c2?v=0e00edb4b94b4555a3d7b71b8d193d6c)
