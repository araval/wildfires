import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Patch
import seaborn as sns
matplotlib.rcParams['font.family'] = "AppleGothic"
sns.set(style='darkgrid', palette='muted')

import pandas as pd
import re
import os

from datetime import datetime
from counties import *

TODAY = datetime.today()
TODAY = TODAY.strftime("%Y-%m-%d") # datestring to name files
SAN_FRANCISCO_LAND_AREA = 30022.4 #acres

def plot_annual_stats(fire_df):
    """
    fire_df: Pandas dataframe 

    Plots number of fires by year
    Plots total area burned by year
    Figures are saved in "images/<today>-annual-stats.png"

    """
    df = fire_df.groupby('year', as_index=False).agg({'area_SF':['sum','max', 'count']})
    df.columns = ['year', 'total_area_burned_SF', 'biggest_fire_area_SF', 'num_fires']
    f, a = plt.subplots(1, 2, figsize = (16, 5))

    a[0].bar(df.year, df.total_area_burned_SF, color='grey', alpha=0.7, label='total area burned')
    a[0].bar(df.year, df.biggest_fire_area_SF, color='orange', alpha=0.7, label='largest fire area')
    a[0].set_xticks(range(2002, 2022, 2))
    a[0].set_ylabel("Area (# San Franciscos)", fontsize=16)
    a[0].legend()

    a[1].bar(df.year, df.num_fires)
    a[1].set_xticks(range(2002, 2022, 2))
    a[1].set_ylabel("Number of Fires", fontsize=16)
    
    filename = "images/{}-annual-stats.png".format(TODAY)
    plt.savefig(filename, bbox_inches='tight', dpi=150)

def plot_monthly_stats(fire_df):
    """
    fire_df: Pandas dataframe 

    Plots number of fires by calendar month
    Plots total area burned by calendar month
    Figures are saved in "images/<today>-monthly-stats.png"

    """
    fire_df['start_date'] = pd.to_datetime(fire_df.start_date)
    fire_df['month'] = fire_df.start_date.apply(lambda x: x.month)
    monthly_df = fire_df.groupby('month', as_index=False).agg({'acres':['sum', 'count', 'max'], 'area_SF': ['sum', 'max']})
    monthly_df.columns = ['month', 'total_area', 'num_fires', 'largest_fire_area', 'total_area_SF', 'largest_fire_SF']
    f, a = plt.subplots(1, 2, figsize = (16, 5))
    a[0].bar(monthly_df.month, monthly_df.total_area_SF, color='grey', alpha=0.5, label='total area burned')
    a[0].bar(monthly_df.month, monthly_df.largest_fire_SF, color='orange', alpha=0.5, label='largest fire area')
    a[0].set_ylabel("Area (# San Franciscos)", fontsize=16)
    a[0].set_xlabel("month", fontsize=16)
    a[0].legend()

    a[1].bar(monthly_df.month, monthly_df.num_fires)
    a[1].set_ylabel("# Fires", fontsize=16)
    a[1].set_xlabel("month", fontsize=16)
    
    filename = "images/{}-monthly-stats.png".format(TODAY)
    plt.savefig(filename, bbox_inches='tight', dpi=150)

def plot_county_stats(fire_df):
    """
    fire_df: Pandas dataframe

    Plots number of fires and area burned by county starting from 2002 until present
    Figures saved in images/<TODAY>-county-num-fires.png
    """

    #calfire excludes county if there are multiple, sometimes
    fire_df['county'].fillna('Multiple Counties', inplace=True) 
    
    # And sometimes, it includes all counties separated by commas, or 'and'
    def clean_county_name(name):
        if "," in name or 'and' in name:
            return 'Multiple Counties'
        else:
            return name
        
    fire_df['county2'] = fire_df.county.apply(clean_county_name)
    
    df = fire_df.groupby("county2", as_index=False).agg({'name':'count', 'acres':['sum', 'max']})
    df.columns = ['county', 'num_fires', 'total_area', 'largest_fire_area']
    
    # throw out 1 fire each from Mexico, Nevada and Oregon
    df = df[~df.county.isin(["State of Oregon", "State of Nevada", "Mexico"])]
    df['color'] = df.county.apply(get_county_color)
    

    """
    Plot number of fires by county
    """
    df = df.sort_values('num_fires', ascending=False)

    plt.figure(figsize=(18, 8))
    plt.bar(df.county, height=df.num_fires, color = df.color.values, alpha=0.7)
    plt.xticks(rotation=90, fontsize=14)
    plt.ylabel("# fires   (2002-present)", fontsize=16)
    plt.xlabel("County", fontsize=16)

    legend_elements = [Patch(facecolor='teal', label='SF Bay Area'),
                      Patch(facecolor='orange', label='SoCal'),
                      Patch(facecolor='pink', label='Sierras/Cascades'),
                      Patch(facecolor='maroon', label='Multiple counties'),
                      Patch(facecolor='grey', label='Northern and Central Coast, Central Valley')]

    plt.legend(handles=legend_elements, loc='best',fancybox=True, frameon=True, facecolor='w', fontsize=14 )

    filename = "images/{}-county-num-fires.png".format(TODAY)
    plt.savefig(filename, bbox_inches='tight', dpi=150)
    
    
    """
    Plot total area burned by county
    """
    df = df.sort_values('total_area', ascending=False)
    df = df[df.county != "Multiple Counties"].copy()

    plt.figure(figsize=(18, 8))
    plt.bar(df.county, height=df.total_area, color = df.color.values, alpha=0.7)
    plt.xticks(rotation=90, fontsize=14)
    plt.ylabel("Total acres burned  (2002-present)", fontsize=16)
    plt.xlabel("County", fontsize=16)

    legend_elements = [Patch(facecolor='teal', label='SF Bay Area'),
                      Patch(facecolor='orange', label='SoCal'),
                      Patch(facecolor='pink', label='Sierras/Cascades'),
                      Patch(facecolor='grey', label='Other')]

    plt.legend(handles=legend_elements, loc='best',fancybox=True, frameon=True, facecolor='w', fontsize=14 )

    filename = "images/{}-county-fire-area.png".format(TODAY)
    plt.savefig(filename, bbox_inches='tight', dpi=150)

def process_dataframes(calfire, wikifire):
    """
    Wikipedia contains more information about each fire, however, it 
    only includes a subset of the actual number of fires in any given year.

    Calfire includes all fires, but it no longer shares data for fires before 2013.
    It also does not include end (contained) date, and a clean notes columns. Additional
    info on fires is presented in its own individual page.

    """

    # Rename column, and add empty columns to concatenate with older wiki data
    calfire.rename(columns={'acres_burned':'acres'}, inplace=True)
    calfire['notes'] = ''
    calfire['contained_date'] = None

    fire_df = pd.concat([wikifire[wikifire.year < 2013], calfire])

    # Convert acres from string to int
    fire_df.acres.fillna("", inplace=True)
    fire_df['acres'] = fire_df.acres.apply(lambda x: int(re.sub(",", "", x)) if x != '' else 0)
    fire_df["area_SF"] = fire_df['acres']/SAN_FRANCISCO_LAND_AREA

    return fire_df

if __name__ == '__main__':
    calfire = pd.read_csv("data/2020-08-26_calfire_data.csv")
    wikifire = pd.read_csv("data/2020-08-27_wiki_calfire_data.csv")
    fire_df = process_dataframes(calfire, wikifire)

    # All figures are saved in images/
    if not os.path.exists('images/'):
        os.mkdir('images')

    plot_annual_stats(fire_df)
    plot_monthly_stats(fire_df)
    plot_county_stats(fire_df)
