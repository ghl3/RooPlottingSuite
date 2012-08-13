#!/usr/bin/env python

import ROOT
import sys
import logging
import glob

from helpers.tools import GetAndStyleHist



def main():
    """ Command-line interface to generate a histogram
    
    It takes an few necessary arguments
    and quickly generates a plot:
    
    -f or --file   : Input File name (or wildcard for glob)
    -h or --hist   : Histogram to draw
    -o or --output : Name of output file (determines type of file) 
    
    Optional arguments:
    -l or --log  : Plot using log scale
    -s or --skip : Ignore files not holding the given histogram
    
    """

    # Read the command line options:
    import optparse
    desc = "This script can be used to quickly make a plot" \
           "from the command line." \
           "  It can loop over root files and plot their histograms \n" \
           "Usage: \n" \
           "makePlot.py histName fileName(s) (options)" 

    vers = "$Revision: 00001 $"

    parser = optparse.OptionParser( description = desc, version = vers,
                                    usage = "%prog [options]" )

    # Optional Arguments
    parser.add_option( "-o", "--output", dest = "output",
                       action = "store", type = "string", 
                       default = "", help = "Name of output file ( including .pdf, .eps, etc)" )
    
    parser.add_option(  "-m", "--lumi", dest = "lumi",
                       action = "store", type = "float", 
                       default = "1.0", help = "Luminosity with which to scale the histograms" )

    parser.add_option( "-v", "--verbose",  action="store_true", dest="verbose", help="Set Output Mode to Verbose")

    parser.add_option( "-l", "--log",      action="store_true", dest="log",     help="Use Log Scale")

    # Parse the command line options:
    ( options, args ) = parser.parse_args()

    options_dict = vars(options)
    
    # Check that we get at least 2 (positional) arguments:
    if len(args) < 2:
        print "Error: Must have two positional arguments: HistName FileName(s)"

    HISTNAME  = args[0]
    FILELIST  = args[ 1 : ]
    OUTPUT    = options.output

    if OUTPUT == "":
        OUTPUT = "%s.pdf" % HISTNAME.replace('/', '_')
                
    FORMAT = "%(levelname)s  %(message)s" 

    logging.basicConfig( level=logging.INFO, format=FORMAT )  

    if options.verbose:
        logging.basicConfig( level=logging.DEBUG )  

    plot = { "Hist" : HISTNAME, "FileList" : [] }

    for file in FILELIST:
        fileList = glob.glob( file )
        if len( fileList ) == 0:
            logging.warning( "No files found in string: %s" % file )
        plot["FileList"].extend( fileList )

    # Make the Plot
    ROOT.gROOT.SetBatch(True)

    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    ROOT.SetOwnership(canvas, False)
    canvas.cd()
        
    hist = GetAndStyleHist( plot )

    if options.lumi:
        lumi = options.lumi
        logging.debug( "Scaling by lumi: %s" % lumi )
        hist.Scale( lumi )

    hist.Draw()

    if options.log:
        canvas.SetLogy( True )
    
    canvas.SaveAs( OUTPUT )
    
    del canvas

    return


if __name__ == "__main__":
    main()
