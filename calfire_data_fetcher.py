from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from datetime import datetime
import os
import logging
import sys

log_format = '%(asctime)s|%(levelname)s| %(message)s'
logging.basicConfig(stream=sys.stdout, format=log_format, level=logging.INFO)

DATE_STRING = datetime.today().strftime(format='%Y-%m-%d')


class CalFire(object):
    def __init__(self):
        self.path_to_chromedriver = os.path.join(os.pardir, "chromedriver")

    def fetch_active_fires(self):
        url = 'https://www.fire.ca.gov/incidents/'
        df = self._fetch_data(url)
        filename = 'data/{}_calfire_active_fires.csv'.format(DATE_STRING)
        df.to_csv(filename, index=None)

    def fetch_all(self, start_year, end_year):
        dfs = []
        for year in range(start_year, end_year+1):
            url = 'https://www.fire.ca.gov/incidents/{}/'.format(year)
            df = self._fetch_data(url)
            df['year'] = year
            dfs.append(df)

        fire_df = pd.concat(dfs)

        filename = 'data/{}_calfire_data.csv'.format(DATE_STRING)
        fire_df.to_csv(filename, index=None)

    def _fetch_data(self, url):
        driver = webdriver.Chrome(self.path_to_chromedriver)
        driver.get(url)

        xpath_base_string = '//*[@id="incidentListTable"]/div/div/'
        fires = []
        page_number = 1
        while page_number:
            try:
                xpath_to_page_button = '//*[@id="incidentListTable"]/div/nav/ul/li[{}]/a'.format(page_number)
                page_button = driver.find_element_by_xpath(xpath_to_page_button)
                page_button.click()
            except NoSuchElementException as e:
                logging.debug(e)
                logging.info("Completed all pages")
                break

            # We scan by row, and the fetch data in each column of the row
            row_num = 2   # row_num 1 is the header
            while row_num:
                try:
                    res = []
                    for col_num in range(1, 6):
                        # col_num = 1 - 5 corresponds to name, date, county, acres, containment
                        xpath_to_element = '{}div[{}]/div[{}]'.format(xpath_base_string, row_num, col_num)
                        element = driver.find_element_by_xpath(xpath_to_element)
                        element = element.text
                        res.append(element)
                    fires.append(res)
                    row_num += 1
                except NoSuchElementException as e:
                    logging.debug(e)
                    logging.info("Got all rows on this page")
                    break
            logging.info("Completed page {}".format(page_number))
            page_number += 1

        driver.quit()
        df = pd.DataFrame(fires, columns=['name', 'start_date', 'county', 'acres', 'containment'])
        return df


if __name__ == '__main__':

    calfire = CalFire()
    calfire.fetch_active_fires()
