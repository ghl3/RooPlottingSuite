#!/usr/bin/env python

import os

import ROOT
from tools import *
from MakeMultiplePlot import DrawMultiplePlot

def MakeMultipleTH1Plot( outputName, request, histCache=None ):
    """ Plot Multiple TH1's on one canvas
    
    - Take a list of input TH1's
    - Create a Canvas
    - Pass those to the 'DrawMultiplePlot' function,
        which will draw them to the canvas
    - Save the canvas
    """

    logging.debug( "MakeHistogramPlot" )

    # Create a canvas:
    ROOT.gROOT.cd()
    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    canvas.cd()

    # Get the histograms from the plot list, 
    # styling when necessary
    histList = []
    
    for plot in request["Plots"]:
        hist = plot["Hist"]
        hist = StyleHist( hist, plot )
        name = plot["Name"]
        histList.append( (name, hist) )

    # Check the histograms
    CompareHistograms( [ pair[1] for pair in (histList) ] ) 

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    legend = DrawMultiplePlot( histList, request )

    AdjustAndDrawLegend( legend, request )

    AdjustCanvas( canvas, request )

    SaveCanvas( canvas, request, outputName )
    
    canvas.Close()
    del canvas

    return
