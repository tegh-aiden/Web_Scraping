import os
import requests
import youtube_dl
from selenium import webdriver
import subprocess
from zipfile import ZipFile
import re
from tqdm import tqdm

parent_dir = ""

driver_path = "C:/Program Files/chromedriver_win32/chromedriver.exe"
brave_path = "C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"

option = webdriver.ChromeOptions()
option.add_argument("--incognito")
option.headless = True
option.add_argument("--start-maximized")
option.binary_location = brave_path
browser = webdriver.Chrome(executable_path = driver_path, options=option)

unknown = list()

for root, dirs, files in os.walk(parent_dir):
    for dir in tqdm(dirs):
        print(dir)
        os.chdir(parent_dir + "/" + dir)
        try:
            with open('link.txt', 'r') as link_text:
                link = link_text.readline()
            link_text.close()
            if len([f for f in os.listdir(os.getcwd())]) > 2:
                continue
            if "dropbox" in link:
                print("Type: DB")
                browser.get(link)
                # Get m3u8
                element = browser.find_element_by_xpath(
                "//*[@id='vjs_video_3_html5_api']/source")
                src = element.get_attribute('src')
                # Get title and formatting
                title = browser.title
                x = min(20, title.find("."))
                title = title[:x].replace(" ", "_")
                title = re.sub(r'[^\w\s]', '', title)
                # Call yt-dl
                cmd = subprocess.Popen("youtube-dl --no-warnings -q -o "+title+".mp4 " + src, shell = True)
                cmd.wait()
                cmd.terminate()
            elif "imgur" in link:
                print("Type: IMG")
                r = requests.get(link + "/zip", stream = True)
                with open('pics.zip', 'wb') as f:
                    for chunk in r.iter_content():
                        f.write(chunk)
                f.close()
                ZipFile('pics.zip').extractall()
            else:
                print("Type: Other")
                unknown.append(dir)
        except:
            print("Exception at " + dir)
print(unknown)
browser.close()
