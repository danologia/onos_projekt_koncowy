from selenium import webdriver
import pandas as pd
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import json
from tqdm import tqdm
import sys
import os
import time
import re
from src.settings import DEFAULT_NODES_DIR, AUTHORS_DIR
import multiprocessing
import logging
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from urllib3.connectionpool import log as urllibLogger
UNKNOWN = 'Nieznane'


def scrape_authors_data(login, password, authors):
    options = Options()
    options.headless = True
    driver = webdriver.Firefox("./", options=options)
    pbar = tqdm(authors)
    driver.get('https://dona.pwr.edu.pl/szukaj/')
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadButton_login")))
    driver.find_element_by_css_selector("#RadButton_login").click()

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadTextBox_uzytkownik")))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadTextBox_haslo")))
    driver.find_element_by_css_selector("#RadTextBox_uzytkownik").send_keys(login)
    driver.find_element_by_css_selector("#RadTextBox_haslo").send_keys(password)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadButton_zaloguj")))
    driver.find_element_by_css_selector("#RadButton_zaloguj").click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadDock_formularze_C_RadSearchBox1_Input")))

    for id, name in pbar:
        try:
            pbar.set_description(f"{id}: {name}")
            driver.get(f"https://dona.pwr.edu.pl/szukaj/default.aspx?nrewid={id}")

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

            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#RadDock1_info_autora_C_RadLabel_liczba_prac")))
            work_and_impact_factor_data = driver.find_element_by_css_selector(
                "#RadDock1_info_autora_C_RadLabel_liczba_prac").text
            tokens = work_and_impact_factor_data.split('\n')
            if len(tokens) > 3:
                impact_factor_line = tokens[3]
                impact_factor = impact_factor_line.split(':')[1].strip()
            else:
                impact_factor = 0

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
                'impact_factor': impact_factor,
                'supervisorships': supervisorships
            }
        except TimeoutException:
            logging.warning(f"Problem with {id}: {name}, replacing with placeholder")
            entry = {
                'id': id,
                'name': name,
                'department': UNKNOWN,
                'orcid': UNKNOWN,
                'disciplines': [],
                'publications': 0,
                'citations': 0,
                'impact_factor': 0,
                'supervisorships': 0
            }
        with open(os.path.join(AUTHORS_DIR, str(id) + ".json"), 'w') as fp:
            json.dump(entry, fp, indent=1, ensure_ascii=False)


if __name__ == '__main__':
    logging.basicConfig(filename='authors_downloading.log', level=logging.DEBUG)
    seleniumLogger.setLevel(logging.WARNING)
    urllibLogger.setLevel(logging.WARNING)
    login = os.environ['LOGIN']
    password = os.environ['PASSWORD']
    nodes = pd.read_csv(DEFAULT_NODES_DIR, dtype=object)
    authors_data = list(zip(nodes['id'].to_list(), nodes['label'].to_list()))
    already_downloaded = [name.split('.')[0] for name in os.listdir(AUTHORS_DIR)]
    print(f"Skipping {len(already_downloaded)} already downloaded authors")
    to_download = [data for data in authors_data if data[0] not in already_downloaded]
    scrape_authors_data(login, password, to_download)