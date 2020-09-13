from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from datetime import datetime
import os
import logging
import sys
import argparse

log_format = '%(asctime)s|%(levelname)s| %(message)s'
logging.basicConfig(stream=sys.stdout, format=log_format, level=logging.INFO)

DATE_STRING = datetime.today().strftime(format='%Y-%m-%d')


class CalFire(object):
    def __init__(self):
        path_to_chromedriver = os.path.join(os.pardir, "chromedriver")
        self.driver = webdriver.Chrome(path_to_chromedriver)

    def get_data(self):
        """
        Read data from disk if file available, else fetch from web.

        Returns
        -------
        Dataframe with fire data.
        """

        calfire_filename = None
        for filename in os.listdir('data/'):
            if 'wiki' not in filename:
                calfire_filename = filename

        if not calfire_filename:
            logging.info("No file with Cal Fire data found locally. Fetching now.")
            df = self.fetch(2013, 2020)
        else:
            logging.info("Using Calfire file {}".format(calfire_filename))
            df = pd.read_csv(calfire_filename)

            file_date = calfire_filename.split("_")[0]
            file_date = pd.to_datetime(file_date)

            data_age = (datetime.today() - file_date).days

            if data_age < 10:
                return df

            if data_age < 30:
                logging.info("Local file is more than 10 days old. Updating with current active fires")
                active_fires = self.fetch_active_fires()
                df.loc[df.name.isin(active_fires.name), :] = active_fires
            else:
                logging.info("Local file is more than a month old. Updating file")
                current_year = datetime.today().year
                fires = self.fetch(current_year, current_year)
                df = pd.concat([df[df.year < current_year], fires])

            os.remove(calfire_filename)

        filename = 'data/{}_calfire_data.csv'.format(DATE_STRING)
        df.to_csv(filename, index=None)
        return df

    def fetch_active_fires(self):
        url = 'https://www.fire.ca.gov/incidents/'
        df = self._fetch_data(url)
        self.driver.quit()
        return df

    def fetch(self, start_year, end_year):
        dfs = []
        for year in range(start_year, end_year+1):
            url = 'https://www.fire.ca.gov/incidents/{}/'.format(year)
            logging.info("Fetching Calfire data for year {}".format(year))
            df = self._fetch_data(url)
            df['year'] = year
            dfs.append(df)

        fire_df = pd.concat(dfs)

        self.driver.quit()
        return fire_df

    def _fetch_data(self, url):
        self.driver.get(url)
        xpath_base_string = '//*[@id="incidentListTable"]/div/div/'
        fires = []
        page_number = 1
        while page_number:
            try:
                xpath_to_page_button = '//*[@id="incidentListTable"]/div/nav/ul/li[{}]/a'.format(page_number)
                page_button = self.driver.find_element_by_xpath(xpath_to_page_button)
                page_button.click()
            except NoSuchElementException as e:
                logging.debug(e)
                logging.debug("Completed all pages")
                break

            # We scan by row, and then fetch data in each column of the row
            row_num = 2   # row_num 1 is the header
            while row_num:
                try:
                    res = []
                    for col_num in range(1, 6):
                        # col_num = 1 - 5 corresponds to name, date, county, acres, containment
                        xpath_to_element = '{}div[{}]/div[{}]'.format(xpath_base_string, row_num, col_num)
                        element = self.driver.find_element_by_xpath(xpath_to_element)
                        element = element.text
                        res.append(element)
                    fires.append(res)
                    row_num += 1
                except NoSuchElementException as e:
                    logging.debug(e)
                    logging.debug("Got all rows on this page")
                    break
            logging.debug("Completed page {}".format(page_number))
            page_number += 1

        df = pd.DataFrame(fires, columns=['name', 'start_date', 'county', 'acres', 'containment'])
        return df


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--update", required=False, help="get only currently active fires")
    ap.add_argument("-s", "--start_year", default=2013, required=False, help="get fires starting from this year")
    ap.add_argument("-e", "--end_year", default=2020, required=False, help="get fires ending on this year")
    args = vars(ap.parse_args())

    calfire = CalFire()
    if args['update']:
        calfire.fetch_active_fires()
    else:
        start_year = int(args['start_year'])
        if start_year < 2013:
            logging.info("Calfire data is only available from 2013 onwards.")
            start_year = 2013
        end_year = int(args['end_year'])
        logging.info("Fetching complete data starting from {} to {}.".format(start_year, end_year))

        calfire.fetch(start_year, end_year)
