
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from OfferPandas import Frame
import simplejson as json
import os
import Tessen


# Apply some nicer plotting options to improve the visualisation.
mplconfig = json.loads(os.path.join(Tessen.__path__[0],
                       "_static/plot_options.json"))

for key, value in mplconfig:
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
    _check_consistency(filtered)

    # Generate the Plots
    fig, axes = _generate_plot(filtered)

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

def _generate_plot(filtered):
    """ Generate the plot figure

    """

    fig, axes = plt.subplots(1, 1)


def _plot_reserve_contour()




