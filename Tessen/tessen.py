#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library Imports
import sys
import os
import datetime
from dateutil.parser import parse
import simplejson as json
from collections import defaultdict
import argparse

# C Library Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# OfferPandas
import OfferPandas

def parse_tessen_args(args):


    parser = argparse.ArgumentParser(
        description='Tessen, a fan curve generator')

    parser.add_argument(
        '-c', '--company',
        help="Company to filter by")

    parser.add_argument(
        '-d', '--date',
        help="Trading Date of interest")

    parser.add_argument(
        '-p', '--period',
        help="Trading Period to create the fan for")

    parser.add_argument(
        '-s', '--station',
        help="Station of Interest")

    parser.add_argument(
        '-i', '--island',
        help="Which island to create the fan for")

    parser.add_argument(
        '-if', '--il_filename',
        help="Filename of the IL data")

    parser.add_argument(
        '-ef', '--energy_filename',
        help='Filename of the Energy data')

    parser.add_argument(
        '-gf', '--genres_filename',
        help="Filename of the Generator Reserve data")

    return parser.parse_args(args)


def main():

    args = parse_tessen_args(sys.argv[1:])

    print args

if __name__ == '__main__':
    main()
