import pandas as pd
from plotter import Plotter
import wikipedia_calfire_scraper as ws
from calfire_data_fetcher import CalFire

import sys

import re
import os

import logging
log_format = '%(asctime)s|%(levelname)s| %(message)s'
logging.basicConfig(stream=sys.stdout, format=log_format, level=logging.INFO)

SAN_FRANCISCO_LAND_AREA = 30022.4   # acres


def get_latest_dataframe():
    """
    If there are files in data/ use the latest file (using dates in filenames)
    If the data folder is empty, fetch fire data and proceed
    """

    wiki_files = []
    calfire_files = []

    for filename in os.listdir('data/'):
        if 'wiki' in filename:
            wiki_files.append(filename)
        else:
            calfire_files.append(filename)

    if len(wiki_files) == 0:
        logging.info("No file with wikipedia data found. Fetching now.")
        wiki_df = ws.get_fires(2002, 2013)
    else:
        wiki_files = sorted(wiki_files)
        logging.info("Using wiki file {}".format(wiki_files[-1]))
        wiki_filename = os.path.join("data", wiki_files[-1])
        wiki_df = pd.read_csv(wiki_filename)

    if len(calfire_files) == 0:
        logging.info("No file with Cal Fire data found. Fetching now.")
        calfire = CalFire()
        calfire_df = calfire.fetch(2013, 2020)
    else:
        calfire_files = sorted(calfire_files)
        logging.info("Using calfire file {}".format(calfire_files[-1]))
        calfire_filename = os.path.join("data", calfire_files[-1])
        calfire_df = pd.read_csv(calfire_filename)

    df = process_dataframes(calfire_df, wiki_df)

    return df


def process_dataframes(calfire, wikifire):
    """
    Wikipedia contains more information about each fire, however, it
    only includes a subset of the actual number of fires in any given year.

    Calfire includes all fires, but it no longer shares data for fires before 2013.
    It also does not include end (contained) date, and a clean notes columns. Additional
    info on fires is presented in its own individual page.
    """

    # Rename column, and add empty columns to concatenate with older wiki data
    calfire.rename(columns={'acres_burned': 'acres'}, inplace=True)
    calfire['notes'] = ''
    calfire['contained_date'] = None

    all_fires = pd.concat([wikifire[wikifire.year < 2013], calfire])

    # Convert acres from string to int
    all_fires.acres.fillna("", inplace=True)
    all_fires['acres'] = all_fires.acres.apply(lambda x: int(re.sub(",", "", x)) if x != '' else 0)
    all_fires["area_SF"] = all_fires['acres']/SAN_FRANCISCO_LAND_AREA

    return all_fires


if __name__ == '__main__':

    # All figures are saved in images/
    if not os.path.exists('images/'):
        os.mkdir('images')

    # Save data in data/
    if not os.path.exists('data/'):
        os.mkdir('data')

    fire_df = get_latest_dataframe()

    plotter = Plotter()
    plotter.plot_annual_stats(fire_df)
    plotter.plot_monthly_stats(fire_df)
    plotter.plot_county_stats(fire_df)
