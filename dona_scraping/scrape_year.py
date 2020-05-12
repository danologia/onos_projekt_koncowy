# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from selenium import webdriver
import pandas as pd
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import json
from tqdm import tqdm
import sys
import os
import time 


# %%
YEAR = 2020
if len(sys.argv) > 1:
    YEAR = int(sys.argv[1])

print(f"Scraping year {YEAR}...")
# %%
options = Options()
options.headless = True
driver = webdriver.Firefox("./", options=options)

# %%
driver.get("https://dona.pwr.edu.pl/szukaj/")

# %%
wait = WebDriverWait(driver, 20)

# %%
wait.until(EC.presence_of_element_located((By.XPATH, "//span[.='Formularz jednostki']")))
driver.find_element_by_xpath("//span[.='Formularz jednostki']").click()

# %%
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#RadDock_formularze_C_RadButton_szukaj_zaawansowane")))
driver.find_element_by_css_selector("#RadDock_formularze_C_RadButton_szukaj_zaawansowane").click()

# %%
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadComboBox_rok_zal_od_Input")))
driver.find_element_by_css_selector("#RadComboBox_rok_zal_od_Input").clear()
driver.find_element_by_css_selector("#RadComboBox_rok_zal_od_Input").send_keys(str(YEAR))
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadComboBox_rok_zal_do_Input")))
driver.find_element_by_css_selector("#RadComboBox_rok_zal_do_Input").clear()
driver.find_element_by_css_selector("#RadComboBox_rok_zal_do_Input").send_keys(str(YEAR))

# %%
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#RadButton_filtry_zastosuj > span:nth-child(1)")))
driver.find_element_by_css_selector("#RadButton_filtry_zastosuj > span:nth-child(1)").click()

# %%
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#RadGrid_glowny_ctl00_ctl03_ctl01_PageSizeDropDownList")))
driver.find_element_by_css_selector("#RadGrid_glowny_ctl00_ctl03_ctl01_PageSizeDropDownList").click()
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#RadGrid_glowny_ctl00_ctl03_ctl01_PageSizeDropDownList_DropDown")))
tmp = driver.find_element_by_css_selector("#RadGrid_glowny_ctl00_ctl03_ctl01_PageSizeDropDownList_DropDown").find_element_by_xpath("//li[.='30']")
driver.execute_script("arguments[0].click();",tmp)

# %%
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadAjaxLoadingPanel1RadGrid_glowny")))
WebDriverWait(driver, 100).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadAjaxLoadingPanel1RadGrid_glowny")))

# %%
num_pages = int(driver.find_element_by_css_selector(".rgInfoPart").find_elements_by_tag_name("strong")[1].text)

print("Scraping start...")
with tqdm(total=num_pages) as pbar:
    while True:
        try:
            rows = driver.find_element_by_css_selector("#RadGrid_glowny_ctl00 > tbody:nth-child(4)").find_elements_by_xpath("./tr")
            page_info = []
            for row in rows:
                entry = {}

                entry['authors'] = []
                authors = row.find_elements_by_xpath('.//span[@class="css_autor"]/..')
                for author in authors:
                    entry['authors'].append({
                        'link': author.get_attribute('href'),
                        'name': author.find_element_by_xpath(".//span").text
                    })

                entry['type'] = row.find_element_by_xpath(".//span[@class='RadLabel RadLabel_Bootstrap']").text
                entry['department'] = row.find_element_by_xpath(".//span[contains(@id, '_jednostka')]/span").text
                entry['year'] = row.find_element_by_xpath("./td[40]").text
                entry['text'] = "\n".join(row.find_element_by_xpath(".//span[contains(@id, '_opis_pracy_grid')]").text.split("\n")[1:])

                page_info.append(entry)

            page_num = driver.find_element_by_css_selector(".rgInfoPart").find_element_by_tag_name("strong").text
            os.makedirs(f"../data/{YEAR}", exist_ok=True)

            with open(f'../data/{YEAR}/{page_num}.json', 'w') as fp:
                json.dump(page_info, fp, indent=1, ensure_ascii=False)
                
            pbar.update(1)
        except:
            print(f"Failed in loading page")

     
        if int(page_num) < num_pages:
            driver.find_element_by_class_name("rgPageNext").click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadAjaxLoadingPanel1RadGrid_glowny")))
            WebDriverWait(driver, 500).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadAjaxLoadingPanel1RadGrid_glowny")))
        else:
            break


# %%


