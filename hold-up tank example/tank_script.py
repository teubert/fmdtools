# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 12:08:05 2020

@author: Daniel Hulse
"""

import sys
sys.path.append('../')

import fmdtools.faultprop as fp
import fmdtools.resultproc as rp
from tank_model import Tank



mdl = Tank()

endresults, resgraph, mdlhist = fp.run_nominal(mdl)

rp.plot_mdlhistvals(mdlhist)
rp.show_graph(resgraph)

endresults, resgraph, mdlhist = fp.run_one_fault(mdl,'Human','NotVisible', time=2)

rp.plot_mdlhistvals(mdlhist, fault='NotVisible', time=2)
rp.show_graph(resgraph,faultscen='NotVisible', time=2)

endresults, resgraph, mdlhist = fp.run_one_fault(mdl,'Human','FalseReach', time=2, gtype='component')

rp.plot_mdlhistvals(mdlhist,fault='FalseReach',time=2)
rp.show_bipartite(resgraph,faultscen='FalseReach', time=2)

#import matplotlib.pyplot as plt
#plt.figure()
#reshist, diff, summary = rp.compare_hist(mdlhist)
#rp.plot_resultsgraph_from(mdl,reshist,time=20)

endclasses, mdlhists = fp.run_list(mdl)
