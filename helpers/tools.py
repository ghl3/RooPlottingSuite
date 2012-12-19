
import glob
import ROOT
import logging
import sys, os
import math

from collections import Iterable

from HistCollector import *


def ParseOptionalArgs( kwargs ):
    """ Parse Common keyword args

    Options are either attached to a 
    request or to a plot
    This function splits
    the given optional arguments
    
    keyword options and examples:

    + Formats=['eps','pdf'] 
    + SuppressLegend=True
    + DrawErrors=True 
    + UseLogScale=True 
    + Minimum=10 
    + Maximum=2 
    + LegendBoundaries=(.8, .8, .95, .95)
    + Name="MyHist" 
    + XAxisTitle="Mass" 
    + YAxisTitle="EventsPerBin"
    + Normalize=True 
    + Rebin=2

    """

    requestOptions = {}
    plotOptions = {}

    for key,val in kwargs.iteritems():

        # Request
        SupportedRequestOptions = ["Formats", "SuppressLegend",
                                   "DrawErrors", "UseLogScale", 
                                   "Minimum", "Maximum", "LegendBoundaries",
                                   "RatioPlot"]
        if key in SupportedRequestOptions:
            requestOptions[key] = val

        # Plot
        SupportedPlotOptions = ["Name", "XAxisTitle", "YAxisTitle",
                                "Normalize", "Rebin", "SkipBins"]
        if key in SupportedPlotOptions:
            plotOptions[key] = val

    # Print warnings about unrecognized
    unrecognized = [k for k in kwargs if k not in requestOptions and k not in plotOptions]

    for key in unrecognized:
        print "WARNING - Ignoring Unrecognized option %s" % (key)

    return (requestOptions, plotOptions)


def GetAndStyleHist( plot, histCache=None ):
    """ Get a histogram, apply style

    """
    hist = GetHist( plot, histCache )
    hist = StyleHist( hist, plot )
    return hist


def GetHist( plot, histCache=None ):
    """ Get, style, and return a single histogram

    Get a single histogram.
    This histogram may exist across
    files, so add those component
    histograms if necessary.
    Style the histogram and return.
    """

    # If not provided, create a chache
    if histCache == None:
        histCache = HistCollector()

    # Get the histName of the histogram
    histName = plot["Hist"]
    if plot.get("Prefix"):
        histName = plot["Prefix"] + histName

    if "{{Sample}}" in histName:
        histName = histName.replace("{{Sample}}", plot["Name"])

    logging.debug( "GetAndStyleHist: Getting Hist: %s" % histName )
    
    if "FileList" not in plot:
        plot["FileList"] = glob.glob( plot["Files"] )

    if len(plot["FileList"]) == 0:
        plot["FileList"] = glob.glob( plot["Files"] )

    # If there are still no files....
    if len(plot["FileList"]) == 0:
        print "Error: No files found in glob string: ", plot["Files"]
        raise Exception("Files")

    # Get the list of files
    files = plot["FileList"]

    if len(files) == 0:
        print "Error: No files supplied in request: ", plot
        raise Exception("Hist Files")

    totalHist = None

    for file in files:

        logging.debug( "Opening File: %s" % file )
        try:
            hist = histCache.GetHist( file, histName )
        except:
            raise 
        if hist == None:
            print "Error: hist (%s, %s) is NONE" % (histName, file)
            raise Exception("Hist")
        if not totalHist:
            ROOT.gROOT.cd()
            totalHist = hist.Clone( histName )
        else:
            totalHist.Add( hist )
            pass
        
        hist.Delete()
        pass

    logging.debug( "Returning Total Hist: %s Entries: %s Integral: %s" % (totalHist, totalHist.GetEntries(), totalHist.Integral() ) )

    return totalHist



def StyleHist( hist, plot ):
    """ Style a histogram and return it

    """

    #if plot.get("Signal"):
    #    plot["Color"] = 2
    #    plot["FillColor"] = 2
    #    plot["LineColor"] = 1

    # Color the same
    if "Color" in plot:
        hist.SetFillColor( plot["Color"] )
        hist.SetLineColor( plot["Color"] )

    # Then, do more detailed coloring
    if "FillColor" in plot:
        hist.SetFillColor( plot["FillColor"] )

    if plot.get("Type") == "BSM":
        hist.SetFillColor(0)
    #else:
    #    hist.SetLineColor( ROOT.kBlack )

    if "LineColor" in plot:
        hist.SetLineColor( plot["LineColor"] )

    if plot.get("Scale"):
        hist.Scale( plot["Scale"] )

    if plot.get("Rebin"):
        RebinHist(hist, plot["Rebin"])

    if plot.get("Signal"):
        hist.SetFillColor(0)
        hist.SetLineColor(1)
        hist.SetLineStyle(1)
        hist.SetLineWidth(2)

    # Ignore certain bins if required.
    # This is done AFTER rebinning is applied
    if plot.get("SkipBins"):
        bin_list = plot["SkipBins"]
        try:
            for bin in bin_list:
                hist.SetBinContent( bin, 0.0 )
                hist.SetBinError( bin, 0.0 )
        except:
            print "Error: Can't ignore bins ", bin_list
        pass

    if "Normalize" in plot:
        if plot["Normalize"] == True:
            hist.Scale( 1.0 / hist.Integral() )
            hist.SetYTitle( "Normalized to Unity" )
        elif plot["Normalize"] == False:
            pass
        else:
            try:
                normalization = float(plot["Normalize"])
            except:
                raise Exception( "Error: Bad normalization value " )
                print plot["Normalize"]
            hist.Scale( normalization / hist.Integral() )
            hist.SetYTitle( "Normalized to %s" % plot["Normalize"] )
            pass

        pass
        
    # If requested, set the axis title
    if "XAxisTitle" in plot:
        hist.SetXTitle( plot["XAxisTitle"] )

    if "YAxisTitle" in plot:
        hist.SetYTitle( plot["YAxisTitle"] )

    return hist


def ScaleHist( hist, plot, request ):
    """ Scale a hist by Lumi if necessary

    Only scale if "Lumi" in request and if
    the hist's plot has "ScaleByLumi" == True
    """

    type = plot["Type"]

    if (type=="MC" or type=="BSM" ) and request.get("ScaleMCByLumi"):
        if "Lumi" not in request:
            print "Error: Asked to scale MC by Lumi, but value of Lumi not supplied"
            raise Exception("GetMCNameHistList - ScaleByLumi")
        if plot["ScaleByLumi"]:
            lumi = request["Lumi"]
            logging.debug( "Scaling Sample %s by lumi: %s" % (plot["Name"], lumi) )
            hist.Scale( lumi )
        pass
    return


def GetDataNameHistList( request, histCache=None ):
    """ Get a datahist from a request list

    """

    dataHistList = []
    dhist = None
    for plot in request["Plots"]:
        if plot["Type"] != "DATA": continue
        if "Title" in plot:
            name = plot["Title"]
        elif "Name" in plot:
            name = plot["Name"]
        else:
            name = plot["Hist"]

        dhist = GetAndStyleHist( plot, histCache )
        logging.debug( "GetDataHist - \t Got Data Hist %s %s" % (name, dhist) )
        dataHistList.append( (name, dhist) )

    return dataHistList


def GetMCNameHistList( request, histCache=None ):
    """ Get a list of pairs: (Name,  Hist) 

    
    Reorder the pairs such that signal samples
    are at the end of the list
    (Which makes them on top since we reverse
    the order when we draw)
    """

    #tmpSignalList = []

    mcHistList = []
    for plot in request["Plots"]:
        if plot["Type"] != "MC": continue
        hist = GetAndStyleHist( plot )
        if "Title" in plot:
            name = plot["Title"]
        elif "Name" in plot:
            name = plot["Name"]
        else:
            name = plot["Hist"]

        # Scale MC by Lumi if necessary
        ScaleHist( hist, plot, request )
        '''
        if request.get("ScaleMCByLumi"):
            if "Lumi" not in request:
                print "Error: Asked to scale MC by Lumi, but value of Lumi not supplied"
                raise Exception("GetMCNameHistList - ScaleByLumi")
            if plot["ScaleByLumi"]:
                lumi = request["Lumi"]
                logging.debug( "Scaling by lumi: %s" % lumi )
                hist.Scale( lumi )
            pass
        '''
        logging.debug( "GetMCNameHistList - \t Got MC Hist %s %s" % (name, hist) )
        #if plot.get("Signal"):
        #    tmpSignalList.append( (name, hist) )
        #else:
        #    mcHistList.append( (name, hist) )
        mcHistList.append( (name, hist) )

    #for pair in tmpSignalList:
    #    mcHistList.append( pair )

    return mcHistList


def GetBSMNameHistList( request, histCache=None ):
    """ Get a list of pairs: (Name,  Hist) 

    
    Reorder the pairs such that signal samples
    are at the end of the list
    (Which makes them on top since we reverse
    the order when we draw)
    """

    #tmpSignalList = []

    bsmHistList = []
    for plot in request["Plots"]:
        if plot["Type"] != "BSM": continue
        hist = GetAndStyleHist( plot )
        if "Title" in plot:
            name = plot["Title"]
        elif "Name" in plot:
            name = plot["Name"]
        else:
            name = plot["Hist"]

        # Scale BSM by Lumi if necessary
        ScaleHist( hist, plot, request )
        '''
        if request.get("ScaleMCByLumi"):
            if "Lumi" not in request:
                print "Error: Asked to scale MC by Lumi, but value of Lumi not supplied"
                raise Exception("GetBSMNameHistList - ScaleByLumi")
            lumi = request["Lumi"]
            logging.debug( "Scaling by lumi: %s" % lumi )
            hist.Scale( lumi )
        '''
        logging.debug( "GetBSMNameHistList - \t Got BSM Hist %s %s" % (name, hist) )
        #if plot.get("Signal"):
        #    tmpSignalList.append( (name, hist) )
        #else:
        #    bsmHistList.append( (name, hist) )
        bsmHistList.append( (name, hist) )

    #for pair in tmpSignalList:
    #    bsmHistList.append( pair )

    return bsmHistList


def GetNameHistList( request, histCache=None ):
    """ Get a list of pairs: (Name,  Hist) 

    
    Reorder the pairs such that signal samples
    are at the end of the list
    (Which makes them on top since we reverse
    the order when we draw)
    """

    #tmpSignalList = []

    histList = []
    for plot in request["Plots"]:

        if "Title" in plot:
            name = plot["Title"]
        elif "Name" in plot:
            name = plot["Name"]
        else:
            name = plot["Hist"]
        hist = GetAndStyleHist( plot )

        # Scale MC by Lumi if necessary
        ScaleHist( hist, plot, request )
        '''
        if request.get("ScaleMCByLumi"):
            if plot["Type"] == "MC": 
                if "Lumi" not in request:
                    print "Error: Asked to scale MC by Lumi, but value of Lumi not supplied"
                    raise Exception("GetMCNameHistList - ScaleByLumi")
                lumi = request["Lumi"]
                logging.debug( "Scaling by lumi: %s" % lumi )
                hist.Scale( lumi )
            pass
        '''
        logging.debug( "GetMCNameHistList - \t Got MC Hist %s %s" % (name, hist) )
        #if plot.get("Signal"):
        #    tmpSignalList.append( (name, hist) )
        #else:
        #    histList.append( (name, hist) )
        histList.append( (name, hist) )

    #for pair in tmpSignalList:
    #    histList.append( pair )

    return histList


def AdjustAndDrawLegend( legend, request ):

    if request.get("SuppressLegend"):
        return
    legend.Draw()


def SetLegendBoundaries( legend, request ):

    if "LegendBoundaries" not in request: return

    legendBoundaryTuple  = request["LegendBoundaries"]

    if len( val ) != 4:
        print "Legend boundaries must be a 4-dim tuple"
        raise Exception("Bad Legend Configuration")

    (legX1, legY1, legX2, legY2) = legendBoundaryTuple

    legend.SetX1( legX1 )
    legend.SetY1( legY1 )

    legend.SetX2( legX2 )
    legend.SetY2( legY2 )
    

#
#
def MakeCanvas(request, ):
    """ Create a canvas and return it

    If a Ratio Plot is requested, we also
    return the ratio plot

    """

    print "Making Canvas"
    
    bottom_min = .05
    top_min = .25


    ROOT.gROOT.cd()
    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    canvas.cd()

    if not request.get("RatioPlot"):
        return (canvas, None, None)
    else:
        print "Doing Ratio Plot"
        BottomPad = ROOT.TPad("BottomPad","BottomPad", 0.0, bottom_min, 1.0, top_min);
        BottomPad.SetTopMargin(0);
        BottomPad.SetBottomMargin(0);
        canvas.cd()
        BottomPad.Draw();
        
        TopPad = ROOT.TPad("TopPad","TopPad", 0.0, top_min, 1.0, 1.0);
        canvas.cd()
        TopPad.Draw();
        TopPad.cd()
    return (canvas, TopPad, BottomPad)


# Possibly unnecessary
# Candidate for deprecation
def MakeLegend( legendEntries, request ):
    """ Create a legend

    A legend's boundaries depend on the number of 
    entries, unless that number exceeds the predefined
    boundaries.
    """
    #SetLegendBoundaries( legend, request )

    #These boundaries are a border, legend may be smaller if necessary
    if "LegendBoundaries" not in request:
        print "Error: No Legend Boundaries Found"
        raise Exception("MakeLegend - Boundaries")

    (legX0, legY0, legX1, legY1) = request["LegendBoundaries"]

    LegendVariableMax = legY1
    LegendVariableMin = legY1 - .05*len(legendEntries)

    legY0 = max( LegendVariableMin, legY0 )
    
    # Unpack the legend boundaries
    #(legX0, legY0, legX1, legY1) = legBoundaries

    legend = ROOT.TLegend( legX0, legY0, legX1, legY1 )
    legend.AppendPad()
    legend.SetFillStyle( 0 )
    legend.SetBorderSize( 0 )

    # show the stacked histograms in the same order
    for (hist, name, style) in legendEntries: 
        logging.debug( "Legend Entries: %s %s %s" % (hist, name, style) )
        legend.AddEntry( hist, name, style )


    return legend


def GetNonZeroMin( histList ):
    """ Return the min bin that is > 0

    Loop over all bins in all histograms and
    return the minimum bin that is non-zero
    """

    NonZeroMin = sys.float_info.max
            
    for hist in histList:
        nBins = hist.GetNbinsX();

        for bin in range( nBins ):
            val = hist.GetBinContent( bin + 1 )
            if val < 0:
                logging.warning( "Adjusting bins - Bin %s has content %s which is < 0 in hist: %s" % (bin+1,val, hist) )
                continue
            if val == 0: 
                continue
            NonZeroMin = min( NonZeroMin, val )
        pass
    
    return NonZeroMin



def ResizeHistogram( template, histList, request={} ):
    """ Resize a template histogram
    
    The "template" histogram is the one to be drawn first
    Resize it so it is within the range of all the other
    histograms.
    Special care is taken for the minimum when log scale is used.
    """

    # Set the Minimum
    if "Minimum" in request:
        minimum = request["Minimum"]
    else:
        minimum = sys.float_info.max
        for hist in histList:
            minimum = min( minimum, hist.GetMinimum() )
    
        minimum = min( 0, minimum )

    # Set the Maximum
    if "Maximum" in request:
        maximum = request["Maximum"]
    else:
        maximum = sys.float_info.min
        for hist in histList:
            maximum = max( maximum, hist.GetMaximum() )

        maximum += math.sqrt( maximum )
        maximum *= 1.4

    # If Log scale, adjust the maximum
    if request.get("UseLogScale"):
        maximum *= 5
        if minimum <= 0:
            minimum = GetNonZeroMin( histList )
            minimum /= 1.05
        else:
            minimum = 0

    template.SetMaximum( maximum )
    template.SetMinimum( minimum )

    return


def RebinHist( hist, bins ):
    """ Rebin a histogram based on supplied bins

    'bins' can be one of two things:

    * A Single Number, in which case this determines
      the factor by which bins are merged.  
      ie, if bins == 2, there are half as many bins

    * A list of bin boundaries.  It must be of 
      length N+1, where N is the new number of 
      of bins.  Each value must coorespond to 
      an already existing bin edge (ie, this
      only merges bins, but can do so to make
      non-uniform binnings)

    See: http://root.cern.ch/root/html/TH1.html#TH1:Rebin

    """

    if bins==None:
        print "Error: Rebin requested, but no bin selected"
        raise Exception("Rebin Error")

    # If it's an integer, collect the bins by
    # that factor
    if isinstance(bins, (int, long)):
        print "Rebinning %s by a factor of %s" % (hist, bins)
        hist.Rebin( bins, "" )

    # If it's a list, rebin with this parameters
    elif isinstance(bins, Iterable):
        import array
        nBins = len([bins]) - 1
        print "Rebinning %s with boundaries: " % hist, bins
        hist.Rebin( nBins, "", array.array(bins) )

    else:
        print "Unknown rebinning parameters supplied", bins
        raise Exception("Rebin Error")

    return

def CompareHistograms( HistList ):
    """ Ensure histograms in the list match 

    """

    if len(HistList) == 0:
        print "Error: Cannot check histograms.  No histograms found"
        raise Exception("No Histograms")
    
    TestHist = HistList[0]

    for hist in HistList:
        if not CompareHists( TestHist, hist ):
            return False
        pass

    return True


def CompareHistogramLists( ListA, ListB ):

    for histA in ListA:
        for histB in ListB:
            if not CompareHists( histA, histB ):
                return false
            pass
        pass
    
    return True


def CompareHists( histA, histB ): 
    """ Compare two hists

    Determine if two histograms have the same
    binning and, in the case of labeled bins,
    the same bin labeling
    """

    # First, determine if they are the same class
    classA = histA.IsA().ClassName()
    classB = histB.IsA().ClassName()

    if classA != classB:
        print "Error: Incompatable histograms"
        print "Histogram %s has class %s and Histogram %s has class %s" % (histA.GetName(), classA, histB.GetName(), classB)
        raise Exception("Incompatable Hists - Class")
        return False

    # Check that their binning is the same
    nBinsA = histA.GetNbinsX()
    nBinsB = histB.GetNbinsX()

    if nBinsA != nBinsB:
        print "Error: Incompatable histograms"
        print "Histogram %s has NbinsX %s and Histogram %s has NbinsX %s" % (histA.GetName(), nBinsA, histB.GetName(), nBinsB)
        raise Exception("Incompatable Hists - NBins")
        return False

    # Check that bins match
    for itr in range(nBinsA):
        bin = itr + 1
        labelA = histA.GetXaxis().GetBinLabel(bin)
        labelB = histB.GetXaxis().GetBinLabel(bin)
        if labelA!= labelB:
            print "Error: Incompatable histograms"
            print "Histogram %s has lable %s and Histogram %s has label %s for bin %s" % (histA.GetName(), labelA, histB.GetName(), labelB, bin)
            raise Exception("Incompatable Hists - Labels")
            return False
        
    return True


def PrintGarbage():
    import gc
    for obj in gc.get_objects():
        if hasattr(obj,"__class__"):
            if obj.__class__.__module__ == 'ROOT':
                print obj
            pass
        else:
            print obj

def AdjustCanvas( canvas, request ):
    """ Adjust a canvas based on a request

    """

    if "Title" in request:
        canvas.SetTitle( request["Title"] )

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

    canvas.RedrawAxis(); 

def PrintCanvas( canvas, outputName ):
    """ Save a canvas

    If pdf, include a title
    """

    if "pdf" in outputName:
        canvas.Print( outputName, "Title:"  )
    else:
        canvas.Print( outputName  )


def SaveCanvas( canvas, request, outputName ):
    """ Save a canvas

    Determine the type from the name
    Add an outputdir if in request
    """
    
    if "OutputDir" in request:
        dir = request["OutputDir"]
        if dir!= "":
            outputName = dir + '/' + outputName
        pass
        
    if "Formats" in request:
        if '.' in outputName:
            outputNameBase = outputName[ : outputName.rfind('.') ]
        else:
            outputNameBase = outputName
        for format in request["Formats"]:
            FullName = outputNameBase + '.' + format
            # print "Saving Canvas as: ", FullName
            PrintCanvas( canvas, FullName )
            if not os.path.exists( FullName ):
                print "Error -  Failed to make the following output: %s" % FullName
                raise Exception("Saving Canvas PRINT")
            pass
        pass
            
    else:
        PrintCanvas( canvas, outputName)
        if not os.path.exists( outputName ):
            print "Error -  Failed to make the following output: %s" % outputName
            raise Exception("Saving Canvas PRINT")
        pass
    
    return
    
def GetBinValue( hist, binName ):
    """ Return the value of a bin by name

    """
    bin = hist.GetXaxis().FindBin( binName )
    return hist.GetBinContent( bin )


def MakeLatexString( string ):
    """ Make a string latex friendly

    """
    return string.replace('_', '\_')

