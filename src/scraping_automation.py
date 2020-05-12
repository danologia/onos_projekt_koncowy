import os
from multiprocessing import Pool


def scrape_year(year):
    yr = 2000 + year
    os.system(f"python ../dona_scraping/scrape_year.py {yr}")


if __name__ == '__main__':
    years = range(10, 21, 1)
    with Pool(16) as p:
        print(p.map(scrape_year, list(years)))