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
pathhelix.py
Created by Shawn on 2011-01-27.
"""

from exceptions import AttributeError, ValueError
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QLine, QRectF
from PyQt4.QtGui import QBrush
from PyQt4.QtGui import QGraphicsItem
from PyQt4.QtGui import QGraphicsSimpleTextItem
from PyQt4.QtGui import QPainter, QPainterPath
from PyQt4.QtGui import QPen, QDrag, QUndoCommand
import styles
from model.virtualhelix import VirtualHelix, StrandType, Parity
from handles.breakpointhandle import BreakpointHandle


class PathHelix(QGraphicsItem):
    """docstring for PathHelix"""
    minorGridPen = QPen(styles.minorgridstroke, styles.PATH_GRID_STROKE_WIDTH)
    majorGridPen = QPen(styles.majorgridstroke, styles.PATH_GRID_STROKE_WIDTH)
    scafPen = QPen(styles.scafstroke, styles.PATH_STRAND_STROKE_WIDTH)
    nobrush = QBrush(Qt.NoBrush)
    baseWidth = styles.PATH_BASE_WIDTH
    
    def __init__(self, vhelix, position, parent):
        super(PathHelix, self).__init__()
        self.vhelix = vhelix
        self.parent = parent
        self._scafBreaktHandles = []
        self._stapBreaktHandles = []
        self._scafCrossoverHandles = []
        self._stapCrossoverHandles = []
        self.scafLines = []
        self.setParity()
        self.setPos(position)
        self.minorGridPainterPath = self.getMinorGridPainterPath()
        self.majorGridPainterPath = self.getMajorGridPainterPath()
        self.rect = QRectF()
        self.updateRect()

    def updateRect(self):
        """Sets rect width to reflect number of bases in vhelix. Sets
        rect height to the width of two bases (one for scaffold and
        one for staple)"""
        canvasSize = self.vhelix.part().getCanvasSize()
        self.rect.setWidth(self.baseWidth*canvasSize)
        self.rect.setHeight(2*self.baseWidth)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        # Minor grid lines
        painter.setBrush(self.nobrush)
        painter.setPen(self.minorGridPen)
        painter.drawPath(self.minorGridPainterPath)
        # Major grid lines
        painter.setPen(self.majorGridPen)
        painter.drawPath(self.majorGridPainterPath)
        # Scaffold lines
        painter.setPen(self.scafPen)
        painter.drawLines(self.scafLines)
        

    def getMinorGridPainterPath(self):
        """
        Returns a QPainterPath object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        path = QPainterPath()
        canvasSize = self.vhelix.part().getCanvasSize()
        # border
        path.addRect(0,0,self.baseWidth*canvasSize, 2*self.baseWidth)
        # minor tick marks
        for i in range(canvasSize):
            if (i % 7 != 0):
                path.moveTo(self.baseWidth*i,0)
                path.lineTo(self.baseWidth*i,2*self.baseWidth)
        # staple-scaffold divider
        path.moveTo(0, self.baseWidth)
        path.lineTo(self.baseWidth*canvasSize, self.baseWidth)
        return path

    def getMajorGridPainterPath(self):
        """
        Returns a QPainterPath object for the major grid lines.
        This is separated from the minor grid lines so different
        pens can be used for each.
        """
        path = QPainterPath()
        canvasSize = self.vhelix.part().getCanvasSize()
        # major tick marks
        for i in range(0,canvasSize+1,7):
                path.moveTo(self.baseWidth*i,0)
                path.lineTo(self.baseWidth*i,2*self.baseWidth)
        return path

    def getScaffoldBreakHandles(self):
        """docstring for getScaffoldBreakHandles"""
        return self._scafBreaktHandles

    def getStapleBreakHandles(self):
        """docstring for getStapleBreakHandles"""
        return self._stapBreaktHandles

    def addScaffoldBreakHandle(self, bh):
        """docstring for addScaffoldBreakHandle"""
        # bh.setParentItem(self)
        self._scafBreaktHandles.append(bh)

    def addStapleBreakHandle(self, bh):
        """docstring for addStapleBreakHandle"""
        # bh.setParentItem(self)
        self._stapBreaktHandles.append(bh)

    def updateBreakBounds(self, strandType):
        """Sorts a list of all breakpoint and crossover handles, and then
        iterates over those handles and sets dragging boundaries for 
        breakpoint handles."""
        if strandType == StrandType.Scaffold:
            handles = sorted(self._scafBreaktHandles +\
                             self._scafCrossoverHandles,\
                             key=lambda handle: handle.baseIndex)
        elif strandType == StrandType.Staple:
            handles = sorted(self._stapBreaktHandles +\
                             self._stapCrossoverHandles,\
                             key=lambda handle: handle.baseIndex)
        else:
            raise AttributeError
        count = len(handles)
        if count == 0:
            return
        maxIndex = self.vhelix.part().getCanvasSize()-1
        if count == 1:
            handles[0].setDragBounds(0,maxIndex)
        else:
            handles[0].setDragBounds(0,handles[1].baseIndex-1)
            for i in range(len(handles[1:-1])):
                handles[i].setDragBounds(handles[i-1].baseIndex+1,\
                                         handles[i+1].baseIndex-1)
            handles[count-1].setDragBounds(handles[count-2].baseIndex+1,\
                                           maxIndex)
    # end def

    def setParity(self):
        """docstring for setParity"""
        if self.vhelix.number() % 2 == 0:
            self.parity = Parity.Even
        else:
            self.parity = Parity.Odd

    def getYoffset(self, strandType):
        """
        This function returns the appropriate Y offset according to the
        rule that even-parity staples and odd-parity scaffolds run in the
        negative-z direction and are drawn in the lower half of the
        path helix grid.
        """
        if (self.parity == Parity.Even and strandType == StrandType.Staple) or \
           (self.parity == Parity.Odd and strandType == StrandType.Scaffold):
            return self.baseWidth + (self.baseWidth >> 1)
        else:
            return self.baseWidth >> 1

    def redrawLines(self, strandType):
        """Draw horizontal lines where non-breakpoint, non-crossover strand
           is present"""
        endpoints = []
        if strandType == StrandType.Scaffold:
            handles = sorted(self._scafBreaktHandles +\
                             self._scafCrossoverHandles,\
                             key=lambda handle: handle.baseIndex)
        elif strandType == StrandType.Staple:
            handles = sorted(self._stapBreaktHandles +\
                             self._stapCrossoverHandles,\
                             key=lambda handle: handle.baseIndex)
        else:
            raise AttributeError
        count = len(handles)
        if count == 0:
            return
        if count % 2 == 1:
            raise ValueError  # should always be even
        else:
            for i in range(0, len(handles), 2):
                # collect endpoints
                endpoints.append([handles[i].baseIndex,\
                                  handles[i+1].baseIndex])

        self.scafLines = []  # get rid of old points
        y = self.getYoffset(strandType)  # determine y offset
        for [x1Index, x2Index] in endpoints:
            x1 = (x1Index * self.baseWidth) + (self.baseWidth >> 1)
            x2 = (x2Index * self.baseWidth) + (self.baseWidth >> 1)
            self.scafLines.append(QLine(x1,y,x2,y))  # create QLine list
        self.update(self.rect)

# end class
