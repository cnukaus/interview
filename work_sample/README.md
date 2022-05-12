## How to generate data  
 
1. async_scrap.py to generate github extract  
2. test_twitter.py to generate twitter activity from recent days  
3. combine_file.py to combine files, and to add linked twitter profile  


Generated files:  

data\combined_GR12_final.csv
data\data description.txt

data\GR12_handleonly.txtsummary_user_info_commits.csv -commit collaboration in the same repo

github_scrap\twitter_search\scrap_output\tweets_of_interest.csv
github_scrap\twitter_search\scrap_output\network_topo.csv - who mentioned who




## function 1. github handle data extractor  

scrap\scrap.py  Extract features - github as data source


status: completed  

Config:  
- need to modify loginEXAMPLE.json to have your valid [personal token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in this file, 
- update test_scrap.py or async_scrap.py (faster) which now points to login.json in parent folder to your own file location  


## function 2. general feature process  

feature\
feature.py
feature_storage.py

status: POC feature filter, derivation built  

## function 3. twitter behaviour extractor  

twitter_search\
get_data.py

status: use github output which contains twitter username as input, extract tweets, to calculate activity by rank, who is mentioning who else to generate relationship network  
next step: search by user + keyword is not returning result. (search by keyword alone okay)


## Next step

- add grouping function of features, feature naming convention
- Unique UserID? across tables such as owocki in github and owocki in ETH chain
- Should field type be a class? (can specify source dataset, version etc)
- combine feature files? need something like Luigi for IO scheduling, or Kedro for pipeline?  
### design
create data type\portfolio hierarchy:  
testing https://github.com/activeloopai/Hub

### complex scenario
- 1. Update distance (I believe the time since last updating their profile) --meta patter is get last n - depend on Data History/Slow Change Dimension

Bio length (characters in their bio) -- various (string) function - looks like should be implemented in user application, rather than here

- 2. feature validity (from_time, to_time)

- 3. how to generate/maintain data type (header)

### Changes:  

7th Nov - added trottle trigger {'message': 'API rate limit exceeded for user ID 5101195.', 'documentation_url': 'https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting'}, possible to use multi-token according to file length
6th Nov - Add multiprocessing for faster scraping.
6th Nov - fix bug when user not available or case is different    
30th Oct: - Add 1 use case of feature derivation

23rd Oct: - created feature processing classes, function to filter feather

18th Oct: - default to all features on github