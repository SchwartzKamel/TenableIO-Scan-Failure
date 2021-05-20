import requests
import datetime
import pandas as pd
from decouple import config

# decouple & config are used when this script is run on a server
ACCESS_KEY = config('ACCESS_KEY', default='')
SECRET_KEY = config('SECRET_KEY', default='')

# TODO - Turn into 'Lambda Form' -> or for Azure Functions
# Generates epoch timestamp for 24 hours ago
epoch = str((datetime.datetime.now() - datetime.timedelta(1)).timestamp())[:10]

# Request variables
base_url = "https://cloud.tenable.com/scans/"
querystring = {"last_modification_date": epoch}
headers = {
    "Accept": "application/json",
    "X-ApiKeys": "accessKey=" + ACCESS_KEY + ";secretKey=" + SECRET_KEY
}

# Get list of scans
response = requests.request(
    "GET", base_url, headers=headers, params=querystring)

# Transform the data into a DataFrame and extract necessary data
scans = response.json()
df_scans = pd.json_normalize(data=scans['scans'])
df_scans = df_scans[['name',
                     'id',
                     'type',
                     'status',
                     'last_modification_date']]
df_scans['last_modification_date'] = pd.to_datetime(
    df_scans['last_modification_date'], unit='s')
# Filter for aborted
df_scans = df_scans[(df_scans["status"].str.match("aborted"))]
df_scans = df_scans.reset_index(drop=True)
# TODO - Write 'df_scans' to DynamoDB/Azure equivalent for next section to read from

# TODO - Split this segment into 'Lambda Form' -> or for Azure Functions
# Check scan_id to see how many hosts were in the scan (if any), new column to add that data
for scan_id in df_scans['id']:
    url = base_url + str(scan_id)
    response = requests.request("GET", url, headers=headers)
    scan_details = response.json()
    if scan_details['hosts'] == []:
        df_scans['host_count'] = "No hosts available"
    else:
        df_scans['host_count'] = str(scan_details['hosts']) + "hosts available"

print(df_scans)
# TODO - Email out report of aborted scan info
