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
slicegraphicsitem.py

Created by Nick Conway on 2010-06-15.
"""

from exceptions import NotImplementedError
from heapq import *
from views.pathview.handles.activeslicehandle import ActiveSliceHandle
from model.enum import LatticeType, Parity, StrandType
from .slicehelix import SliceHelix
from views import styles

import util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QRectF', 'QPointF', 'QEvent', 'Qt', \
                                        'pyqtSignal', 'pyqtSlot', 'QObject'])
util.qtWrapImport('QtGui', globals(), [ 'QGraphicsItem', 'QBrush', \
                                        'QPainterPath', 'QPen'])


class PartItem(QGraphicsItem):
    """
    SliceGraphicsItem is an abstract class to be inherited by
    HoneycombSliceGraphicsItem or SquareSliceGraphicsItem. SliceGraphicsItem
    is the parent of all SliceHelix items, and is responsible for spawning
    and positioning them according to the part dimensions.
    """
    radius = styles.SLICE_HELIX_RADIUS
    
    def __init__(self, part, controller=None, parent=None):
        super(PartItem, self).__init__()
        # data related
        self._part = None
        self.sliceController = controller
        self.parent = parent
        self.setParentItem(parent)
        self.setZValue(100)

        # The deselector grabs mouse events that missed a slice
        # and clears the selection when it gets one
        self.deselector = PartItem.Deselector(self)
        self.deselector.setParentItem(self)
        self.deselector.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.deselector.setZValue(-1)

        # Invariant: keys in _helixhash = range(_nrows) x range(_ncols)
        # where x is the cartesian product
        self._helixhash = {}
        self._nrows, self._ncols = 0, 0
        self._rect = QRectF(0, 0, 0, 0)
        self.setPart(part)

        # Cache of VHs that were active as of last call to activeSliceChanged
        # If None, all slices will be redrawn and the cache will be filled.
        self._previouslyActiveVHs = None
        # Connect destructor. This is for removing a part from scenes.
        self._part.partRemoved.connect(self.destroy)
        self.probe = self.IntersectionProbe(self)
    # end def

    def destroy(self):
        self._part.partRemoved.disconnect(self.destroy)
        self.scene().removeItem(self)
        self.setPart(None)
    # end def

    ############################ Private Methods ############################
    def _upperLeftCornerForCoords(self, row, col):
        pass  # subclass

    def _updateGeometry(self):
        self._rect = QRectF(0, 0, *self.part().dimensions() )

    def _spawnVHelixItemAt(self, row, column):
        x, y = self.part().latticeToSpatial(row, column)
        pt = QPointF(x,y)
        helix = VirtualHelixItem(pt, self)
        helix.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
        self._helixhash[(row, column)] = helix
    # end def

    def _killVHelixItemAt(row, column):
        s = self._helixhash[(row, column)]
        s.scene().removeItem(s)
        del self._helixhash[(row, column)]

    def _setDimensions(self, newDims):
        """A private method used to change the number of rows,
        cols in response to a change in the dimensions of the
        part represented by the receiver"""
        newRows, newCols, ignore = newDims
        if self._nrows > newRows:
            for r in range(newRows, self._nrows):
                for c in range(self._ncols):
                    self._killSliceAt(r, c)
        elif newRows > self._nrows:
            for r in range(self._nrows, newRows):
                for c in range(self._ncols):
                    self._spawnSliceAt(r, c)
        self._nrows = newRows
        # We now have the right number of rows
        if self._ncols > newCols:
            for c in range(newCol, self._ncols):
                for r in range(self._nrows):
                    self._killSliceAt(r, c)
        elif newCols > self._ncols:
            for c in range(self._ncols, newCols):
                for r in range(self._nrows):
                    self._spawnSliceAt(r, c)
        self._ncols = newCols
        self._updateGeometry(newCols, newRows)
        self.prepareGeometryChange()
        # the Deselector copies our rect so it changes too
        self.deselector.prepareGeometryChange()
        self.zoomToFit()

        def _setLattice(self, oldCoords, newCoords):
            """A private method used to change the number of rows,
            cols in response to a change in the dimensions of the
            part represented by the receiver"""
            oldSet = set(oldCoords)
            newSet = set(newCoords)
            for coord in oldCoords:
                if coord not in newSet:
                    self._killVHelixItemAt(*coord)
            # end for
            for coord in newCoords:
                if coord not in oldSet:
                    self._spawnVHelixItemAt(*coord)
            # end for
            self._updateGeometry(newCols, newRows)
            self.prepareGeometryChange()
            # the Deselector copies our rect so it changes too
            self.deselector.prepareGeometryChange()
            self.zoomToFit()

    ############################# Public Methods #############################
    def mousePressEvent(self, event):
        # self.createOrAddBasesToVirtualHelix()
        QGraphicsItem.mousePressEvent(self, event)

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        pass

    def zoomToFit(self):
        thescene = self.scene()
        theview = thescene.views()[0]
        theview.zoomToFit()

    def part(self):
        return self._part

    def setPart(self, newPart):
        if self._part:
            self._part.dimensionsWillChange.disconnect(self._setDimensions)
            self._part.selectionWillChange.disconnect(self.selectionWillChange)
            self._part.activeSliceWillChange.disconnect(self.activeSliceChanged)
            self._part.virtualHelixAtCoordsChanged.disconnect(self.vhAtCoordsChanged)
        if newPart != None:
            self._setDimensions(newPart.dimensions())
            newPart.dimensionsWillChange.connect(self._setDimensions)
            newPart.selectionWillChange.connect(self.selectionWillChange)
            newPart.activeSliceWillChange.connect(self.activeSliceChanged)
            newPart.virtualHelixAtCoordsChanged.connect(self.vhAtCoordsChanged)
        self._part = newPart

    def getVirtualHelixItemByCoord(self, row, column):
        if (row, column) in self._helixhash:
            return self._helixhash[(row, column)]
        else:
            return None

    def selectionWillChange(self, newSel):
        if self.part() == None:
            return
        if self.part().selectAllBehavior():
            return
        for sh in self._helixhash.itervalues():
            sh.setSelected(sh.virtualHelix() in newSel)

    def activeSliceChanged(self, newActiveSliceZIndex):
        newlyActiveVHs = set()
        part = self.part()
        activeSlice = part.activeSlice()
        if self._previouslyActiveVHs:
            for vh in part.getVirtualHelices():
                isActiveNow = vh.hasBaseAt(StrandType.Scaffold, activeSlice)
                if isActiveNow != (vh in self._previouslyActiveVHs):
                    self._helixhash[vh.coords()].update()
                if isActiveNow:
                    newlyActiveVHs.add(vh)
        else:
            for vh in part.getVirtualHelices():
                isActiveNow = vh.hasBaseAt(StrandType.Scaffold, activeSlice)
                if isActiveNow:
                    newlyActiveVHs.add(vh)
            self.update()

    def vhAtCoordsChanged(self, row, col):
        self._helixhash[(row, col)].update()

    class Deselector(QGraphicsItem):
        """The deselector lives behind all the slices and observes mouse press
        events that miss slices, emptying the selection when they do"""
        def __init__(self, parentHGI):
            super(SliceGraphicsItem.Deselector, self).__init__()
            self.parentHGI = parentHGI
        def mousePressEvent(self, event):
            self.parentHGI.part().setSelection(())
            super(SliceGraphicsItem.Deselector, self).mousePressEvent(event)
        def boundingRect(self):
            return self.parentHGI.boundingRect()
        def paint(self, painter, option, widget=None):
            pass

    class IntersectionProbe(QGraphicsItem):
        def boundingRect(self):
            return QRectF(0, 0, .1, .1)
        def paint(self, painter, option, widget=None):
            pass