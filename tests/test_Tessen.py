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


class TestTessenDataFilters(TestTessen):


    def test_single_period_filter(self):
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




if __name__ == '__main__':
    unittest.main()
