"""Synthetic numerical unit checks, NOT original-paper data reproduction."""
import unittest
import numpy as np
from source_methods import fit_coding_direction,project_and_normalize,source_phase_line
class Tests(unittest.TestCase):
 def test_cd(self):
  left=np.zeros((2,4,3)); right=left.copy(); right[:,:,1]=2
  cd=fit_coding_direction(right,left,np.array([False,False,True,True]))
  np.testing.assert_array_equal(cd,[0,1,0]); np.testing.assert_array_equal(project_and_normalize(right,cd,0,2),np.ones((2,4)))
 def test_phase_units(self):
  x=np.arange(0,1.01,.1)[None,:]; out=source_phase_line(x,np.arange(0,1.01,.2),dt_ms=5)
  np.testing.assert_allclose(out['drift_per_10ms'][out['counts']>0],.2)
 def test_no_selectivity(self):
  x=np.zeros((2,4,3))
  with self.assertRaises(ValueError): fit_coding_direction(x,x,np.ones(4,bool))
if __name__=='__main__': unittest.main()
