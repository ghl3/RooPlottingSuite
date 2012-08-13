#!/usr/bin/env python


import ROOT
from ROOT import TFile, TKey
from ROOT import TDirectory, gDirectory

import logging
import os
import re


def main():
    """

    Open an input ROOT file
    Walk through the directory structure
    Find all histograms and print a 
    list of directory, histogram pairs
    """

    # Read the command line options:
    import optparse
    desc = "This script finds all histograms in a ROOT file" \
           " and plots them to one or many output files." 

    vers = "$Revision: 00001 $"

    parser = optparse.OptionParser( description = desc, version = vers,
                                    usage = "%prog [options]" )

    # Optional Arguments
    parser.add_option(  "-m", "--lumi",  dest = "lumi",
                       action = "store", type = "float", 
                       default = "1.0",  help = "Luminosity with which to scale the histograms" )

    parser.add_option(  "-r", "--regex", dest = "regex",
                       action = "store", type = "string", 
                       default = "",     help = "Only print histograms whose name match this regular expression" )

    parser.add_option(  "-d", "--dir",   dest = "dir",
                       action = "store", type = "string", 
                       default = "",     help = "Output Directory" )

    parser.add_option(  "-k", "--kind",  dest = "kind",
                       action = "store", type = "string", 
                       default = "pdf",  help = "Type of output file (pdf, eps, etc)" )

    parser.add_option( "-v", "--verbose",  action="store_true", dest="verbose", help="Set Output Mode to Verbose")
    parser.add_option( "-l", "--log",      action="store_true", dest="log",     help="Use Log Scale")


    # Logic: if -s is supplied, the output goes to
    # a single file of name 
    # ->  dir/output.kind
    # if no output is supplied, the file is
    # ->  dir/fileName.kind

    # Else, it goes to many files whose names
    # are given by:
    # ->  dir/fileDirStructure/histName.kind

    parser.add_option( "-s", "--single",   action="store_true", dest="single",  help="Plot all histograms in a single pdf")

    parser.add_option( "-o", "--output", dest = "output",
                       action = "store", type = "string", 
                       default = "",     help = "Name of output file ( including .pdf, .eps, etc)" )

    # Parse the command line options:
    ( options, args ) = parser.parse_args()
    
    # Check that we get at least 2 (positional) arguments:
    if len(args) < 1:
        print "Error: Must have at least one argument: FileName"
        return

    # Get the file
    FILENAME = args[0]

    # Open the input file
    file = TFile( FILENAME )
    file.cd()

    PathHistList = []
    ExtendHistList( gDirectory, PathHistList )
    dir = options.dir
    if dir != "":
        dir += "/"
    kind = options.kind
    output = options.output

    # Okay, hopefully this list should be filled properly
    # Create the directory structure and print the output histograms
    ROOT.gROOT.SetBatch(True)

    canvas = ROOT.TCanvas("canvas", "Canvas for plot making", 800, 600 )
    ROOT.SetOwnership(canvas, False)
    canvas.cd()

    if options.log:
        canvas.SetLogy( True )

    if options.lumi:
        lumi = options.lumi
        logging.debug( "Scaling by lumi: %s" % lumi )

    regex = None
    if options.regex != "":
        regex = re.compile( options.regex )

    outputName = ""
    if options.single:
        if output != "":
            outputName = dir + output
        else:
            outputName = dir + FILENAME + '.' + kind
        pass
        canvas.Print(outputName + "[");

    for (name, hist) in PathHistList:
        if options.regex != "":
            if not regex.match( name ):
                continue
            pass
        if options.lumi:
            hist.Scale( lumi )

        hist.Draw()

        # Make sure the directory exists
        if options.single:
            pass # outputName already made
        else:
            outputName     =  dir + name     + '.' + kind

        # If necessary, create the dir structure
        CreateDirectoryStructure( outputName )
        
        # Finally, make the output
        canvas.Print( outputName, "Title:" + name )

    if options.single:
        canvas.Print( outputName + "]");

    del canvas

    return


def ExtendHistList( Directory, PathHistList ):
    """ Use Recursion to get list of (directory, hist)
    
    """

    keys = Directory.GetListOfKeys()

    for key in keys:

        obj = key.ReadObj()

        if( obj.IsA().InheritsFrom("TH1") ):
            fullPath = Directory.GetPath()
            fullPath = fullPath[ fullPath.find(":/") + 2 : ]
            fullPath += '/' + obj.GetName()
            PathHistList.append( (fullPath, obj) )

        if( obj.IsA().InheritsFrom("TDirectory") ):
            ExtendHistList( obj, PathHistList )

        pass
    

def CreateDirectoryStructure( name ):

    dir = os.path.dirname( name )
    if dir == '': return
    if not os.path.exists(dir):
        os.makedirs( dir )

    pass


if __name__ == "__main__":
    main()
