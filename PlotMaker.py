
#
# This is a simple module designed to make it simple to produce nice plots
# out of already-produced histograms.  In particular, it is designed to 
# create plots that compare data with predictions (from Monte-Carlo or otherwise)
#

# My git Test

import sys
import glob
import logging #log
import copy
import itertools
import random

# Import native OrderedDict, or use
# local version for python < 2.7
if sys.version_info >= (2, 7):
    from collections import OrderedDict
else:
    from OrderedDict import *

from helpers.MakeStack import *
from helpers.MakeMCStack import *
from helpers.MakeMCDataStack import *
from helpers.MakeMultiplePlot import *
from helpers.MakeQuotientPlot import *
from helpers.MakeMultipleTH1Plot import *
from helpers.MakeLatexTable import *

import ROOT
from HistCollector import *


class PlotMaker( ROOT.TNamed ):
    """ The main class to set samples and generate plots

    This class is used to generate nicely formatted plots by
    combining a number of ROOT files which contain histograms.


    The class holds a vector of samples which
    it divides into:
    * data
    * mc  (monte carlo)
    * bsm (beyond-the-standard-model like samples)
    
    The distinction (and naming conventions) is simply
    a matter of plotting

    These can be set using the methods:

    :py:meth:`~PlotMaker.PlotMaker.AddMCSample`
    :py:meth:`~PlotMaker.PlotMaker.AddDataSample`
    :py:meth:`~PlotMaker.PlotMaker.AddBSMSample`

    Once these are set, one can automatically generate
    plots combining those samples using the PlotMaker's
    plotting methods.  For example, one can run:

    :py:meth:`~PlotMaker.PlotMaker.MakeMCDataStack`

    This will extract the histogram named 'hist' from each
    sample and will plot them and save them to "myPlot.pdf"

    One can specify a number of samples to use (this must be
    a subset of the number of already added samples) using the
    "sampleList" keyword argument.  It takes a list of strings
    representing the names of the samples.  This structure is 
    repeated for all of the plot-making methods.


    The underlying functionality of the class works by passing
    around "JSON" like python dictionaries specifying a list of
    plots to be made and how they are to be styled

    PlotDescription:
    { "Name" : "myName", "File" : "FileString", 
    "FileList" : [ ListOfFiles (obtained via glob) ],
    "MarkerColor" : "myMarkerColor", "LineStyle" : "myLineStyle"}

    The FileList should be a glob of the FileString...
    This is done automatically upon adding the sample, 
    and store both in case it's necessary...

    The mcsamples and bsmsamples
    are dictionaries (only to make nicer code)
    { "NameA" : {PlotDescriptionA}, "NameB" : {PlotDescriptionB} }

    
    All functions to create plots can be provided
    keyword arguments to modify the style of
    drawn plots. See: :py:func:`~helpers.tools.ParseOptionalArgs`


    """

    def __init__( self, name = "PlotMaker", title = "Plot maker object" ):

        #Initialise the base class:
        ROOT.TNamed.__init__( self, name, title )

        # Initialize the logger
        FORMAT = "%(levelname)s  %(message)s"
        logging.basicConfig( level=logging.INFO, format=FORMAT )

        self.SetName( name )
        self.SetTitle( title )
        self.logger = self.getLogger( name )
        self.logger.setLevel( logging.INFO )

        # Tell ROOT to use this style:
        from style.AtlasStyle import AtlasStyle
        style = AtlasStyle()
        ROOT.gROOT.SetStyle( style.GetName() )
        ROOT.gROOT.ForceStyle()
        ROOT.TGaxis.SetMaxDigits( 4 )

        # Create the caching class
        self.histCache = HistCollector()
        self.requestCache = []

        # Use OrderedDicts
        self.__datasamples  = OrderedDict()
        self.__mcsamples    = OrderedDict()
        self.__bsmsamples   = OrderedDict()

        # Default Legend Values
        self.__legendLowX  = 0.75
        self.__legendLowY  = 0.70
        self.__legendHighX = 0.95
        self.__legendHighY = 0.90

        self.__luminosity    = 1.0
        self.__scaleMCByLumi = True
        self.__AtlasLabel    = True
        self.__useLogScale   = False
        self.__doHistRebin   = False
        self.__newBins = None

        self.__outputDir = ""

        self.__defaultcolors     = [29,34,30,33,38,46,41,40,14,21,47,49,9,43,23,45]+[34,46,43,30,31,44,42,47,29,45,33,36,35,27,32,41,39,38,26,37,48,40]+[4,3,2,6,38,33,20,7,8] 
        self.__defaultlinestyles = [4,3,2,5,6,40,41,46,38,33,30,20,7,8,9] # bright colors

        return

    #
    # Simple configuration methods
    #

    def getLogger( self, name ):
        # Set the format of the log messages:
        FORMAT = 'Py:%(name)-25s  %(levelname)-8s  %(message)s'
        import logging
        logging.basicConfig( format = FORMAT )
        # Create the logger object:
        logger = logging.getLogger( name )
        logger.setLevel( logging.INFO )
        return logger

    def RebinHistograms( self, bins ):
        """ Rebin histograms 

        NOT YET FULLY IMPLEMENTED
        """
        self.__doHistRebin = True
        self.__newBins = bins

    def SetLevelInfo( self ) :
        """ Set the level of the logging to INFO 

        """
        logging.basicConfig( level=logging.INFO )
        #self.logger.setLevel( logging.INFO )    

    def SetLevelDebug( self ) :
        """ Set the level of the logging to DEBUG

        """
        logging.basicConfig( level=logging.DEBUG )
        #self.logger.setLevel( logging.DEBUG )    

    def SetAtlasLabel( self, set ) :
        """ Set whether to include the ATLAS label
       
        Takes "True" or "False"
        """
        self.__AtlasLabel = set

    def UseLogScale( self, useLogScale ) :
        """ Set whether to use log scale on the y-axis

        Takes "True" or "False"
        """
        self.__useLogScale = useLogScale

    def ScaleMCByLumi( self, doScale=True ):
        """ Scale all MC by the global Lumi Value

        Set to true or false the scaling
        of all MC by the supplied Lumi
        """
        self.__scaleMCByLumi = doScale

    def SetOutputDir( self, outputDir ) :
        self.__outputDir = outputDir
    
    def GetConfigurationState(self):
        """ Return a dictionary of the config state

        This method is to be used internally.

        Go through the current properties of this
        class and pack them into a dictionary.
        Return that dictionary.
        """
        ConfigState = {}

        ConfigState["UseLogScale"]   = self.__useLogScale
        ConfigState["ScaleMCByLumi"] = self.__scaleMCByLumi
        ConfigState["OutputDir"]     = self.__outputDir
        ConfigState["Lumi"]          = self.__luminosity

        ConfigState["LegendBoundaries"] = (self.__legendLowX,  self.__legendLowY, 
                                           self.__legendHighX, self.__legendHighY)

        return ConfigState



    def SetLegendBoundaries( self, lowX, lowY, highX, highY ):
        """ Set the boundaries of the global legend object

        Takes (x0, y0, x1, y1)
        """
        self.__legendLowX = lowX
        self.__legendLowY = lowY
        self.__legendHighX = highX
        self.__legendHighY = highY
        return
    def SetLegendSize( self, lowX, lowY, highX, highY ):
        """ Backward Compatability """
        SetLegendBoundaries( lowX, lowY, highX, highY )
        

    def SetLuminosity( self, luminosity ):
        """ Set the global luminosity object

        If requested, all MC will be scaled by this value
        """
        self.__luminosity = luminosity
        return

    def SetLumi( self, luminosity ):
        """ Just a reference to :py:meth:`~PlotMaker.PlotMaker.SetLuminosity`

        """
        self.SetLuminosity( luminosity)

    def GetDefaultColor( self, usedcolors ) :
        """ An internal method for choosing a default color

        """
        for color in self.__defaultcolors:
            if color not in usedcolors:
                usedcolors.append( color )
                return color
            
        # If all the colors are used, 
        # Reset and start again:
        del usedcolors[ : ]
        return GetDefaultColor( usedcolors )


    #
    # Sample adding methods
    #

    def AddDataSample( self, name, files, title=None, prefix=None ):
        """ Add a Data Sample 

        Supply it a name and a file (or list of files using '*')
        """

        self.logger.info( "AddDataFile: Adding data file: " + files )

        # Glob the files
        FileList = glob.glob( files )

        if title==None:
            title=name

        # Create the dictionary
        info = { "Name" : name, "Files" : files, "Title" : title, "Prefix" : prefix, 
                 "FileList" : FileList, "Type" : "DATA", "ScaleByLumi" : False }

        if name not in self.__datasamples:
            self.__datasamples[name] = info
        else:
            self.__datasamples[name]["FileList"].extend( FileList )
        pass

        return


    def AddMCSample( self, name, files, prefix=None, 
                     color=None, title=None, linestyle=0, signal=None, 
                     Scale=None, ScaleByLumi=True ):
        """ Add a MC Sample 

        Supply it a name, a file (or list of files using '*')
        Optionally supply a color and a linestyle
        """

        self.logger.info( "AddMCFile:  Adding Monte Carlo file: " + files + " (" + name + ")" )

        # Pick a random color if none supplied
        if color == None:
            color = self.GetNotUsedColor() # HARD CODED FOR NOW...!
        if linestyle == None:
            linestyle = 1 # HARD CODED FOR NOW...!

        if title==None:
            title=name
        
        # Glob the files
        FileList = glob.glob( files )

        # Check if this sample has already been added:
        if name in self.__mcsamples:
            sample = self.__mcsamples[name]
            sample["FileList"].extend( FileList )

        # Otherwise, create the sample
        else:
            info = { "Name" : name, "Files" : files, "FileList" : FileList, 
                     "Title" : title, "Prefix" : prefix,
                     "Scale" : Scale, "Color" : color, 
                     "LineStyle" : linestyle, "Signal" : signal, "Type" : "MC",
                     "ScaleByLumi" : ScaleByLumi }
            self.__mcsamples[name] = info

        return


    def AddBSMSample( self, name, files, prefix=None, 
                      color=None, title=None, linestyle=0, Scale=None ):
        """ Add a BSM Sample 

        Supply it a name, a file (or list of files using '*' )
        Optionally supply a color and a linestyle
        """

        self.logger.info( "AddBSMFile:  Adding BSM Monte Carlo file: " + files + " (" + name + ")" )

        # Pick a random color if none supplied
        if color == None:
            color = self.GetNotUsedColor() # HARD CODED FOR NOW...!
        if linestyle == None:
            linestyle = 1 # HARD CODED FOR NOW...!

        if title==None:
            title=name

        # Glob the files
        FileList = glob.glob( files )

        # Check if this sample has already been added:
        if name in self.__bsmsamples:
            sample = self.__bsmsamples[name]
            sample["FileList"].extend( FileList )

        # Otherwise, create the sample
        else:
            info = { "Name" : name, "Files" : files, "FileList" : FileList, 
                     "Prefix" : prefix, "Scale" : Scale, "ScaleByLumi" : True,
                     "Title" : title, "Color" : color, "LineStyle" : linestyle, "Type" : "BSM" }
            self.__bsmsamples[name] = info

        return


    def PrintAllSamples(self):
        """ Print all samples

        Meant for debugging
        """
        print "Data Samples:"
        for name, sample in self.__datasamples.iteritems():
            for (key, val) in sample.iteritems():
                print " %s : %s " % (key, val),
            print "\n"
            pass
        print ""

        print "MC Samples:"
        for name, sample in self.__mcsamples.iteritems():
            for key, val, in sample.iteritems():
                print " %s : %s " % (key, val),
            print "\n"
            pass
        print ""

        print "BSM Samples:"
        for name, sample in self.__bsmsamples.iteritems():
            for key, val in sample:
                print key, val
        print ""


    def PrintRequestCache(self):
        """ Print the contents of the request cache

        Meant for debugging
        """
        for cache in self.requestCache:
            print cache
            
        return


    def GetNotUsedColor( self ):
        """ Get a color if one isn't already supplied

        Used internally
        """
        usedcolors = []
        for sample in self.__mcsamples.values() + self.__bsmsamples.values():
            usedcolors.append( sample["Color"] )
        
        for color in self.__defaultcolors:
            if color not in usedcolors:
                return color
            pass
        
        # Else, have to throw random numbers
        for i in range( 100 ):
            color = int( random.random()*100 )
            if color not in usedcolors:
                return color
            pass
        
        return 1


    def GetPlot( self, sampleName ) :
        """ Find a stored sample and return a deepcopy

        """
        plot = None

        if sampleName in self.__mcsamples:
            plot = copy.deepcopy( self.__mcsamples[ sampleName ] )

        elif sampleName in self.__bsmsamples:
            plot = copy.deepcopy( self.__bsmsamples[ sampleName ] )

        elif sampleName in self.__datasamples:
            plot = copy.deepcopy( self.__datasamples[ sampleName ] )

        else:
            print "Error: Sample %s not found in either MC or data" % sampleName
            raise Exception("GetSample - Sample")
        
        plot["SampleName"] = sampleName

        return plot



    def GetListOfPlots( self, sample_dict_list, sample_list=[]) :
        """ Return a list of 'Plots' based on the 
        input dictionaries and the sample_list


        Loop through the internally held samples, 
        get the ones that are requested, 
        add any options to the 'plot' dictionary,
        and return the list of plot dictionaries

        Each plot in the returned list of plots should
        be updated with global plotRequests and should
        have a histogram be added
        """

        plot_list = []

        # Make a merged sample dictionary
        # Be sure to Maintain Order
        available_samples = OrderedDict()
        for dict in sample_dict_list:
            for (key, val) in reversed(list(dict.iteritems())):
                available_samples[key] = val
            pass

        # If the sample list is empty, use all samples
        if sample_list == []:
            for name, sample in available_samples.iteritems(): 
                plot = self.GetPlot(sample["Name"]) #copy.deepcopy(sample)
                plot_list.append( plot )
            pass

        else:

            # Reverse the sample list
            sample_list = sample_list[::-1]
            #sample_list.reverse() #reversed(sample_list)

            # Check if the sample is even valid
            all_samples = []
            all_samples.extend( self.__datasamples.keys() )
            all_samples.extend( self.__mcsamples.keys() )
            all_samples.extend( self.__bsmsamples.keys() )

            # Check that all requested samples are actually valid
            for sample in sample_list:
                if sample not in all_samples: #( key for dict in all_samples for (key,val) in dict.iteritems() ):
                    print "Error: Sample %s doesn't exist" % sample
                    raise Exception("Invalid Sample Requested")

            for name in sample_list:
                if name not in available_samples: continue
                sample = available_samples[name]
                plot = self.GetPlot(sample["Name"]) #copy.deepcopy(sample)
                plot_list.append( plot )

        '''
        for sample_dict in sample_dict_list:
            for name, sample in sample_dict.iteritems():
                if sample_list != [] and name not in sample_list: continue
                plot = copy.deepcopy(sample)
                plot_list.append( plot )
            pass
        '''

        if len(plot_list) == 0:
            print "Error: No histograms from sampleList found."
            raise Exception("No Histograms Found")

        return plot_list



    #
    # The methods used to make plots
    #

    def MakeSamplePlot( self, histName, sampleName, outputName="", cache=False, **kwargs ):
        """ Make a plot of a given histogram for a given sample

        For a particular sample given by the sampleName,
        make a plot of the given hist.
        """

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # Create a default name if necessary
        if outputName == "":
            modHistName = histName.replace('/','_')
            outputName = "%s_%s.%s" % (sampleName, modHistName, kind)

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        #foundSample = False

        #plotTemplate = self.GetSample( sampleName ) #None
        #plot = copy.deepcopy( plotTemplate )
        plot = self.GetPlot( sampleName )
        plot.update( plotOptions )
        plot["Hist"]  = histName
        request["Plots"].append( plot )
        request["Type"] = "SamplePlot"
        request["OutputName"] = outputName

        if cache:
            self.requestCache.append( request )
        else:
            return MakeMultiplePlot( outputName, request );


    def MakeEfficiencyPlot( self, numerator, denominator, sampleName, outputName="", cache=False, **kwargs):
        """ Make a plot of the quotient of two histograms

        This function calls :py:meth:`helpers.MakeQuotientPlot.MakeQuotientPlot`

        Supply the numerator and denominator by names
        """

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # Create a default name if necessary
        if outputName == "":
            modHistName = histName.replace('/','_')
            outputName = "%s_%s.%s" % (sampleName, modHistName, kind)

        request = {}
        request["DrawErrors"] = True # Set the default
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity

        if "Maximum" not in request:
            request["Maximum"] = 1.2 # Efficiency Maximum
        request["Plots"] = []

        #foundSample = False

        plotTemplate = self.GetPlot( sampleName ) #None
        plotTemplate["FillColor"] = 0 # No Fill

        # We make two plots,
        # one for numerator and one for denominator
        plotNumerator = copy.deepcopy(plotTemplate)
        plotNumerator.update( plotOptions )
        plotNumerator["Hist"]  = numerator
        plotNumerator["QuotientType"] = "Numerator"
        request["Plots"].append( plotNumerator )

        plotDenominator = copy.deepcopy(plotTemplate)
        plotDenominator.update( plotOptions )
        plotDenominator["Hist"]  = denominator
        plotNumerator["QuotientType"] = "Denominator"
        request["Plots"].append( plotDenominator )

        # Now, the request will create two plots

        request["Type"] = "EfficiencyPlot"
        request["OutputName"] = outputName

        if cache:
            self.requestCache.append( request )
        else:
            MakeQuotientPlot( outputName, request );

        return


    def PlotHistogram( self, hname, filename ):
        """ Present for backward compatability

        """
        self.MakeMCDataPlot( histName=hname, outputName=filename )


    def MakeMCDataStack(self, hist, outputName="", sampleList=[], cache=False, **kwargs):
        """ Make a plot of data and a stack of MC 

        This function calls :py:meth:`helpers.MakeMCDataStack.MakeMCDataStack`

        Deligate the work to the helper function 
        of the same name.
        Here, simply build up the JSON request
        from the current state of the class
        and pass it to the function.
        """
        # Build up the set of samples
        # and add configuration

        # IF necessary, make a default name
        if outputName == "":
            outputName = "%s.pdf" % hist

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # Use black lines between stacks
        if "LineColor" not in plotOptions:
            plotOptions["LineColor"] = ROOT.kBlack

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []
        
        # Configure all plots to be added
        # Do this by collecting the MC and
        # datasamples and setting their
        # histograms to the request HIST

        # Always add all data
        for name, sample in self.__datasamples.iteritems():
            plot = self.GetPlot(sample["Name"]) #copy.deepcopy(sample)
            #plot["Hist"] = hist
            request["Plots"].append( plot )

        # Add the MC and BSM samples to the request
        # based on the sampleList (if there is one)
        #for sample in [plot["Name"] for plot in itertools.chain(self.__mcsamples, self.__bsmsamples]
        mc_bsm_samples = self.GetListOfPlots( [self.__mcsamples, self.__bsmsamples], sampleList ) 
        request["Plots"].extend( mc_bsm_samples )

        # Configure all plots
        for plot in request["Plots"]:
            plot["Hist"] = hist
            plot.update( plotOptions )

        """
        for name, sample in self.__mcsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot.update( plotOptions )
            plot["Hist"] = hist
            request["Plots"].append( plot )

        for name, sample in self.__bsmsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot.update( plotOptions )
            plot["Hist"] = hist
            request["Plots"].append( plot )
        """
        # Set the request type
        request["Type"] = "MCDataStack"
        request["OutputName"] = outputName

        # If cache, wait for later
        # Else, make the histogram now

        if cache:
            self.requestCache.append( request )
        else:
            #MakeMCDataStack.MakeMCDataStack( outputName, request );
            MakeMCDataStack( outputName, request );

        ROOT.gROOT.DeleteAll()

        return


    def MakeStack(self, hist, outputName="", sampleList=[], cache=False, **kwargs):
        """ Make a plot of data and a stack of MC 

        Deligate the work to the helper function 
        of the same name.
        Here, simply build up the JSON request
        from the current state of the class
        and pass it to the function.
        """
        # Build up the set of samples
        # and add configuration

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # IF necessary, make a default name
        if outputName == "":
            outputName = "%s.pdf" % hist

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # If the input sampleList is empty,
        # we interpret that to mean that we use
        # all available samples

        # Configure all plots to be added
        # Do this by collecting the MC and
        # datasamples and setting their
        # histograms to the request HIST
        mc_bsm_samples = self.GetListOfPlots( [self.__mcsamples, self.__bsmsamples], sampleList) 
        for plot in mc_bsm_samples:
            plot["Hist"] = hist
            plot.extend( plotOptions )
        request["Plots"].extend( mc_bsm_samples )

        """
        allSamples = itertools.chain(self.__datasamples.iteritems(), self.__mcsamples.iteritems(), self.__bsmsamples.iteritems())
        for name, sample in allSamples:
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot.update( plotOptions )
            plot["Hist"] = hist
            request["Plots"].append( plot )
        """
        # Set the request type
        request["Type"] = "Stack"
        request["OutputName"] = outputName

        # If cache, wait for later
        # Else, make the histogram now
        if cache:
            self.requestCache.append( request )
        else:
            MakeStack( outputName, request );

        return


    def MakeMCStack(self, hist, outputName="", sampleList=[], cache=False, **kwargs):
        """ Make a plot of data and a stack of MC 

        Deligate the work to the helper function 
        of the same name.
        Here, simply build up the JSON request
        from the current state of the class
        and pass it to the function.
        """
        # Build up the set of samples
        # and add configuration

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # If necessary, make a default name
        if outputName == "":
            outputName = "%s.pdf" % hist

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # Configure all plots to be added
        # Do this by collecting the MC and
        # datasamples and setting their
        # histograms to the request HIST
        mc_bsm_samples = self.GetListOfPlots( [self.__mcsamples, self.__bsmsamples], sampleList) 
        for plot in mc_bsm_samples:
            plot["Hist"] = hist
            # Use black lines between stacks
            if plot['Type'] == 'MC':
                plotOptions["LineColor"] = ROOT.kBlack
            plot.update( plotOptions )
        request["Plots"] = mc_bsm_samples 
        

        """
        allMCSamples = itertools.chain(self.__mcsamples.iteritems(), self.__bsmsamples.iteritems())
        for name, sample in allMCSamples:
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot.update( plotOptions )
            plot["Hist"] = hist
            request["Plots"].append( plot )
        """
        # Set the request type
        request["Type"] = "MCStack"
        request["OutputName"] = outputName

        # If cache, wait for later
        # Else, make the histogram now

        if cache:
            self.requestCache.append( request )
        else:
            MakeMCStack( outputName, request );

        return


    def MakeMultipleSamplePlot( self, histName, sampleList, outputName, cache=False, **kwargs ):
        """ Make a plot all histograms in the list simultaneously

        Plot a particular histogram for all samples
        in the sample list simultaneously.
        The given sample and all histograms must exist.
        """

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # Create a default name if necessary
        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        all_plots = self.GetListOfPlots( [self.__datasamples, self.__mcsamples, self.__bsmsamples], 
                                         sampleList) 
        for plot in all_plots:
            plot.update( plotOptions )
            plot["Hist"] = histName
            plot["Signal"] = False # Ignore Signal
            plot["FillColor"] = 0

        request["Plots"] = all_plots
        request["Type"] = "MultipleSamplePlot"
        request["OutputName"] = outputName

        if cache:
            self.requestCache.append( request )
        else:
            MakeMultiplePlot( outputName, request );

        return


    def MakeMultipleVariablePlot( self, histList, sampleName, outputName="", 
                                  nameList=[], colorList=[], cache=False, **kwargs ):
        """ Make a plot all histograms in the list simultaneously

        For a particular sample given by the sampleName,
        collect every hist in the histList,
        and plot them simultaneously on the same plot.
        The given sample and all histograms must exist.
        """

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # Do some sanity checks
        if nameList != [] and len(nameList) != len(histList):
            print "Error: length of histList and nameList don't match"
            raise Exception("nameList histList conflift")

        if colorList != [] and len(colorList) != len(histList):
            print "Error: length of histList and colorList don't match"
            raise Exception("colorList histList conflift")

        # Create a default name if necessary
        if outputName == "":
            outputName = sampleName
            for name in histList:
                outputName +=  "_%s" % name.replace('/','_') 
            outputName += ".pdf"

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # Loop over all requested histograms,
        # configure the plots, and add them to
        # the plot ist
        for itr, hist in enumerate(histList):
            plot = self.GetPlot( sampleName ) #copy.deepcopy( plotTemplate )
            plot.update( plotOptions )
            if nameList != []: 
                plot["Name"] = nameList[itr]
                plot["Title"] = nameList[itr]
            else: plot["Name"]  = hist
            #if UseNameList:
            #    plot["Name"] = nameList[i]
            if colorList != []: plot["Color"] = colorList[itr]
            else: plot["Color"] = self.__defaultcolors[itr] 
            plot["Hist"]  = hist
            plot["Signal"] = False # Ignore Signal
            plot["FillColor"] = 0
            request["Plots"].append( plot )

        request["Type"] = "MultipleVariablePlot"
        request["OutputName"] = outputName

        if cache:
            self.requestCache.append( request )
        else:
            return MakeMultiplePlot( outputName, request );

        return


    def GetTH1( self, hist, sampleName, style=True, **kwargs ):
        """ Return the specified TH1 object

        Using the native HistCollector, get a histogram
        from a sample (summing if necessary) and return
        """
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )
        
        request={}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )

        plot = self.GetPlot( sampleName ) #copy.deepcopy( self.GetPlot( sampleName ) )
        plot.update( plotOptions )
        plot["Hist"] = hist
        th1 = GetAndStyleHist( plot, self.histCache )
        ScaleHist( th1, plot, request )
        return th1


    def MakeMultipleTH1Plot( self, histList, outputName, nameList=[], cache=False, **kwargs ):
        """ Make a plot all histograms in the list simultaneously

        For a particular sample given by the sampleName,
        collect every hist in the histList,
        and plot them simultaneously on the same plot.
        The given sample and all histograms must exist.
        """

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # Some sanity checks
        if nameList != [] and len(nameList) != len(histList):
            print "Error: length of histList and nameList don't match"
            raise Exception("nameList histList conflift")

        # Create a default name if necessary
        if outputName == "":
            outputName = sampleName
            for name in histList:
                outputName +=  "_%s" % name.replace('/','_') 
            outputName += ".pdf"

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        #foundSample = False

        #UseNameList = False
        #if len( nameList ) == len( histList ):
        #    UseNameList = True

        for idx, hist in enumerate(histList):
            plot = {}
            plot.update( plotOptions )
            if nameList != []: 
                plot["Name"] = nameList[idx]
                plot["Title"] = nameList[idx]
            else: plot["Name"]  = hist.GetName()
            plot["Hist"]  = hist
            plot["Signal"] = False
            plot["Color"] = self.__defaultcolors[ idx ]
            plot["FillColor"] = 0
            request["Plots"].append( plot )

        request["Type"] = "MultipleTH1Plot"
        request["OutputName"] = outputName

        if cache:
            self.requestCache.append( request )
        else:
            MakeMultipleTH1Plot( outputName, request );

        return


    def DrawText(self, text, x0=0.4, y0=0.75, x1=0.6, y1=0.9):
        text_obj = ROOT.TPaveText(x0, y0, x1, y1, "NDC")
        text_obj.SetFillColor(0);
        text_obj.SetBorderSize(0)
        text_obj.SetTextSize(0.08);
        text_obj.AddText(text)
        text_obj.Draw();
        return text_obj
    
    def MakeTable( self, histName, sampleName, outputName="", cache=False, **kwargs ):
        """ Make a table from a given histogram for a given sample

        For now we implement it here...
        """

        logging.debug( "MakeTable" )

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        request = {}
        request.update( self.GetConfigurationState() )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # Get the info for this sample
        plotTemplate = self.GetPlot( sampleName ) #None
        plot = copy.deepcopy( plotTemplate )
        plot.update( plotOptions )
        plot["Hist"]  = histName
        plot["FileList"] = [  ]
        request["Plots"].append( plot )

        # Get a list of all plots
        # (We should have only one)
        histList = GetNameHistList( request ) # hist = GetAndStyleHist( plot )
        
        (name, hist) = histList[0]

        # Now, make the table
        output = open( outputName, "w" )

        Nbins = hist.GetNbinsX()
        
        for bin in range(Nbins):
            binLabel = hist.GetXaxis().GetBinLabel( bin+1 )
            binValue = hist.GetBinContent( bin+1 )
            print >>output, "%s & %#.3g \\\\" % (binLabel, binValue)
        
        print "Made Table: " + outputName
        output.close()

        return


    def MakeSingleCutSelectionTable( self, cutName, channelHistList, outputName="", sampleList=[], 
                                     channelNameList=[], DoTotalMC=True, **kwargs ):
        """ Make a selection table for a particular cut 
        
        If you save a histogram where each bin represents a cut and is labeled, 
        the PlotMaker can make tables for you.

        Table Looks Like This:

        +------------+------------+-----------+-----------+--------------------------+
        |            | Channel 1  | Channel2  | Channel3  | Total (Sum of Channels ) |
        +============+============+===========+===========+======+===================+
        | Sample A   |            |           |           |                          |
        +------------+------------+-----------+-----------+--------------------------+
        | Sample B   |            |           |           |                          |
        +------------+------------+-----------+-----------+--------------------------+
        | Total      |            |           |           |                          |
        +------------+------------+-----------+-----------+--------------------------+
        | Data       |            |           |           |                          |
        +------------+------------+-----------+-----------+--------------------------+
        | BSM1       |            |           |           |                          |
        +------------+------------+-----------+-----------+--------------------------+

        Requred is the list of histograms representing the cut flows for each channel.
        Optional is a name for each channel (this will appear in the table).
        One can set the samples used in this table.
        If DoTotalMC is true, a row showing the sum of MC will be included.

        """

        logging.debug( "MakeTable" )

        if( channelNameList == [] ):
            channelNameList=channelHistList
        
        if len(channelNameList) != len(channelHistList):
            print "Error: Channel Name list doesn't match Channel Hist List"
            raise Exception("Channel Name Hist Mismatch")
            return

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        requestBase = {}
        requestBase.update( self.GetConfigurationState() )
        #requestBase["Lumi"] = self.__luminosity
        requestBase["Plots"] = []
        
        # Get the list of MC and Data Samples
        # ChannelHistogramList = {}

        # Dictionaries of [Sample][Channel]
        # for data, mc, and bsm
        # ie dataSampleChannelList[ sampleA ] = { Channel1: val1, Channel2: val2, etc }
        # and hence dataSampleChannelList[ sampleA ][ Channel1 ] = val1
        dataSampleChannelDict = OrderedDict()
        mcSampleChannelDict   = OrderedDict()
        bsmSampleChannelDict  = OrderedDict()

        from helpers.tools import GetBinValue 

        # Gather the necessary information
        for channel in channelHistList:

            # Get the histograms for this channel
            request = copy.deepcopy( requestBase )

            allSamples = itertools.chain(self.__datasamples.iteritems(), self.__mcsamples.iteritems(), self.__bsmsamples.iteritems())
            for name, sample in allSamples:
                if sampleList != []:
                    if name not in sampleList:
                        continue
                    pass
                plot = copy.deepcopy(sample)
                plot.update( plotOptions )
                plot["Hist"] = channel
                request["Plots"].append( plot )

            # Now, get the histograms for this channel
            
            # Get the data hist
            dataHistList = GetDataNameHistList( request, self.histCache )
        
            # Make a list of the MC (NOT BSM)
            mcHistList   = GetMCNameHistList( request,   self.histCache )

            # Make a list of the BSM Hists
            bsmHistList  = GetBSMNameHistList( request,  self.histCache )

            # Check that all histograms match
            CompareHistograms( [ pair[1] for pair in (dataHistList + mcHistList + bsmHistList) ] ) 

            # Get the value for each histogram

            # Pack up the data
            for (sampleName, hist) in dataHistList:
                value = GetBinValue( hist, cutName )
                if sampleName not in dataSampleChannelDict:
                    dataSampleChannelDict[sampleName] = OrderedDict()
                dataSampleChannelDict[sampleName][channel] = value

            mcTotalValue = 0.0
            for (sampleName, hist) in mcHistList:
                value = GetBinValue( hist, cutName )
                if sampleName not in mcSampleChannelDict:
                    mcSampleChannelDict[sampleName] = OrderedDict()
                mcSampleChannelDict[sampleName][channel] = value
                mcTotalValue += value

            # Add the Sum of MC
            if DoTotalMC and len(mcSampleChannelDict)!=0:
                if "Total MC" not in mcSampleChannelDict:
                    mcSampleChannelDict["Total MC"] = OrderedDict()
                mcSampleChannelDict["Total MC"][channel] = mcTotalValue
                pass

            for (sampleName, hist) in bsmHistList:
                value = GetBinValue( hist, cutName )
                if sampleName not in bsmSampleChannelDict:
                    bsmSampleChannelDict[sampleName] = OrderedDict()
                bsmSampleChannelDict[sampleName][channel] = value

        #
        # Now we have the informaiton, make the tabke
        #

        table = []

        # Make the Top Row
        row = []
        row.append("")
        for channel in channelNameList:
            row.append(" %s " % MakeLatexString(channel))
        table.append(row)
        table.append("toprule")

        # Add the MC Rows
        if(len(mcSampleChannelDict)): 
            table.append("toprule")
        for (sampleName, channelValueDict) in mcSampleChannelDict.iteritems():
            if sampleName == "Total MC":
                table.append("toprule")
            mc_row = []
            mc_row.append(" %s " % MakeLatexString(sampleName))
            for channel in channelHistList:
                mc_row.append("%#.3g" % channelValueDict[channel])
            table.append(mc_row)

        # Add the data row(s)
        if(len(dataSampleChannelDict)): 
            table.append("toprule")
        for (sampleName, channelValueDict) in dataSampleChannelDict.iteritems():
            data_row = []
            data_row.append(" %s " % MakeLatexString(sampleName))
            for channel in channelHistList:
                data_row.append(" %d " % channelValueDict[channel])
            table.append(data_row)

        # Add the BSM rows
        if(len(bsmSampleChannelDict)): 
            table.append("toprule")
        for (sampleName, channelValueDict) in bsmSampleChannelDict.iteritems():
            bsm_row = []
            bsm_row.append(" %s " % MakeLatexString(sampleName))
            for channel in channelHistList:
                bsm_row.append("%#.3g" % channelValueDict[channel])
            table.append(bsm_row)

        latex_table = MakeLatexTable(table)
        output = open( outputName, "w" )
        output.write(latex_table)
        output.close()
        print "Wrote Table: ", outputName
        return
   
    '''


        ###
        ###
        ###

        output = open( outputName, "w" )

        # Make the Top Row
        print >>output, "\\begin{tabular}{r", 
        for num in range(len(channelHistList)):
            print >>output, "|c",
            #print >>output, "|p{.06\\linewidth}",
        print >>output, "}"
        print >>output, "\\toprule"
        print >>output, " ", # Blank Insert
        for channel in channelNameList:
            print >>output, ("& %s " % MakeLatexString(channel)),
        print >>output, "\\\\" # End Line

        # Make the MC Rows
        if(len(mcSampleChannelDict)): print >>output, "\\toprule"
        for (sampleName, channelValueDict) in mcSampleChannelDict.iteritems():
            if sampleName == "Total MC":
                print >>output, "\\toprule"
            print >>output, (" %s " % MakeLatexString(sampleName)),
            for channel in channelHistList:
                print >>output, " & %#.3g " % channelValueDict[ channel ],
            print >>output, " \\\\ "

        # Make the Data
        if(len(dataSampleChannelDict)): print >>output, "\\toprule"
        for (sampleName, channelValueDict) in dataSampleChannelDict.iteritems():
            print >>output, (" %s " % MakeLatexString(sampleName)),
            for channel in channelHistList:
                print >>output, " & %d " % channelValueDict[ channel ],
            print >>output, " \\\\ "

        # Make the BSM Rows
        if(len(bsmSampleChannelDict)): print >>output, "\\toprule"
        for (sampleName, channelValueDict) in bsmSampleChannelDict.iteritems():
            print >>output, (" %s " % MakeLatexString(sampleName)),
            for channel in channelHistList:
                print >>output, " & %#.3g " % channelValueDict[ channel ],
            print >>output, " \\\\ "

        print >>output, "\\bottomrule"
        print >>output, "\\end{tabular}"
        
        print "Made Table: " + outputName
        output.close()
            
        pass
'''

    def MakeSingleChannelSelectionTable( self, channelHistName, sampleList=[], cutList=[], 
                                         outputName="", DoTotalMC=True, DoTotalEfficiency=False, 
                                         DoPreviousEfficiency=False, **kwargs ):
        """ Make a selection table for a particular cut 
        
        Table Looks Like This:

        +--------+-----------+-----------+-----------+
        |        | Sample A  | Sample B  | Sample C  |
        +========+===========+===========+===========+
        | Cut 0  |           |           |           |
        +--------+-----------++----------+-----------+
        | Cut 1  |           |           |           |
        +--------+-----------+-----------+-----------+
        | Cut 2  |           |           |           |
        +--------+-----------+-----------+-----------+
        | Cut 3  |           |           |           |
        +--------+-----------+-----------+-----------+

        Need only one histogram per sample: The channel's cut flow
        """

        logging.debug( "MakeTable" )

        if DoTotalEfficiency or DoPreviousEfficiency:
            DoEfficiency=True
        else:
            DoEfficiency=False

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        request = {}
        request.update( self.GetConfigurationState() )
        #request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # Get the list of MC and Data Samples

        allSampleDict = OrderedDict()
        allSampleDict.update( self.__datasamples )
        allSampleDict.update( self.__mcsamples )
        allSampleDict.update( self.__bsmsamples )

        # Create a list of samples to use
        # based on the arguments
        samples_to_use = []
        if sampleList != []:
            for name in sampleList:
                if name not in allSampleDict:
                    print "Unrecognized sample: ", name
                    return
                samples_to_use.append( allSampleDict[name] )
            pass
        else:
            samples_to_use = [sample for (name, sample) in allSampleDict.iteritems()]

        # Create the plot requests for the samples
        for sample in samples_to_use:
            plot = copy.deepcopy(sample)
            plot["Hist"] = channelHistName
            plot.update( plotOptions )
            request["Plots"].append( plot )

        # Now, get the histograms for this channel
        dataHistList = GetDataNameHistList( request, self.histCache )
        mcHistList   = GetMCNameHistList( request,   self.histCache )
        bsmHistList  = GetBSMNameHistList( request,  self.histCache )

        allHists = dataHistList + mcHistList + bsmHistList 

        # Check that all histograms match (are consistent)
        CompareHistograms( [ pair[1] for pair in allHists ] ) 

        # Get the number of samples
        template = allHists[0][1]
        NumCuts = template.GetNbinsX()
        
        # Now, we create a big ovject to hold the table
        # Make the Titles
        table = []

        # Create the title row
        row = []
        row += " " # Upper Left is empty
        for (name, hist) in mcHistList:
            row.append(name)
        if DoTotalMC and len(mcHistList)!=0:
            row.append("Total")
        for (name, hist) in bsmHistList:
            row.append(name)
        for (name, hist) in dataHistList:
            row.append(name)
        table.append(row)
        table.append("toprule")
        # Now, add the data rows
                
        if DoEfficiency:
            initial_value_list = []
            prev_value_list = []

        first_cut = True
        for cut in range(NumCuts):
         
            row = []
   
            cutIndex = cut + 1 # Silly ROOT Histogram conventions
            cutName = template.GetXaxis().GetBinLabel( cutIndex )

            # If we specify a list of cuts, 
            # only include those ones
            if cutList != []:
                if cutName not in cutList:
                    continue
                pass

            row.append(cutName)

            mc_total = 0

            eff_itr=0
            def ApplyEfficiency(content, initial_value_list, prev_value_list, itr):
                string = None
                if first_cut: 
                    initial_value_list.append( content )
                    prev_value_list.append( content )
                    content = 100.0
                    if DoPreviousEfficiency and DoTotalEfficiency:
                        string = "%.3g\\%% (%.3g\\%%)" % (content, content)
                    else:
                        string = "%.3g\\%%" % content
                else:
                    initial_efficiency = content/initial_value_list[itr]*100.0
                    prev_efficiency = content/prev_value_list[itr]*100.0
                    prev_value_list[itr] = content

                    if DoPreviousEfficiency and DoTotalEfficiency:
                        string = "%.3g\\%% (%.3g\\%%) " % (initial_efficiency, prev_efficiency)
                    elif DoTotalEfficiency and not DoPreviousEfficiency:
                        string = "%.3g\\%% " % initial_efficiency
                    elif DoPreviousEfficiency and not DoTotalEfficiency:
                        prev_value_list[itr] = content
                        string = "%.3g\\%% " % prev_efficiency
                    else:
                        print "Bad Table configuration"
                        raise Exception("Bad Table Configuration")
                return string


            for (name, hist) in mcHistList:
                content = hist.GetBinContent(cutIndex)
                mc_total += content
                if DoEfficiency: 
                    string = ApplyEfficiency(content, initial_value_list, prev_value_list, eff_itr)
                    row.append(string)
                    eff_itr += 1
                else:
                    row.append("%#.3g " % content )
            if DoTotalMC  and len(mcHistList)!=0:
                if DoEfficiency:
                    string = ApplyEfficiency(content, initial_value_list, prev_value_list, eff_itr)
                    row.append(string)
                    eff_itr += 1
                else:
                    row.append("%#.3g " % mc_total)
            for (name, hist) in bsmHistList:
                content = hist.GetBinContent(cutIndex)
                if DoEfficiency:
                    string = ApplyEfficiency(content, initial_value_list, prev_value_list, eff_itr)
                    row.append(string)
                    eff_itr += 1
                else:
                    row.append("%#.3g " % content)
            for (name, hist) in dataHistList:
                content = hist.GetBinContent(cutIndex)
                if DoEfficiency:
                    string = ApplyEfficiency(content, initial_value_list, prev_value_list, eff_itr)
                    row.append(string)
                    eff_itr += 1
                else:
                    row.append("%.3g " % content)
                pass

            first_cut = False
            table.append(row)
        

        latex_table = MakeLatexTable(table)
        output = open( outputName, "w" )
        output.write(latex_table)
        output.close()
        print "Wrote Table: ", outputName
        return

    '''

        output = open( outputName, "w" )

        # Make the title
        # Make the Top Row
        print >>output, "\\begin{tabular}{r", 
        for num in range(len(mcHistList)):
            print >>output, "|c",            
        if DoTotalMC and len(mcHistList)!=0:
            print >>output, "|c",
        for num in range(len(bsmHistList) + len(dataHistList)):
            print >>output, "|c",            
        print >>output, "}"
        print >>output, "\\toprule"
        print >>output, " ", # Blank Insert

        # Make the Titles
        for (name, hist) in mcHistList:
            print >>output, ("& %s " % MakeLatexString(name)),
        if DoTotalMC and len(mcHistList)!=0:
            print >>output, "& Total",
        for (name, hist) in bsmHistList:
            print >>output, ("& %s " % MakeLatexString(name)),
        for (name, hist) in dataHistList:
            print >>output, ("& %s " % MakeLatexString(name)),
        print >>output, "\\\\" # End Line
        print >>output, "\\toprule"
        
        if DoEfficiency:
            initial_value_list = []
            prev_value_list = []

        first_cut = True
        for cut in range(NumCuts):
            
            cutIndex = cut + 1 # Silly ROOT Histogram conventions
            cutName = template.GetXaxis().GetBinLabel( cutIndex )

            # If we specify a list of cuts, 
            # only include those ones
            if cutList != []:
                if cutName not in cutList:
                    continue
                pass

            print >>output, " %s " % (cutName),

            mc_total = 0

            eff_itr=0
            def ApplyEfficiency(content, initial_value_list, prev_value_list, itr):
                if first_cut: 
                    initial_value_list.append( content )
                    prev_value_list.append( content )
                    content = 100.0
                else:
                    initial_efficiency = content/initial_value_list[itr]*100.0
                    previous_efficiency = content/previous_value_list[itr]*100.0

                    if DoTotalEfficiency and not DoPreviousEfficiency:
                        string = "& %.3g " % initial_efficiency
                    if DoPreviousEfficiency and not DoTotalEfficiency:
                        previous_value_list[itr] = content
                        string = "& %.3g " % previous_efficiency
                    if DoPreviousEfficiency and DoTotalEfficiency:
                        string = "& %.3g %.3g " % (initial_efficiency, previous_efficiency)                        
                return string


            for (name, hist) in mcHistList:
                content = hist.GetBinContent(cutIndex)
                mc_total += content
                if DoEfficiency: 
                    string = ApplyEfficiency(content, initial_value_list, eff_itr)
                    print >>output, string
                    eff_itr += 1
                else:
                    print >>output, ("& %#.3g " % content ),
            if DoTotalMC  and len(mcHistList)!=0:
                if DoEfficiency:
                    string = ApplyEfficiency(content, initial_value_list, eff_itr)
                    print >>output, string
                    eff_itr += 1
                else:
                    print >>output, ("& %#.3g " % mc_total ),
            for (name, hist) in bsmHistList:
                content = hist.GetBinContent(cutIndex)
                if DoEfficiency:
                    string = ApplyEfficiency(content, initial_value_list, eff_itr)
                    print >>output, string
                    eff_itr += 1
                else:
                    print >>output, ("& %#.3g " % content),
            for (name, hist) in dataHistList:
                content = hist.GetBinContent(cutIndex)
                if DoEfficiency:
                    string = ApplyEfficiency(content, initial_value_list, eff_itr)
                    print >>output, string
                    eff_itr += 1
                else:
                    print >>output, ("& %.3g " % content),
                pass

            print >>output, " \\\\ "
            first_cut = False
            continue

        print >>output, "\\bottomrule"
        print >>output, "\\end{tabular}"
        
        print "Made Table: " + outputName
        output.close()
            
        pass
'''


    #
    # Plot Generator and Caching
    #

    def GeneratePlot( self, request ):
        """ Take a request and pass it to the cooresponding function:

        This is a central function that simply looks at the type
        of plot associated with a request and, based on that, 
        passes the request to the proper function.

        All possible functions must be hard-coded here.
        This makes it easy for the cache to work, since 
        to generate plots from cached requests, one need
        only loop over the cache and pass each request through
        this function.

        """

        plotType   = request["Type"]
        outputName = request["OutputName"]

        if plotType == "":
            print "Error: No Plot type found"
            raise Exception("PlotGenerator - PlotType")

        elif plotType == "SamplePlot":
            MakeMultiplePlot( outputName, request )

        elif plotType == "EfficiencyPlot":
            MakeQuotientPlot( outputName, request )

        elif plotType == "MCDataStack":
            MakeMCDataStack( outputName, request )

        elif plotType == "Stack":
            MakeStack( outputName, request )

        elif plotType == "MCStack":
            MakeMCStack( outputName, request )

        elif plotType == "MultipleSamplePlot":
            MakeMultiplePlot( outputName, request )

        elif plotType == "MultipleVariablePlot":
            MakeMultiplePlot( outputName, request )

        elif plotType == "MultipleTH1Plot":
            MakeMultipleTH1Plot( outputName, request )

        else:
            print "Error: Plot Type %s not known"
            raise Exception("PlotGenerator - PlotType");


    def FillCachedHistograms( self ):
        """ Cache all histograms in the request cache

        This is the real advantage of the cache:
        - Loop through all requests in the request cache
        - Get the names and files of all histograms that will be needed
        - Loop over each file and cache all the necessary histograms

        The idea is that each file needs to only be opened once, which
        saves a lot of time in I/O
        """

        FileHistMap = {}

        for request in self.requestCache:
            for plot in request["Plots"]:
                
                name = plot["Hist"]
                
                # Each plot may draw from multiple files
                # get those using glob:
                if "FileList" not in plot:
                    FileList = glob.glob( plot["Files"] )

                fileList = plot["FileList"]

                for file in fileList:
                    # Create the list 
                    #if it's not already there
                    if file not in FileHistMap:
                        FileHistMap[ file ] = []
                    # Add to the list:
                    FileHistMap[ file ].append( name )
                pass
            pass

        # Now that we have the list, 
        # Let's cache all histograms
        for file, histlist in FileHistMap.iteritems():
            self.histCache.CacheHists( file, histlist )

        print "Successfully cached all histograms"
    

    def ClearHistCache( self ):
        """ Clear the histogram Cache """
        self.histCache.ClearCache()


    def GeneratePlotsInCache( self ) :
        """ Generate all plots that have been cached
        
        This is to be used after all desired plots
        have been constructed and cached, usually
        at the end of a script
        """

        # Cache the Hists, opening
        # each file only once
        self.FillCachedHistograms()

        # Make the Plots
        for request in self.requestCache:
            self.GeneratePlot( request )

        # Clear the request cache
        del self.requestCache[ : ]

