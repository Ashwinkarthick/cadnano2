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
# from views.pathview.handles.activeslicehandle import ActiveSliceHandle
from model.enum import LatticeType, Parity, StrandType
from .virtualhelixitem import VirtualHelixItem
from .helixitem import HelixItem
from views import styles

from controllers.itemcontrollers.partitemcontroller import PartItemController

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
    _radius = styles.SLICE_HELIX_RADIUS
    
    def __init__(self, modelPart, parent=None):
        """
        modelPart is the modelPart it mirrors
        parent should be  either a SliceRootItem, or an AssemblyItem
        """
        super(PartItem, self).__init__(parent)
        # data related
        self._part = modelPart
        self._scaleFactor = self._radius/modelPart.radius()
        self.setZValue(100)
        
        # make sure paint doesn't get called
        self.setFlag(QGraphicsItem.ItemHasNoContents)
        
        # The deselector grabs mouse events that missed a slice
        # and clears the selection when it gets one
        self.deselector = PartItem.Deselector(self)
        self.deselector.setParentItem(self)
        self.deselector.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.deselector.setZValue(-1)

        # Invariant: keys in _helixhash = range(_nrows) x range(_ncols)
        # where x is the cartesian product
        self._helixhash = {}
        self._virtualHelixHash = {}
        
        self._nrows, self._ncols = 0, 0
        self._rect = QRectF(0, 0, 0, 0)
        # initialize the PartItem with an empty set of old coords
        self._setLattice([], modelPart.generatorFullLattice())

        # Cache of VHs that were active as of last call to activeSliceChanged
        # If None, all slices will be redrawn and the cache will be filled.
        self._previouslyActiveVHs = None
        # Connect destructor. This is for removing a part from scenes.
        self.probe = self.IntersectionProbe(self)
        
        self._controller = PartItemController(self, modelPart)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def parentChangedSlot(self):
        """docstring for parentChangedSlot"""
        print "PartItem.parentChangedSlot"
        pass

    def removedSlot(self):
        """docstring for removedSlot"""
        print "PartItem.removedSlot"
        self.scene().removeItem(self)
        self.setPart(None)
    # end def

    def destroyedSlot(self):
        """docstring for destroyedSlot"""
        print "PartItem.destroyedSlot"
        pass
    # end def

    def movedSlot(self, pos):
        """docstring for partMovedSlot"""
        print "PartItem.partMovedSlot"
        pass

    def xover3pCreatedSlot(self, strand, idx):
        """docstring for xover3pCreatedSlot"""
        print "PartItem.xover3pCreatedSlot"
        pass

    def xover3pDestroyedSlot(self, strand, idx):
        """docstring for xover3pDestroyedSlot"""
        print "PartItem.xover3pDestroyedSlot"
        pass

    def virtualHelixAddedSlot(self, virtualHelix):
        vh = virtualHelix
        coords = vh.coords()
        helixItem = self._helixhash[coords]
        # TODO test to see if self._virtualHelixHash is necessary
        self._virtualHelixHash[coords] = VirtualHelixItem(vh, helixItem)
    # end def
    
    def updatePreXOverHandlesSlot(self, virtualHelix):
        pass
    # end def

    ############################ Private Methods ############################
    def _upperLeftCornerForCoords(self, row, col):
        pass  # subclass

    def _updateGeometry(self):
        self._rect = QRectF(0, 0, *self.part().dimensions() )

    def _spawnHelixItemAt(self, row, column):
        helix = HelixItem(row, column, self)
        # helix.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
        self._helixhash[(row, column)] = helix
    # end def

    def _killHelixItemAt(row, column):
        s = self._helixhash[(row, column)]
        s.scene().removeItem(s)
        del self._helixhash[(row, column)]
    # end def

    def _setLattice(self, oldCoords, newCoords):
        """A private method used to change the number of rows,
        cols in response to a change in the dimensions of the
        part represented by the receiver"""
        oldSet = set(oldCoords)
        oldList = list(oldSet)
        newSet = set(newCoords)
        newList = list(newSet)
        
        for coord in oldList:
            if coord not in newSet:
                self._killHelixItemAt(*coord)
        # end for
        print "attempting to spawn helix"
        for coord in newList:
            # print "test 1"
            if coord not in oldSet:
                # print "spawning helix"
                self._spawnHelixItemAt(*coord)
        # end for
        # self._updateGeometry(newCols, newRows)
        # self.prepareGeometryChange()
        # the Deselector copies our rect so it changes too
        self.deselector.prepareGeometryChange()
        self.zoomToFit()
    # end def

    ############################# Public Methods #############################
    def mousePressEvent(self, event):
        # self.createOrAddBasesToVirtualHelix()
        QGraphicsItem.mousePressEvent(self, event)

    def boundingRect(self):
        return self._rect

    def scaleFactor(self):
        return self._scaleFactor
    # end def
    
    def paint(self, painter, option, widget=None):
        pass

    def zoomToFit(self):
        thescene = self.scene()
        theview = thescene.views()[0]
        theview.zoomToFit()

    def part(self):
        return self._part

    def setPart(self, newPart):
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
            super(PartItem.Deselector, self).__init__()
            self.parentHGI = parentHGI
        def mousePressEvent(self, event):
            self.parentHGI.part().setSelection(())
            super(PartItem.Deselector, self).mousePressEvent(event)
        def boundingRect(self):
            return self.parentHGI.boundingRect()
        def paint(self, painter, option, widget=None):
            pass

    class IntersectionProbe(QGraphicsItem):
        def boundingRect(self):
            return QRectF(0, 0, .1, .1)
        def paint(self, painter, option, widget=None):
            pass