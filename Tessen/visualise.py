""" Python based visualisation method to work on the generic fan
data which has already been produced.

Intended to separate the two so that an interactive JS version of this plot
could be produced at some point.

"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm
from OfferPandas import Frame
import simplejson as json
import os
import Tessen
from collections import defaultdict


# Apply some nicer plotting options to improve the visualisation.
path = os.path.join(Tessen.__path__[0], "_static/plot_options.json")
with open(path) as f:
    mplconfig = json.load(f)

for key, value in mplconfig.iteritems():
    mpl.rcParams[key] = value


def plot_fan(data, filters, fName=None):
    """ Plot the Fan Curve. This is the publically exposed entry point to the
    visualisation. Data is supplied either as a DataFrame, or alternatively
    as a path for a csv file. This is then filtered and the resulting plot
    created.

    Parameters:
    -----------
    data: Pandas DataFrame or CSV path string of generated fan data
    filters: Filters to apply to the data
    fName: Optional - Path to save the generated figure to.

    Returns:
    --------
    fig, axes: The matplotlib objects of the plot

    """

    if data is not isinstance(pd.DataFrame):
        try:
            data = pd.read_csv(data)
        except:
            raise TypeError("""data must be either a pandas DataFrame old_price
                a string containing the location of a csv file, data is
                currently of type %s""" % type(date))

    # Create the data as an OfferFrame and filter the data.
    frame = Frame(data)
    filtered = frame.efilter(filters)

    # Check that the output won't be nonsense, e.g. multiple periods, islands
    _check_consistency(flitered)

    # Aggregate the data
    aggregated_data = _aggregate(filtered)

    # Generate the Plots
    fig, axes = _generate_plot(aggregated_data)

    if fName:
        fig.savefig(fName)

    return fig, axes


def _check_consitency(filtered):
    """ Perform some basic checks upon the Data to provide some useful
    error messages for the users.

    Currently this method checks for
        * islands
        * reserve types
        * trading periods

    Returns:
    --------
    None
    """

    # Island Check
    islands = len(filtered["Island_Name"].unique())
    if islands != 1:
        raise ValueError("""You must only pass a single island, instead You
                        passed %s islands, please check the filters you
                        passed""" % islands)

    # Reserve Type Check
    rtypes = len(filtered["Reserve_Type"].unique())
    if rtypes != 1:
        raise ValueError("""You must only pass a single reserve type, FIR or
        SIR, instead sou passed %s types, please check the filters you
        passed""" % rtypes)

    # Trading Period Check
    periods = len(filtered["Trading_Period"].unique())
    if periods != 1:
        raise ValueError("""You must only pass a single trading period,
        instead sou passed %s periods, please check the filters you
        passed""" % periods)


    # Return None if no errors are raised
    return None

def _aggregate(filtered, il_data=None, price_increments=None):
    """ Aggregate the data together once all of the filters have been applied:
    This is the entirety of the 'logic' for this module,

    Parameters
    ----------
    filtered: The filtered data to be aggregated
    il_data: Optional - Apply the IL stack to the reserve lines as well.

    Returns:
    --------
    aggregated_data: Aggregated data ready for plotting and visualisation
        Is a dictionary with two levels, reserve data and energy data
        the reserve data level is further indexed by reserve price with
        and accompanying energy - reserve offer line

        the energy data is the offer - price tradeoff which is used
        to construct the shading and legend for the energy offers.
    """

    aggregated_data = _construct_reserve_dictionary(filtered,
                    price_increments=price_increments)

    if il_data:
        raise NotImplemented(""" This feature is still to be implemented """)

    return aggregated_data

def _construct_reserve_dictionary(data, price_increments=None):
    """ Iterates through either all of the reserve prices or a subset there
    of for custom views. Will call the _construct_reserve_line function
    on each reserve price to generate the ascending reserve price
    contours.

    Parameters
    ----------
    data: The fan data
    price_increments: Optional, array of floats representing prices of
                       interest, use to specify fewer contours.

    Returns:
    --------
    reserve_accumulations: Dictionary of reserve_price: x, y pairs for plots.

    """
    if not price_increments:
        price_increments = data["Reserve Price"].unique()

    reserve_accumulations = {}

    for rp in price_increments:
        subset = data[data["Reserve Price"] <= rp]
        reserve_accumulations[rp] = _construct_reserve_line(subset)

    return reserve_accumulations

def _construct_reserve_line(data):
    """ Construct an energy and reserve line pairing and returns the values
    These should be increased in energy price to illustrate the fan curve
    trade off behaviour.
    """
    aggregations = {"Incremental Reserve Quantity": np.sum,
                    "Incremental Energy Quantity": np.max,
                    "Energy Price": np.max}

    energy_line = "Incremental Energy Quantity"
    reserve_line = "Incremental Reserve Quantity"

    group_columns = ["Node", "Cumulative Energy Quantity"]

    sort_columns = ["Energy Price", "Incremental Reserve Quantity"]
    ascending = [True, False]

    agg = data.groupby(group_columns, as_index=False).aggregate(aggregations)
    sort_data = agg.sort(columns=sort_columns, ascending=ascending)

    # returns a tuple of two arrays which can be plotted
    return (sort_data["Energy Price"].values,
            sort_data[energy_line].cumsum().values,
            sort_data[reserve_line].cumsum().values)




def _generate_plot(aggregated_data, reserve_colour=cm.Blues,
                   energy_colour=cm.YlOrRd, energy_prices=None):
    """ Generate the plot figure

    """

    fig, axes = plt.subplots(1, 1)

    # Plot the reserve lines:
    axes, res_legend = _plot_reserve_contours(axes, aggregated_data,
                                              cmap=reserve_colour)

    max_reserve = aggregated_data[np.max(aggregated_data.keys())]
    axes, en_legend = _plot_energy_shading(axes, max_reserve,
                                           cmap=energy_colour,
                                           prices=energy_prices)

    plt.gca().add_artist(res_legend)

    # Set the xlim and ylim to a zero basis
    axes.set_xlim(0, axes.get_xlim()[1])
    axes.set_ylim(0, axes.get_ylim()[1])

    axes.set_xlabel("Energy Offer [MW]", fontsize=18)
    axes.set_ylabel("Reserve Offer [MW]", fontsize=18)

    return fig, axes


def _plot_reserve_contours(axes, reserve_accumulations, cmap=cm.Blues):
    """ Non publically exposed function, this plots the reserve lines in
    ascending fashion.

    """

    prices = np.sort(reserve_accumulations.keys())
    colours = cmap(np.linspace(0, 1, len(prices)))
    lines = []

    for price, col in zip(prices, colours):
        eprice, eline, rline = reserve_accumulations[price]
        lines.append(axes.plot(eline, rline, label=price, color=col,
                               linewidth=2)[0])


    res_legend = axes.legend(lines, list(prices), loc='upper right')
    return axes, res_legend

def _plot_energy_shading(axes, all_reserve, prices=None, cmap=cm.YlOrRd):

    all_reserve = np.array(all_reserve)

    if not prices:
        prices = np.unique(all_reserve[:,0])

    low_price = 0
    colours = cmap(np.linspace(0, 1, len(prices)))
    lines = []
    for high_price, c in zip(prices, colours):
        truth_low = all_reserve[:,0] >= low_price
        truth_high = all_reserve[:,0] <= high_price
        eline = np.where(truth_low & truth_high, all_reserve[:,1], 0)
        rline = np.where(truth_low & truth_high, all_reserve[:,2], 0)
        rzeros = np.zeros(len(rline))

        axes.fill_between(eline, rline, rzeros, alpha=0.5, color=c)
        lines.append(axes.plot([0,0], [0,0], label=prices, color=c)[0])
        low_price = high_price

    en_legend = axes.legend(lines, list(prices), loc='upper left')

    return axes, en_legend



