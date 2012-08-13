#!/usr/bin/env python

import os

import ROOT
from tools import *
from MakeMultiplePlot import DrawMultiplePlot

def MakeQuotientPlot( outputName, request, histCache=None ):
    """ Plot Multiple histograms on one canvas

    - Create a Canvas
    - Get the histograms
    - Pass those to the 'DrawMultiplePlot' function,
        which will draw them to the canvas
    - Save the canvas
    """

    logging.debug( "MakeMultiplePlot" )

    # Create a canvas:
    ROOT.gROOT.cd()
    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    canvas.cd()

    # Get the histograms
    # First is numerator, second is denominator
    histList = GetNameHistList( request, histCache )

    # Check the number of histograms
    if len( histList ) != 2:
        print "Error: Expected only 2 histograms for a Quotient Plot"
        raise Exception("Quotient - Histogran Number")
        return    
    

    # Check that the histograms are compatable
    CompareHistograms( [ pair[1] for pair in (histList) ] ) 

    # Make the quotient
    numHist   = histList[0][1]
    denomHist = histList[1][1]

    # Clone the numerator

    Efficiency = numHist.Clone()
    
    # Divide by Denominator
    Efficiency.Divide( denomHist )
    EfficiencyName = histList[0][0]

    # Format for drawing multiple Plot
    EffList = [ (EfficiencyName, Efficiency) ]

    # Pass responsability to MakeMultiplePlot
    legend = DrawMultiplePlot( EffList, request )

    AdjustAndDrawLegend( legend, request )

    AdjustCanvas( canvas, request )

    SaveCanvas( canvas, request, outputName )
    
    canvas.Close()
    del canvas

    return

