
import os
import glob
import ROOT
import log, logging

from tools import *

def MakeMCStack( outputName, request, histCache=None ):
    """ Make a stack of MC and Data, and save it

    - Create a Canvas
    - Get the Data Hist
    - Get the MC Hists
    - Pass those to the 'DrawMCDataStack' function,
        which will draw them to the canvas
    - Save the canvas
    """
    
    # Create a canvas:
    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    canvas.cd()

    # Get the Lists of histograms
    mcHistList  = GetMCNameHistList(  request, histCache ) 
    bsmHistList = GetBSMNameHistList( request, histCache ) 

    CompareHistograms( [ pair[1] for pair in (mcHistList + bsmHistList) ] ) 
    #zip(*mcHistList)[1] + zip(*bsmHistList)[1] )

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    (stack, legend) = DrawMCStack( mcHistList, bsmHistList, request )

    AdjustAndDrawLegend( legend, request )

    #SetLegendBoundaries( legend, request )
    #legend.Draw()

    AdjustCanvas( canvas, request )

    SaveCanvas( canvas, request, outputName )

    canvas.Close()
    del canvas

    return


def DrawMCStack( mcHistList, bsmHistList, request={} ):
    """ Fetch, style, and draw a Data MC Stack


    Get the set of histograms from the request,
    style them, add them to a stack,
    and draw the stack.
    return the pair: (stack, legend)
    """

    logging.debug( "DrawMCDataStack" )

    # Create the sum of MC samples
    addedSamples = None
    for (name, hist) in mcHistList: # + bsmHistList:
        if addedSamples:
            addedSamples.Add ( hist )
        else:
            addedSamples = hist.Clone()
        pass

    # Create a stack of the MC histograms:
    stack = ROOT.THStack( "stack", "Stacked histograms" )
    
    # Now draw the MC histograms one by one:
    legendEntries = []

    for name, hist in mcHistList:
        # mchist.SetFillColor(color)
        # mchist.SetLineColor(color)
        logging.debug( "DrawMCDataStack - Adding Hist to stack: %s %s" % (name, hist) )
        stack.Add( hist )
        legendEntries.append( [hist, name, "f"] )
        #logging.debug( "Adding mc histogram to stack: %s (color = %d )" % (name, color) )
        pass


    ResizeHistogram( stack, [addedSamples] + [pair[1] for pair in bsmHistList], request )

    stack.Draw( "HIST" )

    legendEntries.reverse()
    legend = MakeLegend( legendEntries, request )

    # Draw the BSM hists:
    for name, bsmhist in bsmHistList:
        legend.AddEntry( bsmhist, name, "l" )
        bsmhist.Draw("HIST SAME")


    legend.Draw()

    # Now create the plot:
    # canvas.SaveAs( filename )
    return (stack, legend)
