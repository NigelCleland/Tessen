#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_Tessen
----------------------------------

Tests for `Tessen` module.
"""

# Standard Library Imports
import sys
import os
import datetime
from dateutil.parser import parse

# C Library Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import unittest

from Tessen import Tessen



class TestTessen(unittest.TestCase):

    def setUp(self):
        self.offers = Tessen.load_frame('./test_data/offers20131212.csv')
        self.il = Tessen.load_frame('./test_data/ilreserves20131212.csv')
        self.genres = Tessen.load_frame('./test_data/generatorreserves20131212.csv')

    def length_test(self, df, col, length):
        unique = df[col].unique()
        self.assertTrue(len(unique) == length)

    def in_test(self, df, col, items):
        unique = df[col].unique()
        for i in items:
            self.assertTrue(i in unique)

    def not_in_test(self, df, col, items):
        unique = df[col].unique()
        for i in items:
            self.assertTrue(i not in unique)

    def col_type_test(self, df, col, type):
        self.assertTrue(df[col].dtype == type)


    def tearDown(self):
        pass


class TestTessenDataLoading(TestTessen):

    def test_load_generation(self):
        offers = Tessen.load_frame('./test_data/offers20131212.csv')
        self.assertTrue(isinstance(offers, pd.DataFrame))
        self.assertTrue(type(self.offers["Trading_Date"].ix[0]) == pd.tslib.Timestamp)
        self.assertTrue(self.offers["Trading_Period"].dtype == int)

    def test_load_ilres(self):
        il = Tessen.load_frame('./test_data/ilreserves20131212.csv')
        self.assertTrue(isinstance(il, pd.DataFrame))
        self.assertTrue(type(self.il["Trading_Date"].ix[0]) == pd.tslib.Timestamp)
        self.assertTrue(self.il["Trading_Period"].dtype == int)


    def test_load_genres(self):
        genres = Tessen.load_frame('./test_data/generatorreserves20131212.csv')
        self.assertTrue(isinstance(genres, pd.DataFrame))
        self.assertTrue(type(self.genres["Trading_Date"].ix[0]) == pd.tslib.Timestamp)
        self.assertTrue(self.genres["Trading_Period"].dtype == int)



class TestAllGeneratorLoading(TestTessen):

    def setUp(self):

        self.offers, self.genres = Tessen.load_generator_data(
            './test_data/offers20131212.csv',
            './test_data/generatorreserves20131212.csv',
            periods=(12, 14), companies=("MRPL", "GENE"),
            stations=("TKU", "MTI"), island="North Island")


    def test_datatypes(self):

        self.assertTrue(type(self.offers) == pd.DataFrame)
        self.assertTrue(type(self.genres) == pd.DataFrame)


    def test_periods(self):
        self.length_test(self.offers, "Trading_Period", 2)
        self.length_test(self.genres, "Trading_Period", 2)

        self.in_test(self.offers, "Trading_Period", (12, 14))
        self.in_test(self.genres, "Trading_Period", (12, 14))

        self.not_in_test(self.offers, "Trading_Period", (26, 1))
        self.not_in_test(self.genres, "Trading_Period", (26, 1))


    def test_stations(self):
        self.length_test(self.offers, "Station", 2)
        self.length_test(self.genres, "Station", 2)

        self.in_test(self.offers, "Station", ("TKU", "MTI"))
        self.in_test(self.genres, "Station", ("TKU", "MTI"))

        self.not_in_test(self.offers, "Station", ("HLY", "MAN"))
        self.not_in_test(self.genres, "Station", ("HLY", "MAN"))

    def test_companies(self):
        self.length_test(self.offers, "Company", 2)
        self.length_test(self.genres, "Company", 2)

        self.in_test(self.offers, "Company", ("GENE", "MRPL"))
        self.in_test(self.genres, "Company", ("GENE", "MRPL"))

        self.not_in_test(self.offers, "Company", ("MERI", "CTCT"))
        self.not_in_test(self.genres, "Company", ("MERI", "CTCT"))

    def test_offer_incrementer(self):

        arr = Tessen.stack_columns(self.offers)
        increment = Tessen.incrementalise(arr)

        self.assertTrue(arr["Quantity"].sum() == increment["Incr Quantity"].sum())

    def test_reserve_incrementer(self):

        arr = Tessen.stack_columns(self.genres)
        increment = Tessen.incrementalise(arr)

        self.assertTrue(arr["Quantity"].sum() == increment["Incr Quantity"].sum())




class TestTessenDataFilters(TestTessen):

    def test_single_date(self):

        date = datetime.datetime(2013,12,12)
        date_col = "Trading_Date"

        fdf = Tessen.filter_dates(self.offers, date, date_col)
        unique_dates = fdf[date_col].unique()

        self.assertTrue(len(unique_dates) == 1)
        #self.assertTrue(unique_dates[0] == date.strftime('%Y-%m-%d'))

    def test_incorrect_single_date(self):

        date = datetime.datetime(2013,12,13)


    def test_single_period(self):
        period = 44.0
        period_col = "Trading_Period"

        fdf = Tessen.filter_periods(self.offers, period, period_col)
        unique_periods = fdf[period_col].unique()
        self.assertTrue(len(unique_periods) == 1)
        self.assertTrue(unique_periods[0] == period)
        self.assertFalse(unique_periods[0] == 12)


    def test_multiple_periods(self):
        periods = (33.0, 12, 28)
        period_col = "Trading_Period"
        fdf = Tessen.filter_periods(self.offers, periods, period_col)
        unique_periods = fdf[period_col].unique()

        for p in periods:
            self.assertTrue(p in unique_periods)

        for p in (15, 1, 48):
            self.assertTrue(p not in unique_periods)

        self.assertTrue(len(unique_periods) == len(periods))


    def test_single_company(self):
        company = "MRPL"
        company_col = "Company"

        fdf = Tessen.filter_company(self.offers, company, company_col)
        unique_companies = fdf[company_col].unique()

        self.assertTrue(len(unique_companies) == 1)
        self.assertTrue(unique_companies[0] == company)


    def test_multiple_companies(self):
        companies = ["MRPL", "MERI"]
        company_col = "Company"

        fdf = Tessen.filter_company(self.offers, companies, company_col)
        unique_companies = fdf[company_col].unique()

        self.assertTrue(len(unique_companies) == 2)

        for c in companies:
            self.assertTrue(c in unique_companies)

        for c in ["GENE", "CTCT"]:
            self.assertTrue(c not in unique_companies)


    def test_single_station(self):

        station = "MAN"
        station_col = "Station"

        fdf = Tessen.filter_stations(self.offers, station, station_col)
        unique_stations = fdf[station_col].unique()

        self.assertTrue(len(unique_stations) == 1)
        self.assertTrue(unique_stations[0] == station)

    def test_multiple_station(self):

        stations = ("MAN", "HLY", "OTC")
        station_col = "Station"

        fdf = Tessen.filter_stations(self.offers, stations, station_col)
        unique_stations = fdf[station_col].unique()

        self.assertTrue(len(unique_stations) == len(stations))

        for s in stations:
            self.assertTrue(s in unique_stations)

        for s in ("BEN", "TKU", "MTI"):
            self.assertTrue(s not in unique_stations)

    def test_north_island(self):

        island = "North Island"
        fdf =  Tessen.filter_island(self.offers, island,
                                    node_name="Grid_Injection_Point")

        unique_islands = fdf["Island Name"].unique()

        self.assertTrue(len(unique_islands) == 1)
        self.assertTrue(unique_islands[0] == island)

        # These are South Island Stations
        for s in ("BEN", "MAN", "CYD", "ROX"):
            self.assertTrue(s not in fdf["Station"].unique())

    def test_south_island(self):

        island = "South Island"
        fdf =  Tessen.filter_island(self.offers, island,
                                    node_name="Grid_Injection_Point")

        unique_islands = fdf["Island Name"].unique()

        self.assertTrue(len(unique_islands) == 1)
        self.assertTrue(unique_islands[0] == island)

        # These are South Island Stations
        for s in ("HLY", "OTC", "MTI", "WWD"):
            self.assertTrue(s not in fdf["Station"].unique())


class TestStackCreation(TestTessen):

    def test_gen_col_classify(self):

        band_columns = [x for x in self.offers.columns if "Band" in x]
        classification = Tessen.classify_columns(band_columns)

        k1 = ("Energy", "Energy", 2)
        k2 = "Price"
        v1 = "Band2_Price"
        k3 = "Power"
        v2 = "Band2_Power"

        self.assertTrue(classification[k1][k2] == v1)
        self.assertTrue(classification[k1][k3] == v2)


    def test_res_col_classify(self):

        band_columns = [x for x in self.genres.columns if "Band" in x]
        classification = Tessen.classify_columns(band_columns)

        k1 = ("PLSR", "FIR", 2)
        k2 = "Price"
        v1 = "Band2_Plsr_6S_Price"
        k3 = "Max"
        v2 = "Band2_Plsr_6S_Max"
        k4 = "Percent"
        v3 = "Band2_Plsr_6S_Percent"

        self.assertTrue(classification[k1][k2] == v1)
        self.assertTrue(classification[k1][k3] == v2)
        self.assertTrue(classification[k1][k4] == v3)


    def test_offer_stack_creation(self):
        arr = Tessen.stack_columns(self.offers)

        self.length_test(arr, "Product_Type", 1)
        self.length_test(arr, "Reserve_Type", 1)
        self.length_test(arr, "Band", 5)


    def test_reserve_stack_creation(self):
        arr = Tessen.stack_columns(self.genres)

        self.length_test(arr, "Product_Type", 2)
        self.length_test(arr, "Reserve_Type", 2)
        self.length_test(arr, "Band", 3)



if __name__ == '__main__':
    unittest.main()
