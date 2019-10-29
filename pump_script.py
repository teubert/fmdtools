# -*- coding: utf-8 -*-
"""
File name: pump_script.py
Author: Daniel Hulse
Created: October 2019
Description: A simple example of I/O using faultprop.py and the pump model in ex_pump.py
"""

#Using the model that was set up, we can now perform a few different operations

#First, import the fault propogation library as well as the model
import faultprop as fp
from ex_pump import * #required to import entire module

mdl = pump()


#Before seeing how faults propogate, it's useful to see how the model performs
#in the nominal state to check to see that the model has been defined correctly.
# Some things worth checking:
#   -are all functions on the graph?
#   -are the functions connected with the correct flows?
#   -do any faults occur in the nominal state?
#   -do all the flow states proceed as desired over time?

endresults, resgraph, flowhist, ghist=fp.runnominal(mdl, track={'Wat_1','Wat_2', 'EE_1', 'Sig_1'})
fp.showgraph(resgraph)
fp.plotflowhist(flowhist, 'Nominal')

endresults_bip, resgraph_bip, flowhist, ghist=fp.runnominal(mdl, gtype='bipartite')
fp.showbipartite(resgraph_bip, scale=2)

#
##We might further query the faults to see what happens to the various states
endresults, resgraph, flowhist, ghist=fp.runonefault(mdl, 'MoveWater', 'short', time=10, track={'Wat_1','Wat_2', 'EE_1', 'Sig_1'}, staged=True)
fp.showgraph(resgraph)
fp.plotflowhist(flowhist, 'short', time=10)
t=fp.printresult('MoveWater', 'short', 10, endresults)
print(t)
##in addition to these visualizations, we can also look at the final results 
##to see which specific faults were caused, as well as the flow states
print(endresults)
#
##we can also look at other faults
endresults, resgraph, flowhist, ghist=fp.runonefault(mdl, 'ExportWater', 'block', time=10, track={'Wat_1','Wat_2', 'EE_1', 'Sig_1'}, staged=True)
fp.showgraph(resgraph)
fp.plotflowhist(flowhist, 'blockage', time=10)
# we can also view the results as a bipartite graph
endresults, resgraph_bip2, flowhist, ghist=fp.runonefault(mdl, 'ExportWater', 'block', time=10, gtype='bipartite')
fp.showbipartite(resgraph_bip2, faultscen='ExportWater block', time=10, scale=2)


t=fp.printresult('ExportWater', 'block', 10, endresults)
print(t)
##you can save to a csv this with:
#t.write('tab.ecsv', overwrite=True)


#finally, to get the results of all of the scenarios, we can go through the list
#note that this will propogate faults based on the times vector put in the model,
# e.g. times=[0,3,15,55] will propogate the faults at the begining, end, and at
# t=15 and t=15
resultstab=fp.runlist(mdl)
print(resultstab)
#resultstab.write('tab.ecsv', overwrite=True)