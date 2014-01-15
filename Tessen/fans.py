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


def create_full_fan(energy, reserve):

    energy_hold = energy[energy["Quantity"] > 0]
    df_objects = []

    for stat in energy["Node"].unique():
        single_energy = energy[energy["Node"] == stat]
        single_reserve = reserve[reserve["Node"] == stat]

        singlefan = station_fan(single_energy, single_reserve)
        df_objects.append(singlefan.copy())

    return pd.concat(df_objects, ignore_index=True).fillna(0)

def plotfan(fancurve):

    # Create the Figure:
    fig, axes = plt.subplots(1,1, figsize=(16,9))

    # Plot the Reserve Lines
    reserve_prices = np.sort(fancurve["Reserve_Price"].unique())
    reserve_colours = cm.Blues(np.linspace(0, 1, len(reserve_prices)))
    reserve_legend = []
    reserve_labels = []
    for price, c in zip(reserve_prices, reserve_colours):
        st = fancurve[fancurve["Reserve_Price"] <= price].groupby(["Node", "Energy_Stack"], as_index=False)
        agg = st.aggregate({"Incr_Reserve_Quantity": np.sum, "Incr_Energy_Quantity": np.max, "Price": np.max}).sort("Price")
        agg["Cum_Energy"] = agg["Incr_Energy_Quantity"].cumsum()
        agg["Cum_Reserve"] =  agg["Incr_Reserve_Quantity"].cumsum()

        rl = axes.plot(agg["Cum_Energy"], agg["Cum_Reserve"], label=price, color=c, linewidth=2)
        reserve_legend.append(rl[0])
        reserve_labels.append(price)

    # Plot the Energy Colours...
    price_increments = np.sort(agg["Price"].unique())
    price_colours = cm.YlOrRd(np.linspace(0, 1, len(price_increments)))
    old_price = 0
    energy_legend = []
    energy_legend_labels = []
    for price, c in zip(price_increments, price_colours):

        sub_price = agg[(agg["Price"] >= old_price) & (agg["Price"] <= price)]

        energy_range = sub_price["Cum_Energy"].values
        reserve_range = sub_price["Cum_Reserve"].values
        reserve_zeroes = np.zeros(len(reserve_range))

        axes.fill_between(energy_range, reserve_zeroes, reserve_range, alpha=0.5, color=c)
        ll = axes.plot([0,0],[0,0], color=c, label=price)
        energy_legend.append(ll[0])
        energy_legend_labels.append(price)

        old_price = price

    legend1 = axes.legend(reserve_legend, reserve_labels, loc='upper right')
    legend2 = axes.legend(energy_legend, energy_legend_labels, loc='upper left')
    plt.gca().add_artist(legend1)


    ymax = reserve_range.max()
    xmax = energy_range.max()
    axes.set_xlim(0, xmax+100)

    return fig, axes

