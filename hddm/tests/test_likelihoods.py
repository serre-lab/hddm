import numpy as np
from numpy.random import rand

import unittest

import pymc as pm

import hddm
from hddm.likelihoods import *
from hddm.generate import *
from scipy.integrate import *

from nose import SkipTest

class TestGPU(unittest.TestCase):
    def runTest(self):
        pass
        #self.setUp()
    
    def setUp(self, size=20):
        try:
            import wfpt_gpu
            import pycuda.driver as cuda
            import pycuda
        except ImportError:
            raise SkipTest("Could not import pycuda, skipping tests for GPU version of wfpt.")

        pycuda.tools.mark_cuda_test(wfpt_gpu.pdf_func_complete)
        x = np.random.rand(size)+.5
        x32 = x.astype(np.float32)
        
        self.params_single = {'x':1., 'a': 2., 'z': .5, 't':.3, 'v':.5}
        self.params_multi32 = {'x':x32, 'a': 2., 'z': .5, 't':.3, 'v':.5}
        self.params_multi = {'x':x, 'a': 2., 'z': .5, 't':.3, 'v':.5}
        self.params_multi_multi = self.create_params(x32)

    def create_params(self, x):
        params = {'x':x,
                  'a': np.ones_like(x)*2,
                  'z': np.ones_like(x)*1,
                  't':np.ones_like(x)*.3,
                  'v':np.ones_like(x)*.5}

        return params

    def test_GPU(self):
        logp = hddm.likelihoods.wiener_like_gpu(value=self.params_multi_multi['x'],
                               a=self.params_multi_multi['a'],
                               z=self.params_multi_multi['z'],
                               v=self.params_multi_multi['v'],
                               t=self.params_multi_multi['t'], debug=True)
        logp_single = hddm.likelihoods.wiener_like_gpu_single(value=self.params_multi32['x'],
                                       a=self.params_multi32['a'],
                                       z=self.params_multi32['z'],
                                       v=self.params_multi32['v'],
                                       t=self.params_multi32['t'], debug=True)

        np.testing.assert_array_almost_equal(logp, logp_single, 4)

    def test_GPU_direct(self):
        out = np.empty_like(self.params_multi_multi['x'])
        wfpt_gpu.pdf_func_complete(cuda.In(-(self.params_multi_multi['x']-self.params_multi_multi['t'])),
                                   cuda.In(self.params_multi_multi['a']),
                                   cuda.In(self.params_multi_multi['z']),
                                   cuda.In(self.params_multi_multi['v']),
                                   np.float32(0.0001), np.int16(1), cuda.Out(out),
                                   block = (self.params_multi_multi['x'].shape[0], 1, 1))

        probs = hddm.wfpt.pdf_array(-self.params_multi['x'],
                               self.params_multi['v'],
                               self.params_multi['a'],
                               self.params_multi['z'],
                               self.params_multi['t'],
                               0.0001, 1)


        np.testing.assert_array_almost_equal(out,probs,4)

    def test_simple(self):
        logp = hddm.likelihoods.wiener_like_simple(value=self.params_multi['x'],
                                  a=self.params_multi['a'],
                                  z=self.params_multi['z'],
                                  v=self.params_multi['v'],
                                  t=self.params_multi['t'])

        #t=timeit.Timer("""wiener_like_simple(value=-self.params_multi['x'], a=self.params_multi['a'], z=self.params_multi['z'], v=self.params_multi['v'], ter=self.params_multi['ter'])""", setup="from ddm_likelihood import *")
        #print t.timeit()

        logp_gpu = hddm.likelihoods.wiener_like_gpu(value=self.params_multi_multi['x'],
                               a=self.params_multi_multi['a'],
                               z=self.params_multi_multi['z'],
                               v=self.params_multi_multi['v'],
                               t=self.params_multi_multi['t'])

        self.assertAlmostEqual(np.float32(logp), logp_gpu, 4)

    def test_gpu_global(self):
        logp_gpu_global = hddm.likelihoods.wiener_like_gpu_global(value=self.params_multi_multi['x'],
                                                 a=self.params_multi_multi['a'],
                                                 z=self.params_multi_multi['z'],
                                                 v=self.params_multi_multi['v'],
                                                 t=self.params_multi_multi['t'], debug=True)

        logp_cpu = hddm.likelihoods.wiener_like_cpu(value=self.params_multi_multi['x'],
                                   a=self.params_multi_multi['a'],
                                   z=self.params_multi_multi['z'],
                                   v=self.params_multi_multi['v'],
                                   t=self.params_multi_multi['t'], debug=True)

        np.testing.assert_array_almost_equal(logp_cpu, logp_gpu_global, 4)

        free_gpu()
        
    def benchmark(self):
        logp_gpu = hddm.likelihoods.wiener_like_gpu(value=-self.params_multi_multi['x'],
                                   a=self.params_multi_multi['a'],
                                   z=self.params_multi_multi['z'],
                                   v=self.params_multi_multi['v'],
                                   t=self.params_multi_multi['t'], debug=True)

        logp_gpu_opt = hddm.likelihoods.wiener_like_gpu_opt(value=-self.params_multi_multi['x'],
                                   a=self.params_multi_multi['a'],
                                   z=self.params_multi_multi['z'],
                                   v=self.params_multi_multi['v'],
                                   t=self.params_multi_multi['t'], debug=True)

        logp_cpu = hddm.likelihoods.wiener_like_cpu(value=-self.params_multi_multi['x'],
                                   a=self.params_multi_multi['a'],
                                   z=self.params_multi_multi['z'],
                                   v=self.params_multi_multi['v'],
                                   t=self.params_multi_multi['t'], debug=True)

        #np.testing.assert_array_almost_equal(logp_cpu, logp_gpu, 4)

        #print logp_cpu, logp_gpu

    def benchmark_global(self):
        logp_gpu_global = hddm.likelihoods.wiener_like_gpu_global(value=-self.params_multi_multi['x'],
                                                 a=self.params_multi_multi['a'],
                                                 z=self.params_multi_multi['z'],
                                                 v=self.params_multi_multi['v'],
                                                 t=self.params_multi_multi['t'], debug=False)

        logp_cpu = hddm.likelihoods.wiener_like_cpu(value=-self.params_multi_multi['x'],
                                   a=self.params_multi_multi['a'],
                                   z=self.params_multi_multi['z'],
                                   v=self.params_multi_multi['v'],
                                   t=self.params_multi_multi['t'], debug=False)


    def benchmark_cpu(self):
        logp_cpu = hddm.likelihoods.wiener_like_cpu(value=-self.params_multi_multi['x'],
                                                    a=self.params_multi_multi['a'],
                                                    z=self.params_multi_multi['z'],
                                                    v=self.params_multi_multi['v'],
                                                    t=self.params_multi_multi['t'], debug=True)

def benchmark(size=100, reps=2000):
    import cProfile
    import pstats
#    cProfile.run('import hddm_test; bench = hddm_test.TestLikelihoodFuncs(); bench.setUp(size=%i); [bench.benchmark() for i in range(%i)]'%(size, reps), 'benchmark')
#    p = pstats.Stats('benchmark')
#    p.print_stats('wiener_like')

    cProfile.run('import test_likelihoods; bench = hddm_test.TestLikelihoodFuncs(); bench.setUp(size=%i); [bench.benchmark_global() for i in range(%i)]'%(size, reps), 'benchmark')
    p = pstats.Stats('benchmark')
    p.print_stats('wiener_like')
    free_gpu()

    return p


class TestWfpt(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestWfpt, self).__init__(*args, **kwargs)
        self.bins=50
        self.range_=(-4,4)
        self.samples=5000
        self.x = np.linspace(self.range_[0], self.range_[1], self.bins)
       
    def runTest(self):
        pass

    def test_pdf(self):
        """Test if our wfpt pdf implementation yields the same results as the reference implementation by Navarro & Fuss 2009"""
        try:
            import mlabwrap
        except ImportError:
            print "Could not import mlabwrap, not performing pdf comparison test."
            return

        for i in range(500):
            v = (rand()-.5)*1.5
            t = rand()*.5
            a = 1.5+rand()
            z = .5*rand()
            z_nonorm = a*z
            rt = rand()*4 + t
            err = 10*(-3- ceil(rand()*20))
            # Test if equal up to the 9th decimal.
            matlab_wfpt = mlabwrap.mlab.wfpt(rt, v, a, z_nonorm, err)[0][0]
            python_wfpt = hddm.wfpt.pdf(rt, v, a, z, err)
            print v,t,a,z,z_nonorm,rt,err, matlab_wfpt, python_wfpt
            np.testing.assert_array_almost_equal(matlab_wfpt, python_wfpt, 9)
            
    def test_simple_array(self):
        params_novar = {}
        params_novar['v'] = (rand()-.5)*1.5
        params_novar['t'] = rand()*.5
        params_novar['a'] = 1.5+rand()
        params_novar['z'] = .5
        params_novar['V'] = 0
        params_novar['T'] = 0
        params_novar['Z'] = 0
        samples_novar = hddm.generate.gen_rts(params_novar, samples=self.samples)
        simulated_pdf = hddm.utils.histogram(samples_novar, bins=self.bins, range=self.range_, density=True)[0]

        analytical_pdf = hddm.wfpt.pdf_array(self.x,
                                             params_novar['v'],
                                             params_novar['a'],
                                             params_novar['z'],
                                             params_novar['t'],
                                             err=0.0001, logp=0)

        diff = np.mean(abs(simulated_pdf - analytical_pdf))
        print 'mean err: %f' % diff
        print 'max err: %f' % np.max(abs(simulated_pdf - analytical_pdf))
        # Test if there are no systematic deviations
        self.assertTrue(diff < 0.03)
        #it's very problematic to test agreement between bins
        #np.testing.assert_array_almost_equal(simulated_pdf, analytical_pdf, 1)

    def test_simple_summed_logp(self):
        v = (rand()-.5)*1.5
        t = rand()*.5
        a = 1.5+rand()
        z = .5

        # Test for if sum is the same

        # Generate random valid RTs
        rts = t + rand(5000)*2
        p = [hddm.wfpt.pdf_sign(rt, v, a, z, t, 1e-4) for rt in rts]
        summed_logp = np.sum(np.log(p))

        self.assertTrue(summed_logp == hddm.wfpt.wiener_like_simple(np.array(rts), v, a, z, t, 1e-4)), "Summed logp does not match"

        self.assertTrue(-np.Inf == hddm.wfpt.wiener_like_simple(np.array([1.,2.,3.,0.]), v, a, z, t+.1, 1e-4)), "wiener_like_simple should have returned -np.Inf"
        
            
        
    def test_full_mc_simulated(self):
        """Test for systematic deviations in full_mc by comparing to simulated pdf distribution.
        """
        params = {}
        params['v'] = (rand()-.5)*1.5
        params['t'] = rand()*.5
        params['a'] = 1.5+rand()
        params['z'] = .5
        params['V'] = rand()
        params['T'] = rand()*(params['t']/2.)
        params['Z'] = rand()*(params['z']/2.)
        samples = hddm.generate.gen_rts(params, samples=self.samples)
        empirical_pdf = hddm.utils.histogram(samples, bins=self.bins, range=self.range_, density=True)[0]
        
        analytical_pdf = hddm.wfpt_full.wiener_like_full_mc(self.x,
                                                       params['v'],
                                                       params['V'],
                                                       params['z'],
                                                       params['Z'],
                                                       params['t'],
                                                       params['T'],
                                                       params['a'],
                                                       reps=1000,
                                                       err=0.0001, logp=0)

        # TODO: Normalize according to integral
        diff = np.mean(np.abs(empirical_pdf - analytical_pdf))
        print diff
        # Test if there are no systematic deviations
        self.assertTrue(diff < 0.03)
        #np.testing.assert_array_almost_equal(empirical_pdf, analytical_pdf, 1)


    def test_full_mc(self):
        """"""
        values = np.array([0.3, 0.4, 0.6, 1])
        print "testing %d data points" % (len(values))
    
        v=1; V=0.1; z=0.5; Z=0.1; t=0.3; T=0.1; a=1.5
        #true values obtained by numerical integration
        true_vals = np.log(np.array([0.019925699375943847,
                           1.0586617338544908,
                           1.2906014938998163,
                           0.446972173706388]))
        
        y = np.empty(len(values), dtype=float)
        for i in xrange(len(values)):
            print values[i:i+1]
            y[i] = sum(hddm.wfpt_full.wiener_like_full_mc(values[i:i+1], v, V, z, Z, t, T, a, err=.0001,
                                                            reps=1000000,logp=1))
        np.testing.assert_array_almost_equal(true_vals, y, 2)
            
    def test_pdf_V(self):
        """Test if our wfpt pdf_V implementation yields the right results"""       
        func = lambda v_i,value,err,v,V,z,a: hddm.wfpt.pdf(value, v_i, a, z, err) *norm.pdf(v_i,v,V)

        for i in range(50):
            V = rand()*0.4+0.1
            v = (rand()-.5)*4
            t = rand()*.5
            a = 1.5+rand()
            z = .5*rand()
            rt = rand()*4 + t
            err = 10**(-3- np.ceil(rand()*12))
            # Test if equal up to the 9th decimal.
            res =  quad(func, -np.inf,np.inf,args = (rt,err,v,V,z,a), epsrel=1e-10, epsabs=1e-10)[0]
            np.testing.assert_array_almost_equal(hddm.wfpt_full.pdf_V(rt, v=v, V=V, a=a, z=z, err=err), res)

class TestWfptFull(unittest.TestCase):


    def test_adaptive(self):
          
        for i in range(200):
            V = rand()*0.4+0.1
            v = (rand()-.5)*4            
            T = rand()*0.3
            t = rand()*.5+(T/2)
            a = 1.5+rand()          
            rt = (rand()*4 + t) * np.sign(rand())
            err = 10**-9
            Z = rand()*0.3
            z = .5*rand()+Z/2  
            logp = 0#np.floor(rand()*2)
            nZ = 60
            nT = 60

            my_res = hddm.wfpt_full.full_pdf(rt,v=v,V=0,a=a,z=z,Z=0,t=t, T=T,err=err, nT=5, nZ=5, use_adaptive=1)
            res = hddm.wfpt_full.full_pdf(rt,v=v,V=0,a=a,z=z,Z=0,t=t, T=T,err=err, nT=nT, nZ=nZ, use_adaptive=0)
            
            print "(%d) rt %f, v: %f, V: %f, z: %f, Z: %f, t: %f, T: %f a: %f" % (i,rt,v,V,z,Z,t,T,a)
            print my_res
            print res
            if np.isinf(my_res):
                my_res = 100
            if np.isinf(res):
                res = 100            
            self.assertTrue(not np.isnan(my_res)), "Found NaN in the results"
            self.assertTrue(not np.isnan(res)), "Found NaN in the simulated results"                                                                                    
            np.testing.assert_array_almost_equal(my_res, res,6)

    
    def test_full_pdf(self):
        for i in range(200):
            V = rand()*0.4+0.1
            v = (rand()-.5)*4            
            T = rand()*0.3
            t = rand()*.5+(T/2)
            a = 1.5+rand()          
            rt = (rand()*4 + t) * np.sign(rand())
            err = 10**-8
            Z = rand()*0.3
            z = .5*rand()+Z/2  
            nZ = 60 
            nT = 60 

            my_res = np.zeros(8)
            res = np.zeros(8)
            y_z = np.zeros(nZ+1);
            y_t = np.zeros(nT+1)
            
            for vvv in range(2):
                #test pdf
                my_res[0+vvv*4] = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z,Z=0,t=t, T=0,err=err, nT=nT, nZ=nZ)
                res[0+vvv*4]    = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z,Z=0,t=t, T=0,err=err, nT=0, nZ=0)
                
                #test pdf + Z
                my_res[1+vvv*4] = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z,Z=Z,t=t, T=0,err=err, nT=nT, nZ=nZ)
                hZ = Z/nZ
                for j in range(nZ+1):
                    z_tag = z-Z/2. + hZ*j
                    y_z[j] = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z_tag,Z=0,t=t, T=0,err=err, nT=0, nZ=0)/Z                             
                    res[1+vvv*4] = simps(y_z, x=None, dx=hZ)
                    
                #test pdf + T
                my_res[2+vvv*4] = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z,Z=0,t=t, T=T,err=err, nT=nT, nZ=nZ)
                hT = T/nT
                for j in range(nT+1):
                    t_tag = t-T/2. + hT*j
                    y_t[j] = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z,Z=0,t=t_tag, T=0,err=err, nT=0, nZ=0)/T      
                    res[2+vvv*4] = simps(y_t, x=None, dx=hT)
             
                #test pdf + Z + T
                my_res[3+vvv*4] = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z,Z=Z,t=t, T=T,err=err, nT=nT, nZ=nZ)
                hT = T/nT
                hZ = Z/nZ
                for j_t in range(nT+1):
                    t_tag = t-T/2. + hT*j_t
                    for j_z in range(nZ+1):
                        z_tag = z-Z/2. + hZ*j_z
                        y_z[j_z] = hddm.wfpt_full.full_pdf(rt,v=v,V=V*vvv,a=a,z=z_tag,Z=0,t=t_tag, T=0,err=err, nT=0, nZ=0)/Z/T    
                    y_t[j_t] = simps(y_z, x=None, dx=hZ)             
                    res[3+vvv*4] = simps(y_t, x=None, dx=hT)
                
            print "(%d) rt %f, v: %f, V: %f, z: %f, Z: %f, t: %f, T: %f a: %f" % (i,rt,v,V,z,Z,t,T,a)
            print my_res
            print res
            my_res[np.isinf(my_res)] = 100
            res[np.isinf(res)] = 100            
            self.assertTrue(not any(np.isnan(my_res))), "Found NaN in the results"
            self.assertTrue(not any(np.isnan(res))), "Found NaN in the simulated results"                                                                                    
            np.testing.assert_array_almost_equal(my_res, res,5)
            
        
    def test_failure_mode(self):
        
        rt = 0.6
        for i in range(2):
            rt = rt * -1
            v = 1
            V = 1
            a = 1.5
            z = 0.5
            Z = 0.2
            t = 0.2
            T = 0.1
            nT = 10; nZ =10
    
           
            z = 1.1
            self.assertTrue(hddm.wfpt_full.full_pdf(rt,v=v,V=V,a=a,z=z,Z=Z,t=t, T=T,err=1e-10, nT=10, nZ=10)==0)
            z = -0.1
            self.assertTrue(hddm.wfpt_full.full_pdf(rt,v=v,V=V,a=a,z=z,Z=Z,t=t, T=T,err=1e-10, nT=10, nZ=10)==0)
            z = 0.5
            
            z = 0.1
            Z = 0.25
            self.assertTrue(hddm.wfpt_full.full_pdf(rt,v=v,V=V,a=a,z=z,Z=Z,t=t, T=T,err=1e-10, nT=10, nZ=10)==0)
            z = 0.5
        
        
            a = -0.1
            self.assertTrue(hddm.wfpt_full.full_pdf(rt,v=v,V=V,a=a,z=z,Z=Z,t=t, T=T,err=1e-10, nT=10, nZ=10)==0)
            a = 1.5
            
            t = 0.7
            T = 0
            self.assertTrue(hddm.wfpt_full.full_pdf(rt,v=v,V=V,a=a,z=z,Z=Z,t=t, T=T,err=1e-10, nT=10, nZ=10)==0)            
            t = -0.3
            self.assertTrue(hddm.wfpt_full.full_pdf(rt,v=v,V=V,a=a,z=z,Z=Z,t=t, T=T,err=1e-10, nT=10, nZ=10)==0)          
            t = 0.1
            T = 0.3
            self.assertTrue(hddm.wfpt_full.full_pdf(rt,v=v,V=V,a=a,z=z,Z=Z,t=t, T=T,err=1e-10, nT=10, nZ=10)==0)
            t = 0.2
            T = 0.1

class TestLBA(unittest.TestCase):
    def runTest(self):
        pass
        #self.setUp()
    
    def setUp(self, size=200):
        self.x = np.random.rand(size)
        self.a = np.random.rand(1)+1
        self.z = np.random.rand(1)*self.a
        self.v = np.random.rand(2)+.5
        #self.v_multi = np.random.rand(5)
        self.V = np.random.rand(1)+.5

    def test_lba_single(self):
        try:
            import rpy2.robjects as robjects
            import rpy2.robjects.numpy2ri
            robjects.r.source('lba-math.r')
        except ImportError:
            raise SkipTest("rpy2 not installed, not testing against reference implementation.")

        like_cython = hddm.likelihoods.LBA_like(self.x, self.a, self.z, 0., self.V, self.v[0], self.v[1], logp=False)
        like_r = np.array(robjects.r.n1PDF(t=self.x, x0max=np.float(self.z), chi=np.float(self.a), drift=self.v, sdI=np.float(self.V)))
        np.testing.assert_array_almost_equal(like_cython, like_r,5)

    def call_cython(self):
        return hddm.lba.lba(self.x, self.z, self.a, self.V, self.v[0], self.v[1])

    def call_r(self):
        return np.array(robjects.r.n1PDF(t=self.x, x0max=np.float(self.z), chi=np.float(self.a), drift=self.v, sdI=np.float(self.V)))
        


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWfpt)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestLBA)
    unittest.TextTestRunner(verbosity=2).run(suite)
