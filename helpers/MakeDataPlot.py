
import os
import glob
import ROOT
import logging

from tools import *

def MakeDataPlot( outputName, request, histCache=None ):
    """ Make a stack of MC and Data, and save it

    - Create a Canvas
    - Get the Data Hist
    - Get the MC Hists
    - Pass those to the 'DrawMCDataStack' function,
        which will draw them to the canvas
    - Save the canvas
    """

    if request.get("RatioPlot"):
        print "Error: Ratio Plot not allowed for DataPlot"
        raise Exception()


    # Create the canvas
    (canvas, TopPad, BottomPad) = MakeCanvas(request)

    # Get the data hist
    dataHistList = GetDataNameHistList( request, histCache )

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    (legend) = DrawDataPlot( dataHistList, request )

    AdjustAndDrawLegend( legend, request )

    if not request.get("UseCurrentCanvas"):
        AdjustCanvas( canvas, request )

    if not request.get("UseCurrentCanvas"):
        SaveCanvas( canvas, request, outputName )
        canvas.Close()
        del canvas

    return (legend)


def DrawDataPlot( dataHistList, request={} ):
    """ Fetch, style, and draw a Data MC Stack


    Get the set of histograms from the request,
    style them, add them to a stack,
    and draw the stack.
    return the pair: (stack, legend)
    """

    logging.debug( "DrawDataPlot" )

    # Get the data, checking that there
    # is only one entry
    if len( dataHistList ) != 1:
        print "Error: More than 1 data sample supplied"
        print "Error: Only takes one"
        raise Exception("DrawMCDataStack - DATA")
        return

    # There should be only 1 data hist
    (dName, dhist ) = dataHistList[0]

    # Set the errors of the dhist
    for i in range(dhist.GetNbinsX()):
        i_bin = i+1
        dhist.SetBinError(i_bin, math.sqrt(dhist.GetBinContent(i_bin)))

    ResizeHistogram( dhist, [dhist], request )
    dhist.Draw()

    # Now draw the MC histograms one by one:
    legendEntries = []

    legendEntries.append( [dhist, dName, "lpe"] )

    # Draw the data points again:
    # stack.Draw( "HIST SAME" )
    dhist.Draw()

    legend = MakeLegend( legendEntries, request )
    legend.Draw()

    # Now create the plot:
    # canvas.SaveAs( filename )
    return (legend)
