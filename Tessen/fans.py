import pandas as pd
import numpy as np
import sys
import os
import datetime

#import OfferPandas

def incrementalise(frame):

    def yield_increment(frame):
        frame["Incr Quantity"] = 1
        for index, series in frame.iterrows():
            quantity = series["Quantity"]
            while quantity > 0:
                series["Incr Quantity"] = min(1, quantity)
                yield series.copy()
                quantity -= 1

    return pd.concat(yield_increment(frame), axis=1).T


def create_feasible(percentage, maximum_reserve, maximum_energy):

    capacity_line = np.arange(1, maximum_energy+1)
    reserve_line = capacity_line * percentage / 100.
    reserve_line = np.where(reserve_line <= maximum_reserve,
                            reserve_line, maximum_reserve)
    reserve_line = np.where(reserve_line <= capacity_line[::-1],
                            reserve_line, capacity_line[::-1])

    return dict(zip(capacity_line, reserve_line))
