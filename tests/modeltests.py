# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

"""
modeltests.py

Created by Shawn Douglas on 2011-06-28.

"""

import sys
sys.path.insert(0, '.')

import tests.cadnanoguitestcase
from tests.cadnanoguitestcase import CadnanoGuiTestCase
import time
from model.virtualhelix import VirtualHelix
from model.enum import StrandType


class ModelTests(CadnanoGuiTestCase):
    """
    Create new tests by adding methods to this class that begin with "test".
    See for more detail: http://docs.python.org/library/unittest.html

    Run model tests by calling "python -m tests.modeltests" from cadnano2 root
    directory.
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        """
        CadnanoGuiTestCase.setUp(self)
        # Add extra model-test-specific initialization here

    def tearDown(self):
        """
        The tearDown method is called at the end of running each test,
        generally used to clean up any objects created in setUp
        """
        CadnanoGuiTestCase.tearDown(self)
        # Add model-test-specific cleanup here

    def testFractionalClearStrandCommand(self):
        """
        The new API for clearStrand allows fractional values for
        base indices (see docs/virtualhelix.pdf). This tets them.
        """
        vh = VirtualHelix(numBases=8, idnum=0)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_')

        vh.connectStrand(StrandType.Scaffold, 2, 6)
        vh.connectStrand(StrandType.Staple, 0, 7)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,> <,> <,> <,_ _,_\n0 Staple:   _,> <,> <,> <,> <,> <,> <,> <,_')

        vh.clearStrand(StrandType.Scaffold, 4, 4)
        vh.clearStrand(StrandType.Staple, 3, 5)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,> <,> <,> <,_ _,_\n0 Staple:   _,> <,> <,_ _,_ _,_ _,> <,> <,_')

        vh.undoStack().undo()
        vh.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,> <,> <,> <,_ _,_\n0 Staple:   _,> <,> <,> <,> <,> <,> <,> <,_')

        vh.undoStack().undo()
        
    def testVH(self):
        """
        Perform the VirtualHelix tutorial and make sure that the
        expected changes occur to the sample VirtualHelix
        """
        vh = VirtualHelix(numBases=8, idnum=0)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_')

        vh.connectStrand(StrandType.Scaffold, 2, 6)
        vh.connectStrand(StrandType.Staple, 0, 7)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,> <,> <,> <,_ _,_\n0 Staple:   _,> <,> <,> <,> <,> <,> <,> <,_')

        vh.clearStrand(StrandType.Scaffold, 3.5, 4.5)
        vh.clearStrand(StrandType.Staple, 2.5, 5.5)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,_ _,> <,> <,_ _,_\n0 Staple:   _,> <,> <,_ _,_ _,_ _,> <,> <,_')

        vh1 = VirtualHelix(numBases=5, idnum=1)
        vh1.connectStrand(StrandType.Staple, 0, 4)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,_ _,> <,> <,_ _,_\n0 Staple:   _,> <,> <,_ _,_ _,_ _,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,> <,> <,> <,> <,_')

        vh.installXoverFrom3To5(StrandType.Staple, 2, vh1, 2)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,_ _,> <,> <,_ _,_\n0 Staple:   _,> <,_ 1:2,> <,_ _,_ _,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,> <,_ 0:2,> <,> <,_')

        vh.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,_ _,> <,> <,_ _,_\n0 Staple:   _,> <,> <,_ _,_ _,_ _,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,> <,> <,> <,> <,_')

        vh1.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,_ _,> <,> <,_ _,_\n0 Staple:   _,> <,> <,_ _,_ _,_ _,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_')

        vh.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,_ _,> <,> <,_ _,_\n0 Staple:   _,> <,> <,> <,> <,> <,> <,> <,_')

        vh.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,> <,> <,> <,_ _,_\n0 Staple:   _,> <,> <,> <,> <,> <,> <,> <,_')

        vh.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,> <,> <,> <,_ _,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_')

        vh.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_')

        vh.connectStrand(StrandType.Scaffold, 2, 4)
        vh.connectStrand(StrandType.Scaffold, 0, 7)
        vh.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,> <,> <,_ _,_ _,_ _,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_')
    
    def testClearCrossovers(self):
        vh = VirtualHelix(numBases=8, idnum=0)
        vh.connectStrand(StrandType.Staple, 0, 7)
        vh1 = VirtualHelix(numBases=5, idnum=1)
        vh1.connectStrand(StrandType.Staple, 0, 5)
        vh1.installXoverFrom3To5(StrandType.Staple, 3, vh, 2)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,> <,> <,1:3 _,> <,> <,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,> <,> <,> <,0:2 _,_')
        vh1.clearStrand(StrandType.Staple, 0, 5)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,> <,> <,_ _,> <,> <,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_')
        vh1.undoStack().undo()
        vh1.undoStack().undo()
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,> <,> <,> <,> <,> <,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,> <,> <,> <,> <,_')
        vh.installXoverFrom3To5(StrandType.Staple, 2, vh1, 3)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,> <,_ 1:3,> <,> <,> <,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,> <,> <,_ 0:2,> <,_')
        vh1.clearStrand(StrandType.Staple, 0, 5)
        self.assertEqual(repr(vh), '0 Scaffold: _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,> <,_ _,> <,> <,> <,> <,> <,_')
        self.assertEqual(repr(vh1), '1 Scaffold: _,_ _,_ _,_ _,_ _,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_')
        

if __name__ == '__main__':
    print "Running Model Tests"
    tests.cadnanoguitestcase.main()
