
import os
import glob
import ROOT
import log, logging

from tools import *

def MakeStack( outputName, request, histCache=None ):
    """ Make a stack of MC and Data, and save it

    - Create a Canvas
    - Get the Data Hist
    - Get the MC Hists
    - Pass those to the 'DrawMCDataStack' function,
        which will draw them to the canvas
    - Save the canvas
    """

    # Create a canvas:
    ROOT.gROOT.cd()
    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    canvas.cd()
    canvas.cd()

    # Get the data hist
    nameHistList = []
    
    nameHistList.extend( GetDataNameHistList( request, histCache ) )
    nameHistList.extend( GetMCNameHistList(   request, histCache ) )
    nameHistList.extend( GetBSMNameHistList(  request, histCache ) )

    # Check that all histograms match
    CompareHistograms( [ pair[1] for pair in nameHistList ] ) 

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    (stack, legend) = DrawStack( nameHistList, request )


    AdjustAndDrawLegend( legend, request )

    #SetLegendBoundaries( legend, request )
    #legend.Draw()


    AdjustCanvas( canvas, request )

    SaveCanvas( canvas, request, outputName )

    canvas.Close()
    del canvas

    return


def DrawStack( nameHistList, request={} ):
    """ Fetch, style, and draw a Data MC Stack


    Get the set of histograms from the request,
    style them, add them to a stack,
    and draw the stack.
    return the pair: (stack, legend)
    """

    logging.debug( "DrawMCDataStack" )

    # Get the data, checking that there
    # is only one entry
    
    # Silly trick to get the (key,val) of the only entry in the dict
    #for (dName, dhist) in dataHistDict.iteritems(): break
    (dName, dhist ) = nameHistList[0]

    ResizeHistogram( dhist, [pair[1] for pair in nameHistList], request )

    # Create a stack of the MC histograms:
    stack = ROOT.THStack( "stack", "Stacked histograms" )
    
    # Now draw the MC histograms one by one:
    legendEntries = []

    for name, hist in nameHistList:
        # mchist.SetFillColor(color)
        # mchist.SetLineColor(color)
        logging.debug( "DrawMCDataStack - Adding Hist to stack: %s %s" % (name, hist) )
        stack.Add( hist )
        legendEntries.append( [hist, name, "f"] )
        #logging.debug( "Adding mc histogram to stack: %s (color = %d )" % (name, color) )
        pass

    stack.Draw( "HIST" )

    legendEntries.reverse()
    legend = MakeLegend( legendEntries, request )

    legend.Draw()

    # Now create the plot:
    # canvas.SaveAs( filename )
    return (stack, legend)
