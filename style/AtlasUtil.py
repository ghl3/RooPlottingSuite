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
def AtlasLabel( x, y, color = 1, experiment="Atlas", preliminary=False, public=False ):
   docStatus = "Internal"
   if preliminary: docStatus = "Preliminary"
   if public: docStatus = ""
   textMap = {
      'Atlas':'ATLAS #font[42]{%s}' % docStatus, 
      'AtlasCms':'ATLAS+CMS #font[42]{%s}' % docStatus,
   }
   
   # ROOT is needed of course:
   import ROOT
   # Draw the "ATLAS" part:
   l = ROOT.TLatex()
   l.SetNDC()
   l.SetTextFont( 72 )
   l.SetTextColor( color )
   atlas = l.DrawLatex( x, y, textMap[experiment] )
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
def DrawTextOneLine( x, y, text, color = 1, size = 0.04, NDC = True, halign = "left", valign = "bottom", skipLines = 0 ):
    halignMap = {"left":1, "center":2, "right":3}
    valignMap = {"bottom":1, "center":2, "top":3}
    
    scaleLineHeight = 1.0
    if valign == "top": scaleLineHeight = 0.8
    if skipLines: text = "#lower[%.1f]{%s}" % (skipLines*scaleLineHeight,text)

    # Draw the text quite simply:
    import ROOT
    l = ROOT.TLatex()
    if NDC: l.SetNDC()
    l.SetTextAlign( 10*halignMap[halign] + valignMap[valign] )
    l.SetTextColor( color )
    l.SetTextSize( size )
    l.DrawLatex( x, y, text )
    return l
def DrawText( x, y, text, color = 1, size = 0.04, NDC = True, halign = "left", valign = "bottom" ):
    objs = []
    skipLines = 0
    for line in text.split('\n'):
       objs.append( DrawTextOneLine( x, y, line, color, size, NDC, halign, valign, skipLines ) )
       if NDC == True: y -= 0.05 * size/0.04
       else:
         skipLines += 1
       
    return objs

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
    return DrawText( x, y, "#intLdt = " + str( lumi ) + " pb^{-1}", color )

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
def DrawLuminosityFb( x, y, lumi, color = 1, sqrts = 7, size = 0.04, twoLines = True ):
    if isinstance( lumi, float ): lumi = "%.1f" % lumi
    if isinstance( sqrts, float ): sqrts = "%.0f" % sqrts
    text = "#intLdt = %s fb^{-1}, #sqrt{s} = %s TeV" % (lumi, sqrts)
    if twoLines: text = text.replace( ", ", "\n  " )
    return DrawText( x, y, text, color, size )

def DrawLuminosityFbSplit( x, y, lumi, color = 1, sqrts = 7, size = 0.04, twoLines = True ):
   if isinstance( lumi, float ) or isinstance( lumi, int ): lumi = "%.1f" % lumi
   if isinstance( sqrts, float ) or isinstance( sqrts, int ): sqrts = "%.0f" % sqrts
   lumi = lumi.split(" + ")
   sqrts = sqrts.split(" and ")
   text = ["#sqrt{s} = %s TeV:  #lower[-0.17]{#scale[0.57]{#int}}Ldt = %s fb^{-1}" % (s,l) for l,s in zip( lumi, sqrts ) ]
   text = ", ".join( text )
   if twoLines: text = text.replace( ", ", "\n" )
   return DrawText( x, y, text, color, size )
   
