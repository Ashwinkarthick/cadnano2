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


import util
# import cadnano2.util as util
from operator import attrgetter

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QUndoStack', 'QUndoCommand'])

class Strand(QObject):
    def __init__(self, strandSet, baseIdxLow, baseIdxHigh):
        super(Strand, self).__init__(strandSet)
        self._strandSet = strandSet
        self._baseIdxLow = baseIdxLow  # base index of the strand's left boundary
        self._baseIdxHigh = baseIdxHigh  # base index of the right boundary
        self._strand5p = None
        self._strand3p = None
        self._oligo = None
        self._sequence = None
        self._decorators = {}
        # dynamic methods for mapping high/low connection /indices 
        # to corresponding 3Prime 5Prime 
        if strandSet.isDrawn5to3():
            self.idx5Prime = self.lowIdx
            self.idx3Prime = self.highIdx
            self.lowConnection = self.connection5p
            self.setLowConnection = self.set5pConnection
            self.highConnection = self.connection3p
            self.setHighConnection = self.set3pConnection
        else:
            self.idx5Prime = self.highIdx
            self.idx3Prime = self.lowIdx
            self.lowConnection = self.connection3p
            self.setLowConnection = self.set3pConnection
            self.highConnection = self.connection5p
            self.setHighConnection = self.set5pConnection
    # end def

    def __repr__(self):
        clsName = self.__class__.__name__
        return "%s(%s, %s)"%(clsName, self._baseIdxLow, self._baseIdxHigh)

    def generator3pStrand(self):
        """
        Iterate from self to the final _strand3p == None
        5prime to 3prime
        Includes originalCount to check for circular linked list
        """
        originalCount = 0
        node = self
        f = attrgetter('_strand3p')
        while node and originalCount == 0:
            yield node
            # equivalen to: node = node._strand3p
            node = f(node)
            if node == self:
                originalCount += 1
    # end def

    ### SIGNALS ###
    strandHasNewOligoSignal = pyqtSignal(QObject)
    strandDestroyedSignal = pyqtSignal(QObject)
    strandRemovedSignal = pyqtSignal(QObject)
    strandResizedSignal = pyqtSignal(QObject, tuple)
    strandXover3pCreatedSignal = pyqtSignal(QObject, int)
    strandXover3pRemovedSignal = pyqtSignal(QObject, int)
    strandDecoratorCreatedSignal = pyqtSignal(QObject, QObject, int)
    strandDecoratorDestroyedSignal = pyqtSignal(QObject, int)

    ### SLOTS ###


    ### Methods ###
    def undoStack(self):
        return self._strandSet.undoStack()

    def setStrandSet(self, strandSet):
        """docstring for setStrandSet"""
        self._strandSet = strandSet

    def strandSet(self):
        return self._strandSet
    # end def
    
    def numBases(self):
        return self._baseIdxHigh - self._baseIdxLow + 1
    # end def
    
    def virtualHelix(self):
        return self._strandSet.virtualHelix()
    # end def
    
    def part(self):
        return self._strandSet.part()
    # end def
    
    def oligo(self):
        return self._oligo
    # end def

    def setOligo(self, newOligo):
        self._oligo = newOligo
        # return the signal
        # return self.strandHasNewOligoSignal.emit, (self,)
        self.strandHasNewOligoSignal.emit(self)
    # end def
    
    def length(self):
        return self._baseIdxHigh - self._baseIdxLow + 1
    # return 
    def decorators(self):
        return self.decorators
    #end def

    def addDecorators(self, additionalDecorators):
        """
        used in adding additional decorators during a merge operation
        """
        self._decorators.update(additionalDecorators)
    # def

    def removeDecoratorsOutOfRange(self):
        decs = self._decorators
        idxMin, idMax = self.idxs() 
        for key in decs:
            if key > idxMax or key < idxMin:
                decs.pop(key)
            #end if
        # end for
    # end def

    def destroy(self):
        # QObject also emits a destroyed() Signal
        self.setParent(None)
        self.deleteLater()
    # end def

    def idxs(self):
        return (self._baseIdxLow, self._baseIdxHigh)
    # end def

    def setIdxs(self, idxs):
        self._baseIdxLow = idxs[0]
        self._baseIdxHigh = idxs[1]
    # end def

    def lowIdx(self):
        return self._baseIdxLow
    # end def

    def highIdx(self):
        return self._baseIdxHigh
    # end def

    def isDrawn5to3(self):
        return self._strandSet.isDrawn5to3()
    # end def

    def connection3p(self):
        return self._strand3p
    # end def

    def connection5p(self):
        return self._strand5p
    # end def

    def set3pConnection(self, strand):
        self._strand3p = strand
    # end def

    def set5pConnection(self, strand):
        self._strand5p = strand
    # end def

    def resize(self):
        pass
    # end def
    
    def getResizeBounds(self, index):
        """
        returns a tuple (lowInd, highInd)
        of indices for use with resizing a strand from one endpoint
        
        use this information the move an endpoint as low as lowInd + 1 and as
        high as highInd - 1
        """
        neighbors = self._strandSet.getNeighbors(self)
        if index == self._baseIdxLow:
            if neighbors[0]:
                low = neighbors[0].highIdx()
            else:
                low = self.part().minBaseIndex()-1
            return low, self._baseIdxHigh
        else:
            # Assume it's the self._baseIdxHigh
            if neighbors[1]:
                high = neighbors[1].lowIdx()
            else:
                high = self.part().maxBaseIndex()
            return self._baseIdxLow, high
    # end def

    class ResizeCommand(QUndoCommand):
        def __init__(self, strand, newIndices):
            super(ResizeCommand, self).__init__()
            self.strand = strand
            self.oldIndices = strand.idxs()
            self.newIndices = newIndices
        # end def

        def redo(self):
            std = self.strand
            nI = self.newIndices
            std.setIdxs(nI)
            std.strandResizedSignal.emit(std, nI)
        # end def

        def undo(self):
            std = self.strand
            oI = self.oldIndices
            std.setIdxs(oI)
            std.strandResizedSignal.emit(std, oI)
        # end def
    # end class

    def copy(self):
        pass
    # end def

    def shallowCopy(self):
        """
        can't use python module 'copy' as the dictionary _decorators
        needs to be shallow copied as well, but wouldn't be if copy.copy()
        is used, and copy.deepcopy is undesired
        """
        nS = Strand(self._strandSet, *self.idxs())
        nS._oligo = self._oligo
        nS._strand5p = self._strand5p
        nS._strand3p = self._strand3p
        # required to shallow copy the dictionary
        nS._decorators = dict(self._decorators.items())
        nS._sequence = self._sequence
        nS._note = self._note
        return nS
    # end def

    def deepCopy(self, strandSet, oligo):
        """
        can't use python module 'copy' as the dictionary _decorators
        needs to be shallow copied as well, but wouldn't be if copy.copy()
        is used, and copy.deepcopy is undesired
        """
        nS = Strand(strandSet, *self.idxs())
        nS._oligo = oligo
        decs = nS._decorators
        for key, decOrig in self._decorators:
            decs[key] = decOrig.deepCopy()
        # end fo
        nS._sequence = self._sequence
        nS._note = self._note
        return nS
    # end def
