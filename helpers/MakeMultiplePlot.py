#!/usr/bin/env python

import os

import ROOT
from tools import *
from RatioPlot import DrawRatioPlot


def MakeMultiplePlot( outputName, request, histCache=None ):
    """ Plot Multiple histograms on one canvas

    - Create a Canvas
    - Get the histograms
    - Pass those to the 'DrawMultiplePlot' function,
        which will draw them to the canvas
    - Save the canvas
    """

    logging.debug( "MakeMultiplePlot" )
    
    # Create a canvas:
    #if not request.get("UseCurrentCanvas"):
    #    ROOT.gROOT.cd()
    #    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    #    canvas.cd()
    (canvas, TopPad, BottomPad) = MakeCanvas(request)
    print "Canvas in method: ", canvas
    
    # Get the data hist
    histList = GetNameHistList( request, histCache )

    CompareHistograms( [ pair[1] for pair in (histList) ] ) 

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    legend = DrawMultiplePlot( histList, request )

    AdjustAndDrawLegend(legend, request)

    AdjustCanvas(canvas, request)

    ratio=None

    if request.get("RatioPlot"):
        BottomPad.cd()
        ratio_list = DrawRatioPlot(request, histList[1:], histList[1])
        TopPad.cd()

    if not request.get("UseCurrentCanvas"):
        SaveCanvas( canvas, request, outputName )    
        canvas.Close()
        del canvas

    return (histList, legend, ratio_list, TopPad, BottomPad)


def DrawMultiplePlot( histList, request={} ):
    """ Draw a series of histograms on one plot

    Take a series of input histograms,
    draw them all to the same plot
    """

    logging.debug( "DrawMultiplePlot" )
        
    if len( histList ) == 0:
        print "Error: No hists supplied for DrawMultiple"
        raise Exception("DrawMultiple - HIST INPUT")
        return
    
    # Create the sum of MC samples
    addedSamples = None
    for (name, h1d) in histList:
        if addedSamples:
            addedSamples.Add ( h1d )
        else:
            addedSamples = h1d.Clone()
        pass

    # Get the first hist as a template
    (firstName, firstHist) = histList[0]

    ResizeHistogram( firstHist, [pair[1] for pair in histList], request )

    legendEntries = []

    if request.get("DrawErrors"):
        firstHist.Draw()
    else:
        firstHist.Draw("HIST")

    for (name, hist) in histList:

        if request.get("DrawErrors"):
            hist.Draw("SAME")
        else:
            hist.Draw("SAMEHIST")

        legendEntries.append( [hist, name, "l"] )
        pass


    legend = MakeLegend( legendEntries, request )

    """
    legend = ROOT.TLegend( 0.8, 0.8, 0.9, 0.9 )
    legend.AppendPad()
    legend.SetFillStyle( 0 )
    legend.SetBorderSize( 0 )

    # show the stacked histograms in the same order
    #legendEntries.reverse()
    for (hist, name, style) in legendEntries: 
        legend.AddEntry( hist, name, style )
    """

    legend.Draw()

    # Now create the plot:
    # canvas.SaveAs( filename )
    return legend


