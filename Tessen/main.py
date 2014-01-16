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
import fan
import plot

def tessen(args, reserve_prices=None, energy_prices=None):
    """ Main Function


    # Load some default parameters in case simple arguments aren't
    # passed, this ensures at least something will be produced
    with open('_static/default_options.json') as f:
            filters = json.load(f)

    if args.energy_filename is None:
        raise ValueError("You must pass an energy offer file")

    if args.genres_filename is None:
        raise ValueError("You must pass a generator reserve offer file")

    # Parse the Filters
    reserve_filters = parse_filters(filters, args)

    # Load the files
    try:
        Energy = OfferPandas.load_offerframe(args.energy_filename)
        Reserve = OfferPandas.load_offerframe(args.genres_filename)
    except:
        raise ValueError("\n\
You must pass a valid energy filename and a valid\n\
reserve filename, instead you passed\n\
energy_filename: %s\n\
reserve_filename: %s\n" % (args.energy_filename,
                           args.genres_filename))

    # Energy Filters is a subset of Reserve filters without the PLSR/FIR/SIR
    energy_filters = reserve_filters.copy()
    energy_filters.pop("Reserve_Type")
    energy_filters.pop("Product_Type")

    # Filter the two Datasets
    filt_energy = Energy.efilter(energy_filters)
    filt_reserve = Reserve.efilter(reserve_filters)

    # Create the fan curve
    fan_data = fan.create_full_fan(filt_energy, filt_reserve)

    # Visualise it
    plot.fan_visualisation(fan_data)
    plt.show()


def parse_filters(filters, args):
    """ Take the command line arguments passed (if not null) and
    add them to a dictionary. Will default to using the default
    arguments contained in the json configuration file.

    Parameters
    ----------
    filters: Dictionary containing the default configuration
    args: argparse object

    """

    if not type(filters) == dict:
        raise TypeError("filters must be a dict, not type %s" % type(filters))


    filters = appenddict(filters, "Trading_Period", args.period)
    filters = appenddict(filters, "Trading_Date", args.date)
    filters = appenddict(filters, "Company", args.company)
    filters = appenddict(filters, "Island_Name", args.island)
    filters = appenddict(filters, "Station", args.station)
    filters = appenddict(filters, "Reserve_Type", args.reserve_type)
    filters = appenddict(filters, "Product_Type", args.product_type)

    return filters


def appenddict(d, key, value):
    if value is not None:
        if key == "Trading_Period":
            d[key] = int(value)
        else:
            d[key] = value
    return d


def parse_tessen_args(args):
    """ Parse Command Line Arguments """

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

    parser.add_argument(
        '-rt', '--reserve_type',
        help="FIR or SIR, type of Reserve")

    parser.add_argument(
        '-pt', '--product_type',
        help="Reserve Product, PLSR or TWDSR")

    return parser.parse_args(args)


def main():
    args = parse_tessen_args(sys.argv[1:])
    tessen(args)


if __name__ == '__main__':

    main()

