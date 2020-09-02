from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas.errors import OutOfBoundsDatetime


def get_dataframe(year):
    """
    :param year: int. The year we want data for.
    :return: Pandas dataframe
    """
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
    Returns the correct table from various tables present in a wikipedia page based on header-content

    :param tables: (list). List of tables
    :return: table
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


def get_fires(min_year, max_year):
    fires = []
    for year in range(min_year, max_year+1):
        df = get_dataframe(year)
        fires.append(df)
    return clean_data(fires)


def get_start_date(row):
    """
    Some years include year in their dates "5th August, 2020"
    Other years do not, as in "5th August", considering the year is obvious from the page
    we are looking at.
    """
    day = row['start_date'].split(",")[0]
    date_string = '{}, {}'.format(day, row['year'])
    return pd.to_datetime(date_string)


def get_end_date(row):
    """
    Similar issues as start_date (see function get_start_date)
    In addition, a fire can be active, in which case contained date is null. We will use
    today's date as 'contained_date'
    """
    day = row['contained_date'].split(",")[0]
    date_string = '{}, {}'.format(day, row['year'])
    try:
        date = pd.to_datetime(date_string)
    except OutOfBoundsDatetime:
        date = datetime.today().date()
    return date


def clean_data(fires):

    """
    This does the following:
    1. Rename columns to remove naming inconsistencies
       "contained_date" is listed as "Contained Date", "Contained date", "Containment date" etc.
       "start_date" is listed as "Start Date", "Start date" etc.
    2. Delete columns "Ref" and "KM2" which are present in tables for some years, and not for others
    3. Format date strings. Some years have year included in date and some do not
    4. For active fires, set end-dates to today.

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


if __name__ == '__main__':
    fire_df = get_fires(2002, 2020)
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    filename = '{}_wiki_calfire_data.csv'.format(date_string)
    fire_df.to_csv(filename, index=None)
