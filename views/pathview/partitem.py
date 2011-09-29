#!/usr/bin/env python
# encoding: utf-8

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

from controllers.itemcontrollers.partitemcontroller import PartItemController
from virtualhelixitem import VirtualHelixItem

import util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QUndoCommand', 'QUndoStack',
                                       'QGraphicsPathItem'])

class PartItem(QGraphicsPathItem):
    def __init__(self, modelPart, toolManager, parent):
        super(PartItem, self).__init__(parent)
        self._modelPart = modelPart
        self._virtualHelixHash = {}
        self._toolManager = toolManager
        self._controller = PartItemController(self, modelPart)

    ### SIGNALS ###

    ### SLOTS ###
    def parentChangedSlot(self):
        """docstring for partParentChangedSlot"""
        print "PartItem.partParentChangedSlot"
        pass

    def removedSlot(self):
        """docstring for partDestroyedSlot"""
        print "PartItem.partDestroyedSlot"
        pass

    def destroyedSlot(self):
        """docstring for partDestroyedSlot"""
        print "PartItem.partDestroyedSlot"
        pass

    def movedSlot(self, pos):
        """docstring for partMovedSlot"""
        print "PartItem.partMovedSlot"
        pass

    def virtualHelixAddedSlot(self, modelVirtualHelix):
        """
        When a virtual helix is added to the model, this slot handles
        the instantiation of a virtualhelix item.
        """
        # print "PartItem.virtualHelixAddedSlot"
        vh = modelVirtualHelix
        vhi = VirtualHelixItem(self, modelVirtualHelix)
        vhi.setPos
        self._virtualHelixHash[vh.coords()] = vhi

    def updatePreXOverHandlesSlot(self, virtualHelix):
        pass
    # end def
    
    def xover3pCreatedSlot(self, strand, idx):
        """docstring for xover3pCreatedSlot"""
        print "PartItem.xover3pCreatedSlot"
        pass

    def xover3pDestroyedSlot(self, strand, idx):
        """docstring for xover3pDestroyedSlot"""
        print "PartItem.xover3pDestroyedSlot"
        pass


    ### METHODS ###
    def modelPart(self):
        """Return a reference to the model's part object"""
        return self._modelPart

    def _setVirtualHelixItemList(self, newList, zoomToFit=True):
        """
        Give me a list of VirtualHelix and I'll parent them to myself if
        necessary, position them in a column, adopt their handles, and
        position them as well.
        """
        y = 0  # How far down from the top the next PH should be
        leftmostExtent = 0
        rightmostExtent = 0
        
        scene = self.scene()
        vhiRect = None
        vhiHRect = None
        
        for vhi in newList:
            vhi.setParentItem(self.dummyChild)
            vhi.setPos(0, y)
            if not vhiRect:
                vhiRect = vhi.boundingRect().height()
                step = vhiRect.height() + styles.PATH_HELIX_PADDING
            # end if
            
            # get the VirtualHelixItemHandle
            vhiH = vhi.handle()
            
            if vhiH.parentItem() != self.vhihSelectionGroup:
                vhiH.setParentItem(self)
                
            if not vhiHRect:
                vhiHRect = vhih.boundingRect()
            
            vhiH.setPos(-2 * vhiHRect.width(), y + (vhiRect.height() - vhiHRect.height()) / 2)
            
            leftmostExtent = min(leftmostExtent, -2 * vhiHRect.width())
            rightmostExtent = max(rightmostExtent, vhiH.width())
            y += step
            # self.updatePreXOverHandles()
        # end for
        self._virtualHelixList = newList
        if zoomToFit:
            self.scene().views()[0].zoomToFit()
    # end def
    
    def activeVirtualHelixItem(self):
        return self._activeVirtualHelixItem
    
    def setActiveVirtualHelixItem(self, newActiveVHI):
        if newActiveVHI != self._activeVirtualHelixItem:
            self._modelPart.setActiveVirtualHelix(newActiveVHI.virtualHelix())
            self.setPreXOverHandlesVisible(newActiveVHI, True)
    # end def
    
    def preXOverHandlesVisible(self):
        return self._preXOverHandles != None
    # end def
    
    def setPreXOverHandlesVisible(self, virtualHelixItem, shouldBeVisible):
        """
        self._preXoverHandles list references prexovers parented to other
        PathHelices such that only the activeHelix maintains the list of
        visible prexovers
        
        A possible more efficient solution is to maintain the list _preXoverHandles
        in pathhelixgroup, in fact this method should live in pathhelixgroup
        """
        vhi = virtualHelixItem
        if vhi == None:
            return
        # end if
        areVisible = self._preXOverHandles != None
        vh = vhi.virtualHelix()
        partItem = self
        part = self.part()
        
        # clear PCHs
        # for pch in self._preXOverHandles:
        #     if pch.scene():
        #         pch.scene().removeItem(pch)
        if areVisible:
            map(lambda pch: pch.remove() if pch.scene() else None, self._preXOverHandles)

            self._preXOverHandles = None

        if shouldBeVisible:
            self._preXOverHandles = []
            for strandType, facingRight in \
                    product(('vStrandScaf', 'vStrandStap'), (True, False)):
                # Get potential crossovers in (fromVBase, toVBase) format
                potentialXOvers = vh.potentialCrossoverList(facingRight, getattr(vh,strandType)())
                numBases = vh.numBases()
                # assert(all(index < numBases for neighborVH, index in potentialXOvers))
                
                for (fromVBase, toVBase) in potentialXOvers:
                    # create one half
                    pch = PreXoverItem(ph, fromVBase, toVBase, not facingRight)
                    # add to list
                    self._preXOverHandles.append(pch)
                    # create the complement
                    otherPH = phg.pathHelixForVHelix(toVBase.vHelix())
                    pch = PreXoverItem(otherPH, toVBase, fromVBase, not facingRight)
                    # add to list
                    self._preXOverHandles.append(pch)
                # end for
            # end for
            part.virtualHelixAtCoordsChanged.connect(self.updatePreXOverHandles)
        self._XOverCacheEnvironment = (vh.neighbors(), vh.numBases())
    # end def

    def updatePreXOverHandles(self):
        cacheConstructionEnvironment = self._XOverCacheEnvironment
        vhi = self.activeVirtualHelixItem()
        if vhi == None:
            return
        vh = vhi.virtualHelix()
        currentEnvironment = (vh.neighbors(), vh.numBases())
        if cacheConstructionEnvironment != currentEnvironment and\
           self.preXOverHandlesVisible():
            self.setPreXOverHandlesVisible(vhi, False)
            self.setPreXOverHandlesVisible(vhi, True)
    # end def
