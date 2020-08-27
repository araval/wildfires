from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from datetime import datetime
import os

path_to_chromedriver = os.path.join(os.pardir, "chromedriver")
driver = webdriver.Chrome(path_to_chromedriver) 

XPATH_BASE_STRING = '//*[@id="incidentListTable"]/div/div/div[{}]/'

dfs = []
for year in range(2013, 2021): #current calfire website contains data starting from 2013 
    url = 'https://www.fire.ca.gov/incidents/{}/'.format(year)
    print(url)
    driver.get(url)
    
    fires = []
    page_number = 1
    while page_number:
        try:
            page_button = driver.find_element_by_xpath('//*[@id="incidentListTable"]/div/nav/ul/li[{}]/a'.format(page_number))
            page_button.click()
        except NoSuchElementException as e:
            print("Completed all pages")
            break
        for row_num in range(2, 12): # row_num 1 is the header
            try:
                res []
                for i in range(1, 6):
                    # i = 1 - 5 corresponds to name, date, county, acres, containment
                    element = driver.find_element_by_xpath('{}div[{}]/div[{}]'.format(XPATH_BASE_STRING, row_num, i)).text
                    res.append(element)
                fires.append(res)
            except NoSuchElementException as e:
                print("Got all rows on this page")
                break
        print("Completed page {}".format(page_number))
        page_number += 1
    df = pd.DataFrame(fires, columns=['name', 'start_date', 'county', 'acres_burned', 'containment'])
    df['year'] = year
    dfs.append(df)
        
driver.quit()
fire_df = pd.concat(dfs)
now = datetime.now()
date_string = now.strftime(format='%Y-%m-%d')
filename = '{}_calfire_data.csv'.format(date_string)
fire_df.to_csv(filename, index=None)
