"""
The Fans module is the main component of the Tessen package.
It, takes an OfferPandas Frame and does all of the configuration necessary
in order to create the fan curve excluding the plotting.
"""

import pandas as pd
import numpy as np
import sys
import os
import datetime
from OfferPandas import Frame, load_offerframe

def incrementalise(frame):
    """ Function which takes a Frame object and converts the Energy Quantities
    into an incremental fashion. E.g. a 60MW offer will create 60 duplicate
    rows in the frame.

    This is used to make mapping energy and reserve offers together simpler.

    Parameters
    ----------
    frame: OfferPandas.Frame object

    Returns:
    --------
    incr_frame: pd.DataFrame object, incremental dataframe

    """

    def _yield_increment(frame):
        frame["Incr_Energy_Quantity"] = 1
        for index, series in frame.iterrows():
            quantity = series["Quantity"]
            while quantity > 0:
                series["Incr_Energy_Quantity"] = min(1, quantity)
                yield series.copy()
                quantity -= 1

    # We do pass empty dataframes on occasion
    if len(frame) == 0:
        return None

    incr_frame = pd.concat(_yield_increment(frame), axis=1).T
    incr_frame["Energy_Stack"] = incr_frame["Incr_Energy_Quantity"].cumsum()
    return incr_frame


def create_feasible(percentage, maximum_reserve, maximum_energy):
    """ Create a dictionary mapping energy dispatch and reserve dispatch
    together for given parameters. This is done for each reserve price
    which may then be aggregated together by comparing the stacks in the
    fan curve:

    Parameters
    ----------
    percentage: float of the form xx.x note not a that decimal representation
    maximum_reserve: float, maximum limit on the amount of reserve
    maximum_energy: float, maximum (available) limit on energy, nameplate
                    capacity. Note in reality this capacity is adjusted down
                    as you move higher up the reserve stack as additional
                    reserve must be taken into account. This can lead to
                    gaps in the level of reserve which are filled with the
                    fillna function later.

    Returns
    -------
    Dictionary mapping an integer energy line with an equivalent reserve
    dispatch

    """

    capacity_line = np.arange(1, maximum_energy+1)
    reserve_line = capacity_line * percentage / 100.
    reserve_line = np.where(reserve_line <= maximum_reserve,
                            reserve_line, maximum_reserve)
    reserve_line = np.where(reserve_line <= capacity_line[::-1],
                            reserve_line, capacity_line[::-1])

    return dict(zip(capacity_line, reserve_line))

def station_fan(energy, reserve):

    # If no reserve data exists just return the frame with zeros
    if len(reserve) == 0:
        energysort = energy[energy["Quantity"] > 0]
        incr_energy = incrementalise(energysort)
        incr_energy["Reserve_Price"] = 0
        incr_energy["Reserve_Quantity"] = 0
        return incr_energy

    energysort = energy[energy["Quantity"] > 0]
    reserve_copy = reserve.sort("Price")
    incr_energy = incrementalise(energysort)

    maximum_energy = incr_energy["Max_Output"].values[0]
    bathtub = {}

    for i, (percent, price, quantity) in reserve_copy[["Percent",
                                "Price", "Quantity"]].iterrows():
        bathtub[price] =  create_feasible(percent, quantity, maximum_energy)
        maximum_energy -= quantity

    stationf = []
    for price in bathtub:
        resam = np.array(bathtub[price].values())
        incr_re = resam[1:] - resam[:-1]
        reserve_map = dict(zip(bathtub[price].keys()[:-1], incr_re))
        hold = incr_energy.copy()
        hold["Reserve_Price"] = price
        hold["Reserve_Quantity"] = hold["Energy_Stack"].map(bathtub[price])
        hold["Incr_Reserve_Quantity"] = hold["Energy_Stack"].map(reserve_map)
        hold["Reserve_Quantity"].fillna(0)
        stationf.append(hold)

    return pd.concat(stationf, ignore_index=True)


def create_full_fan(energy, reserve):
    def _create_fan(energy, reserve):
        energy_hold = energy[energy["Quantity"] > 0]
        for stat in energy_hold["Node"].unique():
            single_energy = energy_hold[energy_hold["Node"] == stat]
            single_reserve = reserve[reserve["Node"] == stat]

            singlefan = station_fan(single_energy, single_reserve)
            yield singlefan

    return pd.concat(_create_fan(energy, reserve),
                     ignore_index=True).fillna(0)



def create_full_fanb(energy, reserve):

    energy_hold = energy[energy["Quantity"] > 0]
    df_objects = []

    for stat in energy_hold["Node"].unique():
        single_energy = energy_hold[energy_hold["Node"] == stat]
        single_reserve = reserve[reserve["Node"] == stat]

        singlefan = station_fan(single_energy, single_reserve)
        df_objects.append(singlefan.copy())

    return pd.concat(df_objects, ignore_index=True).fillna(0)
