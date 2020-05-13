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
import re
from src.settings import NODES_DIR, AUTHORS_DIR

UNKNOWN = 'Nieznane'


def scrape_authors_data(authors):
    options = Options()
    options.headless = True
    driver = webdriver.Firefox("./", options=options)
    pbar = tqdm(authors)
    all_entries = []
    for id, name in pbar:
        pbar.set_description(f"{id}: {name}")
        driver.get(f"https://dona.pwr.edu.pl/szukaj/default.aspx?nrewid={id}")

        wait = WebDriverWait(driver, 20)

        # %%
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadDock1_info_autora_C_RadLabel_pytanie1")))
        author_info = driver.find_element_by_css_selector("#RadDock1_info_autora_C_RadLabel_pytanie1").text
        data = author_info.split("\n")

        department_info = data[0]
        department_tokens = department_info.rsplit(', ', maxsplit=1)
        if len(department_tokens) > 1:
            department = department_tokens[1].strip(']')
        else:
            department = UNKNOWN

        # %%
        if len(data) > 1:
            orcid_data = data[1]
            match = re.search(r"ORCID:\s*(.+)\s*", orcid_data)
            if match:
                orcid = match.group(1)
            else:
                orcid = UNKNOWN
        else:
            orcid = UNKNOWN

        # %%
        if len(data) > 2:
            disciplines = data[2]
            match = re.search(r"dyscypliny:\s*(.+)\s*", disciplines)
            if match:
                disciplines = match.group(1).split(', ')
            else:
                disciplines = []
        else:
            disciplines = []

        # %%

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadTabStrip_dane_wyszukane")))
        button_row = driver.find_element_by_css_selector("#RadTabStrip_dane_wyszukane").text.split('\n')
        publications_number = '0'
        citations = '0'
        supervisorships = '0'
        for button in button_row:
            match = re.match(r"(.+):\s*(.+)", button)
            if match:
                bt_name = match.group(1)
                bt_value = match.group(2)
                if bt_name == 'Prace':
                    publications_number = bt_value.strip()
                elif bt_name == 'Promotorstwa':
                    supervisorships = bt_value.strip()
                elif bt_name == 'Cytowania':
                    citations = bt_value.strip()
        # %%

        entry = {
            'id': id,
            'name': name,
            'department': department,
            'orcid': orcid,
            'disciplines': disciplines,
            'publications': publications_number,
            'citations': citations,
            'supervisorships': supervisorships
        }
        all_entries.append(entry)
    return all_entries


if __name__ == '__main__':
    nodes = pd.read_csv(NODES_DIR)
    authors_data = list(zip(nodes['id'].to_list(), nodes['label'].to_list()))
    all_entries = scrape_authors_data(authors_data)
    with open(AUTHORS_DIR, 'w') as fp:
        json.dump(all_entries, fp, indent=1, ensure_ascii=False)