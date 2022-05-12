import pandas as pd
import os

filedir = os.getcwd()


file_path = os.path.join(filedir,'..','sample_output.txt') 

# if file is saved per line json - which is default. 
# You can get single nested json array if calling get_pages_in_parallel( f_type='json')
df = pd.read_json(file_path,lines=True)
print(df)