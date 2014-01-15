import pandas as pd
import numpy as np
import sys
import os
import datetime

#import OfferPandas

def incrementalise(frame):

    def yield_increment(frame):
        frame["Incr_Energy_Quantity"] = 1
        for index, series in frame.iterrows():
            quantity = series["Quantity"]
            while quantity > 0:
                series["Incr_Energy_Quantity"] = min(1, quantity)
                yield series.copy()
                quantity -= 1

    if len(frame) == 0:
        return None

    incr_frame = pd.concat(yield_increment(frame), axis=1).T
    incr_frame["Energy_Stack"] = incr_frame["Incr_Energy_Quantity"].cumsum()
    return incr_frame


def create_feasible(percentage, maximum_reserve, maximum_energy):

    capacity_line = np.arange(1, maximum_energy+1)
    reserve_line = capacity_line * percentage / 100.
    reserve_line = np.where(reserve_line <= maximum_reserve,
                            reserve_line, maximum_reserve)
    reserve_line = np.where(reserve_line <= capacity_line[::-1],
                            reserve_line, capacity_line[::-1])

    return dict(zip(capacity_line, reserve_line))

def station_fan(energy, reserve):

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
    Dict = {}

    for i, (percent, price, quantity) in reserve_copy[["Percent",
                                "Price", "Quantity"]].iterrows():
        Dict[price] =  create_feasible(percent, quantity, maximum_energy)
        maximum_energy -= quantity

    stationf = []
    for price in Dict:
        resam = np.array(Dict[price].values())
        incr_re = resam[1:] - resam[:-1]
        incr_dict = dict(zip(Dict[price].keys()[:-1], incr_re))
        hold = incr_energy.copy()
        hold["Reserve_Price"] = price
        hold["Reserve_Quantity"] = hold["Energy_Stack"].map(Dict[price])
        hold["Incr_Reserve_Quantity"] = hold["Energy_Stack"].map(incr_dict)
        hold["Reserve_Quantity"].fillna(0)
        stationf.append(hold)

    return pd.concat(stationf, ignore_index=True)

