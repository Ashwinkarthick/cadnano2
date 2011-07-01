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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import test.cadnanoguitestcase
from test.cadnanoguitestcase import CadnanoGuiTestCase
from model.enum import StrandType
from model.virtualhelix import VirtualHelix


class FunctionalTests(CadnanoGuiTestCase):
    """
    Functional tests are end-to-end tests that simulate user interaction
    with the interface and verify that the final outputs (e.g. staple
    sequences) are correct.

    Run these tests by calling "python -m test.functionaltests" from cadnano2
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

    def testMethod(self):
        # Create part
        partButton = self.mainWindow.topToolBar.widgetForAction(self.mainWindow.actionNewSquarePart)
        self.click(partButton)

        # Init refs
        sgi = self.documentController.sliceGraphicsItem
        phg = self.documentController.pathHelixGroup
        ash = self.documentController.pathHelixGroup.activeSliceHandle()

        # Playback user input
        self.mousePress(sgi.getSliceHelixByCoord(0, 0), position=QPoint(19, 13), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.slicescene)
        self.mouseMove(sgi.getSliceHelixByCoord(0, 0), position=QPoint(19, 14), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.slicescene)
        self.mouseRelease(sgi.getSliceHelixByCoord(0, 0), position=QPoint(19, 14), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.slicescene)
        self.mousePress(phg.getPathHelix(0), position=QPoint(630, 10), modifiers=Qt.AltModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseRelease(phg.getPathHelix(0), position=QPoint(630, 10), modifiers=Qt.AltModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mousePress(phg.getPathHelix(0), position=QPoint(889, 27), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(889, 30), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(873, 30), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(856, 30), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(829, 34), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(765, 37), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(714, 37), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(664, 37), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(630, 34), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(600, 30), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(576, 27), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(539, 24), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(495, 24), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(458, 24), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(431, 24), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(411, 24), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseMove(phg.getPathHelix(0), position=QPoint(394, 24), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)
        self.mouseRelease(phg.getPathHelix(0), position=QPoint(394, 24), modifiers=Qt.NoModifier, qgraphicsscene=self.mainWindow.pathscene)

        # Verify model for correctness
        refvh0 = """0 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"""
        self.assertEqual(refvh0, repr(self.app.v[0]))

if __name__ == '__main__':
    print "Running Functional Tests"
    test.cadnanoguitestcase.main()
