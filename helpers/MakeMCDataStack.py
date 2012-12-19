
import os
import glob
import ROOT
import logging

from tools import *

def MakeMCDataStack( outputName, request, histCache=None ):
    """ Make a stack of MC and Data, and save it

    - Create a Canvas
    - Get the Data Hist
    - Get the MC Hists
    - Pass those to the 'DrawMCDataStack' function,
        which will draw them to the canvas
    - Save the canvas
    """
    
    # Create a canvas:
    #ROOT.gROOT.cd()
    #canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    #canvas.cd()
    
    if not request.get("UseCurrentCanvas"):
        (canvas, TopPad, BottomPad) = MakeCanvas(request)

    # Get the data hist
    dataHistList = GetDataNameHistList( request, histCache )

    # Make a list of the MC (NOT BSM)
    mcHistList   = GetMCNameHistList( request, histCache )

    # Make a list of the BSM Hists
    bsmHistList  = GetBSMNameHistList( request, histCache )

    # Check that all histograms match
    CompareHistograms( [ pair[1] for pair in (dataHistList + mcHistList + bsmHistList) ] ) 

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    (stack, legend) = DrawMCDataStack( dataHistList, mcHistList, bsmHistList, request )

    AdjustAndDrawLegend( legend, request )

    #SetLegendBoundaries( legend, request )
    #legend.Draw()
    
    if not request.get("UseCurrentCanvas"):
        AdjustCanvas( canvas, request )

    if request.get("RatioPlot"):
        BottomPad.cd()
        BottomPad.SetGrid();
        ratio = DrawRatioPlot(mcHistList, dataHistList, request)

    if not request.get("UseCurrentCanvas"):
        SaveCanvas( canvas, request, outputName )
        canvas.Close()
        del canvas

    return

    


def DrawMCDataStack( dataHistList, mcHistList, bsmHistList, request={} ):
    """ Fetch, style, and draw a Data MC Stack


    Get the set of histograms from the request,
    style them, add them to a stack,
    and draw the stack.
    return the pair: (stack, legend)
    """

    logging.debug( "DrawMCDataStack" )

    # Get the data, checking that there
    # is only one entry
    
    if len( dataHistList ) != 1:
        print "Error: More than 1 data sample supplied"
        print "Error: Only takes one"
        raise Exception("DrawMCDataStack - DATA")
        return

    # There should be only 1 data hist
    (dName, dhist ) = dataHistList[0]

    ResizeHistogram( dhist, [dhist] + [pair[1] for pair in mcHistList + bsmHistList], request )
    dhist.Draw()

    # Create a stack of the MC histograms:
    stack = ROOT.THStack( "mcstack", "Stacked MC histograms" )
    
    # Now draw the MC histograms one by one:
    legendEntries = []

    for name, mchist in mcHistList:
        # mchist.SetFillColor(color)
        # mchist.SetLineColor(color)
        logging.debug( "DrawMCDataStack - Adding MC Hist to stack: %s %s" % (name, mchist) )
        stack.Add( mchist )
        #stack.Draw( "HIST SAME" )
        legendEntries.append( [mchist, name, "f"] )
        #logging.debug( "Adding mc histogram to stack: %s (color = %d )" % (name, color) )
        pass

    stack.Draw( "HIST SAME" )
    legendEntries.append( [dhist, dName, "lpe"] )

    # Draw the data points again:
    # stack.Draw( "HIST SAME" )
    dhist.Draw( "SAME" )

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


def DrawRatioPlot(mcList, dataHistList, request=None):
    """ Take a list of histograms and draw the ratio of their sum

    The properties of the ratio are specified in the 
    optional 'request' option (but no such properties
    are supported as of now)

    """

    if len( dataHistList ) != 1:
        print "Error: More than 1 data sample supplied"
        print "Error: Only takes one"
        raise Exception("DrawMCDataStack - DATA")
        return

    # There should be only 1 data hist
    (dName, dhist ) = dataHistList[0]

    # Get the total MC
    (templateName, templateHist) = mcList[0]
    denominator = templateHist.Clone(templateName + "_denominator")
    for (name, hist) in mcList[1:]:
        denominator.Add(hist)

    # Get the Ratio
    ratio = dhist.Clone(dName + "_ratio")        
    ratio.Divide(denominator)

    ratio.SetAxisRange( 0, 2, "Y" )

    # Treate the case of ~0.0/~0.0 as 1.0
    for bin_idx in range(dhist.GetNbinsX()):
        if dhist.GetBinContent(bin_idx+1) < .00001 and denominator.GetBinContent(bin_idx+1) < .00001:
            Quot.SetBinContent(bin_idx+1, 1.0)
            print "Setting 0/0 content to 1.0"


    ratio.Draw()

    return ratio
