import urllib
import requests
import time
import re
import numpy as np
import pandas as pd
import json
from selenium import webdriver
from bs4 import BeautifulSoup as bs
steamAPIKey = "STEAMAPIKEY"
browser = webdriver.Chrome()
browser.set_script_timeout(1000)
maxpages = 3 #Max pages to scrape
url_base = "http://store.steampowered.com/search/?sort_by=Name_ASC&tags=21978&page=" #URL of steam store
url_details_base = "http://store.steampowered.com/api/appdetails?appids=" #URL for additional game information
url_playercount_base = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?key=" #URL to get playercount
url_page_base = "http://store.steampowered.com/app/"
string_ignore = ["353370", "353380", "358040"] #These 3 appids appear on every page, ignore them
totallinkcount = 0
#Intialize lists to store data
list_appid = []
list_name = []
list_price = []
list_playercount = []
list_earlyaccess = []
list_releasedate = []
list_developer = []
list_publisher = []
list_windows = []
list_mac = []
list_linux = []
list_languages = []
list_oculus = []
list_vive = []
list_wmr = [] #Windows mixed reality
list_url = []

validLanguages = ["English", "Spanish", "Mandarin", "Arabic", "Japanese", "Russian", "Portuguese", "Punjabi", "Hindi", "Urdu","Chinese","French","German","Italian","Korean","Vietnamese"]

with open("pagedata.txt", "w+") as file:
    for pagenumber in range(maxpages):
        linkcount = 0
        url_final = url_base + str(pagenumber) #Update page number
        browser.get(url_final)
        res = browser.page_source #Grab html from selenium
        res_bs = bs(res, "html.parser") #Beautify returned html
        for link in res_bs.find_all('a'):
            if "http://store.steampowered.com/app/" in link.get("href"): #Ignore items from string_ignore
                if any(
                        ignored_string in link.get("href")
                        for ignored_string in string_ignore):
                    continue
                item = link.get("href")
                item_list = item.split("/")
                appid = item_list[4] #Grab appid
                name = item_list[5] #Grab app name
                list_appid.append(appid)
                list_name.append(name)
                url_details_final = url_details_base + appid
                browser.get(url_details_final)
                response_details = browser.page_source
                response_details = response_details.encode('utf-8', 'ignore')
                response_details_json = json.loads(browser.find_element_by_tag_name("body").text.encode('utf-8', 'ignore'))
                appid=str(appid)
                try:
                    releasedate = response_details_json[appid]["data"]["release_date"]["date"]
                except KeyError:
                    releasedate = np.nan
                try:
                    developer = response_details_json[appid]["data"]["developers"][0]
                except KeyError:
                    developer = np.nan
                try:
                    publisher = response_details_json[appid]["data"]["publishers"][0]
                except KeyError:
                    publisher = np.nan
                try:
                    windows = response_details_json[appid]["data"]["platforms"]["windows"]
                except KeyError:
                    windows = np.nan
                try:
                    mac = response_details_json[appid]["data"]["platforms"]["mac"]
                except KeyError:
                    mac = np.nan
                try:
                    linux = response_details_json[appid]["data"]["platforms"]["linux"]
                except KeyError:
                    linux = np.nan
                try:
                    languages = ""
                    languagesString = response_details_json[appid]["data"]["supported_languages"]
                    languages = [word for word in validLanguages if word in languagesString]
                except KeyError:
                    languages = np.nan

                list_releasedate.append(releasedate)
                list_developer.append(developer)
                list_publisher.append(publisher)
                list_windows.append(windows)
                list_mac.append(mac)
                list_linux.append(linux)
                list_languages.append(languages)

                #list_releasedate.append(releasedate)
                try:
                    price = (re.search("\$\d+(?:\.\d+)?",
                                       response_details)).group()[1:] #Get price from html, handle if no price found
                except AttributeError:
                    print("Price not found")
                    print(appid)
                    if "\"is_free\":false" in response_details:
                        price = np.nan
                    else:
                        price = 0
                #print(price)
                list_price.append(price)
                url_playercount_final = url_playercount_base + steamAPIKey + "&format=json&appid=" + appid
                response_playercount = requests.get(url_playercount_final) #Get current playercount of game
                playercount_dict = json.loads(response_playercount.text)
                try: #Parse the returned json file
                    list_playercount.append(
                        playercount_dict["response"]["player_count"])
                except KeyError:
                    list_playercount.append(np.nan)

                if "Early Access" in response_details:
                    list_earlyaccess.append(True)
                else:
                    list_earlyaccess.append(False)
                
                url_page_final = url_page_base + appid
                browser.get(url_page_final)
                pagehtml = browser.page_source
                if "vr_htcvive\":true" in pagehtml:
                    vive = True
                else:
                    vive = False
                if "vr_oculusrift\":true" in pagehtml:
                    oculus = True
                else:
                    oculus = False
                if "vr_windowsmr\":true" in pagehtml:
                    wmr = True
                else:
                    wmr = False

                list_vive.append(vive)
                list_oculus.append(oculus)
                list_wmr.append(wmr)
                list_url.append(url_page_final)

                linkcount += 1
                totallinkcount += 1
                print("Total items: "+str(totallinkcount))
                if totallinkcount%100 == 0: #Every 100 requests wait for 2 minutes.  Steam blocks requests if sent too frequently.
                    print("Sleep 120 seconds")
                    time.sleep(120)
        if (linkcount <= 3): #If 3 or less items present, then page has no new games on it.
            break
    browser.close() #Exit selenium

df = pd.DataFrame({ #Combine lists to pandas dataframe
    "AppID": list_appid,
    "Name": list_name,
    "PlayerCount": list_playercount,
    "PriceUSD": list_price,
    "EarlyAccess": list_earlyaccess,
    "ReleaseDate": list_releasedate,
    "Developer": list_developer,
    "Publisher": list_publisher,
    "Windows": list_windows,
    "Mac": list_mac,
    "Linux": list_linux,
    "Languages": list_languages,
    "WindowsMixedReality": list_wmr,
    "Vive": list_vive,
    "Oculus": list_oculus,
    "URL": list_url
})
print(df)
df.to_csv("Data.csv",encoding='utf-8-sig')
