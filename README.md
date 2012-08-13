RooPlottingSuite
================

A set of tools for making plots using ROOT histograms



# This package contains a set of pyroot
# scripts meant to easily create nice
# plots from a set of input
# ROOT type histograms

# It consists of the following components:



# - PlotGenerator.py  
#  -- This is the main interface pyroot
#  script that interprets the input
#  and deligates it to helper scripts

# - PlotMaker.py
# -- This is a class which can be
# used to organize MC and data samples,
# set colors and options,
# and make plots quickly and easily

# - plotTypes
# -- This Directory holdsa set of scripts 
# which make individualized types of plots
# and use some common tools



# EXECUTABLES:

# - makePlots.py
# -- This is an executable that can
# be run from the command line
# It is essentially a wrapper for
# PlotMaker.py that interprets
# command line arguments

# - plotHistsInFile.py
# -- This is an executable that opens
# up an input ROOT file and makes
# plots of all histograms in that file



