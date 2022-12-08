#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from requests_html import HTMLSession



def main():
    # Instantiate options
    opts = Options()
    # opts.add_argument(" — headless") # Uncomment if the headless version needed
    opts.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    # Set the location of the webdriver
    s = Service(r"D:\tools\chromedriver.exe")

    # Instantiate a webdriver
    driver = webdriver.Chrome(options=opts, service=s)
    
    for c in string.ascii_lowercase:
        driver.get(r'https://dictionary.apa.org/browse/' + c)
        with open(c + ".html", 'w', encoding='utf-8') as fp:
            fp.write(driver.page_source)

    driver.quit()

# Main body
if __name__ == '__main__':
    main()