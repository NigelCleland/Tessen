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
import datetime


# Apply some nicer plotting options to improve the visualisation.
path = os.path.join(Tessen.__path__[0], "_static/plot_options.json")
with open(path) as f:
    mplconfig = json.load(f)

for key, value in mplconfig.iteritems():
    mpl.rcParams[key] = value


def plot_fan(data, filters=None, fName=None, reserve_prices=None,
             energy_prices=None, reserve_colour=cm.Blues,
             energy_colour=cm.YlOrRd, set_xlim=None, set_ylim=None,
             energy_cleared=None, reserve_cleared=None):
    """ Plot the Fan Curve. This is the publically exposed entry point to the
    visualisation. Data is supplied either as a DataFrame, or alternatively
    as a path for a csv file. This is then filtered and the resulting plot
    created.

    Parameters:
    -----------
    data: Pandas DataFrame or CSV path string of generated fan data
    filters: Filters to apply to the data, optional, depends upon the data
             passed as to whether these are necessary.
    fName: Optional - Path to save the generated figure to.
    reserve_prices: Optional, array of reserve prices to assess for clearer
                    visualisations
    energy_prices: Optional, array of energy prices for clearer simpler visuals
    reserve_colour: Matplotlib colour map to visualise the reserve prices
    energy_colour: Matplotlib colour map to visualise the energy prices
    set_xlim: Default None, Optional, set a defined x axis limit
    set_ylim: Default None, Optional set a defined y axis limit
    energy_cleared: Default None, Optional, The level of energy cleared
    reserve_cleared: Default None, Optional, the level of reserve cleared

    Returns:
    --------
    fig, axes: The matplotlib objects of the plot
    fName: Optional, the fan curve saved in the location.

    """

    begin_time = datetime.datetime.now()
    estimate = 1
    print """ I'm beginning to plot the fan now, I estimate this will
    take me at least %s seconds""" % estimate

    if not isinstance(data, pd.DataFrame):
        try:
            data = pd.read_csv(data)
        except:
            raise TypeError("""data must be either a pandas DataFrame old_price
                a string containing the location of a csv file, data is
                currently of type %s""" % type(date))

    # Create the data as an OfferFrame and filter the data.
    frame = Frame(data)
    if filters:
        filtered = frame.efilter(filters)
    else:
        filtered = frame

    # Check that the output won't be nonsense, e.g. multiple periods, islands
    _check_consistency(filtered)

    # Aggregate the data
    aggregated_data = _aggregate(filtered, price_increments=reserve_prices)

    # Generate the Plots
    fig, axes = _generate_plot(aggregated_data, energy_prices=energy_prices,
                               energy_colour=energy_colour,
                               reserve_colour=reserve_colour,
                               set_xlim=set_xlim, set_ylim=set_ylim)

    if fName:
        fig.savefig(fName)

    elapsed_time = datetime.datetime.now() - begin_time
    print """I've completed the fan curve and optionally saved it to %s, I
    actually took %s seconds to complete this curve""" % (fName,
                elapsed_time.seconds)

    return fig, axes


def _check_consistency(filtered):
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

    Parameters:
    -----------
    data: Data for a single reserve price.

    Returns
    -------
    Energy Price: Array of Energy Prices values
    Energy Line: Cumulative Array of Energy values
    Reserve Line: Cumulative Array of Reserve values
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
                   energy_colour=cm.YlOrRd, energy_prices=None,
                   set_xlim=None, set_ylim=None, energy_cleared=None,
                   reserve_cleared=None):
    """ The nitty gritty of generating the plot figure

    Parameters:
    -----------
    aggregated_data: A dictionary of reserve prices to energy and reserve lines
    reserve_colour: What reserve_colour to use
    energy_colour: What energy colour to use
    energy_prices: Optional energy prices to specify
    set_xlim: Default None, Optional, define a xlimit value to use
    set_ylim: Default None, Optional, define a ylimit value to use
    energy_cleared: Default None, Optional, The level of energy cleared
    reserve_cleared: Default None, Optional, the level of reserve cleared

    Returns:
    --------
    fig, axes: Matplotlib objects

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

    if energy_cleared:
        yl, yh = 0, max(axes.get_ylim()[1], set_ylim)
        axes.plot((energy_cleared, energy_cleared), (yl, yh),
                   c='r', linewidth=3)

    if reserve_cleared:
        # Get xvalues that span across the plot
        xl, xh = 0, max(axes.get_xlim()[1], set_xlim)
        axes.plot((xl, xh), (reserve_cleared, reserve_cleared),
                    c='b', linewidth=3)

    # Set the xlim and ylim to a zero basis
    if set_xlim:
        axes.set_xlim(0, set_xlim)
    else:
        axes.set_xlim(0, axes.get_xlim()[1])

    if set_ylim:
        axes.set_ylim(0, set_ylim)
    else:
        axes.set_ylim(0, axes.get_ylim()[1])

    axes.set_xlabel("Energy Offer [MW]")
    axes.set_ylabel("Reserve Offer [MW]")

    return fig, axes


def _plot_reserve_contours(axes, reserve_accumulations, cmap=cm.Blues):
    """ Non publically exposed function, this plots the reserve lines in
    ascending fashion. Iterates through each key value pairing in the
    reserve dictionary and plots them in turn.

    Parameters:
    -----------
    axes: matplotlib axes object
    reserve_accumulations: Dictionary of reserve price, line pairs
    cmap: The colour map to use

    Returns:
    --------
    axes, res_legend: matplotlib objects

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
    """ Plot the energy shading region.
    Accomplishes this by taking the most expensive reserve (e.g. full dispatch)
    and shading under this according to price.

    Parameters:
    -----------
    axes: matplotlib axes object
    all_reserve: The most expensive reserve item, a tuple
    prices: What energy prices to visualise
    cmap: What energy colour map to use, defaults to YlOrRd

    Returns:
    --------
    axes, en_legend: matplotlib objects

    """
    all_reserve = np.array(all_reserve).T

    if not prices:
        prices = np.unique(all_reserve[:,0])
    prices = np.sort(prices)

    low_price = 0
    colours = cmap(np.linspace(0, 1, len(prices)))
    lines = []
    for high_price, c in zip(prices, colours):
        eline = all_reserve[:,1]
        rline = _reserve_interval(all_reserve, low_price, high_price)
        rzeros = np.zeros(len(rline))

        axes.fill_between(eline, rline, rzeros, alpha=0.5, color=c)
        lines.append(axes.plot([0,0], [0,0], label=prices, color=c)[0])
        low_price = high_price

    en_legend = axes.legend(lines, list(prices), loc='upper left')

    return axes, en_legend


def _reserve_interval(array, low_price, high_price):
    """ Masks an array for the energy price contours to return the
    regions which fall within a given price range.
    This is used to shade the energy regions of the plot accordingly

    Parameters:
    -----------
    array: A numpy array of energy price, energy line and reserve line values
    low_price: The minimum price
    high_price: The maximum price

    Returns:
    --------
    array: A numpy array of the same length as the reserve line. This line
           has been masked with zeros for non added areas (e.g. depending
            upon the energy price for those areas.)
    """
    tlow = array[:,0] >= low_price
    thigh = array[:,0] <= high_price
    return np.where(tlow & thigh, array[:,2], 0)



