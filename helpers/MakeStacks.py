
import os
import glob
import ROOT
import log, logging

from tools import *

"""
This is just a work in progress.
The goal is to merge the modules:
  - MakeStack
  - MakeMCStack
  - MakeMCDataStack

by using the same DrawStack method, 
and only drawing data or bsm hists after the fact.

Issues: 

  - Getting the datat to be the 1st entry in the legend
  - Resizing the Canvas after the data or bsm hists are drawn

"""



def MakeStack( outputName, request, histCache=None ):
    """ Make a stack of MC and Data, and save it

    - Create a Canvas
    - Get the Data Hist
    - Get the MC Hists
    - Pass those to the 'DrawMCDataStack' function,
        which will draw them to the canvas
    - Save the canvas
    """

    """
    # Tell ROOT to use this style:
    from style.AtlasStyle import AtlasStyle
    style = AtlasStyle()
    ROOT.gROOT.SetStyle( style.GetName() )
    ROOT.gROOT.ForceStyle()
    ROOT.TGaxis.SetMaxDigits( 4 )
    """
    
    # Create a canvas:
    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    ROOT.SetOwnership(canvas, False)

    canvas.cd()

    # Get the data hist
    nameHistList = []
    
    nameHistList.extend( GetDataNameHistList( request, histCache ) )
    nameHistList.extend( GetMCNameHistList(   request, histCache ) )
    nameHistList.extend( GetBSMNameHistList(  request, histCache ) )

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    (stack, legend) = DrawStack( nameHistList, request )

    SetLegendBoundaries( legend, request )
    legend.Draw()

    # Add the ATLAS notations:
    if request.get("AtlasLabel") == True:
        import AtlasUtil
        AtlasUtil.AtlasLabel( 0.20, 0.85 )
        if "Lumi" in request:
            lumi = request("Lumi")
            AtlasUtil.DrawLuminosity( 0.20, 0.76, lumi )
        pass


    if request.get("UseLogScale"):
        canvas.SetLogy()        


    if "OutputDir" in request:
        dir = request["OutputDir"]
        if dir!= "":
            outputName = dir + '/' + outputName
        pass

    if "pdf" in outputName:
        canvas.Print( outputName, "Title:"  )
    else:
        canvas.Print( outputName )

    # Check that the file was created
    if not os.path.exists( outputName ):
        print "Error - MakeMultiplePlot failed to make the following output: %s" % outputName
        raise Exception("MakeMultiplePlot PRINT")


    del canvas

    return


def MakeMCDataStack( outputName, request, histCache=None ):
    """ Make a stack of MC and Data, and save it

    - Create a Canvas
    - Get the Data Hist
    - Get the MC Hists
    - Pass those to the 'DrawMCDataStack' function,
        which will draw them to the canvas
    - Save the canvas
    """

    """
    # Tell ROOT to use this style:
    from style.AtlasStyle import AtlasStyle
    style = AtlasStyle()
    ROOT.gROOT.SetStyle( style.GetName() )
    ROOT.gROOT.ForceStyle()
    ROOT.TGaxis.SetMaxDigits( 4 )
    """
    
    # Create a canvas:
    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    ROOT.SetOwnership(canvas, False)

    canvas.cd()

    # Get the data hist
    dataHistList = GetDataNameHistList( request, histCache )

    # Make a list of the MC (NOT BSM)
    mcHistList   = GetMCNameHistList( request, histCache )

    # Make a list of the BSM Hists
    bsmHistList  = GetBSMNameHistList( request, histCache )

    # Pass them to the drawing function
    # We collect the return so it isn't destroyed
    (stack, legend) = DrawStack( mcHistList, request )

    

    SetLegendBoundaries( legend, request )
    legend.Draw()

    # Add the ATLAS notations:
    if request.get("AtlasLabel") == True:
        import AtlasUtil
        AtlasUtil.AtlasLabel( 0.20, 0.85 )
        if "Lumi" in request:
            lumi = request("Lumi")
            AtlasUtil.DrawLuminosity( 0.20, 0.76, lumi )
        pass


    if request.get("UseLogScale"):
        canvas.SetLogy()        


    if "OutputDir" in request:
        dir = request["OutputDir"]
        if dir!= "":
            outputName = dir + '/' + outputName
        pass

    if "pdf" in outputName:
        canvas.Print( outputName, "Title:"  )
    else:
        canvas.Print( outputName  )

    # Check that the file was created
    if not os.path.exists( outputName ):
        print "Error - MakeMultiplePlot failed to make the following output: %s" % outputName
        raise Exception("MakeMultiplePlot PRINT")


    del canvas

    return



#
# The "Drawing" method
#



def DrawStack( nameHistList, request={} ):
    """ Fetch, style, and draw a Data MC Stack


    Get the set of histograms from the request,
    style them, add them to a stack,
    and draw the stack.
    return the pair: (stack, legend)
    """

    logging.debug( "DrawMCDataStack" )

    if len( nameHistList ) == 0:
        print "Error: No Histograms supplied to stack"
        raise Exception( "DrawStack - Histograms" )
        
    (dName, dhist ) = nameHistList[0]

    # Create the sum of MC samples
    addedSamples = None
    for (name, hist) in nameHistList:
        if addedSamples:
            addedSamples.Add ( hist )
        else:
            addedSamples = hist.Clone()
        pass

    maximum = max( [ addedSamples.GetMaximum(), dhist.GetMaximum() ] )
    maximum *= 1.4

    minimum = min( [ addedSamples.GetMinimum(), dhist.GetMinimum() ] )
    minimum /= 1.4

    ResizeHistogram( dhist, [pair[1] for pair in nameHistList], request )
    #dhist.Draw()

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

    stack.SetMaximum( maximum )
    #stack.SetMinimum( minimum )

    if request.get("UseLogScale"):
        stack.SetMinimum( min( 1.0, minimum) )
    else:
        stack.SetMinimum( 0.0 )

    stack.Draw( "HIST" )

    legendEntries.reverse()
    legend = MakeLegend( legendEntries, request )

    legend.Draw()

    # Now create the plot:
    # canvas.SaveAs( filename )
    return (stack, legend)

