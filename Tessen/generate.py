"""

"""

import pandas as pd
import numpy as np
from OfferPandas import Frame, load_offerframe

import sys
import os
import datetime
import time


def create_fan(energy, reserve, fName=None, return_fan=True, break_tp=False,
               force_plsr_only=True, *args, **kargs):
    """ A wrapper which implements some optional filtering arguments
    to speed up the process, otherwise iterating can take a very large time.

    Can handle the breakdown as well into trading period pieces.

    Parameters:
    -----------

    Returns:
    --------
    """

    # Set up a time reporting function:
    begin_time = datetime.datetime.now()


    filtered_energy = energy.efilter(*args, **kargs)
    if force_plsr_only:
        filtered_reserve = reserve.efilter(Product_Type="PLSR", *args, **kargs)
    else:
        print """Warning, TWDSR is still a little funky and the visualisation
        of it in a composite fan diagram can be misleading. Most notably it
        is difficult to show how it integrates when PLSR is also
        dispatched\n"""
        filtered_reserve = reserve.efilter(*args, **kargs)


    estimate_number = len(filtered_energy[["Node",
                            "Trading_Period_ID"]].drop_duplicates()) * 2
    print """I'm beginning to create fan curves, I estimate I'll need to do
at least %s of these which may take at least %s seconds, hold tight""" % (
            estimate_number, estimate_number * 0.008)


    fan = _create_fan(filtered_energy, filtered_reserve)

    elapsed_time = datetime.datetime.now() - begin_time
    number_fans = len(fan[["Node", "Trading_Period_ID", "Reserve_Type",
                           "Reserve Price"]].drop_duplicates())
    print "I successfully calculated %s fans in %s seconds" % (number_fans,
                 elapsed_time.seconds)

    if fName:
        if break_tp:
            print "I'll now begin saving these to individual trading period files"
            for each in fan["Trading_Period_ID"].unique():
                single = fan[fan["Trading_Period_ID"] == each]
                new_ext = '_' + str(each) + '.csv'
                single_name = fName.replace('.csv', new_ext)
                single.to_csv(single_name, header=True, index=False)

        else:
            print "I'll now begin saving these to a single file"
            fan.to_csv(fName, header=True, index=False)

    if return_fan:
        return fan

    return None

def _create_fan(energy, reserve):
    """Given an energy and reserve offer frame, PLSR, will construct the
    full fan curve for these on a station by station, band by band and by
    reserve type.

    These fans may then be filtered and visualised using the visualise
    functionality.

    Parameters:
    -----------
    energy: An energy offer frame, fans will be created for every permutation
            in this frame.
    reserve: The corresponding reserve offer frame.

    Returns
    -------
    DataFrame: A DataFrame containing the fan object
    """

    station_dates = energy[["Node", "Trading_Period_ID"]].drop_duplicates()
    fan_assembly = []

    for index, station, tpid in station_dates.itertuples():
        single_energy = energy.efilter(Trading_Period_ID=tpid,
                               Node=station)
        for reserve_type in ("FIR", "SIR"):
            single_reserve = reserve.efilter(Trading_Period_ID=tpid,
                        Node=station, Reserve_Type=reserve_type)

            fan_assembly.append(station_fan(single_energy, single_reserve,
                                            assumed_reserve=reserve_type))

    return pd.concat(fan_assembly, ignore_index=True)

def station_fan(energy, reserve, assumed_reserve=None):
    """ Create the fan information for a given station and single reserve type.
    If multiple reserve types are passed this will fail miserably.

    Parameters:
    -----------
    energy: Energy OfferFrame containing the information about a single
            station and trading period

    reserve: PLSR OfferFrame containing the informaiton about a single
            station, trading period and reserve type, note TWDSR should work.

    Returns:
    --------
    DataFrame: A stacked DataFrame object containing the fan data for a
               particular station.

    """
    energy = energy[energy["Quantity"] > 0]

    if len(energy) == 0:
        return None

    station_metadata = get_station_metadata(energy)

    # Do an check just in case the reserve is equal to zero.
    # Will return an energy only version, all reserve set to zero.
    # Don't need to concat there should only be a single version.
    if len(reserve) == 0:
        return create_energy_stack(energy, station_metadata,
                            assumed_reserve=assumed_reserve)

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
    nameplate_capacity = remaining_capacity = energy["Max_Output"].values[0]

    # Filter Reserve Offers, create a band stack for each pairing
    nonzero_reserve = reserve[reserve["Quantity"] > 0]
    if len(nonzero_reserve) == 0:
        return create_energy_stack(energy, station_metadata,
                            assumed_reserve=assumed_reserve)

    # Do a check for zero priced reserve offers here,
    # If there aren't any then add one to the band stacks call.
    # Add a zero reserve stack array as it will have no impact upon
    # The actual fan created, note this may create additional fans
    # But the tradeoff is a small one.
    band_stacks = []
    if 0. not in nonzero_reserve["Price"]:
        band_stacks.append(create_energy_stack(energy, station_metadata,
                                 assumed_reserve=assumed_reserve))

    for (index, percent, price, quantity, reserve_type, product_type
        ) in nonzero_reserve[["Percent", "Price", "Quantity", "Reserve_Type",
                             "Product_Type"]].itertuples():

        # Check for TWDSR, set percent to essentially infinity.
        if product_type == "TWDSR":
            percent = 1000000

        reserve_stack = feasible_reserve_region(energy_stack, price, quantity,
                                                percent, nameplate_capacity,
                                                remaining_capacity,
                                                product_type)

        # Update the remaining capacity
        remaining_capacity -= quantity

        # Create a Band DataFrame
        full_metadata = update_metadata(station_metadata, reserve_type,
                                 product_type, percent)

        band_stacks.append(band_dataframe(reserve_stack, full_metadata))

    return pd.concat(band_stacks)

def create_energy_stack(energy, station_metadata, assumed_reserve=None):
    energy_version = energy_only(energy)
    full_metadata = update_metadata(station_metadata, assumed_reserve,
                                        "PLSR", 0)
    return band_dataframe(energy_version, full_metadata)


def energy_only(energy):
    """ Mimics the fan curve for an energy only station by setting all
    reserve poritons of the stack to zero.
    """
    sorted_energy = energy.sort("Price")
    energy_stack = incremental_energy_stack(
                sorted_energy[["Price", "Quantity"]].values)

    length = energy_stack.shape[0]
    energy_version = np.zeros((length, 8))
    energy_version[:, :4] = energy_stack

    return energy_version

def update_metadata(station_metadata, reserve_type, product_type, percent):
    full_metadata = station_metadata.copy()
    full_metadata["Reserve_Type"] = reserve_type
    full_metadata["Product_Type"] = product_type
    full_metadata["Reserve_Percent"] = percent

    return full_metadata

def band_dataframe(full_stack, full_metadata):
    """ Creates a DataFrame for a single band taking into account the full
    stack along with the metadata for it.
    Returns this DataFrame which may then be added together to create the
    station frame.
    """

    columns = ["Energy Price", "Energy Quantity",
               "Incremental Energy Quantity", "Cumulative Energy Quantity",
               "Reserve Price", "Reserve Quantity",
               "Incremental Reserve Quantity", "Cumulative Reserve Quantity"]

    # Create the DataFrame for a single band
    df = pd.DataFrame(full_stack, columns=columns)

    # Add the metadata
    for key, value in full_metadata.iteritems():
        df[key] = value

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

    partial_arrays = [np.zeros((1,4))]
    for p, q in pairs:
        # Incremental Capacity
        partial = np.zeros((np.ceil(q), 4))
        partial[:,2] = np.ones(np.ceil(q))
        if np.ceil(q) != q:
            partial[-1, 2] = q % 1

        # Price and Quantity
        partial[:,0] = p
        partial[:,1] = q
        partial_arrays.append(partial)

    full_array = np.concatenate(partial_arrays)
    full_array[:,3] = np.cumsum(full_array[:,2])
    return full_array


def feasible_reserve_region(stack, res_price, res_quantity, res_percent,
                            nameplate_capacity, remaining_capacity,
                            product_type):

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
    reserve_type: string, either "PLSR" or "TWDSR". indicates some special
                  behaviour for "TWDSR".


    Returns:
    --------
    reserve_coupling: numpy array of energy and reserve values.

    """

    length = stack.shape[0]

    # Update the capacity line to be of the size of the full capacity but
    # shifted to reflect what capacity has already been used by cheaper reserve
    # offers.
    utilised_capacity = nameplate_capacity - remaining_capacity
    capacity_line = nameplate_capacity - stack[:,3]
    capacity_line = np.where(capacity_line - utilised_capacity <= 0,
                             0, capacity_line - utilised_capacity)

    # Create a line due to the proportionality constraint.
    # Note percentages are reported as is...
    # Still need to figure out how to do TWD here...
    reserve_line = stack[:,3] * res_percent /100.

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