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
from PyQt4.QtCore import QLine, QRectF, QPointF, QPoint
from PyQt4.QtGui import QBrush, QColor
from PyQt4.QtGui import QGraphicsItem
from PyQt4.QtGui import QGraphicsSimpleTextItem
from PyQt4.QtGui import QPainter, QPainterPath
from PyQt4.QtGui import QPen, QDrag, QUndoCommand, QPolygonF
import ui.styles as styles
from model.enum import EndType, LatticeType, StrandType
from model.virtualhelix import VirtualHelix
from weakref import ref
from handles.pathhelixhandle import PathHelixHandle
from handles.loophandle import LoopItem, SkipItem
from handles.precrossoverhandle import PreCrossoverHandle
from math import floor
from cadnano import app
from util import *
from itertools import product

baseWidth = styles.PATH_BASE_WIDTH
ppL5 = QPainterPath()  # Left 5' PainterPath
ppR5 = QPainterPath()  # Right 5' PainterPath
ppL3 = QPainterPath()  # Left 3' PainterPath
ppR3 = QPainterPath()  # Right 3' PainterPath
# set up ppL5 (left 5' blue square)
ppL5.addRect(0.25 * baseWidth, 0.125 * baseWidth,\
             0.75 * baseWidth, 0.75 * baseWidth)
# set up ppR5 (right 5' blue square)
ppR5.addRect(0, 0.125 * baseWidth,\
             0.75 * baseWidth, 0.75 * baseWidth)
# set up ppL3 (left 3' blue triangle)
l3poly = QPolygonF()
l3poly.append(QPointF(baseWidth, 0))
l3poly.append(QPointF(0.25 * baseWidth, 0.5 * baseWidth))
l3poly.append(QPointF(baseWidth, baseWidth))
ppL3.addPolygon(l3poly)
# set up ppR3 (right 3' blue triangle)
r3poly = QPolygonF()
r3poly.append(QPointF(0, 0))
r3poly.append(QPointF(0.75 * baseWidth, 0.5 * baseWidth))
r3poly.append(QPointF(0, baseWidth))
ppR3.addPolygon(r3poly)


class PathHelix(QGraphicsItem):
    """
    PathHelix is the primary "view" of the VirtualHelix data.
    It manages the ui interactions from the user, such as
    dragging breakpoints or crossovers addition/removal,
    and updates the data model accordingly.

    parent should be set to...
    """
    minorGridPen = QPen(styles.minorgridstroke, styles.MINOR_GRID_STROKE_WIDTH)
    minorGridPen.setCosmetic(True)
    majorGridPen = QPen(styles.majorgridstroke, styles.MAJOR_GRID_STROKE_WIDTH)
    majorGridPen.setCosmetic(True)
    
    scafPen = QPen(styles.scafstroke, 2)
    nobrush = QBrush(Qt.NoBrush)
    baseWidth = styles.PATH_BASE_WIDTH

    def __init__(self, vhelix, pathHelixGroup):
        super(PathHelix, self).__init__()
        self.setAcceptHoverEvents(True)  # for pathtools
        self._pathHelixGroup = pathHelixGroup
        self._scafBreakpointHandles = []
        self._stapBreakpointHandles = []
        self._scafXoverHandles = []
        self._stapXoverHandles = []
        self._preXOverHandles = None
        self._segmentPaths = None
        self._endptPaths = None
        self._loopPaths = None
        self._minorGridPainterPath = None
        self._majorGridPainterPath = None
        self.step = 21  # 32 for Square lattice
        self.setZValue(styles.ZPATHHELIX)
        self.rect = QRectF()
        self._vhelix = None
        self._handle = None
        self._mouseDownBase = None
        self._skipitem = SkipItem()
        self._loopitem = LoopItem()
        self.setVHelix(vhelix)
        if app().ph != None:  # Convenience for the command line -i mode
            app().ph[vhelix.number()] = self
    # end def

    def activeTool(self):
        return self.controller().activeTool()

    def controller(self):
        return self._pathHelixGroup.controller()

    def pathHelixGroup(self):
        return self._pathHelixGroup

    def vhelix(self):
        return self._vhelix
        
    def phgroup(self):
        return self._pathHelixGroup
    # end def

    def undoStack(self):
        return self.vhelix().undoStack()

    def setVHelix(self, newVH):
        if self._vhelix:
            self._vhelix.basesModified.disconnect(self.vhelixBasesModified)
            self._vhelix.vhelixDimensionsModified.disconnect(\
                                             self.vhelixDimensionsModified)
        self._vhelix = newVH
        newVH.basesModified.connect(self.vhelixBasesModified)
        newVH.dimensionsModified.connect(self.vhelixDimensionsModified)
        self.vhelixDimensionsModified()
        self.vhelixBasesModified()

    def handle(self):
        if self._handle:
            return self._handle
        self._handle = PathHelixHandle(self.vhelix(),parent=self._pathHelixGroup)
        return self._handle

    def number(self):
        return self._vhelix.number()

    def row(self):
        return self._vhelix.row()

    def col(self):
        return self._vhelix.col()

    def evenParity(self):
        return self._vhelix.evenParity()

    def vhelixDimensionsModified(self):
        """Sets rect width to reflect number of bases in vhelix. Sets
        rect height to the width of two bases (one for scaffold and
        one for staple)"""
        canvasSize = self._vhelix.part().numBases()
        self.prepareGeometryChange()
        self.rect.setWidth(self.baseWidth * canvasSize)
        self.rect.setHeight(2 * self.baseWidth)
        self._minorGridPainterPath = None
        self._majorGridPainterPath = None

    def boundingRect(self):
        return self.rect

    ################# Crossover Handles #################
    def preXOverHandlesVisible(self):
        return self._preXOverHandles!=None
    
    def setPreXOverHandlesVisible(self, shouldBeVisible):
        areVisible = self._preXOverHandles != None
        if areVisible and not shouldBeVisible:
            for pch in self._preXOverHandles:
                if pch.scene():
                    pch.scene().removeItem(pch)
            self._preXOverHandles = None
        elif not areVisible and shouldBeVisible:
            self._preXOverHandles = []
            for strandType, facingRight in product((StrandType.Scaffold, StrandType.Staple), (True, False)):
                # Get potential crossovers in [neighborVirtualHelix, index] format
                potentialXOvers = self.vhelix().potentialCrossoverList(facingRight, strandType)
                for (neighborVH, fromIdx) in potentialXOvers:
                    pch = PreCrossoverHandle(self, strandType, fromIdx, neighborVH, fromIdx, not facingRight)
                    self._preXOverHandles.append(pch)
            self.vhelix().part().virtualHelixAtCoordsChanged.connect(self.updatePreXOverHandles)
    
    def updatePreXOverHandles(self):
        self.setPreXOverHandlesVisible(False)
        self.setPreXOverHandlesVisible(True)
    
    def makeSelfActiveHelix(self):
        self._pathHelixGroup.setActiveHelix(self)
    
    ################# Loading and Updating State From VHelix #################
    def vhelixBasesModified(self):
        self._endpoints = None  # Clear endpoint drawing cache
        self._segmentPaths = None  # Clear drawing cache of lines
        self._loopPaths = None
        # Reset active helix if necessary
        if self.phgroup().getActiveHelix() == self:
            self.makeSelfActiveHelix()
        self.update()

    ############################# Drawing ##########################
    def paint(self, painter, option, widget=None):
        # Note that the methods that fetch the paths
        # cache the paths and that those caches are
        # invalidated as the primary mechanism
        # of updating after a change in vhelix's bases
        painter.save()
        painter.setBrush(self.nobrush)
        painter.setPen(self.minorGridPen)
        painter.drawPath(self.minorGridPainterPath())  # Minor grid lines
        painter.setPen(self.majorGridPen)
        painter.drawPath(self.majorGridPainterPath())  # Major grid lines
        painter.setBrush(Qt.NoBrush)
        segmentPaths, endptPths = self.segmentAndEndptPaths()
        for sp in segmentPaths:
            pen, path = sp
            painter.setPen(pen)
            painter.drawPath(path)
        painter.setPen(Qt.NoPen)
        for ep in endptPths:
            brush, path = ep
            painter.setBrush(brush)
            painter.drawPath(path)
        # Now draw loops and skips
        painter.setBrush(Qt.NoBrush)
        for paintCommand in self.loopPaths():
            painter.setPen(paintCommand[0])
            painter.drawPath(paintCommand[1])
            painter.setPen(paintCommand[2])
            painter.drawPath(paintCommand[3])
        painter.restore()

    def minorGridPainterPath(self):
        """
        Returns a QPainterPath object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        if self._minorGridPainterPath:
            return self._minorGridPainterPath
        path = QPainterPath()
        canvasSize = self._vhelix.part().numBases()
        # border
        path.addRect(0, 0, self.baseWidth * canvasSize, 2 * self.baseWidth)
        # minor tick marks
        for i in range(canvasSize):
            if (i % 7 != 0):
                x = round(self.baseWidth * i) + .5
                path.moveTo(x, 0)
                path.lineTo(x, 2 * self.baseWidth)
        # staple-scaffold divider
        path.moveTo(0, self.baseWidth)
        path.lineTo(self.baseWidth * canvasSize, self.baseWidth)
        self._minorGridPainterPath = path
        return path

    def majorGridPainterPath(self):
        """
        Returns a QPainterPath object for the major grid lines.
        This is separated from the minor grid lines so different
        pens can be used for each.
        """
        if self._majorGridPainterPath:
            return self._majorGridPainterPath
        path = QPainterPath()
        canvasSize = self._vhelix.part().numBases()
        # major tick marks  FIX: 7 is honeycomb-specific
        for i in range(0, canvasSize + 1, 7):
            x = round(self.baseWidth * i) + .5
            path.moveTo(x, .5)
            path.lineTo(x, 2 * self.baseWidth - .5)
        self._majorGridPainterPath = path
        return path

    def segmentAndEndptPaths(self):
        """Returns an array of (pen, penPainterPath, brush, brushPainterPath)
        for drawing segment lines and handles."""
        if self._segmentPaths and self._endptPaths:
            return (self._segmentPaths, self._endptPaths)
        self._segmentPaths = []
        self._endptPaths = []
        vh = self.vhelix()
        for strandType in (StrandType.Scaffold, StrandType.Staple):
            top = self.strandIsTop(strandType)
            segments, ends3, ends5 = self._vhelix.getSegmentsAndEndpoints(strandType)
            for (startIndex, endIndex) in segments:
                startPt = self.baseLocation(strandType, startIndex, centerY=True)
                endPt = self.baseLocation(strandType, endIndex, centerY=True)
                pp = QPainterPath()
                pp.moveTo(*startPt)
                pp.lineTo(*endPt)
                color = vh.colorOfBase(strandType, int(startIndex))
                width = styles.PATH_STRAND_STROKE_WIDTH
                pen = QPen(color, width)
                self._segmentPaths.append((pen, pp))
            for e3 in ends3:
                upperLeft = self.baseLocation(strandType, e3)
                bp = QPainterPath()
                color = vh.colorOfBase(strandType, e3)
                brush = QBrush(color)
                bp.addPath(ppR3.translated(*upperLeft) if top else\
                                                    ppL3.translated(*upperLeft))
                self._endptPaths.append((brush, bp))
            for e5 in ends5:
                upperLeft = self.baseLocation(strandType, e5)
                bp = QPainterPath()
                color = vh.colorOfBase(strandType, e5)
                brush = QBrush(color)
                bp.addPath(ppL5.translated(*upperLeft) if top else\
                                                    ppR5.translated(*upperLeft))
                self._endptPaths.append((brush, bp))
        return (self._segmentPaths, self._endptPaths)
 
    def loopPaths(self):
        """
        Returns an array of:
        (loopPen, loopPainterPath, skipPen, skipPainterPath)
        for drawing loops and skips
        """
        if self._loopPaths:
            return self._loopPaths
        self._loopPaths = []
        vh = self.vhelix()
        lpen = self._loopitem.getPen()
        spen = self._skipitem.getPen()
        for strandType in (StrandType.Scaffold, StrandType.Staple):
            top = self.strandIsTop(strandType)
            lp = QPainterPath()
            sp = QPainterPath()
            count = len(vh._loop(strandType))
            if count > 0:
                for index, loopsize in vh._loop(strandType).iteritems(): 
                    ul = self.baseLocation(strandType, index)
                    if loopsize > 0:
                        path = self._loopitem.getLoop(top)
                        lp.addPath(path.translated(*ul))
                    else:
                        path = self._skipitem.getSkip()
                        sp.addPath(path.translated(*ul))
                # end for
            # end if
            self._loopPaths.append((lpen, lp, spen, sp))
        # end for
        return self._loopPaths
    # end def
    
    def strandIsTop(self, strandType):
        return self.evenParity() and strandType == StrandType.Scaffold\
           or not self.evenParity() and strandType == StrandType.Staple

    def baseAtLocation(self, x, y, clampX=False, clampY=False):
        """Returns the (strandType, index) under the location x,y or None.
        
        It shouldn't be possible to click outside a pathhelix and still call
        this function. However, this sometimes happens if you click exactly
        on the top or bottom edge, resulting in a negative y value.
        """
        baseIdx = int(floor(x / self.baseWidth))
        minBase, maxBase = 0, self.vhelix().numBases()
        if baseIdx < minBase or baseIdx >= maxBase:
            if clampX:
                baseIdx = clamp(baseIdx, minBase, maxBase-1)
            else:
                return None
        if y < 0:
            y = 0  # HACK: zero out y due to erroneous click
        strandIdx = floor(y * 1. / self.baseWidth)
        if strandIdx < 0 or strandIdx > 1:
            if clampY:
                strandIdx = int(clamp(strandIdx, 0, 1))
            else:
                return None
        if self.strandIsTop(StrandType.Scaffold):
            strands = StrandType.Scaffold, StrandType.Staple
        else:
            strands = StrandType.Staple, StrandType.Scaffold
        return (strands[int(strandIdx)], baseIdx)

    def baseLocation(self, strandType, baseIdx, center=False, centerY=False):
        """Returns the coordinates of the upper left corner of the base
        referenced by strandType and baseIdx. If center=True, returns the
        center of the base instead of the upper left corner."""
        if self.strandIsTop(strandType):
            y = 0
        else:
            y = self.baseWidth
        x = baseIdx * self.baseWidth
        if center:
            x += self.baseWidth / 2
            y += self.baseWidth / 2
        if centerY:
            y += self.baseWidth / 2
        return (x, y)
# end class
# but wait, there's more! Now, for Events
# which can be more easily installed with less code duplication
# in a dynamic way

################################ Events ################################
forwardedEvents = ('hoverEnter', 'hoverLeave', 'hoverMove', 'mousePress',\
                   'mouseMove', 'mouseRelease')
defineEventForwardingMethodsForClass(PathHelix, 'PathHelix', forwardedEvents)
# end class
