
#
# This is a simple module designed to make it simple to produce nice plots
# out of already-produced histograms.  In particular, it is designed to 
# create plots that compare data with predictions (from Monte-Carlo or otherwise)
#

import ROOT
import glob
import log, logging
import copy
import itertools

from helpers.MakeStack import *
from helpers.MakeMCStack import *
from helpers.MakeMCDataStack import *
from helpers.MakeMultiplePlot import *
from helpers.MakeQuotientPlot import *
from helpers.MakeMultipleTH1Plot import *

from HistCollector import *


# Needs ordered dicts to work 100%
# if they don't exist, samples will be
# presented in a different order
# (but numbers, plots will be correct)
if sys.version_info >= (2, 7):
    from collections import OrderedDict
else:
    OrderedDict = dict

"""

 Initialize the internal variables:
 The class holds a vector of samples which
 it divides into:
  - data
  - mc  (monte carlo)
  - bsm (beyond-the-standard-model like samples)
        #
 The distinction (and naming conventions) is simply
 a matter of plotting


 These are vectors of dictionaries, where
 each dictionary describes a sample
 These are meant to directly interface
 with the PlotGenerator function:


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

 Lists of pairs of: (name, plot)


"""



class PlotMaker( ROOT.TNamed ):

    def __init__( self, name = "PlotMaker", title = "Plot maker object" ):

        #Initialise the base class:
        ROOT.TNamed.__init__( self, name, title )


        # Testing
        ROOT.TH1.AddDirectory(ROOT.kFALSE)


        # Initialize the logger
        FORMAT = "%(levelname)s  %(message)s"
        logging.basicConfig( level=logging.INFO, format=FORMAT )

        self.SetName( name )
        self.SetTitle( title )
        self.logger = log.getLogger( name )
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

        # Ugly solution, hopefully will find better one:
        self.__datasamples  = OrderedDict() #{}
        self.__mcsamples    = OrderedDict() #{}
        self.__bsmsamples   = OrderedDict() #{}

        '''
        if sys.version_info >= (2, 7):
            from collections import OrderedDict
            self.__datasamples  = OrderedDict() #{}
            self.__mcsamples    = OrderedDict() #{}
            self.__bsmsamples   = OrderedDict() #{}
        else:
            self.__datasamples  = {}
            self.__mcsamples    = {}
            self.__bsmsamples   = {}
        '''

        # Default Legend Values
        self.__legendLowX  = 0.75
        self.__legendLowY  = 0.70
        self.__legendHighX = 0.95
        self.__legendHighY = 0.90

        #self.__2DlegendLowX  = 0.62
        #self.__2DlegendLowY  = 0.82
        #self.__2DlegendHighX = 0.85
        #self.__2DlegendHighY = 0.99

        self.__luminosity    = 1.0
        self.__scaleMCByLumi = True
        self.__AtlasLabel    = True
        self.__useLogScale   = False
        self.__doHistRebin   = False
        self.__newBins = None


        self.__outputDir = ""

        # colors for stacks
        #  self.__defaultcolors = [ 2,3,4,5,6,7,8,9 ] # simple choice (high intensity)
        #  self.__defaultcolors = [40,41,46,38,33,30,20,7,8,9,32,25,28] # dark colors

        self.__defaultcolors     = [4,3,2,5,6,40,41,46,38,33,30,20,7,8,9] # bright colors
        self.__defaultlinestyles = [4,3,2,5,6,40,41,46,38,33,30,20,7,8,9] # bright colors

        return

    #
    # Simple configuration methods
    #

    def RebinHistograms( self, bins ):
        self.__doHistRebin = True
        self.__newBins = bins

    def SetLevelInfo( self ) :
        logging.basicConfig( level=logging.INFO )
        #self.logger.setLevel( logging.INFO )    

    def SetLevelDebug( self ) :
        logging.basicConfig( level=logging.DEBUG )
        #self.logger.setLevel( logging.DEBUG )    

    def SetAtlasLabel( self, set ) :
        self.__AtlasLabel = set

    def UseLogScale( self, useLogScale ) :
        self.__useLogScale = useLogScale

    def ScaleMCByLumi( self, doScale=True ):
        # Set to true or false the scaling
        # of all MC by the supplied Lumi
        self.__scaleMCByLumi = doScale

    def SetOutputDir( self, outputDir ) :
        self.__outputDir = outputDir

    
    def GetConfigurationState(self):
        """ Return a dictionary of the config state


        Go through the current properties of this
        class and pack them into a dictionary.
        Return that dictionary.
        """
        ConfigState = {}

        ConfigState["UseLogScale"]   = self.__useLogScale
        ConfigState["ScaleMCByLumi"] = self.__scaleMCByLumi
        ConfigState["OutputDir"]     = self.__outputDir

        ConfigState["LegendBoundaries"] = (self.__legendLowX,  self.__legendLowY, 
                                           self.__legendHighX, self.__legendHighY)

        return ConfigState

    def SetLegendBoundaries( self, lowX, lowY, highX, highY ):
        self.__legendLowX = lowX
        self.__legendLowY = lowY
        self.__legendHighX = highX
        self.__legendHighY = highY
        return

    def SetLuminosity( self, luminosity ):
        self.__luminosity = luminosity
        return

    def SetLumi( self, luminosity ):
        self.SetLuminosity( luminosity)

    def GetDefaultColor( self, usedcolors ) :
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

    def AddDataSample( self, name, files ):
        self.logger.info( "AddDataFile: Adding data file: " + files )

        # Glob the files
        FileList = glob.glob( files )

        # Create the dictionary
        info = { "Name" : name, "Files" : files, "FileList" : FileList, "Type" : "DATA" }

        # Add it to the data list
        self.__datasamples[name] = info
        return


    def AddMCSample( self, name, files, color=None, linestyle=0, signal=None ):
        self.logger.info( "AddMCFile:  Adding Monte Carlo file: " + files + " (" + name + ")" )

        # Pick a random color if none supplied
        if color == None:
            color = self.GetNotUsedColor() # HARD CODED FOR NOW...!
        if linestyle == None:
            linestyle = 1 # HARD CODED FOR NOW...!
        
        # Glob the files
        FileList = glob.glob( files )

        # Check if this sample has already been added:
        #nameList = ( x[0] for x in self.__mcsamples )

        if name in self.__mcsamples:
            sample = self.__mcsamples[name]
            sample["FileList"].extend( FileList )

        # Otherwise, create the sample
        else:
            info = { "Name" : name, "Files" : files, "FileList" : FileList,
                     "Color" : color, "LineStyle" : linestyle, "Signal" : signal, "Type" : "MC" }
            self.__mcsamples[name] = info

        return

    def AddBSMSample( self, name, files, color=None, linestyle=0 ):
        self.logger.info( "AddBSMFile:  Adding BSM Monte Carlo file: " + files + " (" + name + ")" )

        # Pick a random color if none supplied
        if color == None:
            color = self.GetNotUsedColor() # HARD CODED FOR NOW...!
        if linestyle == None:
            linestyle = 1 # HARD CODED FOR NOW...!

        # Glob the files
        FileList = glob.glob( files )

        # Check if this sample has already been added:
        if name in self.__bsmsamples:
            sample = self.__bsmsamples[name]
            sample["FileList"].extend( FileList )

        # Otherwise, create the sample
        else:
            info = { "Name" : name, "Files" : files, "FileList" : FileList,
                     "Color" : color, "LineStyle" : linestyle, "Type" : "BSM" }
            self.__bsmsamples[name] = info

        return

    def PrintAllSamples(self):

        print ""

        print "Data Samples:"
        for name, sample in self.__datasamples.iteritems():
            for (key, val) in sample.iteritems():
                print " %s : %s " % (key, val),
            print ""
            print ""
            pass
        print ""

        print "MC Samples:"
        for name, sample in self.__mcsamples.iteritems():
            for key, val, in sample.iteritems():
                print " %s : %s " % (key, val),
            print ""
            print ""
            pass
        print ""

        print "BSM Samples:"
        for name, sample in self.__bsmsamples.iteritems():
            for key, val in sample:
                print key, val
        print ""


    def PrintRequestCache(self):

        for cache in self.requestCache:
            print cache
            
        return

    def GetNotUsedColor( self ):
        """ Get a color if one isn't already supplied


        Probably unnecesarily complicated...
        """
        usedcolors = []
        for sample in self.__mcsamples.values() + self.__bsmsamples.values():
            usedcolors.append( sample["Color"] )
        
        for color in self.__defaultcolors:
            if color not in usedcolors:
                return color
            pass
        
        # Else, have to throw random numbers
        import random
        for i in range( 100 ):
            color = int( random.random()*100 )
            if color not in usedcolors:
                return color
            pass
        
        return 1

###
###
###



    def GeneratePlot( self, request ):
        """ Take a request and pass it to the approprie function:

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

        elif plotType == "MCDataStack":
            MakeMCDataStack( outputName, request )

        elif plotType == "MCStack":
            MakeMCStack( outputName, request )

        elif plotType == "Stack":
            MakeStack( outputName, request )

        elif plotType == "MultipleVariablePlot":
            MakeMultiplePlot( outputName, request )


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

        # A map of fileName : [ HistA, HistB, ...etc ]

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

        print "Starting to cache histograms"

        for file, histlist in FileHistMap.iteritems():
            self.histCache.CacheHists( file, histlist )

        print "Successfully cached all histograms"
    

    def ClearHistCache( self ):
        self.histCache.ClearCache()


    def GetSample( self, sampleName ) :
        """ Find a stored sample and return a deepcopy

        """
        plotTemplate = None

        if sampleName in self.__mcsamples:
            plotTemplate = copy.deepcopy( self.__mcsamples[ sampleName ] )

        elif sampleName in self.__bsmsamples:
            plotTemplate = copy.deepcopy( self.__bsmsamples[ sampleName ] )

        elif sampleName in self.__datasamples:
            plotTemplate = copy.deepcopy( self.__datasamples[ sampleName ] )

        else:
            print "Error: Sample %s not found in either MC or data" % sampleName
            raise Exception("GetSample - Sample")
        
        return plotTemplate


    def GeneratePlotsInCache( self ) :

        # Cache the Hists, opening
        # each file only once
        self.FillCachedHistograms()


        # Make the Plots
        for request in self.requestCache:
            self.GeneratePlot( request )

        # Clear the request cache
        del self.requestCache[ : ]



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
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        #request["SuppressLegend"] = True
        #request["Title"] = histName

        foundSample = False

        plotTemplate = self.GetSample( sampleName ) #None

        plot = copy.deepcopy( plotTemplate )
        plot.update( plotOptions )
        plot["Hist"]  = histName
        request["Plots"].append( plot )
        request["Type"] = "SamplePlot"
        request["OutputName"] = outputName


        if cache:
            self.requestCache.append( request )
        else:
            MakeMultiplePlot( outputName, request );

        return


    def MakeEfficiencyPlot( self, numerator, denominator, sampleName, outputName="", cache=False, **kwargs):
        """ Make a plot of the quotient of two histograms

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
        request["Lumi"] = self.__luminosity
        if "Maximum" not in request:
            request["Maximum"] = 1.2 # Efficiency Maximum
        request["Plots"] = []

        #request["SuppressLegend"] = True
        #request["Title"] = histName

        foundSample = False

        plotTemplate = self.GetSample( sampleName ) #None
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




    def MakeMCDataStack(self, hist, outputName="", sampleList=[], cache=False, **kwargs):
        """ Make a plot of data and a stack of MC 

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

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []
        
        # Configure all plots to be added
        # Do this by collecting the MC and
        # datasamples and setting their
        # histograms to the request HIST
        for name, sample in self.__datasamples.iteritems():
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            request["Plots"].append( plot )

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
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # If the input sampleList is empty,
        # we interpret that to mean that we use
        # all available samples


        # Configure all plots to be added
        # Do this by collecting the MC and
        # datasamples and setting their
        # histograms to the request HIST
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


        '''
        for name, sample in self.__datasamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot.update( plotOptions )
            plot["Hist"] = hist
            request["Plots"].append( plot )

        for name, sample in self.__mcsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            request["Plots"].append( plot )


        for name, sample in self.__bsmsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            request["Plots"].append( plot )
        '''

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


        # IF necessary, make a default name
        if outputName == "":
            outputName = "%s.pdf" % hist

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # Configure all plots to be added
        # Do this by collecting the MC and
        # datasamples and setting their
        # histograms to the request HIST
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

        '''
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
            plot["Hist"] = hist
            request["Plots"].append( plot )
        '''

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



    '''
    def MakeMultipleMCDataStackself, histList, outputName ):
        
        
        # CAN NOTE BE USED WITH CACHE
        canvas = TCanvas("MultipleCanvas" "")
        canvas.Print( outputName + "[" )
        
        for hist in histList:
            MakeMCDataStack( hist, outputName, False )

        canvas.Print( outputName + "]" )

        pass
    '''

    def MakeMultipleSamplePlot( self, hist, sampleList, outputName, cache=False, **kwargs ):
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
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        allSamples = itertools.chain(self.__datasamples.iteritems(), self.__mcsamples.iteritems(), self.__bsmsamples.iteritems())
        for name, sample in allSamples:
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot.update( plotOptions )
            plot["Hist"] = hist
            plot["Signal"] = False # Ignore Signal
            plot["FillColor"] = 0
            request["Plots"].append( plot )

        request["Type"] = "MultipleSamplePlot"
        request["OutputName"] = outputName

        if cache:
            self.requestCache.append( request )
        else:
            MakeMultiplePlot( outputName, request );

        return



    def MakeMultipleVariablePlot( self, histList, sampleName, outputName="", nameList=[], cache=False, **kwargs ):
        """ Make a plot all histograms in the list simultaneously

        For a particular sample given by the sampleName,
        collect every hist in the histList,
        and plot them simultaneously on the same plot.
        The given sample and all histograms must exist.
        """

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )


        # Create a default name if necessary
        if outputName == "":
            outputName = sampleName
            for name in histList:
                outputName +=  "_%s" % name.replace('/','_') 
            outputName += ".pdf"

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        foundSample = False
        plotTemplate = self.GetSample( sampleName ) #None

        '''
        if sampleName in self.__mcsamples:
            plotTemplate = copy.deepcopy( self.__mcsamples[ sampleName ] )
        elif sampleName in self.__datasamples:
            plotTemplate = copy.deepcopy( self.__datasamples[ sampleName ] )
        else:
            print "Error: Sample %s not found in either MC or data" % sampleName
            raise Exception("MakeMultipleVariablePlot - Sample")
        '''

        UseNameList = False
        if len( nameList ) == len( histList ):
            UseNameList = True

        histItr = 0
        for hist in histList:
            plot = copy.deepcopy( plotTemplate )
            plot.update( plotOptions )
            if UseNameList:
                plot["Name"] = nameList[histItr]
            else:
                plot["Name"]  = hist
            plot["Hist"]  = hist
            plot["Signal"] = False # Ignore Signal
            plot["Color"] = self.__defaultcolors[ histItr ]
            plot["FillColor"] = 0

            request["Plots"].append( plot )
            histItr += 1
        
            
        '''
        # Check if the requested sampe is in MC
        if sampleName in self.__mcsamples + self.__datasamples:
            foundSample = True
            # If so, build the list of plots:
            histItr = 0
            for hist in histList:
                plot = copy.deepcopy(self.__mcsamples[ sampleName ])
                plot["Name"]  = hist
                plot["Hist"]  = hist
                plot["Signal"] = False # Ignore Signal
                plot["Color"] = self.__defaultcolors[ histItr ]
                print plot, hist, self.__defaultcolors[ histItr ]
                request["Plots"].append( plot )
                print request["Plots"]
                print ""
                histItr += 1
            pass

        # Check if the requested sampe is in MC
        if sampleName in self.__datasamples:
            foundSample = True            
            # If so, build the list of plots:
            histItr = 0
            for hist in histList:
                plot = copy.deepcopy(self.__datasamples[ sampleName ])
                plot["Hist"] = hist
                plot["Color"] = self.__defaultcolors[ histItr ]
                print plot
                request["Plots"].append( plot )
                histItr += 1
            pass

        '''

        request["Type"] = "MultipleVariablePlot"
        request["OutputName"] = outputName

        if cache:
            self.requestCache.append( request )
        else:
            MakeMultiplePlot( outputName, request );

        return


    def GetTH1( self, hist, sampleName, **kwargs ):
        
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )
        
        plot = copy.deepcopy( self.GetSample( sampleName ) )
        plot.update( plotOptions )
        plot["Hist"] = hist
        return GetHist( plot, self.histCache )


    def MakeMultipleTH1Plot( self, histList, outputName, nameList=[], cache=False, **kwargs ):
        """ Make a plot all histograms in the list simultaneously

        For a particular sample given by the sampleName,
        collect every hist in the histList,
        and plot them simultaneously on the same plot.
        The given sample and all histograms must exist.
        """

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )

        # Create a default name if necessary
        if outputName == "":
            outputName = sampleName
            for name in histList:
                outputName +=  "_%s" % name.replace('/','_') 
            outputName += ".pdf"

        request = {}
        request.update( self.GetConfigurationState() )
        request.update( requestOptions )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        foundSample = False

        UseNameList = False
        if len( nameList ) == len( histList ):
            UseNameList = True


        for idx, hist in enumerate(histList):
            plot = {}
            plot.update( plotOptions )
            if UseNameList:
                plot["Name"] = nameList[idx]
            else:
                plot["Name"]  = hist.GetName()
            plot["Hist"]  = hist
            plot["Signal"] = False # Ignore Signal
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



    def MakeTable( self, histName, sampleName, outputName="", cache=False, **kwargs ):
        """ Make a table from a given histogram for a given sample

        For now we implement it here...
        """

        logging.debug( "MakeTable" )

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )


        request = {}
        request.update( self.GetConfigurationState() )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # Get the info for this sample
        plotTemplate = self.GetSample( sampleName ) #None
        plot = copy.deepcopy( plotTemplate )
        plot.update( plotOptions )
        plot["Hist"]  = histName
        plot["FileList"] = [  ]
        request["Plots"].append( plot )

        print "Plot request: ", request

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


    def MakeSingleCutSelectionTable( self, cutName, channelHistList, outputName="", sampleList=[], channelNameList=[], DoTotalMC=True, **kwargs ):
        """ Make a selection table for a particular cut 
        
        Table Looks Like This:

                    Channel1  Channel2  Channel3 |  Total (Sum of channels)
                  _________________________________________________________
        Sample A |
        Sample B |
        Sample C |
        -------- |
        Total    |
        -------- |
        Data     |
        ---------|
        BSM A    |
        BSM B    |

        Need to get Histograms: Channel1, Channel2, Channel3 from {Samples}

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
        requestBase["Lumi"] = self.__luminosity
        requestBase["Plots"] = []
        
        # Get the list of MC and Data Samples

        ChannelHistogramList = {}


        # Dictionaries of [Sample][Channel]
        # for data, mc, and bsm
        # ie dataSampleChannelList[ sampleA ] = { Channel1: val1, Channel2: val2, etc }
        # and hence dataSampleChannelList[ sampleA ][ Channel1 ] = val1

        #from collections import OrderedDict

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


            '''
            for name, sample in self.__datasamples.iteritems():
                plot = copy.deepcopy(sample)
                plot.update( plotOptions )
                plot["Hist"] = channel
                request["Plots"].append( plot )

            for name, sample in self.__mcsamples.iteritems():
                if sampleList != []:
                    if name not in sampleList:
                        continue
                    pass
                plot = copy.deepcopy(sample)
                plot.update( plotOptions )
                plot["Hist"] = channel
                request["Plots"].append( plot )

            for name, sample in self.__bsmsamples.iteritems():
                if sampleList != []:
                    if name not in sampleList:
                        continue
                    pass
                plot = copy.deepcopy(sample)
                plot.update( plotOptions )
                plot["Hist"] = channel
                request["Plots"].append( plot )
            '''
            # Now, get the histograms for this channel
            
            # Get the data hist
            dataHistList = GetDataNameHistList( request, self.histCache )
        
            # Make a list of the MC (NOT BSM)
            mcHistList   = GetMCNameHistList( request, self.histCache )

            # Make a list of the BSM Hists
            bsmHistList  = GetBSMNameHistList( request, self.histCache )

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
            if DoTotalMC:
                if "Total MC" not in mcSampleChannelDict:
                    mcSampleChannelDict["Total MC"] = OrderedDict()
                mcSampleChannelDict["Total MC"][channel] = mcTotalValue
                pass

            for (sampleName, hist) in bsmHistList:
                value = GetBinValue( hist, cutName )
                if sampleName not in bsmSampleChannelDict:
                    bsmSampleChannelDict[sampleName] = OrderedDict()
                bsmSampleChannelDict[sampleName][channel] = value

            # Get a list of ( name, binValue) for data, mc, and bsm
            #dataValueList = [ ( name, GetBinValue(hist) ) for (name, hist) in dataHistList ]
            #mcValueList   = [ ( name, GetBinValue(hist) ) for (name, hist) in mcHistList ]
            #bsmValueList  = [ ( name, GetBinValue(hist) ) for (name, hist) in bsmHistList ]


            # Pack it into the Giant object
            #ChannelHistogramList[ channel ] = ( dataValueList, mcValueList, bsmValueList )

            # Okay, we're done.  Move on to the next channel
            
        #
        # Now we have the informaiton, make the tabke
        #

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
                print >>output, " & %d " % channelValueDict[ channel ],
            print >>output, " \\\\ "



        print >>output, "\\bottomrule"
        print >>output, "\\end{tabular}"

        
        print "Made Table: " + outputName
        output.close()
            
        pass




    def MakeSingleChannelSelectionTable( self, channelHistName, sampleList=[], cutList=[], outputName="", **kwargs ):
        """ Make a selection table for a particular cut 
        
        Table Looks Like This:

                SampleA  SampleB  SampleC  SampleD
              _____________________________________
        Cut0 |
        Cut1 |
        Cut2 |
        Cut3 |
        

        Need only one histogram per sample: The channel's cut flow

        """

        logging.debug( "MakeTable" )

        # Parse the optional arguments
        ( requestOptions, plotOptions ) = ParseOptionalArgs( kwargs )


        request = {}
        request.update( self.GetConfigurationState() )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []
        
        # Get the list of MC and Data Samples

        allSamples = itertools.chain(self.__datasamples.iteritems(), self.__mcsamples.iteritems(), self.__bsmsamples.iteritems())
        for name, sample in allSamples:
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = channelHistName
            plot.update( plotOptions )
            request["Plots"].append( plot )


        '''
        for name, sample in self.__datasamples.iteritems():
            plot = copy.deepcopy(sample)
            plot["Hist"] = channelHistName
            plot.update( plotOptions )
            request["Plots"].append( plot )
            
        for name, sample in self.__mcsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = channelHistName
            plot.update( plotOptions )
            request["Plots"].append( plot )

        for name, sample in self.__bsmsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = channelHistName
            plot.update( plotOptions )
            request["Plots"].append( plot )
        '''

        # Now, get the histograms for this channel
            
        # Get the data hist
        dataHistList = GetDataNameHistList( request, self.histCache )
        
        # Make a list of the MC (NOT BSM)
        mcHistList   = GetMCNameHistList( request,   self.histCache )

        # Make a list of the BSM Hists
        bsmHistList  = GetBSMNameHistList( request,  self.histCache )

        allHists = dataHistList + mcHistList + bsmHistList 

        # Check that all histograms match
        #CompareHistograms( [ pair[1] for pair in (dataHistList + mcHistList + bsmHistList) ] ) 
        CompareHistograms( [ pair[1] for pair in allHists ] ) 


        # Get the number of samples
        #template = dataHistList[0][1]
        template = allHists[0][1]

        NumCuts = template.GetNbinsX()

        output = open( outputName, "w" )

        # Make the title
        # Make the Top Row
        print >>output, "\\begin{tabular}{r", 
        for num in range(len(mcHistList) + len(bsmHistList) + len(dataHistList)):
            print >>output, "|c",            
            #print >>output, "|p{.06\\linewidth}",
        print >>output, "}"
        print >>output, "\\toprule"
        print >>output, " ", # Blank Insert
        for (name, hist) in mcHistList:
            print >>output, ("& %s " % MakeLatexString(name)),
        for (name, hist) in bsmHistList:
            print >>output, ("& %s " % MakeLatexString(name)),
        for (name, hist) in dataHistList:
            print >>output, ("& %s " % MakeLatexString(name)),
        print >>output, "\\\\" # End Line
        print >>output, "\\toprule"

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

            for (name, hist) in mcHistList:
                print >>output, ("& %#.3g " % hist.GetBinContent(cutIndex)),
            for (name, hist) in bsmHistList:
                print >>output, ("& %#.3g " % hist.GetBinContent(cutIndex)),
            for (name, hist) in dataHistList:
                print >>output, ("& %.3g " % hist.GetBinContent(cutIndex)),
            

            print >>output, " \\\\ "

        print >>output, "\\bottomrule"
        print >>output, "\\end{tabular}"
        
        print "Made Table: " + outputName
        output.close()
            
        pass


    '''

    def MakeCutFlowTable( self, cutName, channelHistList=[], sampleList=[], outputName="", cache=False ):
        """ Make a table from a given histogram for a given sample

        For now we implement it here...
        """

        logging.debug( "MakeTable" )

        request = {}
        request.update( self.GetConfigurationState() )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []


        for histogram in channelHistList:
            pass

        # Build the Request
        for name, sample in self.__datasamples.iteritems():
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            request["Plots"].append( plot )

        for name, sample in self.__mcsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            plot.update( plotOptions )
            request["Plots"].append( plot )

        for name, sample in self.__bsmsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            request["Plots"].append( plot )

        print "Plot request: ", request

        #
        # Get the histograms:
        #

        # Get the data hist
        dataHistList = GetDataNameHistList( request, histCache )
        
        # Make a list of the MC (NOT BSM)
        mcHistList   = GetMCNameHistList( request, histCache )

        # Make a list of the BSM Hists
        bsmHistList  = GetBSMNameHistList( request, histCache )

        # Check that all histograms match
        CompareHistograms( [ pair[1] for pair in (dataHistList + mcHistList + bsmHistList) ] ) 


        # Now, make the table
        
        output = open( outputName, "w" )

        template = dataHistList[0][1]
        
        Nbins = template.GetNbinsX()
        
        


        for name, hist in mcHistList:
            binLabel = hist.GetXaxis().GetBinLabel( bin+1 )
            binValue = hist.GetBinContent( bin+1 )
            print >>output, "%s & %.3f \\\\" % (binLabel, binValue)

            
        for bin in range(Nbins):
            binLabel = hist.GetXaxis().GetBinLabel( bin+1 )
            binValue = hist.GetBinContent( bin+1 )
            print >>output, "%s & %.3f \\\\" % (binLabel, binValue)
        
        
        output.close()


        return

    '''

    '''

    def MakeMultipleTable( self, hist, sampleList=[], outputName="", name="", cache=False ):
        # STILL A WORK IN PROGRESS...
        """ Make a table from a given histogram for a given sample

        For now we implement it here...
        """

        logging.debug( "MakeTable" )

        request = {}
        request.update( self.GetConfigurationState() )
        request["Lumi"] = self.__luminosity
        request["Plots"] = []

        # Build the Request
        for name, sample in self.__datasamples.iteritems():
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            request["Plots"].append( plot )

        for name, sample in self.__mcsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            plot.update( plotOptions )
            request["Plots"].append( plot )

        for name, sample in self.__bsmsamples.iteritems():
            if sampleList != []:
                if name not in sampleList:
                    continue
                pass
            plot = copy.deepcopy(sample)
            plot["Hist"] = hist
            request["Plots"].append( plot )

        print "Plot request: ", request

        #
        # Get the histograms:
        #

        # Get the data hist
        dataHistList = GetDataNameHistList( request, histCache )
        
        # Make a list of the MC (NOT BSM)
        mcHistList   = GetMCNameHistList( request, histCache )

        # Make a list of the BSM Hists
        bsmHistList  = GetBSMNameHistList( request, histCache )

        # Check that all histograms match
        CompareHistograms( [ pair[1] for pair in (dataHistList + mcHistList + bsmHistList) ] ) 


        # Now, make the table
        
        output = open( outputName, "w" )

        template = dataHistList[0][1]
        
        Nbins = template.GetNbinsX()
        
        


        for name, hist in mcHistList:
            binLabel = hist.GetXaxis().GetBinLabel( bin+1 )
            binValue = hist.GetBinContent( bin+1 )
            print >>output, "%s & %.3f \\\\" % (binLabel, binValue)

            
        for bin in range(Nbins):
            binLabel = hist.GetXaxis().GetBinLabel( bin+1 )
            binValue = hist.GetBinContent( bin+1 )
            print >>output, "%s & %.3f \\\\" % (binLabel, binValue)
        
        
        output.close()


        return

    '''
