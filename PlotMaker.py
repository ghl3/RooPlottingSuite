
#
# This is a simple module designed to make it simple to produce nice plots
# out of already-produced histograms.  In particular, it is designed to 
# create plots that compare data with predictions (from Monte-Carlo or otherwise)
#

import ROOT
import glob
import log, logging

class PlotMaker( ROOT.TNamed ):

    def __init__( self, name = "PlotMaker", title = "Plot maker object" ):

        # Initialise the base class:
        ROOT.TNamed.__init__( self, name, title )
        self.SetName( name )
        self.SetTitle( title )
        self.logger = log.getLogger( name )
        self.logger.setLevel( logging.INFO )

        # Initialize the internal variables:
        self.__datafiles = []
        self.__mcsamples = {}
        self.__bsmsamples = {}
        self.__colors = {}
        self.__linestyles = {}


        self.__legendLowX = 0.65
        self.__legendLowY = 0.5
        self.__legendHighX = 0.9
        self.__legendHighY = 0.9

        self.__2DlegendLowX = 0.62
        self.__2DlegendLowY = 0.82
        self.__2DlegendHighX = 0.85
        self.__2DlegendHighY = 0.99

        self.__luminosity = 1.0
        self.__scaleMCByLumi = False
        self.__AtlasLabel = True
        self.__useLogScale = False

        # colors for stacks
        #  self.__defaultcolors = [ 2,3,4,5,6,7,8,9 ] # simple choice (high intensity)
        #  self.__defaultcolors = [40,41,46,38,33,30,20,7,8,9,32,25,28] # dark colors
        self.__defaultcolors = [4,3,2,5,6,40,41,46,38,33,30,20,7,8,9] # bright colors
        return


#    def SetLoggerLevel( self, level ) :
#        self.__logger.setLevel( level )


    def SetLevelInfo( self ) :
        self.logger.setLevel( logging.INFO )    

    def SetLevelDebug( self ) :
        self.logger.setLevel( logging.DEBUG )    

    def SetAtlasLabel( self, set ) :
        self.__AtlasLabel = set

    def UseLogScale( self, useLogScale ) :
        self.__useLogScale = useLogScale

    def ScaleMCByLumi( self, doScale=True ):
        # Set to true or false the scaling
        # of all MC by the supplied Lumi
        self.__scaleMCByLumi = doScale

    def AddDataFile( self, filename ):
        self.logger.info( "AddDataFile: Adding data file: " + filename )
        self.__datafiles += [ filename ]
        return

    def AddMCFile( self, mctype, filename, color=None, linestyle=0 ):
        self.logger.info( "AddMCFile:  Adding Monte Carlo file: " + filename + " (" + mctype + ")" )
        if color != None:
            self.__colors[ mctype ] = color
        if linestyle != None:
            self.__linestyles[ mctype ] = linestyle
        if mctype in self.__mcsamples.keys():
            self.__mcsamples[ mctype ] += [ filename ]
        else:
            self.__mcsamples[ mctype ]  = [ filename ]
            pass
        return

    def AddBSMFile( self, bsmtype, filename, weight=1.0, color=None, linestyle=None ):
        self.logger.info( "AddBSMFile:  Adding BSM file: " + filename + " (" + bsmtype + "," + str( weight ) + ")" )
        if color != None:
            self.__colors[ bsmtype ] = color
        if linestyle != None:
            self.__linestyles[ bsmtype ] = linestyle
        if bsmtype in self.__bsmsamples.keys():
            self.__bsmsamples[ bsmtype ] += [ [ filename, weight ] ]
        else:
            self.__bsmsamples[ bsmtype ]  = [ [ filename, weight ] ]
            pass
        return

    
    def AddMultipleMCFiles( self, mctype, fileExpression, color=None ):
        
        # Take a RegEx and use glob to
        # add multiple files at once
        
        FileList = glob.glob( fileExpression )
        
        if len( FileList ) == 0 :
            self.logger.warning( "No files added from: %s" % fileExpression )
            return
            
        for file in FileList:
            self.AddMCFile( mctype, file, color )
                
    def AddMultipleDataFiles( self, fileExpression ):
        
        # Take a RegEx and use glob to
        # add multiple files at once
                    
        FileList = glob.glob( fileExpression )
        
        if len( FileList ) == 0 :
            self.logger.warning("No files added from: %s " % fileExpression)
            return

        for file in FileList:
            self.AddDataFile( file )

    def SetLegendSize( self, lowX, lowY, highX, highY ):
        self.__legendLowX = lowX
        self.__legendLowY = lowY
        self.__legendHighX = highX
        self.__legendHighY = highY
        return

    def SetLuminosity( self, luminosity ):
        self.__luminosity = luminosity
        return

    def GetDefaultColor( self, usedcolors ) :
        for color in self.__defaultcolors:
            if color not in usedcolors:
                usedcolors.append( color )
                return color
            
        # If all the colors are used, 
        # Reset and start again:
        del usedcolors[ : ]
        return GetDefaultColor( usedcolors )

    def GetDataHist( self, hname ):

        # Return a list of data hists
        
        result = None
        for dfile in self.__datafiles:
            tfile = ROOT.TFile.Open( dfile, "READ" )
            if not file:
                raise IOError( 1, "File '" + dfile + "' could not be opened" )
            dhist = tfile.Get( hname )
            if not dhist:
                raise IOError( 5, "Histogram '" + hname + "' not found in file '" + dfile + "'" )
            if not result:
                ROOT.gROOT.cd()
                result = dhist.Clone( hname + "_data" )
            else:
                result.Add( dhist )
                pass
            tfile.Close()
            pass
        return result

    def GetMCHists( self, hname ):

        # Return a dictionary of { name : hist }

        result = {}
        #color = 1
        for mctype, mcfiles in self.__mcsamples.iteritems():
            #mcfiles = self.__mcsamples[ mctype ]
            typeHist = None
            for mcfile in mcfiles:
                tfile = ROOT.TFile.Open( mcfile, "READ" )
                if not tfile:
                    raise IOError( 1, "File '" + mcfile + "' could not be opened" )
                mchist = tfile.Get( hname )
                if not mchist:
                    raise IOError( 5, "Histogram '" + hname + "' not found in file '" + mcfile + "'" )
                if not typeHist:
                    ROOT.gROOT.cd()
                    typeHist = mchist.Clone( hname + "_" + mctype )
                else:
                    typeHist.Add( mchist )
                    pass
                tfile.Close()
                pass
            #typeHist.SetFillStyle( 1001 )
            #typeHist.SetFillColor( color )
            #color += 1
            result[ mctype ] = typeHist
            pass
        return result

    def GetBSMHists( self, hname ):
        result = {}
        lstyle = 1
        for bsmtype, files in self.__bsmsamples.iteritems():
            #files = self.__bsmsamples[ bsmtype ]
            typeHist = None
            for bsmfile in files:
                tfile = ROOT.TFile.Open( bsmfile[ 0 ], "READ" )
                if not tfile:
                    raise IOError( 1, "File '" + bsmfile[ 0 ] + "' could not be opened" )
                hist = tfile.Get( hname )
                if not hist:
                    raise IOError( 5, "Histogram '" + hname + "' not found in file '" + bsmfile[ 0 ] + "'" )
                # Rescale the histogram with the specified weight:
                hist.Scale( bsmfile[ 1 ] )
                if not typeHist:
                    ROOT.gROOT.cd()
                    typeHist = hist.Clone( hname + "_" + bsmtype )
                else:
                    typeHist.Add( hist )
                    pass
                tfile.Close()
                pass
            #typeHist.SetFillStyle( 0 )
            #typeHist.SetLineStyle( lstyle )
            #typeHist.SetLineColor( lstyle )
            #lstyle += 1
            #if lstyle == 9:
            #    lstyle = 2
            result[ bsmtype ] = typeHist
            pass
        return result


######################
# plot 1D histograms #
######################

    def PlotHistogram( self, hname, filename ):

        # Create a canvas:
        canvas = ROOT.TCanvas( hname + "_canvas", "Canvas for plot making", 800, 600 )
        canvas.cd()

        dhist    = self.GetDataHist( hname )
        mchists  = self.GetMCHists( hname )
        bsmhists = self.GetBSMHists( hname )

        (stack, legend) = self.__DrawHistogram( hname, dhist, mchists, bsmhists )

        if self.__useLogScale:
            canvas.SetLogy()

        canvas.SaveAs( filename )
        return

    def PlotMultipleHistograms( self, hnameList, filename ):

        if len(hnameList) == 0:
            self.logger.error( "No Histograms supplied" )
            return

        # Create a canvas:
        canvas = ROOT.TCanvas(  "canvas", "Canvas for plot making", 800, 600 )
        canvas.cd()

        canvas
        canvas.Print(filename + "[");

        for hname in hnameList:

            dhist    = self.GetDataHist( hname )
            mchists  = self.GetMCHists( hname )
            bsmhists = self.GetBSMHists( hname )

            (stack, legend) = self.__DrawHistogram( hname, dhist, mchists, bsmhists )

            if self.__useLogScale:
                canvas.SetLogy()
                canvas.Print( filename )

            pass

        canvas.Print(filename + "]");

        return
        

    def PlotProbabilityHistogram( self, hname, filename ):

        # Create a canvas:
        canvas = ROOT.TCanvas( hname + "_canvas", "", 800, 1000 )
        canvas.Divide(1,2, 0.01, 0.01)

        canvas.cd(1).SetLogy()
        
        dhist = self.GetDataHist( hname )
        mchists = self.GetMCHists( hname )
        bsmhists = self.GetBSMHists( hname )

        (stack, legend) = self.__DrawHistogram( hname, dhist, mchists, bsmhists )

        canvas.cd(2).SetLogy()

        (legend ) = self.__DrawProbabilityPlot( hname, bsmhists )

        canvas.SaveAs( filename )
        return


######################
# internal functions #
######################
        


    def __DrawHistogram( self, hname, dhist, mchists, bsmhists ):
        # Retrieve the data and MC histograms:

        # Create the histogram representing the sum of all MC samples
        # Seems like a strange loop, but okay:
        addedSamples = None
        for mctype, h1d in mchists.iteritems():
            # make projections and add them
            #h1d = mchists[ mctype ]
            if( self.__scaleMCByLumi):
                h1d.Scale( self.__luminosity )
            if addedSamples:
                addedSamples.Add ( h1d )
            else:
                addedSamples = h1d.Clone()
            pass

        maximum = max( [ addedSamples.GetMaximum(), dhist.GetMaximum() ] + \
                       [ bsmhists[ bsmtype ].GetMaximum() for bsmtype in bsmhists.keys() ] )
        maximum *= 1.4

        # Create a canvas:
        #canvas = ROOT.TCanvas( hname + "_canvas", "Canvas for plot making",
        #                       800, 600 )
        #canvas.cd()
        # Plot the data first:
        dhist.SetMaximum( maximum )
        dhist.Draw()

        # Create a stack of the MC histograms:
        stack = ROOT.THStack( hname + "_mcstack", "Stacked MC histograms" )
        # Every element should be a list of the form [histo, "name", "style"]

        # Now draw the MC histograms one by one:
        legendEntries = []
        usedcolors = []
        #color = 2
        for mctype, mchist in mchists.iteritems():
            #mchist = mchists[ mctype ]
            if mctype in self.__colors:
                color = self.__colors[ mctype ]
            else:
                color = self.GetDefaultColor( usedcolors )
            mchist.SetFillColor(color)
            mchist.SetLineColor(color)
            stack.Add( mchist )
            stack.Draw( "HIST SAME" )
            legendEntries.append( [mchist, mctype, "f"] )
            self.logger.debug( "Adding mc histogram to stack: %s (color = %d )" % (mctype, color) )
            pass

        # Draw the data points again:
        dhist.Draw( "SAME" )

        # Create a legend for the plot:
        legend = ROOT.TLegend( self.__legendLowX, self.__legendLowY,
                               self.__legendHighX, self.__legendHighY )
        legend.AppendPad()
        legend.SetFillStyle( 0 )

        legend.AddEntry( dhist, "data", "lpe" )
        # show the stacked histograms in the same order
        legendEntries.reverse()
        for e in legendEntries: legend.AddEntry( e[0], e[1], e[2] )

        # Draw the BSM histograms one-by-one and draw the legend:
        for bsmtype, bsmhist in bsmhists.iteritems():
            #bsmhist = bsmhists[ bsmtype ]
            if( self.__scaleMCByLumi):
                bsmhist.Scale( self.__luminosity )
            if bsmtype in self.__colors:
                color = self.__colors[ bsmtype ]
            else:
                color = self.GetDefaultColor( usedcolors )
            bsmhist.SetLineColor( color )
            if bsmtype in self.__linestyles:
                lstyle = self.__linestyles[ bsmtype ]
                bsmhist.SetLineStyle( lstyle )
            self.logger.debug( "Adding bsm histogram to stack: %s (color = %d, lstyle = %d )" % (bsmtype, color, lstyle) )
            bsmhist.Draw( "HIST SAME" )
            legend.AddEntry( bsmhist, bsmtype, "l" )
            pass
        legend.Draw()

        # Add the ATLAS notations:
        if self.__AtlasLabel:
            import AtlasUtil
            AtlasUtil.AtlasLabel( 0.20, 0.85 )
            AtlasUtil.DrawLuminosity( 0.20, 0.76, self.__luminosity )

        # Now create the plot:
        #canvas.SaveAs( filename )
        return (stack, legend)


    
    def __DrawProbabilityPlot( self, hTitle, bsmhists ):

        legend2 = ROOT.TLegend( self.__legendLowX, self.__legendLowY,
                                self.__legendHighX, self.__legendHighY )
        legend2.AppendPad()
        legend2.SetFillStyle( 0 )
        
        maxim = -1
            # Draw the BSM histograms one-by-one:
        for bsmtype, h1d in bsmhists.iteritems():
            h1d = bsmhists[ bsmtype ]
            if h1d.GetEntries() < 1:
                continue
            if bsmtype in self.__colors:
                color = self.__colors[ bsmtype ]
            else:
                color = self.GetDefaultColor( usedcolors )
            h1d.SetLineColor( color )
            if bsmtype in self.__linestyles:
                lstyle = self.__linestyles[ bsmtype ]
                h1d.SetLineStyle( lstyle )
            if hTitle!="":
                h1d.SetTitle(hTitle)
            h1d.GetYaxis().SetTitle("probability")
            # normalization
            area = h1d.Integral()
            if area > 0:
                h1d.Scale(1.0/area)
            else:
                continue
            hmax = h1d.GetMaximum()
            if hmax > maxim:
                maxim = hmax
            legend2.AddEntry( h1d, bsmtype, "l" )
            #  + " (x" + str( self.__bsmsamples[ bsmtype ][ 0 ][ 1 ] ) + ")"
                #lstyle += 1
            pass

        first = True
        for bsmtype, h1d in bsmhists.iteritems():
            h1d = bsmhists[ bsmtype ]
            if h1d.GetEntries() < 1:
                continue
            h1d.SetMaximum( 1.5 * maxim )
            if first:
                h1d.Draw( "HIST" )
                first = False
            else:
                h1d.Draw( "HIST SAME" )
            pass

        legend2.Draw()
        return legend2


###############################


###############################
# plot slices of 2D histogram #
###############################

    def DrawHoriSliceFrom2D( self, hname, filename, firstBin=0, lastBin=-1,
                             hTitle="", plotSigMC=True, overlaySigMC=False ):
        # Retrieve the data and MC histograms:
        dhist = self.GetDataHist( hname )
        mchists = self.GetMCHists( hname )
        bsmhists = self.GetBSMHists( hname )

        ROOT.gStyle.SetTitleFillColor(0)

        # Create a canvas:
        if plotSigMC and (not overlaySigMC):
            cv = ROOT.TCanvas( hname + "_canvas", "", 800, 1000 )
            cv.Divide(1,2,0.01,0.01)
        else:
            cv = ROOT.TCanvas( hname + "_canvas", "", 800, 600 )

        # Create the histogram representing the sum of all MC samples
        addedSamples = None
        for mctype in mchists.keys():
            # make projections and add them
            h2d = mchists[ mctype ]
            title = h2d.GetTitle() + ": "
            yaxis = h2d.GetYaxis()
            label = yaxis.GetBinLabel(firstBin)
            h1d = h2d.ProjectionX(title+label+mctype, firstBin, lastBin)
            if addedSamples:
                addedSamples.Add ( h1d )
            else:
                addedSamples = h1d.Clone()
            pass

        cv.cd(1).SetLogy()
        
        # Plot the data first:
        title = dhist.GetTitle() + ": "
        yaxis = dhist.GetYaxis()
        label = yaxis.GetBinLabel(firstBin)
        hData = dhist.ProjectionX(title+label, firstBin, lastBin)
        if hTitle==0:
            hData.SetTitle(title+label)
        else:
            hData.SetTitle(hTitle)
        hData.GetYaxis().SetTitle( dhist.GetZaxis().GetTitle() )
        minimum = min( [ 0.02, addedSamples.GetMinimum(), hData.GetMinimum() ] )
        minimum *= 0.5
        minimum += 2e-2
        maximum = max( [ 100, addedSamples.GetMaximum(), hData.GetMaximum() ] )
        maximum *= 2.0        
        hData.SetMinimum( minimum )
        hData.SetMaximum( maximum )
        if hTitle!="":
            hData.SetTitle(hTitle)
        hData.Draw()

        # Create a legend for the plot:
#         legend1 = ROOT.TLegend( self.__legendLowX, self.__legendLowY,
#                                self.__legendHighX, self.__legendHighY )
        legend1 = ROOT.TLegend( 0.72, 0.55, 0.97, 0.998 )
        legend1.AppendPad()
#        legend1.SetFillStyle( 0 )
        legend1.SetFillColor( 0 )
        legend1.AddEntry( hData, "data", "lpe" )


        # Create a stack of the MC histograms:
        stack = ROOT.THStack( hname + "_mcstack", "Stacked MC histograms" )
        # Now draw the MC histograms one by one:
        lstyle = 1
        #color = 2
        usedcolors = []
        # Every element should be a list of the form [histo, "name", "style"]
        legendEntries = []
        for mctype in mchists.keys():
            # draw projections
            h2d = mchists[ mctype ]
            title = h2d.GetTitle() + ": "
            yaxis = h2d.GetYaxis()
            label = yaxis.GetBinLabel(firstBin)
            hist = h2d.ProjectionX(title+label+mctype, firstBin, lastBin)
            hist.SetFillStyle( 1001 )
            if mctype in self.__colors:
                color = self.__colors[ mctype ]
            else:
                color = self.GetDefaultColor( usedcolors )
            hist.SetFillColor( color )
            hist.SetLineColor( color )
            if mctype in self.__linestyles:
                lstyle = self.__linestyles[mctype]
                hist.SetLineStyle( lstyle )
            stack.Add( hist )
            legendEntries.append( [hist, mctype, "f"] )
            #lstyle += 1
            pass

        legendEntries.reverse()
        for e in legendEntries: legend1.AddEntry( e[0], e[1], e[2] )

        # Draw the data points again:
        stack.Draw( "HIST SAME" )
        hData.Draw( "SAME" )

        legend1.Draw();
        
        # Add the ATLAS notations:
        import AtlasUtil
        AtlasUtil.AtlasLabel( 0.20, 0.85 )
        AtlasUtil.DrawLuminosity( 0.20, 0.76, self.__luminosity )

        if not plotSigMC and not overlaySigMC:
            cv.SaveAs( filename )
            return addedSamples
        elif plotSigMC:
            cv.cd(2).SetLogy()


        if not overlaySigMC:
            legend2 = ROOT.TLegend( 0.72, 0.65, 0.97, 0.998 )
            legend2.AppendPad()
            legend2.SetFillColor( 0 )
#             legend2.SetFillStyle( 0 )
            pass
        else:
            legend2 = legend1
        if overlaySigMC and not plotSigMC:
            lstyle = 2
        else:
            lstyle = 1
        #color = 1
        first = 1
        maxim = -1
        minim = 10
        hists1d = []
        # Draw the BSM histograms one-by-one:
        for bsmtype in bsmhists.keys():
            h2d = bsmhists[ bsmtype ]
            if h2d.GetEntries() < 1:
                continue
            title = h2d.GetTitle() + ": "
            yaxis = h2d.GetYaxis()
            label = yaxis.GetBinLabel(firstBin)
            hists1d += [ h2d.ProjectionX(title+label+bsmtype, firstBin, lastBin) ]
            if hists1d[-1].GetEntries() < 1:
                continue
            if color in self.__colors:
                color = self.__colors[ mctype ]
            else:
                color = self.GetDefaultColor( usedcolors )
            hists1d[-1].SetLineColor( color )
            hists1d[-1].SetLineStyle( lstyle )
            if not overlaySigMC:
                # normalization
                area = hists1d[-1].Integral()
                if area > 0:
                    hists1d[-1].Scale(1.0/area)
                else:
                    continue
                pass
            hmax = hists1d[-1].GetMaximum()
            if hmax > maxim:
                maxim = hmax
                hists1d[0].SetMaximum( 1.5 * maxim )

            hmin = hists1d[-1].GetMinimum()
            if hmin > minim:
                minim = hmin
                hists1d[0].SetMinimum( 0.5 * minim )

            legend2.AddEntry( hists1d[-1], bsmtype
#                               + " (x" + str( self.__bsmsamples[ bsmtype ][ 0 ][ 1 ] ) + ")"
                              , "l" )

            if overlaySigMC and not plotSigMC:
                lstyle += 1
                if lstyle == 9:
                    lstyle = 2
                    pass

        if hTitle!="":
            hists1d[0].SetTitle(hTitle)
        hists1d[0].GetYaxis().SetTitle("probability")
        if not overlaySigMC or plotSigMC:
            hists1d[0].Draw( "HIST" )
        else:
            hists1d[0].Draw( "HIST,SAME" )
        for h in range(1,len(hists1d)):
            hists1d[h].Draw( "HIST SAME" )
            pass

        legend2.Draw()


        # Now create the plot:
        cv.SaveAs( filename )
        return addedSamples

###############################



######################
# plot 2D histograms #
######################

    def Draw2Dhisto( self, hname, filename, hTitle="", plotSigMC=True ):
        # Retrieve the data and MC histograms:
        dhist = self.GetDataHist( hname )
        mchists = self.GetMCHists( hname )
        bsmhists = self.GetBSMHists( hname )

        topMargin = ROOT.gStyle.GetPadTopMargin()
        bottomMargin = ROOT.gStyle.GetPadBottomMargin()
        rightMargin = ROOT.gStyle.GetPadRightMargin()
        leftMargin = ROOT.gStyle.GetPadLeftMargin()
        ROOT.gStyle.SetPadTopMargin(0.12)
        ROOT.gStyle.SetPadBottomMargin(0.12)
        ROOT.gStyle.SetPadRightMargin(0.16)
        ROOT.gStyle.SetPadLeftMargin(0.19)

        ROOT.gStyle.SetPalette(1)
        ROOT.gStyle.SetTitleFillColor(0)

        # Create a canvas:
        canvas = ROOT.TCanvas( hname + "_cnvs", "Canvas for 2D plots", 800, 600 )
        canvas.cd()

        # Sum together the background histograms
        if len(mchists)<1:
            self.logger.error("ERROR in Draw2Dhisto: empty mchists" )
            return

        hBkg = None
        for mctype in mchists.keys():
            h2d = mchists[ mctype ]
            if not hBkg:
                hBkg = h2d.Clone(hname+mctype+" Bkg")
            else:
                hBkg.Add( h2d )
            pass

        maximum = max( [ hBkg.GetMaximum(), dhist.GetMaximum() ] )
        maximum *= 2.0        
        hBkg.SetMaximum( maximum )

        hBkg.SetFillColor(4)

        canvas.cd().SetLogz()

        if hTitle!="":
            hBkg.SetTitle(hTitle)
        # Plot the background first, the the data
        hBkg.Draw( "COLZ" )

        dhist.Draw( "BOX,SAME" )

        # Create a legend for the plot:
        legend1 = ROOT.TLegend( self.__2DlegendLowX, self.__2DlegendLowY,
                               self.__2DlegendHighX, self.__2DlegendHighY )
        legend1.AppendPad()
        legend1.SetFillStyle( 1001 )
        legend1.SetFillColor( 0 )
        legend1.AddEntry( dhist, "data", "lfa" )
        legend1.AddEntry( hBkg, "background", "fa" )
        legend1.Draw();
        
        # Add the ATLAS notations:
        import AtlasUtil
        AtlasUtil.AtlasLabel( 0.35, 0.91 )
        AtlasUtil.DrawLuminosity( 0.01, 0.91, self.__luminosity )

        canvas.SaveAs( filename )

        if not plotSigMC:
            ROOT.gStyle.SetPadTopMargin(topMargin)
            ROOT.gStyle.SetPadBottomMargin(bottomMargin)
            ROOT.gStyle.SetPadRightMargin(rightMargin)
            ROOT.gStyle.SetPadLeftMargin(leftMargin)
            return


        tStyle = ROOT.gStyle.GetOptTitle()
        ROOT.gStyle.SetOptTitle(1)
        counter=1
        # Draw the BSM histograms one-by-one:
        for bsmtype in bsmhists.keys():
            canvas.cd().SetLogz()
            h2d = bsmhists[ bsmtype ]
            if h2d.GetEntries() < 1:
                continue
            # normalization
            area = h2d.Integral()
            if area > 0:
                h2d.Scale(1.0/area)
                h2d.SetTitle( h2d.GetTitle() + ": " + bsmtype
#                               + " (x" + str( self.__bsmsamples[ bsmtype ][ 0 ][ 1 ] ) + ")"
                              )
                h2d.GetZaxis().SetTitle("probability")
                if hTitle!="":
                    h2d.SetTitle(hTitle)
                h2d.Draw( "COLZ" )

            if area == 0:
                canvas.cd().SetLogz(0)
                h2d.Draw()

            filename2 = "signal_"+bsmtype+"_"+filename
            canvas.SaveAs( filename2 )
            counter += 1
            pass

        ROOT.gStyle.SetOptTitle(tStyle)
        ROOT.gStyle.SetPadTopMargin(topMargin)
        ROOT.gStyle.SetPadBottomMargin(bottomMargin)
        ROOT.gStyle.SetPadRightMargin(rightMargin)
        ROOT.gStyle.SetPadLeftMargin(leftMargin)

        return

###############################



###############################
# plot slices of 3D histogram #
###############################

    def DrawHoriSliceFrom3D( self, hname, filename, firstBin=0, lastBin=-1, hTitle="", plotSigMC=True ):
        # Retrieve the data and MC histograms:
        dhist = self.GetDataHist( hname )
        mchists = self.GetMCHists( hname )
        bsmhists = self.GetBSMHists( hname )

        topMargin = ROOT.gStyle.GetPadTopMargin()
        bottomMargin = ROOT.gStyle.GetPadBottomMargin()
        rightMargin = ROOT.gStyle.GetPadRightMargin()
        leftMargin = ROOT.gStyle.GetPadLeftMargin()
        ROOT.gStyle.SetPadTopMargin(0.14)
        ROOT.gStyle.SetPadBottomMargin(0.14)
        ROOT.gStyle.SetPadRightMargin(0.16)
        ROOT.gStyle.SetPadLeftMargin(0.16)

        ROOT.gStyle.SetPalette(1)
        ROOT.gStyle.SetTitleFillColor(0)

        # Create a canvas:
        canvas = ROOT.TCanvas( hname + "_cv", "Canvas for 2D plots", 800, 600 )
        canvas.cd()

        # Sum together the background histograms
        if len(mchists)<1:
            self.logger.error( "ERROR in DrawHoriSliceFrom3D: empty mchists" )
            return

        hBkg = None
        for mctype in mchists.keys():
            h3d = mchists[ mctype ]
            title = h3d.GetTitle() + ": "
            zaxis = h3d.GetZaxis()
            label = zaxis.GetBinLabel(firstBin)
            zaxis.SetRange(firstBin, lastBin)
            h2d = h3d.Project3D("yx")
            h2d.SetName(title+label+mctype+" Bkg")
            if hTitle==0:
                h2d.SetTitle(title+label)
            else:
                h2d.SetTitle(hTitle)
            if not hBkg:
                hBkg = h2d.Clone(title + "_Bkg")
            else:
                hBkg.Add( h2d )
            pass

        hBkg.SetFillColor(4)

        title = dhist.GetTitle() + ": "
        zaxis = dhist.GetZaxis()
        label = zaxis.GetBinLabel(firstBin)
        zaxis.SetRange(firstBin, lastBin)
        hData = dhist.Project3D("yx")
        hData.SetName(title+label)
        if hTitle==0:
            hData.SetTitle(title+label+": "+bsmtype)
        else:
            hData.SetTitle(hTitle)


        maximum = max( [ hBkg.GetMaximum(), hData.GetMaximum() ] )
        maximum *= 2.0        
        hBkg.SetMaximum( maximum )

        # Plot the background first, the the data
        hBkg.Draw( "COLZ" )
        hData.Draw( "BOX,SAME" )

        # Create a legend for the plot:
        legend1 = ROOT.TLegend( self.__2DlegendLowX, self.__2DlegendLowY,
                               self.__2DlegendHighX, self.__2DlegendHighY )
        legend1.AppendPad()
        legend1.SetFillStyle( 1001 )
        legend1.SetFillColor( 0 )
        legend1.AddEntry( hData, "data", "lfa" )
        legend1.AddEntry( hBkg, "background", "fa" )
        legend1.Draw();

        # Add the ATLAS notations:
        import AtlasUtil
        AtlasUtil.AtlasLabel( 0.35, 0.91 )
        AtlasUtil.DrawLuminosity( 0.01, 0.91, self.__luminosity )

        canvas.SaveAs( filename )

        if not plotSigMC:
            ROOT.gStyle.SetPadTopMargin(topMargin)
            ROOT.gStyle.SetPadBottomMargin(bottomMargin)
            ROOT.gStyle.SetPadRightMargin(rightMargin)
            ROOT.gStyle.SetPadLeftMargin(leftMargin)
            return


        tStyle = ROOT.gStyle.GetOptTitle()
        ROOT.gStyle.SetOptTitle(1)
        counter=1
        # Draw the BSM histograms one-by-one:
        for bsmtype in bsmhists.keys():
            canvas.cd().SetLogz()
            h3d = bsmhists[ bsmtype ]
            if h3d.GetEntries() < 1:
                continue
            title = h3d.GetTitle() + ": "
            zaxis = h3d.GetZaxis()
            label = zaxis.GetBinLabel(firstBin)
            zaxis.SetRange(firstBin, lastBin)
            h2d = h3d.Project3D("yx")
            if h2d.GetEntries() < 1:
                continue
            h2d.SetName(title+label+" Sig: "+bsmtype)
            if hTitle==0:
                h2d.SetTitle(title+label+": "+bsmtype)
            else:
                h2d.SetTitle(hTitle)      
            # normalization
            area = h2d.Integral()
            if area > 0:
                h2d.Scale(1.0/area)
                h2d.SetTitle( h3d.GetTitle() + ": " + bsmtype
#                               + " (x" + str( self.__bsmsamples[ bsmtype ][ 0 ][ 1 ] ) + ")"
                              )
                h2d.GetZaxis().SetTitle("probability")
                if hTitle!="":
                    h2d.SetTitle(hTitle)
                h2d.Draw( "COLZ" )
            if area == 0:
                canvas.cd().SetLogz(0)
                h2d.Draw()
            filename2 = "signal_"+bsmtype+"_"+filename
            canvas.SaveAs( filename2 )
            counter += 1
            pass


        ROOT.gStyle.SetOptTitle(tStyle)
        ROOT.gStyle.SetPadTopMargin(topMargin)
        ROOT.gStyle.SetPadBottomMargin(bottomMargin)
        ROOT.gStyle.SetPadRightMargin(rightMargin)
        ROOT.gStyle.SetPadLeftMargin(leftMargin)
        
        return

###############################

