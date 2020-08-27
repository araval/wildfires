from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime

def get_dataframe(year):
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
    for table in tables:
        for t in table.contents:

            try:
                header = t.find_all('tr')[0]
                header = header.find_all('th')
            except Exception as e:
                continue
            try:
                header = [name.get_text().strip() for name in header]
            except Exception as e:
                continue
            if len(header) > 1 and header[1] == 'County':
                return header, table

def get_fires(min_year, max_year):
    fires = []
    for year in range(min_year, max_year+1):
        df = get_dataframe(year)
        fires.append(df)

    fire_df = clean_data(fires)
    return fire_df

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
    Similar issues as start_date.
    In addition, a fire can be active, in which case contained date is null. We will use
    today's date as 'contained_date'
    """
    day = row['contained_date'].split(",")[0]
    date_string = '{}, {}'.format(day, row['year'])
    try:
        date = pd.to_datetime(date_string)
    except Exception as e:
        date = datetime.today().date()
    return date

def clean_data(fires):

    # rename columns to remove naming inconsistencies
    # "contained_date" is listed as "Contained Date", "Contained date", "Containment date" etc.
    # "start_date" is listed as "Start Date", "Start date" etc.
    column_names = [] #collect names from all dfs
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
        # remove columns. These are either redundant, or not available across all years
        if 'Km2' in df.columns:
            df.drop('Km2', axis=1, inplace=True)
        if 'Ref' in df.columns:
            df.drop("Ref", axis=1, inplace=True)

    fire_df = pd.concat(fires)
    fire_df['start_date'] = fire_df.apply(get_start_date, axis=1)
    fire_df['contained_date'] = fire_df.apply(get_end_date, axis=1) 
     
    fire_df.columns = [colname.lower() for colname in fire_df.columns]
    return fire_df

if __name__ == '__main__':
    fire_df = get_fires(2002, 2020)
    now = datetime.now()
    date_string = now.strftime(format='%Y-%m-%d')
    filename = '{}_wiki_calfire_data.csv'.format(date_string)
    fire_df.to_csv(filename, index=None)
