import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import time
import io
from datetime import datetime
import re
import os
import json

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
    #initialise composition_element
    composition_element = None
   # Find the specific <div> element with id="section-materialsAndSuppliersAccordion"
    try:
        div_element = soup.find('div', {'id': 'section-materialsAndSuppliersAccordion'})
        composition_element = div_element.find('h3', text='Composition')
    except:
        pass
    if composition_element:
    # Find all <h4> elements that represent different materials (e.g., Shell, Pocket lining)
        material_headers = div_element.find_all('h4')
        if material_headers:
            for header in material_headers:
                # Get the material name (e.g., Shell, Pocket lining)
                material_name = header.text.strip()

                # Get the <p> element containing the material information
                material_info = header.find_next('p')

                # Extract the text content of the <p> element
                material_text = material_info.get_text(strip=True)

                # Append the material information with the corresponding tag
                fabric += f",[{material_name}] {material_text} "
        else:
            fabric = ",[Material] "
            for x in div_element.find_all('li'):
                for y in x.find_all('p'):
                    fabric = fabric + y.text
    try:
        additional_info_h3 = div_element.find('h3', text=' Additional material information')
        recycled_info_list = additional_info_h3.find_next('ul').find_all('li', text=lambda text: 'Recycled' in text or 'Organic' in text)

        if recycled_info_list:
            # Extract the text content of all the <li> elements containing "Recycled" information and store them in a list
            recycled_texts = [item.get_text(strip=True) for item in recycled_info_list]
            # Join all the elements in the list to form a single string
            recycled_info = ", ".join(recycled_texts)
            fabric += ", [Recycled] " + recycled_info
    except:
        pass
    return fabric

params = {
    'sort': 'stock',
    'image-size': 'small',
    'image': 'model',
    'offset': "1",
    'page-size': "50"}

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0'}

retries = 3  # Maximum number of retries
delay = 2  # Delay between retries in seconds

for attempt in range(retries):
    try:
        req = requests.get(
            'https://www2.hm.com/en_gb/ladies/new-arrivals/clothes/_jcr_content/main/productlisting.display.json',
            params=params,
            headers=headers)
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
        'page-size': str(page_size)}

    retries = 3  # Maximum number of retries
    delay = 2  # Delay between retries in seconds

    for attempt in range(retries):
        try:
            req = requests.get(
                'https://www2.hm.com/en_gb/ladies/new-arrivals/clothes/_jcr_content/main/productlisting.display.json',
                params=params,
                headers=headers)
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


def read_the_csv(file):
    df = pd.read_csv(file)
    return df

# split the material string into three lists [main material], [secondary material], [recycled material]
def parse_material_compositions(materialstring, recycled_tag='Recycled'):
    try:
        splitup = (materialstring.split(","))
    except:
        return [[],[],[]]
    lists = []
    newlist = []
    for i in splitup:
        i = i.strip()
        if len(i) == 0:
            continue
        if i[0] == "[":
            try:
                # If new list is empty do not append
                if newlist:
                    lists.append(newlist)
            except: 
                pass
            newlist = []
        newlist.append(i)
    lists.append(newlist)
    # clean square bracket tag from lists except recycled
    for l in lists:
        try:
            b = l[0].split('] ')
            l[0] = b[1]
        
            if b[0] == "[Recycled":  
                l.insert(0, "Recycled")
        except: 
            pass
    return lists

def get_recycled(lists):
    # recycled list is the one where the first element is 'Recycled'
    for i in lists:
        try:
            if(i[0] == "Recycled"):
                return i[1:]
        except:
            pass

def get_main(lists):
    # Main is always first list
    return lists[0]

def get_secondary(lists):
    # Obsolete however if needed returns list that is not recycled and not first
    if len(lists) <2:
        return
    secondary = []
    for i in lists[1:]:
        if(i[0] == "Recycled"):
            continue
        secondary.append(i)
    if len(secondary) == 0:
        return
    return secondary

def remove_trademark_symbol(input_string):
    # Define a regular expression pattern to match the trademark symbol (\u2122 and \U00002122) in a case-insensitive manner
    pattern = r'\\[Uu]([0-9a-fA-F]{4,8})'
    # Use re.sub() to replace all occurrences of the pattern with an empty string
    cleaned_string = re.sub(pattern, '', input_string)
    return cleaned_string

def split_material_and_percentage(input_string):
    # Define a regular expression pattern to match the material and percentage parts
    pattern = r'^(.*?)(\d+\%)$'
    # Use the re.match function to find the pattern in the input_string
    match = re.match(pattern, input_string)
    if match:
        # The first group (index 1) contains the material part
        material = match.group(1).strip()
        # The second group (index 2) contains the percentage part
        percentage = match.group(2).strip()
        material = remove_trademark_symbol(material)
        return material, percentage
    else:
        # If no match is found, return the entire string as material and an empty string for percentage
        return input_string.strip(), ""

def add_columns_and_values(df):
    # Iterate through each row of the DataFrame
    for index, row in df.iterrows():
        composition_list = get_main((parse_material_compositions(row["fabric"])))
        # Extracting the material name and percentage from the list
        for item in composition_list:
            try:
                material, percentage = split_material_and_percentage(item)
                percentage = float(percentage.strip('%'))
                # Adding a new column to the DataFrame if it doesn't exist
                if material.upper() not in df.columns:
                    df[material.upper()] = 0  # Initializing the column with None
                # Assigning the percentage value to the corresponding cell
                df.at[index, material.upper()] = percentage
            except:
                # old fabric function may of failed so we will try the link again to get the materials
                link = str(row['link'])
                new_fabric_value = fabric_function(link)
                df.at[index, 'fabric'] = new_fabric_value 
                composition_list = get_main((parse_material_compositions(new_fabric_value)))
                # Extracting the material name and percentage from the list
                for item in composition_list:
                    try:
                        material, percentage = split_material_and_percentage(item)
                        percentage = float(percentage.strip('%'))
                        # Adding a new column to the DataFrame if it doesn't exist
                        if material.upper() not in df.columns:
                            df[material.upper()] = 0  # Initializing the column with None
                        # Assigning the percentage value to the corresponding cell
                        df.at[index, material.upper()] = percentage
                    except:
                        pass
                pass
    return df


def add_recycled_columns_and_values(df):
    for index, row in df.iterrows():
        composition_list = get_recycled((parse_material_compositions(row["fabric"])))
        if composition_list:
            for item in composition_list:
                try:
                    material, percentage = split_material_and_percentage(item)
                    material = 'Sustainable ' + material
                    percentage = float(percentage.strip('%'))
                    # Adding a new column to the DataFrame if it doesn't exist
                    if material.upper() not in df.columns:
                        df[material.upper()] = 0  # Initializing the column with None
                    # Assigning the percentage value to the corresponding cell
                    df.at[index, material.upper()] = percentage
                except:
                    pass
    return df

def process_build_file(df, dt):
    materialsdf =add_columns_and_values(df)
    recycledmaterialsdf =add_recycled_columns_and_values(materialsdf)
    recycledmaterialsdf['Date'] = dt
    return recycledmaterialsdf;

def dataframe_to_json(df):
    json_string = df.to_json(orient='records')
    return json_string

current_datetime = datetime.now().strftime('%Y%m%d-%H%M%S')
df = process_build_file(df, current_datetime)
csv_filename = f"data/data_{current_datetime}.csv"

# Save the DataFrame to the CSV file
df.to_csv(csv_filename, index=False)

# Obsolete print (no longer used)
print(dataframe_to_json(df))
