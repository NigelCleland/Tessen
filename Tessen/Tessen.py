#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library Imports
import sys
import os
import datetime
from dateutil.parser import parse
import simplejson as json
from collections import defaultdict

# C Library Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Use a Static JSON file to provide default column names
# These can be overridden on a function by function basis
BASE_DIRECTORY = os.path.dirname(__file__)
with open(os.path.join(BASE_DIRECTORY, 'static_names.json')) as f:
    STATIC = json.load(f)

def load_frame(filename, date_col=STATIC['date_col'],
               period_col=STATIC['period_col']):

    df = pd.read_csv(filename)
    df = convert_dates(df, date_col=date_col)
    df = convert_periods(df, period_col=period_col)

    df = strip_title_columns(df)

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


def filter_dates(df, dates, date_col=STATIC['date_col']):
    dates = _check_iterator(dates)
    datetime_dates = []
    for d in dates:
        if not type(d) == datetime.datetime:
            datetime_dates.append(parse(d))
        else:
            datetime_dates.append(d)
    parsed_dates = [x.strftime('%Y-%m-%d') for x in datetime_dates]
    return _general_filter(df, date_col, parsed_dates)


def filter_periods(df, periods, period_col=STATIC['period_col']):
    periods = _check_iterator(periods)
    parsed_periods = [int(x) for x in periods]
    return _general_filter(df, period_col, parsed_periods)


def filter_stations(df, stations, station_col=STATIC['station_col']):
    stations = _check_iterator(stations)
    return _general_filter(df, station_col, stations)


def filter_company(df, companies, company_col=STATIC['company_col']):
    companies = _check_iterator(companies)
    return _general_filter(df, company_col, companies)


def filter_island(df, island, node_name, bus_id=STATIC['bus_name'],
                  island_name=STATIC['island_name']):

    # Load the mapping and get rid of the dupes
    map_name = os.path.join(BASE_DIRECTORY, STATIC["nodal_meta"])
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

    offers = load_frame(offer_filename)
    genres = load_frame(genres_filename)

    if dates:
        offers = filter_dates(offers, dates)
        genres = filter_dates(genres, dates)

    print len(offers)

    if periods:
        offers = filter_periods(offers, periods)
        genres = filter_periods(genres, periods)

    if companies:
        offers = filter_company(offers, companies)
        genres = filter_company(genres, companies)

    if stations:
        offers = filter_stations(offers, stations)
        genres = filter_stations(genres, stations)

    if island:
        offers = filter_island(offers, island, STATIC['offer_node'])
        genres = filter_island(genres, island, STATIC['genres_node'])


    return offers, genres


def strip_title_columns(df):
    df.rename(columns={x: x.strip().title() for x in df.columns},
                      inplace=True)

    return df

def classify_columns(band_columns):

    classification = defaultdict(dict)
    for b in band_columns:
        band = int(b.split('_')[0][-1])
        param = b.split('_')[-1]

        # Note can I write these better. Nested Ternaries are ugly
        reserve = "FIR" if "6S" in b else "SIR" if "60S" in b else "Energy"
        product = "PLSR" if "Plsr" in b else "TWDSR" if "Twdsr" in b else "IL" if "6S" in b else "Energy"

        classification[(product, reserve, band)][param] = b

    return classification


def stack_columns(df):

    def yield_single_stack(df):

        general_columns = [x for x in df.columns if "Band" not in x]
        band_columns = [x for x in df.columns if "Band" in x]
        classification = classify_columns(band_columns)

        for key in classification:
            allcols = general_columns + classification[key].values()

            single = df[allcols].copy()
            single["Product_Type"] = key[0]
            single["Reserve_Type"] = key[1]
            single["Band"] = key[2]
            single.rename(columns={v: k for k, v in classification[key].items()}, inplace=True)
            yield single

    arr = pd.concat(yield_single_stack(df), ignore_index=True)
    max_names = ("Power", "Max")
    arr.rename(columns={x: "Quantity" for x in max_names}, inplace=True)
    return arr


def incrementalise(df):
    """ Take a Stacked DataFrame and Incrementalise It """

    def yield_increment(df):
        df["Incr Quantity"] = 1
        for index, series in df.iterrows():
            quantity = series["Quantity"]
            while quantity > 0:
                series["Incr Quantity"] = min(1, quantity)
                yield series.copy()
                quantity -= 1

    return pd.concat(yield_increment(df), axis=1).T




if __name__ == '__main__':
    pass

