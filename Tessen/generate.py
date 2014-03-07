"""

"""

import pandas as pd
import numpy as np
from OfferPandas import Frame, load_offerframe

import sys
import os
import datetime

def station_fan(energy, reserve):

    station_metadata = get_station_metadata(energy)




def get_station_metadata(offer_data):
    """ Look into the station offer data and grab out some metadata which will
    be useful in applying at the end, do not want to work with concatting files
    together.

    Inputs:
    -------
    offer_data: A OfferPandas.Frame energy offer frame (preferred) from
                which to extract useful metadata.

    Returns:
    --------
    meta_data: Dictionary, contains metadata information about the station.

    """
    excluded_columns = ("Band", "Price", "QUantity", "Product_Type",
                        "Reserve_Type", "Is_Injection", "Is_Hvdc",
                        "Created_Date", "Last_Amended_Date")

    meta_data = {item: offer_data[item][offer_data.index[0]] for item in
                    offer_data.columns if item not in excluded_columns}

    return meta_data

def incremental_energy_stack(pairs):
    """ Takes an array of price quantity pairs and returns a numpy array
    of this transformed into a single increment version (using step size 1)

    Inputs:
    -------
    pairs: numpy array of Nx2 dimension containing price and quantity pairs.

    Returns:
    --------
    stack: a (M+1x4) array where M is the sum of the quantities offered in
           the pairs input. Columns are (Price, Quantity, Incremental Quantity,
            Cumulative Quantity)

    """

    if pairs.shape[1] != 2:
        raise ValueError("Shape of the array passed to the function must\
be a Nx2 array, current size is %sx%s" % pairs.shape)

    total_offer = sum(pairs[:,1])
    stack = np.zeros((total_offer+1, 4))
    # Incremental Offer Columns
    stack[1:,2] = np.ones(total_offer)
    # Cumulative Offer Column
    stack[:,3] = np.arange(0, total_offer+1)
    # Price, Quantity Columns
    qprev = 1
    for p, q in pairs:
        stack[qprev:qprev+q,0] = p
        stack[qprev:qprev+q,1] = q

        qprev += q

    return stack



if __name__ == '__main__':

    pass