""" Bulk modes of operation

"""

# Standard Library
import glob
import os
import sys
import shutil
from dateutil.parser import parse
import itertools
import calendar
import datetime

# C Library
import pandas as pd
import numpy as np


# OfferPandas
from OfferPandas import Frame, load_offerframe

# Tessen extenions
import generate
import visualise


# This is hacky......
energy_headers = ["Company","Grid_Injection_Point","Station","Unit","Trading_Date","Trading_Period","Max_Output","Max_Ramp_Up_Rate","Max_Ramp_Down_Rate","Band1_Power","Band1_Price","Band2_Power","Band2_Price","Band3_Power","Band3_Price","Band4_Power","Band4_Price","Band5_Power","Band5_Price","Created_Date","Last_Amended_Date"]

reserve_headers = ["Company","Grid_Point","Trading_Date","Trading_Period","Station","Unit","Band1_PLSR_6s_price","Band1_PLSR_6s_max","Band1_PLSR_6s_percent","Band1_PLSR_60s_price","Band1_PLSR_60s_max","Band1_PLSR_60s_percent","Band1_TWDSR_6s_price","Band1_TWDSR_6s_max","Band1_TWDSR_60s_price","Band1_TWDSR_60s_max","  Band2_PLSR_6s_price","Band2_PLSR_6s_max","Band2_PLSR_6s_percent","Band2_PLSR_60s_price","Band2_PLSR_60s_max","Band2_PLSR_60s_percent","Band2_TWDSR_6s_price","Band2_TWDSR_6s_max","Band2_TWDSR_60s_price","Band2_TWDSR_60s_max","Band3_PLSR_6s_price","Band3_PLSR_6s_max","Band3_PLSR_6s_percent","Band3_PLSR_60s_price","Band3_PLSR_60s_max","Band3_PLSR_60s_percent","Band3_TWDSR_6s_price","Band3_TWDSR_6s_max","Band3_TWDSR_60s_price","Band3_TWDSR_60s_max","Created_Date","Last_Amended_Date"
]

def bulk_run(dates, save_location, temporary_location, energy_data,
             plsr_data, reserve_mode="FIR", *args, **kargs):
    """ Iterate through date_periods creating an Offer Fan for each one
    which will be saved in the save_location. Will also generate the fan
    curve data for each of the instances to be saved in the temporary_location.

    Parameters:
    -----------

    Returns:
    --------

    """

    energy_maps = build_file_maps(energy_data, "offers")
    plsr_maps = build_file_maps(plsr_data, "generatorreserves")

    # Get a unique set of datetime objects
    unique_dates = set([parse(x, dayfirst=True) for x in dates])

    # Get two lists of the unique energy and reserve files
    unique_energy = set([energy_maps[x] for x in unique_dates])
    unique_reserve = set([plsr_maps[x] for x in unique_dates])

    eframe = Frame(pd.concat((pd.read_csv(x, names=energy_headers) for x in unique_energy), ignore_index=True))
    rframe = Frame(pd.concat((pd.read_csv(x, names=reserve_headers) for x in unique_reserve), ignore_index=True))


    # Do some rough hacky filtering
    eframe = Frame(eframe[eframe["Company"] != "COMPANY"])
    rframe = Frame(rframe[rframe["Company"] != "COMPANY"])

    # Drop to a csv file then reload. Fucking Hacky but I'm feeling lazy
    # This gets around the header and object type problems I've been having
    eframe.to_csv(temporary_location, header=True)
    eframe = load_offerframe(temporary_location)

    rframe.to_csv(temporary_location, header=True)
    rframe = load_offerframe(temporary_location)

    #print eframe.dtypes, rframe.dtypes
    #print unique_dates, dates

    edates = eframe.efilter(Trading_Date=dates)
    rdates = rframe.efilter(Trading_Date=dates)

    #print edates, rdates

    fan = generate.create_fan(edates, rdates, fName=temporary_location, *args, **kargs)

    for date in dates:
        for period in xrange(1,49):
            fName = os.path.join(save_location, "fancurve%s%02d.png" % (parse(date,dayfirst=True).strftime("%Y%m%d"), int(period)))
            filters = {"Trading_Date": date, "Trading_Period": period, "Reserve_Type": reserve_mode}
            visualise.plot_fan(fan, filters=filters, fName=fName)





def build_file_maps(file_location, pattern):

    all_files = glob.glob(file_location + '/*.csv')
    # Maps a single day to the file which holds it.
    mapping = {}
    for f in all_files:
        for d in parse_daily_dates(f, pattern, '.csv'):
            mapping[d] = f

    return mapping






def scrub_string(x, pattern, ext):
    """ Take a string and get it into a position where it could be
    converted to a datetime object

    Parameters:
    -----------
    x: The string to be parsed
    pattern: Pattern in the basename to match against
    ext: Filename extension
    rename: Optional second string incase filenames have changed.

    Returns:
    --------
    datestring: A string which can be parsed
    """
    base_str = os.path.basename(x)
    # In case a file changes midway through.
    # Get rid of some of the last little things which can get left over
    # in the file names
    final_replacers = (pattern, ext, ext.lower(), ext.upper(), '_', ".csv")
    datestring = base_str
    for each in final_replacers:
        datestring = datestring.replace(each, '')

    return datestring

def parse_daily_dates( x, pattern, ext):
    """ This has two modes of operation, single_mode or multi mode.
    In single mode  a single datetime object is returned. This is needed
    to use the datetime objects as dictionary keys

    In multimode a list of dates may be returned. This can then be
    flattened. This is useful for situations when a combination of
    monthly and daily files exist.
    Parameters:
    -----------
    x: The string to be parsed
    pattern: Pattern in the basename to match against
    ext: Filename extension
    rename: Optional second string incase filenames have changed.
    single_mode: Boolean, which mode to use

    Returns:
    --------
    datetime object or list of datetime objects depending upon single mode
    """
    datestring = scrub_string(x, pattern, ext)
    # Check if it's a monthly file or a daily one
    if len(datestring) == 6:
        date = datetime.datetime.strptime(datestring, '%Y%m')
        dates = [datetime.datetime(date.year, date.month, x) for x in
                 range(1, calendar.monthrange(date.year, date.month)[1] + 1)]
        return dates

    elif len(datestring) == 8:
        return [datetime.datetime.strptime(datestring, '%Y%m%d')]

    else:
        return None

