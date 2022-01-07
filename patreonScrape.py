from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import requests
import re
from tqdm import tqdm
import asyncio
import aiohttp

EMAIL = ""
PASS = ""

driver_path = "C:/Program Files/chromedriver_win32/chromedriver.exe"
brave_path = "C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"
chrome_path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"

parent_dir = os.getcwd()

class patreon_Scrape:
    def __init__(self, driver_path, browser_path, executor = None, session_id = None):
        if executor is None:
            option = webdriver.ChromeOptions()
            option.add_argument("--incognito")
            option.add_argument("--start-maximized")
            option.binary_location = browser_path
            self.browser = webdriver.Chrome(executable_path = driver_path, options=option)
            print(self.browser.command_executor._url)
            print(self.browser.session_id)
            self.browser.get("https://www.patreon.com/")
            WebDriverWait(self.browser, 5)
            self.login(EMAIL, PASS)
            WebDriverWait(self.browser, 10).until(EC.title_contains("Home"))
        else:
            option = webdriver.ChromeOptions()
            option.headless = True
            self.browser = webdriver.Remote(command_executor= executor, options=option)
            self.browser.session_id = session_id
        self.session = aiohttp.ClientSession()

    #Input login info
    def login(self, username, password):
        element = self.browser.find_element_by_link_text('Log In')
        element.click()
        element = self.browser.find_element_by_xpath("//*[@id='email']")
        element.send_keys(username)
        element = self.browser.find_element_by_xpath("//*[@id='password']")
        element.send_keys(password)
        try:
            element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//form/div[5]/button")))
            element.click()
        except TimeoutException:
            print("Element not found")
            self.browser.quit()
        print("Logged In")

    #Get post links and print them
    def get_x_posts(self, x, patreon_user_link):
        element = WebDriverWait(self.browser, 10).until(EC.title_contains("Home"))
        self.browser.get(patreon_user_link)
        wait = 10
        counter = 0
        for i in range(x):
            try:
                element = WebDriverWait(self.browser, 90, poll_frequency = 3).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='renderPageContentWrapper']/div[1]/div[3]/div/div/div/div[4]/div/div/div[5]/button")))
                element.click()
                counter += 1
                WebDriverWait(self.browser, wait)
            except ElementClickInterceptedException:
                wait += 10
                continue
            except TimeoutException:
                break
        element = self.browser.find_element_by_xpath("//*[@id='renderPageContentWrapper']/div[1]/div[3]/div/div/div/div[4]/div/div/ul")
        links = [link.get_attribute("href") for link in element.find_elements_by_tag_name('a') if link.get_attribute("data-tag") == "post-published-at"]
        with open("Links.txt", "w+") as text_file:
            for link in links:
                text_file.write(link + "\n")
        text_file.close()

    async def scrape_post(self, post_url, token):
        self.browser.get(post_url)
        title = self.browser.title
        x = min(20, title.find(" | "))
        title = re.sub(r'[^\w\s]', '', title)
        title = str(token) + "_" + title[:x].replace(" ", "_")
        try:
            element = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH,
            "//*[@id='renderPageContentWrapper']/div[1]/div/div/div[2]/div[3]/div/div/div/div/div")))
            print()
            print(title)
            post = element.find_elements_by_xpath('div')
        except TimeoutException:
            print("Timeout")
            return
        if len(post) == 1:
            body = post[0]
            body.screenshot(title + '.png')
        else:
            path = os.path.join(parent_dir, title) + "/"
            os.mkdir(path)
            content = post[0]
            body = post[1]
            print(content.get_attribute('class'))
            if content.get_attribute('class') == 'sc-jrAGrp lihEVP':
                content = content.find_element_by_tag_name('a')
                link = content.get_attribute('href')
                with open(path + 'link.txt', 'w') as link_text:
                    link_text.write(link)
                link_text.close()
            else:
                await self.scrape_image(content, path)
            WebDriverWait(self.browser, 3)
            with open(path + 'sc.png','wb') as f:
                f.write(body.screenshot_as_png)
            f.close()

    async def scrape_image(self, content, path):
        n = len(content.find_elements_by_tag_name("img"))
        img = content.find_element_by_xpath(".//div/img")
        img.click()
        sources = []
        if n == 1:
            img = self.browser.find_element_by_xpath("/html/body/div[2]/div[3]/div[2]/div[1]/div/img")
            sources.append(img.get_attribute('src'))
            button = self.browser.find_element_by_xpath("/html/body/div[2]/div[3]/button")
            button.click()
        else:
            button = self.browser.find_element_by_xpath("/html/body/div[2]/div[3]/button[2]")
            for i in range(n):
                img = self.browser.find_element_by_xpath("/html/body/div[2]/div[3]/div[2]/div[1]/div/img")
                sources.append(img.get_attribute('src'))
                button.click()
            button = self.browser.find_element_by_xpath("/html/body/div[2]/div[3]/button[3]")
            button.click()
        download_tasks = (
            self.download(sources[i], path + str(i)) for i in range(len(sources))
            )
        await asyncio.gather(*download_tasks)

    async def download(self, src, name, chunk_size = 100000):
        match = re.search(r'/1\..+\?', src)
        ext = match.group()[2:-1]
        async with self.session.get(src) as response:
            with open(name + ext, 'wb') as file:
                while True:
                    chunk = await response.content.read(chunk_size)
                    if not chunk:
                        break
                    file.write(chunk)
            file.close()

async def main():
    # To continue debugging with same session, copy and pass
    # executor address and session id from stdout
    p = patreon_Scrape(driver_path, chrome_path)
    with open('', 'r') as f:
        links = f.readlines()
    f.close()
    for i in range(len(links)):
        await o.scrape_post(links[i], i)
    await o.session.close()

if __name__ == '__main__':
    try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    except Exception as e:
        print(e)
    finally:
        loop.close()
