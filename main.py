import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import csv
import re
import datetime
import time
import whois
import socket


def get_whois(domain):
    query = whois.whois(domain)
    # print(type(query.expiration_date))
    # print(query)
    if type(query.creation_date) == list and type(query.expiration_date) == list:
        creation_date = str(query.creation_date[0].strftime("%B %d, %Y"))
        expiration_date = str(query.expiration_date[0].strftime("%B %d, %Y"))
    elif type(query.creation_date) == list or type(query.expiration_date) == list:
        if type(query.creation_date) == list:
            creation_date = str(query.creation_date[0].strftime("%B %d, %Y"))
            expiration_date = str(query.expiration_date.strftime("%B %d, %Y"))
        elif type(query.expiration_date) == list:
            creation_date = str(query.creation_date.strftime("%B %d, %Y"))
            expiration_date = str(query.expiration_date[0].strftime("%B %d, %Y"))
    elif query.creation_date == None and query.expiration_date == None:
        creation_date = 'No date detected'
        expiration_date = "No date detected"
    else:
        creation_date = str(query.creation_date.strftime("%B %d, %Y"))
        expiration_date = str(query.expiration_date.strftime("%B %d, %Y"))

    whois_server = query.whois_server if query.whois_server else 'No Whois Server Detected'
    name_servers = query.name_servers if query.name_servers else ['No Name Servers Detected','No Name Servers Detected']

    whois_row = [whois_server, name_servers[0] + ", " + name_servers[1], creation_date, expiration_date]

    return whois_row


#### Main Function ####
def scrape(domains):
    whois_row= []
    # function_time = time.time()
    df = []

    #### Format For "Date Added" Column ####
    date = datetime.datetime.now() 
    read_date = date.strftime("%B %d, %Y")

    #### Intializes Header For Googlesheets ####
    dataset = [["Domain", "Theme", "Detected", "Mosaic Server", "Date Added","IP Address", 'FQDN', "Whois Server", "Name Servers", "Creation Date", "Expiration Date"]]


    #### Loops through each domain performing a get request ####
    for domain in domains:
        FQDN = ''
        ip_address = ''
        theme_detected = ''
        no_theme_detected = ''
        url = "https://" + domain[0]
        serv = str(domain[1])
        #print(domain)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'}

        # print(domain)
        try:
            ip_address = socket.gethostbyname(domain[0])
            FQDN = socket.getfqdn(domain[0])
            whois_row = get_whois(domain[0])
            # print(whois_row)
        except socket.error:
            ip_address = 'Not Found'
            FQDN = 'Not Found'
        #### Get request ####
        try:
            request = requests.get(url, headers=headers,timeout=10) # stream=True, timeout=5
        except requests.exceptions.RequestException:
            #### Intializes a row to add the googlesheet if no connection ####
            dataset.append([url, "No Connection", "No", serv, read_date, ip_address, FQDN] + whois_row)
            # insert_to_table([url, "No Connection", "No", serv, read_date, ip_address, FQDN] + whois_row)
            # continue
            return 'No connection'


        #### Makes sure it's a 200 status on the response ####
        #### Will grab <link> tags and <script> tags from source code ####
        if request.status_code != 200:
            # print('No 200 Status Code')
            dataset.append([url, "No 200 Status Code", "No", serv, read_date, ip_address, FQDN] + whois_row)
            # insert_to_table([url, "No 200 Status Code", "No", serv, read_date, ip_address, FQDN] + whois_row)
            continue
        else:
            content = request.content
            soup = BeautifulSoup(content, 'html.parser')
            links = [link.get('href') for link in soup.find_all('link')]
            scripts = [link.get('src') for link in soup.find_all('script')]
            all_links = links + scripts

            #### If no links found adds to googlesheet for current domain ###
            if all_links == []:
                dataset.append([url, "No link tag", "No", serv, read_date, ip_address, FQDN] + whois_row)
                # insert_to_table([url, "No link tag", "No", serv, read_date, ip_address, FQDN] + whois_row)
                continue 

            # print(links)

            #### Loops through all links found and matches the regular expression looking for "/wp-content/themes/" ####
            #### Grabs the word after "themes/" which will most likely be the theme they are using ####
            for link in all_links:
                link = str(link)
                if re.search(r"(https?://\.)?(www\.)?(\w+)?(\.\w+)?/wp-content/themes/([\w'-]+)/*", link):
                    # print(link)
                    pattern = re.compile(r"(https?://\.)?(www\.)?(\w+)?(\.\w+)?/wp-content/themes/([\w'-]+)/*")
                    matches = pattern.finditer(link)
                    theme_detected = [match.group(5) for match in matches]
                    # print(theme_detected)
                else:
                    # print(link)
                    no_theme_detected = "No theme Detected"
                    # print('no match')
            # print(theme_detected)
            if theme_detected != '':
                row = [url, theme_detected[0], "Yes", serv, read_date, ip_address, FQDN] + whois_row
            else:
                row = [url, no_theme_detected, "No", serv, read_date, ip_address, FQDN] + whois_row 

            ### Adds row to dataset to be entered in googlesheets ####
            # insert_to_table(row)
            dataset.append(row)

    #### stores as pandas dataframe *may need for future use* ####
    df = pd.DataFrame(dataset, columns=["Domain", "Theme", "Detected", "Mosaic Server", "Date Added","IP Address", 'FQDN', "Whois Server", "Name Servers", "Creation Date", "Expiration Date"])
    # print(df)
    return df
    # return dataset
    # print(whois_row)


    # ### logs the time when the script ran ###

    # execution_time = (time.time() - function_time) 
    # log_file = open('log.txt', 'a')
    # log_file.write(date.strftime("%c") + ", " + read_date + " Execution Time for Script: {} sec".format(round(execution_time, 2)) + "\n")
    # log_file.close()

    # print(f" Execution Time for Script: {round(execution_time, 2)} sec")
    # print(len(dataset))





