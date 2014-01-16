"""
Plots,

Plots takes care of the nitty gritty of actually plotting the fan curve
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns


def plot_reserve_lines(ax, data, prices=None, colour=cm.Blues):

    # Handle Prices as either discrete or, default to using all prices

    if prices is None:
        prices = data["Reserve_Price"].unique()

    # Sort the Prices and get the colour array
    prices = np.sort(prices)
    colours = colour(np.linspace(0, 1, len(prices)))
    lines = []

    for price, col in zip(prices, colours):
        # Filter by price, group it then aggregate
        ep, rp = configure_reserve_data(data, price)
        lines.append(ax.plot(ep, rp, label=price, color=col, linewidth=1.5)[0])

    # Create the legend object
    res_legend = ax.legend(lines, list(prices), loc='upper right')
    return res_legend


def configure_data(data, price=None):
    aggregations = {"Incr_Reserve_Quantity": np.sum,
                    "Incr_Energy_Quantity": np.max,
                    "Price": np.max}

    sort_columns = ["Price", "Incr_Reserve_Quantity"]
    sort_ascending = [True, False]

    if price is not None:
        price_subset = data[data["Reserve_Price"] <= price]
    else:
        price_subset = data.copy()

    grouped_prices = price_subset.groupby(["Node", "Energy_Stack"],
                                          as_index=False)
    aggegated = grouped_prices.aggregate(aggregations)
    sorted_data = aggegated.sort(columns=sort_columns,
                                 ascending=sort_ascending)

    return sorted_data



def configure_reserve_data(data, price):
    sorted_data = configure_data(data, price=price)
    energy_points = sorted_data["Incr_Energy_Quantity"].cumsum().values
    reserve_points = sorted_data["Incr_Reserve_Quantity"].cumsum().values

    return energy_points, reserve_points


def plot_energy_shading(ax, data, prices=None, colour=cm.YlOrRd):
    """ Plot the Energy Shading """

    if prices is None:
        prices = data["Price"].unique()

    prices = np.sort(prices)
    colours = colour(np.linspace(0, 1, len(prices)))
    lines = []

    old_price = 0
    for price, col in zip(prices, colours):
        ep, rp = configure_energy_data(data, old_price, price)
        rzero = np.zeros(len(rp))
        # Plot the shading
        ax.fill_between(ep, rzero, rp, alpha=0.5, color=col)
        # Plot a point to use in the label
        lines.append(ax.plot([0,0], [0,0], label=price, color=col)[0])
        # Update the old price
        old_price = price

    # Create the legend
    en_legend = ax.legend(lines, list(prices), loc='upper left')

    return en_legend


def configure_energy_data(data, old_price, new_price):
    sorted_data = configure_data(data, price=None)
    ge_old, le_new = ((sorted_data["Price"] >= old_price),
                     (sorted_data["Price"] <= new_price))

    energy_points = sorted_data["Incr_Energy_Quantity"].cumsum()
    reserve_points = sorted_data["Incr_Reserve_Quantity"].cumsum()

    energy_range = energy_points[ge_old & le_new].values
    reserve_range = reserve_points[ge_old & le_new].values
    return energy_range, reserve_range





def fan_visualisation(fancurve, reserve_prices=None, reserve_colour=cm.Blues,
                                energy_prices=None, energy_colour=cm.YlOrRd):
    """ Create the fan curve visualisation
    """


    # Create the Figure:
    fig, axes = plt.subplots(1,1, figsize=(16,9))

    # Reserve Plot
    res_legend = plot_reserve_lines(axes, fancurve, prices=reserve_prices,
                                    colour=reserve_colour)

    # Energy Plot
    en_legend = plot_energy_shading(axes, fancurve, prices=energy_prices,
                                    colour=energy_colour)

    # Update the legends to create the dual legend
    plt.gca().add_artist(res_legend)

    # Set the xlim and ylim to a zero basis
    axes.set_xlim(0, axes.get_xlim()[1])
    axes.set_ylim(0, axes.get_ylim()[1])

    axes.set_xlabel("Energy Offer [MW]", fontsize=18)
    axes.set_ylabel("Reserve Offer [MW]", fontsize=18)

    return fig, axes


def plotfan(fancurve):
    """ Create the fan curve visualisation
    """


    # Create the Figure:
    fig, axes = plt.subplots(1,1, figsize=(16,9))

    # Plot the Reserve Lines
    reserve_prices = np.sort(fancurve["Reserve_Price"].unique())
    reserve_colours = cm.Blues(np.linspace(0, 1, len(reserve_prices)))
    reserve_legend = []
    reserve_labels = []
    for price, c in zip(reserve_prices, reserve_colours):
        st = fancurve[fancurve["Reserve_Price"] <= price].groupby(["Node", "Energy_Stack"], as_index=False)
        agg = st.aggregate({"Incr_Reserve_Quantity": np.sum, "Incr_Energy_Quantity": np.max, "Price": np.max}).sort(columns=["Price", "Incr_Reserve_Quantity"], ascending=[True, False])
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

    ymax = axes.get_ylim()[1]
    xmax = energy_range.max()
    axes.set_xlim(0, xmax+100)
    axes.set_ylim(0, ymax)

    axes.set_xlabel("Energy Offer [MW]", fontsize=18)
    axes.set_ylabel("Reserve Offer [MW]", fontsize=18)

    return fig, axes


if __name__ == '__main__':
    pass

