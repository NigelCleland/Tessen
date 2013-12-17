#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library Imports
import sys
import os
import datetime
from dateutil.parser import parse
import simplejson as json

# C Library Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIRECTORY = os.path.dirname(__file__)
with open(os.path.join(BASE_DIRECTORY, 'static_names.json')) as f:
    STATICS = json.load(f)

def load_frame(filename, date_col=STATIC['date_col'],
               period_col=STATIC['period_col']):

    df = pd.read_csv(filename)
    df = convert_dates(df, date_col=STATIC['date_col'])
    df = convert_periods(df, period_col=STATIC['period_col'])

    return df

def convert_dates(df, date_col=None):

    unique_dates = df[date_col].unique()
    date_map = {date: datetime.datetime.strptime(date, '%d/%m/%Y') for date in unique_dates}
    df[date_col] = df[date_col].map(date_map)
    return df

def convert_periods(df, period_col=None):
    df[period_col] = df[period_col].astype(int)
    return df


def _general_filter(df, col, iterator):
    return pd.concat([df[df[col] == it] for it in iterator], ignore_index=True)


def _single_filter(df, col, item):
    return df[df[col] == item]


def _check_iterator(x):
    if not hasattr(x, '__iter__'):
        return [x]
    return x


def filter_dates(df, dates, date_col=None):
    dates = _check_iterator(dates)
    datetime_dates = []
    for d in dates:
        if not type(d) == datetime.datetime:
            datetime_dates.append(parse(d))
        else:
            datetime_dates.append(d)
    parsed_dates = [x.strftime('%Y-%m-%d') for x in datetime_dates]
    return _general_filter(df, date_col, parsed_dates)


def filter_periods(df, periods, period_col=None):
    periods = _check_iterator(periods)
    parsed_periods = [int(x) for x in periods]
    return _general_filter(df, period_col, parsed_periods)


def filter_stations(df, stations, station_col=None):
    stations = _check_iterator(stations)
    return _general_filter(df, station_col, stations)


def filter_company(df, companies, company_col=None):
    companies = _check_iterator(companies)
    return _general_filter(df, company_col, companies)


def filter_island(df, island, node_name=None, bus_id=STATIC['bus_name'],
                  island_name=STATIC['island_name']):

    # Load the mapping and get rid of the dupes
    map_name = os.path.join(base_directory, STATIC["nodal_meta"])
    island_map = pd.read_csv(map_name)
    imap = island_map[[bus_id, island_name]].drop_duplicates()

    # Strip due to extra whitespace on some nodes
    df[node_name] = df[node_name].apply(lambda x: x.strip())
    mdf = df.merge(imap, left_on=node_name, right_on=bus_id)

    # Simple filter is fine as only single islands are possible
    return mdf[mdf[island_name] == island]


def load_generator_data(offer_filename, genres_filename, dates=None,
                        periods=None, companies=None, stations=None,
                        island=None):

    pass


if __name__ == '__main__':
    pass

