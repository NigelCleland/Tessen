Tessen
======

A [Tessen](http://en.wikipedia.org/wiki/Japanese_war_fan) is a  Japanese hand fans used in warfare by the Samurai class of feudal Japan.

This repo is not about Samurai though.

Tessen is a tool for visualising energy and reserve offers.
An example can be found in the sample data directory.

It is currently in a working, but could be prettier state.
Note that this library is quite tightly coupled to the
[OfferPandas](https://github.com/NigelCleland/OfferPandas) and you will need
a recent version of this for the functionality to work.
OfferPandas is a custom pandas DataFrame for handling energy and reserve
market data offers including improved metadata and filtering functionality.

An example of a Tessen is below:

![What a pretty picture](https://github.com/NigelCleland/Tessen/blob/full_rewrite/example_fan.png?raw=True)

TWDSR
-----

TWDSR can currently be implemented although the behaviour is not quite right.
As background a TWDSR dispatched unit cannot be offered for energy as no
water is running through the turbine.
But it can be offered as spinning reserve.
How TWDSR fits into the wider picture of a plot like the Tessen fan curve is
still to be determined.

IL
----

Interruptible load is planned to be included in the nextupdate

Other Information
-----------------

* Free software: BSD license
* Documentation: http://Tessen.rtfd.org.

Todo
--------

* Tests
* IL Offers
* Beautify the plot
* "Fix" TWDSR