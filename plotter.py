import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Patch
import seaborn as sns

import pandas as pd
from datetime import datetime
from counties import *

matplotlib.rcParams['font.family'] = "AppleGothic"
sns.set(style='darkgrid', palette='muted')

TODAY = datetime.today()
TODAY = TODAY.strftime("%Y-%m-%d")   # date-string to name files


class Plotter(object):

    def __init__(self, df):
        self.df = df

    def generate_all_plots(self):
        self.plot_annual_stats()
        self.plot_monthly_stats()
        self.plot_county_stats()
        self.plot_largest_fires()

    def plot_annual_stats(self):
        """
        Plots number of fires by year
        Plots total area burned by year

        Parameters
        ----------
        df (Pandas dataframe): dataframe containing wildfire data.

        Returns
        -------
        Figures are saved in "images/<today>-annual-stats.png".
        """
        df = self.df.groupby('year', as_index=False).agg({'area_SF': ['sum', 'max', 'count']})
        df.columns = ['year', 'total_area_burned_SF', 'biggest_fire_area_SF', 'num_fires']
        f, a = plt.subplots(1, 2, figsize=(16, 5))

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

    def plot_monthly_stats(self):
        """
        Plots number of fires by calendar month
        Plots total area burned by calendar month

        Returns
        -------
        Nothing. Figures are saved in "images/<today>-monthly-stats.png"
        """

        df = self.df.copy()
        df['start_date'] = pd.to_datetime(df.start_date)
        df['month'] = df.start_date.apply(lambda x: x.month)
        monthly_df = df.groupby('month', as_index=False).agg({'acres': ['sum', 'count', 'max'],
                                                              'area_SF': ['sum', 'max']})
        monthly_df.columns = ['month', 'total_area', 'num_fires', 'largest_fire_area',
                              'total_area_SF', 'largest_fire_SF']
        f, a = plt.subplots(1, 2, figsize=(16, 5))
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

    def plot_county_stats(self):
        """
        Plots number of fires and area burned by county starting from 2002 until present

        Returns
        -------
        Nothing.
        Figures saved in images/<TODAY>-county-num-fires.png
        """

        df = self.df.copy()
        # calfire excludes county if there are multiple, sometimes
        df['county'].fillna('Multiple Counties', inplace=True)

        # And sometimes, it includes all counties separated by commas, or 'and'
        def clean_county_name(name):
            if "," in name or 'and' in name:
                return 'Multiple Counties'
            else:
                return name

        df['county2'] = df.county.apply(clean_county_name)

        df = df.groupby("county2", as_index=False).agg({'name': 'count', 'acres': ['sum', 'max']})
        df.columns = ['county', 'num_fires', 'total_area', 'largest_fire_area']

        # throw out 1 fire each from Mexico, Nevada and Oregon
        df = df[~df.county.isin(["State of Oregon", "State of Nevada", "Mexico"])]
        df['color'] = df.county.apply(get_county_color)

        # Plot number of fires by county
        df = df.sort_values('num_fires', ascending=False)

        plt.figure(figsize=(18, 8))
        plt.bar(df.county, height=df.num_fires, color=df.color.values, alpha=0.7)
        plt.xticks(rotation=90, fontsize=14)
        plt.ylabel("# fires   (2002-present)", fontsize=16)
        plt.xlabel("County", fontsize=16)

        legend_elements = [Patch(facecolor='teal', label='SF Bay Area'),
                           Patch(facecolor='orange', label='SoCal'),
                           Patch(facecolor='pink', label='Sierras/Cascades'),
                           Patch(facecolor='maroon', label='Multiple counties'),
                           Patch(facecolor='grey', label='Northern and Central Coast, Central Valley')]

        plt.legend(handles=legend_elements, loc='best', fancybox=True, frameon=True, facecolor='w', fontsize=14)

        filename = "images/{}-county-num-fires.png".format(TODAY)
        plt.savefig(filename, bbox_inches='tight', dpi=150)

        # Plot total area burned by county
        df = df.sort_values('total_area', ascending=False)
        df = df[df.county != "Multiple Counties"].copy()

        plt.figure(figsize=(18, 8))
        plt.bar(df.county, height=df.total_area, color=df.color.values, alpha=0.7)
        plt.xticks(rotation=90, fontsize=14)
        plt.ylabel("Total acres burned  (2002-present)", fontsize=16)
        plt.xlabel("County", fontsize=16)

        legend_elements = [Patch(facecolor='teal', label='SF Bay Area'),
                           Patch(facecolor='orange', label='SoCal'),
                           Patch(facecolor='pink', label='Sierras/Cascades'),
                           Patch(facecolor='grey', label='Other')]

        plt.legend(handles=legend_elements, loc='best', fancybox=True, frameon=True, facecolor='w', fontsize=14)

        filename = "images/{}-county-fire-area.png".format(TODAY)
        plt.savefig(filename, bbox_inches='tight', dpi=150)

    def plot_largest_fires(self, n=20):
        """
        Plots n largest fires

        Parameters
        ----------
        n (int): number of fires

        Returns
        -------
        Nothing.
        Figures saved in images/<TODAY>-largest_fires.png
        """
        df = self.df.sort_values(by='acres', ascending=False)
        df = df.iloc[:n, :].copy()
        df.county.fillna("", inplace=True)

        # Add year to fire name for display in plot
        def get_display_name(row):
            name = row['name']
            new_name = name.split("(")[0].strip()
            display_name = '{}, {}'.format(new_name, row.year)
            return display_name

        df['display_name'] = df.apply(get_display_name, axis=1)

        # We will color code the last five years, all other years will be grey
        current_year = datetime.today().year
        years = [i for i in range(current_year, current_year - 5, -1)]
        colors = ['#cc3300', '#ff8c66', '#e6ac00', '#ffd24d', '#ffdf80']

        def get_color(year):
            if year in years:
                return colors[years.index(year)]
            else:
                return 'grey'

        df['color'] = df.year.apply(get_color)

        plt.figure(figsize=(18, 8))
        plt.bar(df.display_name, height=df.area_SF, color=df.color, alpha=0.6)

        legend_elements = [Patch(facecolor=colors[i], label=str(years[i])) for i in range(5)]
        plt.legend(handles=legend_elements, loc='best', fancybox=True, frameon=True, facecolor='w', fontsize=14)

        plt.xticks(rotation=90, fontsize=16)
        plt.yticks(fontsize=16)

        plt.ylabel("Fire area    (# SFs)", fontsize=16)
        plt.title("Twenty Largest Fires", fontsize=24)

        filename = "images/{}-largest_fires.png".format(TODAY)
        plt.savefig(filename, bbox_inches='tight', dpi=150)
