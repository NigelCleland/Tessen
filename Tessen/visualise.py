""" Python based visualisation method to work on the generic fan
data which has already been produced.

Intended to separate the two so that an interactive JS version of this plot
could be produced at some point.

"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
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

def _aggregate(filtered, il_data=None):
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

    aggregated_data = defaultdict(dict)

    return None

def _construct_reserve_dictionary(data, price_increments=None):

    if not price_increments:
        price_increments = data["Reserve Price"].unique()

    reserve_accumulations = {}

    for rp in price_increments:
        subset = data[data["Reserve Price"] <= rp]
        reserve_accumulations[rp] = _construct_reserve_line(subset)

    return reserve_accumulations

def _construct_reserve_line(data)::
    aggregations = {"Incremental Reserve Quantity": np.sum,
                    "Incremental Energy Quantity": np.max,
                    "Energy Price": np.max}

    energy_line = "Incremental Energy Quantity"
    reserve_line = "Incremental Reserve Quantity"

    group_columns = ["Node", "Cumulative Energy Quantity"]

    sort_columns = ["Energy Price", "Incremental Reserve Quantity"]
    ascending = [True, False]

`   agg = data.groupby(group_columns, as_index=False).aggregate(aggregations)
    sort_data = agg.sort_columns(columns=sort_columns, ascending=ascending)
    return sort_data[energy_line].cumsum(), sort_data[reserve_line].cumsum()




def _generate_plot(aggregated_data):
    """ Generate the plot figure

    """

    fig, axes = plt.subplots(1, 1)


def _plot_reserve_contours(axes, data):
    """ Non publically exposed function, this plots the reserve lines in
    ascending fashion.

    """

    return None

def _plot_energy_shading(axes, data):

    return None
