from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas.errors import OutOfBoundsDatetime
from dateutil.parser._parser import ParserError

import logging
import sys

log_format = '%(asctime)s|%(levelname)s| %(message)s'
logging.basicConfig(stream=sys.stdout, format=log_format, level=logging.INFO)


def get_dataframe(year):
    """
    Scrapes data from Wikipedia page for <year>

    Parameters
    ----------
    year (int): The year to fetch data for.

    Returns
    -------
    Pandas dataframe with wildfire data
    """
    logging.info("Fetching year: {}".format(year))
    url = "https://en.wikipedia.org/wiki/{}_California_wildfires".format(year)
    html_page = requests.get(url).text
    parsed_page = BeautifulSoup(html_page, "html.parser")  
    tables = parsed_page.findAll("table")

    header, table = get_correct_table(tables)
    
    rows = table.find_all('tr')[1:]
    my_dict = {}
    for i, row in enumerate(rows):
        columns = row.find_all('td')
        entry = [x.get_text().strip() for x in columns]
        if len(entry) == 6:
            entry.append("")
        entry.append(year)
        my_dict[i] = entry

    df = pd.DataFrame(my_dict).T

    header.append("year")
    df.columns = header
    return df


def get_correct_table(tables):
    """
    Get correct table from various tables present in a wikipedia page based on header-content

    Parameters
    ----------
    tables (list of xml table elements)

    Returns
    -------
    table
        The correct table that contains fire information.
    """
    for table in tables:
        for t in table.contents:

            try:
                header = t.find_all('tr')[0]
                header = header.find_all('th')
            except AttributeError:
                continue
            try:
                header = [name.get_text().strip() for name in header]
            except Exception:
                continue
            if len(header) > 1 and header[1] == 'County':
                return header, table


def get_start_date(row):
    """
    Helper function for function 'clean_data' below.
    Some years include year in their dates "5th August, 2020"
    Other years do not, as in "5th August", considering the year is obvious from the page
    we are looking at.

    row: A row from a Pandas dataframe
    """
    day = row['start_date'].split(",")[0]
    date_string = '{}, {}'.format(day, row['year'])
    return pd.to_datetime(date_string)


def get_end_date(row):
    """
    Helper function for function 'clean_data' below.
    Similar issues as start_date (see function get_start_date)
    In addition, a fire can be active, in which case contained date is null. We will use
    today's date as 'contained_date'

    row: A row from a Pandas dataframe
    """
    day = row['contained_date'].split(",")[0]
    date_string = '{}, {}'.format(day, row['year'])
    try:
        date = pd.to_datetime(date_string)
    except OutOfBoundsDatetime:
        date = datetime.today().date()
    except ParserError:
        date = None
    return date


def clean_data(fires):

    """
    This function does the following:
    1. Rename columns to remove naming inconsistencies
       "contained_date" is listed as "Contained Date", "Contained date", "Containment date" etc.
       "start_date" is listed as "Start Date", "Start date" etc.
    2. Delete columns "Ref" and "KM2" which are present in tables for some years, and not for others
    3. Format date strings. Some years have year included in date and some do not
    4. For active fires, set end-dates to today.

    Parameters
    ----------
    fires (list): list of dataframes

    Returns
    -------
    Single dataframe with cleaned data
    """
    # Collect names from all dfs
    column_names = []
    for df in fires:
        column_names += list(df.columns)
    col_map = {}
    for name in column_names:
        if 'contain' in name.lower():
            col_map[name] = 'contained_date'
        elif 'start' in name.lower():
            col_map[name] = 'start_date'

    for df in fires:
        df.rename(columns=col_map, inplace=True)
        # Remove columns. These are either redundant, or not available across all years
        if 'Km2' in df.columns:
            df.drop('Km2', axis=1, inplace=True)
        if 'Ref' in df.columns:
            df.drop("Ref", axis=1, inplace=True)

    fires = pd.concat(fires)
    fires['start_date'] = fires.apply(get_start_date, axis=1)
    fires['contained_date'] = fires.apply(get_end_date, axis=1)
     
    fires.columns = [colname.lower() for colname in fires.columns]
    return fires


def get_fires(start_year, end_year):
    """
    Parameters
    ----------
    start_year, end_year (ints)
    Get data from <start_year> to <end_year> inclusive.

    Returns
    -------
    Pandas Dataframe
    """
    fires = []
    for year in range(start_year, end_year+1):
        df = get_dataframe(year)
        fires.append(df)
    return clean_data(fires)

def get_data():

    for filename in os.listdir('data/'):
        if 'wiki' in filename:
            wiki_files.append(filename)

    if len(wiki_files) == 0:
        logging.info("No file with wikipedia data found. Fetching now.")
        wiki_df = ws.get_fires(2002, 2013)
    else:
        wiki_files = sorted(wiki_files)
        logging.info("Using wiki file {}".format(wiki_files[-1]))
        wiki_filename = os.path.join("data", wiki_files[-1])
        wiki_df = pd.read_csv(wiki_filename)

    return wiki_df


if __name__ == '__main__':
    fire_df = get_fires(2002, 2020)
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    filename = '{}_wiki_calfire_data.csv'.format(date_string)
    fire_df.to_csv(filename, index=None)