# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 10:51:57 2021

@author: dhulse
"""
import unittest
import sys, os
sys.path.insert(1, os.path.join('..'))
from example_tank.tank_model import Tank
from example_tank.tank_opt import x_to_rcost_leg, x_to_totcost_leg, x_to_descost
from example_tank.tank_optimization_model import Tank as Tank2
from fmdtools.faultsim.search import ProblemInterface
from fmdtools.faultsim import propagate
import fmdtools.resultdisp as rd
from fmdtools.modeldef import SampleApproach, NominalApproach
from CommonTests import CommonTests
import numpy as np
import multiprocessing as mp



class TankTests(unittest.TestCase, CommonTests):
    def setUp(self):
        self.mdl = Tank()
        self.optmdl = Tank2()
    def test_model_copy_same(self):
        self.check_model_copy_same(Tank(),Tank(), [5,10,15], 10, max_time=20)
    def test_model_copy_different(self):
        self.check_model_copy_different(Tank(), [5,10,15], max_time=20)
    def test_model_reset(self):
        mdl = Tank(); mdl2 = Tank()
        self.check_model_reset(mdl, mdl2, [5,10,15], max_time=20)
    def test_approach_parallelism(self):
        """Test whether the pump simulates the same when simulated using parallel or staged options"""
        app = SampleApproach(self.mdl)
        self.check_approach_parallelism(self.mdl, app)
        app1 = SampleApproach(self.mdl, defaultsamp={'samp':'evenspacing','numpts':4})
        self.check_approach_parallelism(self.mdl, app1)
    def test_same_rcost(self):
        
        kwarg_options = [dict(staged=True),
                         dict(staged=False),
                         dict(staged=True, pool=mp.Pool(4)),
                         dict(staged=False, pool=mp.Pool(4))] 
        mdl= Tank2()
        res_vars_i = {param:1 for param,v in mdl.params.items() if param not in ['capacity','turnup']}
        
        for kwarg in kwarg_options:
            prob = ProblemInterface("res_problem", mdl, **kwarg)
            
            prob.add_simulation("des_cost", "external", x_to_descost)
            prob.add_objectives("des_cost", cd="cd")
            prob.add_variables("des_cost",'capacity', 'turnup')
            
            app = SampleApproach(mdl)
            prob.add_simulation("res_sim", "multi", app.scenlist, include_nominal=True,
                                upstream_sims = {"des_cost":{'params':{"capacity":"capacity", "turnup":"turnup"}}})
            res_vars = [(var, None) for var in res_vars_i.keys()]
            prob.add_variables("res_sim", *res_vars, vartype="param")
            prob.add_objectives("res_sim", cost="expected cost", objtype="endclass")
            prob.add_combined_objective('tot_cost', 'cd', 'cost')
            for des_var in [[15, 0.5], [22, 0.1], [18,0]]:
                rvar = [*res_vars_i.values()][:27]
                lvar = [*res_vars_i.values()][27:]
                prob.clear()
                prob.update_sim_vars("res_sim", newparams={'capacity':des_var[0], 'turnup':des_var[1]})
                inter_cost = prob.cost([*res_vars_i.values()])
                func_cost = x_to_rcost_leg(rvar, lvar, des_var)
                self.assertAlmostEqual(inter_cost, func_cost)
                
                inter_totcost=prob.tot_cost(des_var, [*res_vars_i.values()])
                func_totcost=x_to_totcost_leg(des_var, rvar, lvar)
                self.assertAlmostEqual(inter_totcost, func_totcost)
                
    def test_comp_mode_inj(self):
        """ Tests that component modes injected in functions end up in their respective
        components."""
        mdl = Tank()
        compmodes = [mode for c in mdl.fxns['Human'].components.values() for mode in c.faultmodes]
        compname = {mode:cname for cname,c in mdl.fxns['Human'].components.items() for mode in c.faultmodes}
        for compmode in compmodes:
            mdl = Tank()
            scen = {'Human': compmode}
            propagate.propagate(mdl,1, fxnfaults=scen)
            self.assertIn(compmode, mdl.fxns['Human'].faults)
            self.assertIn(compmode, mdl.fxns['Human'].components[compname[compmode]].faults)
    def test_different_components(self):
        """ Tests that model copies have different components"""
        mdl=Tank()
        mdl_copy = mdl.copy()
        for compname, comp, in mdl.fxns['Human'].components.items():
            self.assertNotEqual(mdl_copy.fxns['Human'].components[compname],comp)
            self.assertNotEqual(mdl_copy.fxns['Human'].components[compname].__hash__(),comp.__hash__())
    def test_local_tstep(self):
        """ Tests running the model with a different local timestep in the Store_Liquid function"""
        mdl_global = Tank(modelparams = {'phases':{'na':[0],'operation':[1,20]}, 'times':[0,5,10,15,20], 'tstep':1, 'units':'min', 'use_local':False})
        _, mdlhist_global = propagate.one_fault(mdl_global,'Store_Water','Leak', time=2)
        mdlhist_global = rd.process.flatten_hist(mdlhist_global)
        
        mdl_loc_low = Tank(params={'reacttime':2, 'store_tstep':0.1})
        _, mdlhist_loc_low = propagate.one_fault(mdl_loc_low,'Store_Water','Leak', time=2)
        mdlhist_loc_low = rd.process.flatten_hist(mdlhist_loc_low)
        
        self.compare_results(mdlhist_global, mdlhist_loc_low)
        
        mdl_loc_high = Tank(params={'reacttime':2, 'store_tstep':3.0})
        _, mdlhist_loc_high = propagate.one_fault(mdl_loc_high,'Store_Water','Leak', time=2)
        mdlhist_loc_high = rd.process.flatten_hist(mdlhist_loc_high)
        for i in [2,5,8,12]:
            slice_global = rd.process.get_flat_hist_slice(mdlhist_global,t_ind=i)
            slice_loc_high = rd.process.get_flat_hist_slice(mdlhist_loc_high ,t_ind=i)
            self.compare_results(slice_global, slice_loc_high)
    def test_epc_math(self):
        """Spot check of epc math work in human error calculation"""
        mdl=Tank()
        ratecalc = 0.02 * ((4-1)*0.1+1)* ((4-1)*0.6+1)* ((1.1-1)*0.9+1)
        self.assertEqual(mdl.fxns['Human'].components['look'].failrate, ratecalc)
    def test_save_load_nominal(self):
        for extension in [".pkl",".csv",".json"]:
            self.check_save_load_onerun(self.mdl, "tank_mdlhist"+extension, "tank_endclass"+extension, 'nominal')
    def test_save_load_onefault(self):
        for extension in [".pkl",".csv",".json"]:
            self.check_save_load_onerun(self.mdl, "tank_mdlhist"+extension, "tank_endclass"+extension, 'one_fault', faultscen=('Import_Water', 'Stuck', 5))
    def test_save_load_multfault(self):
        for extension in [".pkl",".csv",".json"]:
            faultscen = {5:{"Import_Water": ['Stuck']},10:{"Store_Water":["Leak"]}}
            self.check_save_load_onerun(self.mdl, "tank_mdlhist"+extension, "tank_endclass"+extension, 'mult_fault', faultscen =faultscen )
    def test_save_load_singlefaults(self):
        self.check_save_load_approach(self.mdl, "tank_mdlhists.pkl", "tank_endclasses.pkl", 'single_faults')
        self.check_save_load_approach(self.mdl, "tank_mdlhists.csv", "tank_endclasses.csv", 'single_faults')
        self.check_save_load_approach(self.mdl, "tank_mdlhists.json", "tank_endclasses.json", 'single_faults')
    def test_save_load_singlefaults_indiv(self):
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "pkl", 'single_faults')
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "csv", 'single_faults')
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "json", 'single_faults')
    def test_save_load_nominalapproach(self):
        app = NominalApproach()
        app.add_seed_replicates("replicates", 10)
        self.check_save_load_approach(self.mdl, "tank_mdlhists.pkl", "tank_endclasses.pkl", 'nominal_approach', app=app)
        self.check_save_load_approach(self.mdl, "tank_mdlhists.csv", "tank_endclasses.csv", 'nominal_approach', app=app)
        self.check_save_load_approach(self.mdl, "tank_mdlhists.json", "tank_endclasses.json", 'nominal_approach', app=app)
    def test_save_load_nominalapproach_indiv(self):
        app = NominalApproach()
        app.add_seed_replicates("replicates", 10)
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "pkl", 'nominal_approach', app=app)
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "csv", 'nominal_approach', app=app)
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "json", 'nominal_approach', app=app)
    def test_save_load_nestedapproach(self):
        app = NominalApproach()
        app.add_seed_replicates("replicates", 10)
        self.check_save_load_approach(self.mdl, "tank_mdlhists.pkl", "tank_endclasses.pkl", 'nested_approach', app=app)
        self.check_save_load_approach(self.mdl, "tank_mdlhists.csv", "tank_endclasses.csv", 'nested_approach', app=app)
        self.check_save_load_approach(self.mdl, "tank_mdlhists.json", "tank_endclasses.json", 'nested_approach', app=app)
    def test_save_load_nestedapproach_indiv(self):
        app = NominalApproach()
        app.add_seed_replicates("replicates", 10)
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "pkl", 'nested_approach', app=app)
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "csv", 'nested_approach', app=app)
        self.check_save_load_approach_indiv(self.mdl, "tank_mdlhists", "tank_endclasses", "json", 'nested_approach', app=app)
    def test_save_load_approach(self):
        app = SampleApproach(self.mdl)
        self.check_save_load_approach(self.mdl,"tank_mdlhists.pkl", "tank_endclasses.pkl", 'approach', app=app)
        self.check_save_load_approach(self.mdl,"tank_mdlhists.csv", "tank_endclasses.csv", 'approach', app=app)
        self.check_save_load_approach(self.mdl,"tank_mdlhists.json", "tank_endclasses.json", 'approach', app=app)
    def test_save_load_approach_indiv(self):
        app = SampleApproach(self.mdl)
        self.check_save_load_approach_indiv(self.mdl,"tank_mdlhists", "tank_endclasses", "pkl", 'approach', app=app)
        self.check_save_load_approach_indiv(self.mdl,"tank_mdlhists", "tank_endclasses", "csv", 'approach', app=app)
        self.check_save_load_approach_indiv(self.mdl,"tank_mdlhists", "tank_endclasses", "json", 'approach', app=app)

if __name__ == '__main__':
    
    #suite = unittest.TestSuite()
    #suite.addTest(TankTests("test_local_tstep"))
    #runner = unittest.TextTestRunner()
    #runner.run(suite)
    
    #suite = unittest.TestSuite()
    #suite.addTest(TankTests("test_save_load_approach"))
    #runner = unittest.TextTestRunner()
    #runner.run(suite)
    
    suite = unittest.TestSuite()
    suite.addTest(TankTests("test_same_rcost"))
    runner = unittest.TextTestRunner()
    runner.run(suite)
    
    #unittest.main()
    
    #mdl = Tank()
    #scen = {'Human': 'NotDetected'}
    #propagate.propagate(mdl,scen,1)    