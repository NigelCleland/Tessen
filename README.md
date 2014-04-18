# Tessen

A [Tessen](http://en.wikipedia.org/wiki/Japanese_war_fan) is a  Japanese hand fans used in warfare by the Samurai class of feudal Japan.

This repo is not about Samurai though.

Tessen is a tool for visualising energy and reserve offers.
You want to do this because energy and reserve are co-optimised and
the interaction between the markets can lead to some quite strange effects
occurring. This is primarily due to the inverse bathtub set of constraints
which limit the simultaneous dispatch of both energy and reserve.

It is currently in a working, but could be prettier state.
Note that this library is quite tightly coupled to the
[OfferPandas](https://github.com/NigelCleland/OfferPandas) and you will need
a recent version of this for the functionality to work.
OfferPandas is a custom pandas DataFrame for handling energy and reserve
market data offers including improved metadata and filtering functionality.

To see how to use Tessen in a simplified circumstance check out the
[Example iPython Notebook](http://nbviewer.ipython.org/urls/raw.githubusercontent.com/NigelCleland/Tessen/develop/sample_data/Example_Tessen.ipynb?create=1)

An example of a Tessen is below:

![What a pretty picture](https://github.com/NigelCleland/Tessen/blob/full_rewrite/example_fan.png?raw=True)

## Key Project Goals

## Notable Missing Features

### TWDSR

TWDSR can currently be implemented although the behaviour is not quite right.
As background a TWDSR dispatched unit cannot be offered for energy as no
water is running through the turbine.
But it can be offered as spinning reserve.
How TWDSR fits into the wider picture of a plot like the Tessen fan curve is
still to be determined.

### IL

Interruptible load is planned to be included in the next update.


## Other Information


* Free software: [BSD license](https://github.com/NigelCleland/Tessen/blob/develop/LICENSE)
* Documentation: http://Tessen.rtfd.org.

## Todo

See the [Enhancement Features](https://github.com/NigelCleland/Tessen/issues?labels=enhancement&page=1&state=open) page on Github.


