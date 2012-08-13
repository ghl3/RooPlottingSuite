# $Id: AtlasUtil.py 212171 2011-10-06 10:08:54Z skreiss $
#
# Module providing some convenience functions for decorating ATLAS plots.
#

##
# @short Function producing the "ATLAS Preliminary" sign
#
# There is a usual format for the "ATLAS Preliminary" sign on the plots,
# this function takes care of using that. Plus, it makes it simple to
# remove/change the "Preliminary" part if/when necessary.
#
# @param x The X position of the text in the [0,1] interval
# @param y The Y position of the text in the [0,1] interval
# @param color The color of the text
def AtlasLabel( x, y, color = 1 ):
    # ROOT is needed of course:
    import ROOT
    # Draw the "ATLAS" part:
    l = ROOT.TLatex()
    l.SetNDC()
    l.SetTextFont( 72 )
    l.SetTextColor( color )
    l.DrawLatex( x, y, "ATLAS" )
    # Draw the "Preliminary" part:
    l.SetTextFont( 42 )
    l.DrawLatex( x + 0.12, y, "Internal" )
    return

##
# @short Function drawing generic text on the plots
#
# This is just to save the user a few lines of code in his/her script
# when putting some additional comments on a plot.
#
# @param x The X position of the text in the [0,1] interval
# @param y The Y position of the text in the [0,1] interval
# @param text The text to be displayed
# @param color The color of the text
def DrawText( x, y, text, color = 1 ):
    # Draw the text quite simply:
    import ROOT
    l = ROOT.TLatex()
    l.SetNDC()
    l.SetTextColor( color )
    l.DrawLatex( x, y, text )
    return

##
# @short Function drawing the luminosity value on the plots
#
# This is just a convenience function for putting a pretty note
# on the plots of how much luminosity was used to produce them.
#
# @param x The X position of the text in the [0,1] interval
# @param y The Y position of the text in the [0,1] interval
# @param lumi The luminosity value in 1/pb
# @param color The color of the text
def DrawLuminosity( x, y, lumi, color = 1 ):
    DrawText( x, y, "#intLdt = " + str( lumi ) + " pb^{-1}", color )
    return

##
# @short Function drawing the luminosity value on the plots in fb-1
#
# This is just a convenience function for putting a pretty note
# on the plots of how much luminosity was used to produce them.
#
# @param x The X position of the text in the [0,1] interval
# @param y The Y position of the text in the [0,1] interval
# @param lumi The luminosity value in 1/fb
# @param color The color of the text
def DrawLuminosityFb( x, y, lumi, color = 1 ):
    DrawText( x, y, "#intLdt = " + str( lumi ) + " fb^{-1}", color )
    return
