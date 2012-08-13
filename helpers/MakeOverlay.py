#!/usr/bin/env python

from ROOT import TFile, TCanvas, TH1, TLegend
from ROOT import TImage, gROOT

def MakeOverlay( json_request ):

    # Get the input files

    gROOT.SetBatch(True)
    canvas = TCanvas("Canvas", "Canvas")
    canvas.SetBatch(True) 

    PlotList = json_request[ "Plots" ]

    first = True

    FileList = []
    HistList = []

    for plot in PlotList:

        print "Plotting %s %s" % (plot["File"], plot["Hist"])
        
        file = TFile.Open( plot["File"] )
        hist = file.Get( plot["Hist"] )
        
        FileList.append( file )
        HistList.append( hist )

        if "Color" in plot:
            hist.SetLineColor( plot["Color"] )

        canvas.cd()

        if first:
            hist.Draw("goff")
            first = False
        else:
            hist.Draw( "goffSAME" )

    # Configure the canvas
    if "Log" in json_request:
        canvas.SetLogY( True )




    #canvas.GetPainter().SaveImage(canvas, "/usr/bin/hexdump", TImage.kPng);


    # Now Save the canvas
    # to a string:
    from cStringIO import StringIO
    import sys

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    canvas.GetPainter().SaveImage(canvas, "/dev/stdout", TImage.kPng);
    sys.stdout = old_stdout

    #print mystdout

    #canvas.Print("file.jpg")



    return

if __name__ == "__main__":
    main()
