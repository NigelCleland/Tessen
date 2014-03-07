"""

"""

import pandas as pd
import numpy as np
from OfferPandas import Frame, load_offerframe

import sys
import os
import datetime

def station_fan(energy, reserve):
    """ Create the fan information for a given station and single reserve type.
    If multiple reserve types are passed this will fail miserably.

    Parameters:
    -----------

    Returns:
    --------
    DataFrame: A stacked DataFrame object containing the fan data for a
               particular station.

    """
    station_metadata = get_station_metadata(energy)

    if len(reserve["Reserve_Type"].unique()) > 1:
        raise ValueError("Must only pass a single Reserve Type, you passed\
            more than 1")

    # Create the Energy Stack
    sorted_energy = energy.sort("Price")
    energy_stack = incremental_energy_stack(
                sorted_energy[["Price", "Quantity"]].values)

    # Get the nameplate capacity of the station, all values are duplicates
    # so we just take the first one. Set initial remaining capacity equal to
    # the nameplate capacity
    nameplate_capacity = energy["Max_Output"].values[0]
    remaining_capacity = nameplate_capacity

    # Filter Reserve Offers, create a band stack for each pairing
    nonzero_reserve = reserve[reserve["Quantity"] > 0]

    band_stacks = []
    for (percent, price, quantity,
         reserve_type, product_type) in nonzero_reserve[["Percent", "Price",
                        "Quantity", "Reserve_Type", "Product_Type"]]:

        # Check for TWDSR, set percent to essentially infinity.
        if product_type == "TWDSR":
            percent = 1000000

        reserve_stack = feasible_reserve_region(energy_stack, price, quantity,
                                                percent, nameplate_capacity,
                                                remaining_capacity)

        # Update the remaining capacity
        remaining_capacity -= quantity

        # Create a Band DataFrame
        band_df = band_dataframe(reserve_stack, station_metadata, reserve_type,
                                 product_type)

        band_stacks.append(band_df)

    return pd.concat(band_stacks)




def band_dataframe(full_stack, station_metadata, reserve_type,
                      product_type):
    """ Creates a DataFrame for a single band taking into account the full
    stack along with the metadata for it.
    Returns this DataFrame which may then be added together to create the
    station frame.
    """


    full_metadata = station_metadata.copy()
    full_metadata["Reserve_Type"] == reserve_type
    full_metadata["Product_Type"] == product_type

    columns = ["Energy Price", "Energy Quantity",
               "Incremental Energy Quantity", "Cumulative Energy Quantity",
               "Reserve Price", "Reserve Quantity",
               "Incremental Reserve Quantity", "Cumulative Reserve Quantity"]

    # Create the DataFrame for a single band
    df = pd.DataFrame(full_stack, columns=columns)

    # Add the metadata
    for key, value in full_metadata:
        df[key] == value

    return df



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
    excluded_columns = ("Band", "Price", "Quantity", "Product_Type",
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

def feasible_reserve_region(stack, res_price, res_quantity, res_percent,
                            nameplate_capacity, remaining_capacity):
    """
    Create a feasible region array with information about energy and reserve
    prices for a single band. This array contains information on an incremental
    fashion regarding the energy and reserve tradeoff. Ideally should keep
    all of the data together in one place:

    Parameters:
    -----------
    stack: The full energy stack as previously calculated.
    res_price: The band reserve price
    res_quantity: Maximum band reserve quantity
    res_percent: The percentage for the reserve band, note TWDSR will be
                 arbitrarily high
    nameplate_capacity: The original capacity (nameplate) of the unit
    remaining_capacity: Subtracting the reserve bands at lower price quantities
                        from the nameplate capacity to leave a residual
                        quantity


    Returns:
    --------
    reserve_coupling: numpy array of energy and reserve values.

    """


    length = stack.shape[0]

    # Update the capacity line to be of the size of the full capacity but
    # shifted to reflect what capacity has already been used by cheaper reserve
    # offers.
    capacity_line = np.zeros((nameplate_capacity+1))
    capacity_line[:remaining_capacity+1] = np.arange(0,
            remaining_capacity+1)[::-1]

    # Create a line due to the
    reserve_line = stack[:,3] * res_percent
    reserve_line = np.where(reserve_line <= res_quantity, reserve_line,
                            res_quantity)
    # Adjust for the modified capacity line
    reserve_line = np.where(reserve_line <= capacity_line, reserve_line,
                            capacity_line)

    # Create an incremental reserve line as well
    incremental_reserve_line = np.zeros(len(reserve_line))
    incremental_reserve_line[1:] = reserve_line[1:] - reserve_line[:-1]


    # Create a new array and add the values
    reserve_coupling = np.zeros((length, 8))
    reserve_coupling[:, :4] = stack
    reserve_coupling[:, 4] = res_price
    reserve_coupling[:, 5] = res_quantity
    reserve_coupling[:, 6] = incremental_reserve_line
    reserve_coupling[:, 7] = reserve_line


    return reserve_coupling


if __name__ == '__main__':

    pass