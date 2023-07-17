import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import time
import io

def fabric_function(link):
    base_url = 'https://www2.hm.com'
    url = base_url + link

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    }

    with requests.Session() as session:
        retries = 3  # Maximum number of retries
        delay = 2  # Delay between retries in seconds

        for attempt in range(retries):
            try:
                req = session.get(url, headers=headers)
                req.raise_for_status()  # Raise an exception if the request was unsuccessful
                break  # If successful, exit the retry loop
            except (requests.RequestException, ConnectionError):
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    raise  # If all retries fail, raise the exception

        soup = bs(req.content, 'html.parser')

    fabric = ""

    for x in soup.find_all('li'):
        for y in x.find_all('p'):
            fabric = y.text

    # Add a delay between requests
    time.sleep(2)
    return fabric


params = {
    'sort': 'stock',
    'image-size': 'small',
    'image': 'model',
    'offset': "1",
    'page-size': "50"
}


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0'
}

retries = 3  # Maximum number of retries
delay = 2  # Delay between retries in seconds

for attempt in range(retries):
    try:
        req = requests.get(
            'https://www2.hm.com/en_gb/ladies/new-arrivals/clothes/_jcr_content/main/productlisting.display.json',
            params=params,
            headers=headers
        )
        req.raise_for_status()  # Raise an exception if the request was unsuccessful
        break  # If successful, exit the retry loop
    except (requests.RequestException, ConnectionError):
        if attempt < retries - 1:
            time.sleep(delay)
            continue
        else:
            raise  # If all retries fail, raise the exception

init = req.json()

page_size = 500
total_products = int(init['total'])
offset = 0
df = pd.DataFrame()
print(total_products)
while offset < total_products:
    params = {
        'sort': 'stock',
        'image-size': 'small',
        'image': 'model',
        'offset': str(offset),
        'page-size': str(page_size)
    }

    retries = 3  # Maximum number of retries
    delay = 2  # Delay between retries in seconds

    for attempt in range(retries):
        try:
            req = requests.get(
                'https://www2.hm.com/en_gb/ladies/new-arrivals/clothes/_jcr_content/main/productlisting.display.json',
                params=params,
                headers=headers
            )
            req.raise_for_status()  # Raise an exception if the request was unsuccessful
            break  # If successful, exit the retry loop
        except (requests.RequestException, ConnectionError):
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            else:
                raise  # If all retries fail, raise the exception

    data = req.json()
    new_df = pd.DataFrame(data['products'])
    new_df['fabric'] = new_df.link.apply(fabric_function)
    
    df = pd.concat([df, new_df], axis=0, ignore_index=True)
    offset += page_size

# csv_string = df.to_csv(index=False)

# # Read the CSV string and print each line
# csv_io = io.StringIO(csv_string)
# for line in csv_io:
#     print(line.strip())

import json
def dataframe_to_json(df):
    json_string = df.to_json(orient='records')
    return json_string

print(dataframe_to_json(df)
