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
functionaltests.py

Created by Shawn Douglas on 2011-06-28.
"""

import sys
sys.path.insert(0, '.')

import time
from PyQt4.QtCore import Qt, QPoint
from controllers.documentcontroller import DocumentController
from data.dnasequences import sequences
from model.enum import StrandType
from model.virtualhelix import VirtualHelix
from model.decoder import decode
import tests.cadnanoguitestcase
from tests.cadnanoguitestcase import CadnanoGuiTestCase


class FunctionalTests(CadnanoGuiTestCase):
    """
    Functional tests are end-to-end tests that simulate user interaction
    with the interface and verify that the final outputs (e.g. staple
    sequences) are correct.

    Run these tests by calling "python -m tests.functionaltests" from cadnano2
    root directory.
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        """
        CadnanoGuiTestCase.setUp(self)
        # Add extra initialization here

    def tearDown(self):
        """
        The tearDown method is called at the end of running each test,
        generally used to clean up any objects created in setUp
        """
        CadnanoGuiTestCase.tearDown(self)
        # Add functional-test-specific cleanup here

    def getTestSequences(self, designname, sequencesToApply):
        """
        Called by a sequence-verification functional test to read in a file
        (designname), apply scaffold sequence(s) to that design, and return
        the set of staple sequences."""
        # set up the document
        inputfile = "tests/functionaltestinputs/%s" % designname
        document = decode(file(inputfile).read())
        self.documentController = DocumentController(document, inputfile)
        self.setWidget(self.documentController.win, False, None)
        # apply one or more sequences to the design
        for sequenceName, startVHelixNum, startIndex in sequencesToApply:
            sequence = sequences.get(sequenceName, None)
            vh = self.app.v[startVHelixNum]
            vh.applySequenceAt(StrandType.Scaffold, startIndex, sequence)
        part = self.documentController.activePart()
        generatedSequences = part.getStapleSequences()
        return set(generatedSequences.splitlines())

    def getRefSequences(self, designname):
        """docstring for getRefSequences"""
        staplefile = "tests/functionaltestinputs/%s" % designname
        with open(staplefile, 'rU') as f:
            readSequences = f.read()
        return set(readSequences.splitlines())

    ####################### Staple Comparison Tests ########################
    def testStapleOutput_simple42(self):
         """
         Test applying M13mp18 sequence to a 42-base scaffold and perfectly
         complementary 42-base staple.

         This is the original template end-to-end functional test for correct
         staple sequence generation.

         The convention for making staple sequence tests is to put two files
         in the tests/functionaltestinputs directory: a cadnano source file 
         (json, or nno), and a csv file with the correct staple output.

         The test should first get a test set of staples by calling
         getTestSequences with a designname and sequencesToApply
         (a list of tuples with sequence name and position where the sequence
         should be applied).

         Then we finish by reading in the reference staple set and comparing
         it to the generated set.
         """
         designname = "simple42.nno"
         refname = "simple42.csv"
         sequences = [("M13mp18", 0, 0)]  # list of (sequencename, vhnum, index)
         testSet = self.getTestSequences(designname, sequences)
         refSet = self.getRefSequences(refname)
         self.assertEqual(testSet, refSet)

    def testStapleOutput_simple42legacy(self):
        """
        Same as simple42, but the source file is in cadnano1 json format.
        """
        designname = "simple42legacy.json"
        refname = "simple42legacy.csv"
        sequences = [("p7308", 0, 0)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_loop_size_1(self):
        """Test sequence output with a single loop of size 1."""
        designname = "loop_size_1.json"
        refname = "loop_size_1.csv"
        sequences = [("M13mp18", 0, 14)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_skip(self):
        """Simple design with a single skip."""
        designname = "skip.json"
        refname = "skip.csv"
        sequences = [("M13mp18", 0, 14)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_loops_and_skips(self):
        """Loop and skip stress test."""
        designname = "loops_and_skips.json"
        refname = "loops_and_skips.csv"
        sequences = [("M13mp18", 0, 0)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_Nature09_monolith(self):
        designname = "Nature09_monolith.json"
        refname = "Nature09_monolith.csv"
        sequences = [("p7560", 4, 73)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_Nature09_squarenut(self):
        designname = "Nature09_squarenut.json"
        refname = "Nature09_squarenut.csv"
        sequences = [("p7560", 15, 100)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_Science09_prot120_98_v3(self):
        designname = "Science09_prot120_98_v3.json"
        refname = "Science09_prot120_98_v3.csv"
        sequences = [("p7704", 0, 105)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_Science09_beachball_v1(self):
        designname = "Science09_beachball_v1.nno"
        refname = "Science09_beachball_v1.csv"
        sequences = [("p7308", 10, 221)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    def testStapleOutput_Science09_beachball_v1_json(self):
        designname = "Science09_beachball_v1.json"
        refname = "Science09_beachball_v1.csv"
        sequences = [("p7308", 10, 221)]
        testSet = self.getTestSequences(designname, sequences)
        refSet = self.getRefSequences(refname)
        self.assertEqual(testSet, refSet)

    ####################### Standard Functional Tests ########################
    def testActiveSliceHandleAltShiftClick(self):
        # Create a new Honeycomb part
        newHoneycombPartButton = self.mainWindow.topToolBar.widgetForAction(\
                                       self.mainWindow.actionNewHoneycombPart)
        self.click(newHoneycombPartButton)
        # Click each SliceHelix
        sliceGraphicsItem = self.documentController.sliceGraphicsItem
        slicehelix1 = sliceGraphicsItem.getSliceHelixByCoord(0, 0)
        slicehelix2 = sliceGraphicsItem.getSliceHelixByCoord(0, 1)
        self.click(slicehelix1, qgraphicsscene=self.mainWindow.slicescene)
        self.click(slicehelix2, qgraphicsscene=self.mainWindow.slicescene)
        # Click the activeSliceHandle with ALT and SHIFT modifiers
        pathHelixGroup = self.documentController.pathHelixGroup
        activeSliceHandle = pathHelixGroup.activeSliceHandle()
        self.mousePress(activeSliceHandle,\
                        modifiers=Qt.AltModifier|Qt.ShiftModifier,\
                        qgraphicsscene=self.mainWindow.pathscene)
        # Check the model for correctness
        vh0 = self.app.v[0]
        vh1 = self.app.v[1]
        str0 = "0 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
        str1 = "1 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
        self.assertEqual(repr(vh0), str0)
        self.assertEqual(repr(vh1), str1)

    def testEndpointAltClick(self):
        # Create a new Honeycomb part
        newHoneycombPartButton = self.mainWindow.topToolBar.widgetForAction(\
                                       self.mainWindow.actionNewHoneycombPart)
        self.click(newHoneycombPartButton)
        # Click each SliceHelix
        sliceGraphicsItem = self.documentController.sliceGraphicsItem
        slicehelix1 = sliceGraphicsItem.getSliceHelixByCoord(0, 0)
        slicehelix2 = sliceGraphicsItem.getSliceHelixByCoord(0, 1)
        self.mousePress(slicehelix1, qgraphicsscene=self.mainWindow.slicescene)
        self.mousePress(slicehelix2, qgraphicsscene=self.mainWindow.slicescene)
        # Click the path helices with the ALT modifier
        pathHelixGroup = self.documentController.pathHelixGroup
        ph0 = pathHelixGroup.getPathHelix(0)
        ph1 = pathHelixGroup.getPathHelix(1)
        self.mousePress(ph0, position=QPoint(410, 10),\
                        modifiers=Qt.AltModifier,\
                        qgraphicsscene=self.mainWindow.pathscene)
        self.mousePress(ph0, position=QPoint(450, 10),\
                        modifiers=Qt.AltModifier,\
                        qgraphicsscene=self.mainWindow.pathscene)
        self.mousePress(ph1, position=QPoint(410, 30),\
                        modifiers=Qt.AltModifier,\
                        qgraphicsscene=self.mainWindow.pathscene)
        self.mousePress(ph1, position=QPoint(450, 30),\
                        modifiers=Qt.AltModifier,\
                        qgraphicsscene=self.mainWindow.pathscene)
        # Check the model for correctness
        vh0 = self.app.v[0]
        vh1 = self.app.v[1]
        str0 = "0 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
        str1 = "1 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
        self.assertEqual(repr(vh0), str0)
        self.assertEqual(repr(vh1), str1)
        # self.debugHere()  # Stop simulation and give control to user


if __name__ == '__main__':
    print "Running Functional Tests"
    tests.cadnanoguitestcase.main()
