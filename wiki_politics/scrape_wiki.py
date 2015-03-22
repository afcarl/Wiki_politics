#!/usr/bin/env python
"""
coding=utf-8
"""
# imports
# *********************************
import csv
import os
import requests
import bs4
import urlparse
import pandas as pd
import numpy as np
import logging
# global variables
# *********************************
import time


__author__ = 'bjherger'
__version__ = '1.0'
__email__ = '13herger@gmail.com'
__status__ = 'Development'
__maintainer__ = 'bjherger'


# functions
# *********************************

def create_politician_df(base_url):
    logging.info('Creating politician DataFrame from URL: ' + str(base_url))
    # Get page, find table
    wiki_page = requests.get(base_url)
    wiki_soup = bs4.BeautifulSoup(wiki_page.text)
    table_soup = wiki_soup.find_all('table', {'class': 'sortable wikitable'})[0]

    # Find headers, normalize
    table_headers = [header.getText() for header in table_soup.find_all('th')]
    table_headers = [header.lower().replace(' ', '_').encode('ascii', errors='ignore') for header in table_headers]

    results_list = list()
    # Iterate through rows (politicians), pull data
    for row in table_soup.find_all('tr')[1:]:

        # Create dict containing cells for this row
        cells = [cell.get_text().encode('ascii', errors='ignore') for cell in row.find_all('td')]
        row_dict = dict(zip(table_headers, cells))

        # Deal with name, individual URL separately
        for cell in row.find_all('span', {'class': 'fn'}):

            # Overwrite name, due to issue with getText()
            row_dict['name'] = cell.get_text().encode('ascii', errors='ignore')

            # Check if individual URl exists, and add full URL if it does
            if (cell.find('a') is not None) and (cell.find('a').get('href', None) is not None):
                partial_url = cell.find('a').get('href', None)
                full_url = urlparse.urljoin(base_url, partial_url)
                row_dict['indiv_url'] = full_url

        # Add result to running list
        results_list.append(row_dict)

    # Transition to DataFrame, and subset to non-null URL
    result_df = pd.DataFrame(results_list)
    result_df = result_df[pd.notnull(result_df['indiv_url'])]

    # Include full text for House individual pages, write to pickle and CSV
    result_df['indiv_text'] = result_df['indiv_url'].apply(parse_individual_page)
    return result_df


def parse_individual_page(indiv_url):
    logging.info('Parsing individual URL: ' + str(indiv_url))
    indiv_url = requests.get(indiv_url)
    indiv_soup = bs4.BeautifulSoup(indiv_url.text)
    paragraph_list = [paragraph.get_text().encode('ascii', errors='ignore') for paragraph in indiv_soup.find_all('p')]
    full_string = '\n'.join(paragraph_list)
    logging.debug('Full string for page: ' + full_string)
    return full_string


def main():

    # Setup logging and directories
    logging.basicConfig(level=logging.INFO)
    output_directory = 'data/'
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Create House DataFrame, remove null URL entries
    house_df = create_politician_df(
        'http://en.wikipedia.org/wiki/Current_members_of_the_United_States_House_of_Representatives')

    house_df.to_pickle(os.path.join(output_directory, 'house_df.pkl'))
    house_df.to_csv(os.path.join(output_directory, 'house_df.csv'), quoting=csv.QUOTE_ALL)

    senate_df = create_politician_df('http://en.wikipedia.org/wiki/List_of_current_United_States_Senators')
    senate_df.to_pickle(os.path.join(output_directory, 'senate_df.pkl'))
    senate_df.to_csv(os.path.join(output_directory, 'senate_df.csv'))
# main
# *********************************

if __name__ == '__main__':
    main()


