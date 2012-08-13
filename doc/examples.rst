
.. _contents:

.. _library-intro:


Examples
========


Initialize the Plot Maker

.. code-block:: python

   pm = PlotMaker("PlotMaker", "Plot Maker")
   pm.SetLevelDebug()
   pm.SetLumi( 1000 ) # 5 fb-1
   pm.SetLegendBoundaries( .75, .65, .95, .90 )
   pm.UseLogScale( True )


Add the samples and set their properties

.. code-block:: python

   # Add the Data
   pm.AddDataSample( files="Data/ttbarCycle.data11_7TeV_*.*.root", name="data11 7TeV" )
   pm.SetLumi( 984 )

   # Add the Monte-Carlo Backgrounds
   pm.AddMCSample( files="MonteCarlo/ttbarCycle.ttbar.All.root",   name="ttbar",    color=38 )
   pm.AddMCSample( files="MonteCarlo/ttbarCycle.ttbar_WZ.*.root",  name="ttbar WZ",  color=30 )

   pm.AddMCSample( files="MonteCarlo/ttbarCycle.SingleTop*.root",  name="SingleTop", color=46 )

   pm.AddMCSample( files="MonteCarlo/ttbarCycle.WW.Np*.root",     name="Diboson",   color=44 )
   pm.AddMCSample( files="MonteCarlo/ttbarCycle.WZ.Np*.root",     name="Diboson",   color=44 )
   pm.AddMCSample( files="MonteCarlo/ttbarCycle.ZZ.Np*.root",     name="Diboson",   color=44 )     



Create some simple plots comparing MC to Data

.. code-block:: python
   
   pm.MakeMCDataStack( "DileptonMass", outputName="Plots/DileptonMass.pdf" sampleList=sampleSet, 
   		       outputName=outputName, Formats=["eps","pdf"] )
		      
   # Use a subset of the samples
   TopSamples = ["ttbar", "ttbar WZ"]
   pm.MakeMCDataStack( "DileptonMass", outputName="Plots/DileptonMass_TopOnly.pdf" sampleList=TopSamples,  
   		       outputName=outputName, Formats=["eps","pdf"] )

   # Make several formats simultaneously
   pm.MakeMCDataStack( "DileptonMass", outputName="DileptonMass", Formats=["eps","pdf","png"] )



If you save a histogram where each bin represents a cut and is labeled, the PlotMaker can make tables for you.
See :py:meth:`~PlotMaker.PlotMaker.MakeSingleCutSelectionTable` and :py:meth:`~PlotMaker.PlotMaker.MakeSingleCutSelectionTable` for details.

.. code-block:: python

   # Make a cut-flow table for a single channel for various samples
   pm.MakeSingleChannelSelectionTable( channelHistName="CutFlow/SameSign_EE", sampleList=TopSamples, 
   				       outputName="Table/CutFlow_SameSign_EE_TopSamples.tex" ) 


   # Make a table of the number of events after a single cut for various channels				       
   pm.MakeSingleCutSelectionTable( "CutOnTwoJets", channelNameList=["Dilepton EE","Dilepton EM","Dilepton MM"], 
   				   channelHistList=["CutFlow/Dilepton_EE","CutFlow/Dilepton_EM","CutFlow/Dilepton_MM"],
   				   sampleList=TopSamples, outputName="Table/SelectedEvents_CutOnTwoJets_DileptonChannels.tex" )         

