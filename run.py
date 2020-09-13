import pandas as pd
from plotter import Plotter
import wikipedia_calfire_scraper as wf
from calfire_data_fetcher import CalFire
import sys
import re
import os

import logging
log_format = '%(asctime)s|%(levelname)s| %(message)s'
logging.basicConfig(stream=sys.stdout, format=log_format, level=logging.INFO)

SAN_FRANCISCO_LAND_AREA = 30022.4   # acres


def get_combined_dataframe():
    """
    Gather data from Calfire and Wikipedia, and combine the two dataframes

    Wikipedia contains more information about each fire, however, it
    only includes a subset of the actual number of fires in any given year.

    Calfire includes all fires, but it no longer shares data for fires before 2013.
    It also does not include end (contained) date, and a clean notes columns. Additional
    info on fires is presented in its own individual page.

    Returns
    -------
    Dataframe with all data from 2002 - present
    """

    cf = CalFire()
    calfire = cf.get_data()
    wikifire = wf.get_data()

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

    fire_df = get_combined_dataframe()

    logging.info("Generating plots")
    plotter = Plotter()
    plotter.plot_annual_stats(fire_df)
    plotter.plot_monthly_stats(fire_df)
    plotter.plot_county_stats(fire_df)
