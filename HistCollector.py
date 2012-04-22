
import ROOT
import log, logging


class HistCollector():
    """ A cache for histograms

    This is a class that is able to
    gather histograms from ROOT files.
    It can also act as a chache
    to speed up performance.
    """

    def __init__( self ):
        self.FileHistCache = {}
        

    def ClearCache( self ):
        self.FileHistCache.clear()


    '''
    def CloneHistFromFile( self, tfile, name, cache=False ):

        logging.debug( "HistCollector - \t Not in cache: %s %s" % (file, name) )
        logging.debug( "HistCollector - \t Opening File: %s" % file )
        
        logging.debug( "HistCollector - \t Getting Hist: %s" % name )

        ROOT.gROOT.cd()
        hist = tfile.Get( name )
        if not hist:
            raise IOError( 5, "Histogram '" + name + "' not found in file '" + file + "'" )
        
        ROOT.gROOT.cd()
        returnHist = hist.Clone()
        #returnHist.Add( hist )
                
        if returnHist.GetEntries() == 0 :
            logging.debug(" GetHist - Hist: %s in file: %s has 0 entries" % (name, file) )
            
        if cache:
            self.FileHistCache[ (file, name) ] = returnHist #.Clone()

        hist.Delete()
        return returnHist
    '''

    def GetHist( self, file, name, cache=False ):
        
        logging.debug( "HistCollector - \t Getting File %s Hist %s" %  (file, name) )

        # Check if the hist is in the cache:
        if (file, name) in self.FileHistCache:
            logging.debug( "HistCollector - \t Found in cache: %s %s" % (file, name) )
            return FileHistCache[ (file, name) ]
        
        logging.debug( "HistCollector - \t Not in cache: %s %s" % (file, name) )
        logging.debug( "HistCollector - \t Opening File: %s" % file )
        #tfile = ROOT.TFile.Open( file, "READ" )
        tfile = ROOT.TFile( file )
        if not tfile:
            raise IOError( 1, "File '" + file + "' could not be opened" )

        logging.debug( "HistCollector - \t Getting Hist: %s" % name )
        ROOT.gROOT.cd()
        hist = tfile.Get( name )
        if not hist:
            raise IOError( 5, "Histogram '" + name + "' not found in file '" + file + "'" )

        ROOT.gROOT.cd()
        returnHist = hist.Clone()
        #returnHist.Add( hist )
        #hist = hist.Clone()
        hist.Delete()
        del hist
        
        if returnHist.GetEntries() == 0 :
            logging.debug(" GetHist - Hist: %s in file: %s has 0 entries" % (name, file) )

        if cache:
            self.FileHistCache[ (file, name) ] = returnHist #.Clone()
        
        tfile.Close()
        tfile.Delete() # Testing
        del tfile

        if returnHist == None:
            print "Error: hist (%s, %s) is NONE" % (name, file)
            raise Exception("Hist")
        
        return returnHist


    def CacheHists( self, file, histList ):
        
        logging.debug( "HistCollector - \t Caching hists in file %s" %  (file) )

        for hist in histList:
            logging.debug( "HistCollector - \t Going to cache hist: %s " %  (hist) )

        #tfile = ROOT.TFile.Open( file, "READ" )
        tfile = ROOT.TFile( file )
        if not tfile:
            raise IOError( 1, "File '" + file + "' could not be opened" )

        for name in histList:

            # Check if the hist is in the cache:
            if (file, name) in self.FileHistCache:
                logging.debug( "HistCollector - \t Found in cache: %s %s" % (file, name) )
                continue
        
            logging.debug( "HistCollector - \t Not in cache: %s %s" % (file, name) )
            logging.debug( "HistCollector - \t Opening File: %s" % file )

            logging.debug( "HistCollector - \t Getting Hist: %s" % name )
            hist = tfile.Get( name )
            if not hist:
                raise IOError( 5, "Histogram '" + name + "' not found in file '" + file + "'" )

            ROOT.gROOT.cd()
            returnHist = hist.Clone()
            #returnHist.Add( hist )
            hist.Delete()
            del hist

            if returnHist.GetEntries() == 0 :
                logging.debug(" GetHist - Hist: %s in file: %s has 0 entries" % (name, file) )

            self.FileHistCache[ (file, name) ] = returnHist #.Clone()

        # Got all histograms
        # Now we're done
        tfile.Close()
        tfile.Delete()
        del tfile

