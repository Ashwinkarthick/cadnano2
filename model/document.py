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

from parts.honeycombpart import HoneycombPart
from parts.squarepart import SquarePart
from strand import Strand
from operator import itemgetter
import util
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QUndoCommand', 'QUndoStack'])


class Document(QObject):
    """
    The Document class is the root of the model. It has two main purposes:
    1. Serve as the parent all Part objects within the model.
    2. Track all sub-model actions on its undoStack.
    """
    def __init__(self):
        super(Document, self).__init__()
        self._undoStack = QUndoStack()
        self._parts = []
        self._assemblies = []
        self._controller = None
        
        # the dictionary maintains what is selected
        self._selectionDict = {}
        # the added list is what was recently selected or deselected
        self._selectedChangedDict = {}

    ### SIGNALS ###
    documentPartAddedSignal = pyqtSignal(QObject)  # part
    
    # dict of tuples of objects using the reference as the key, and the value is
    # a tuple with meta data
    # in the case of strands the metadata would be which endpoints of selected
    # e.g. { objectRef: (value0, value1),  ...}
    documentSelectedChangedSignal = pyqtSignal(dict)   # dict of tuples of items and data 
    documentSelectionFilterChangedSignal = pyqtSignal(list)
    ### SLOTS ###

    ### ACCESSORS ###
    def undoStack(self):
        """
        This is the actual undoStack to use for all commands. Any children
        needing to perform commands should just ask their parent for the
        undoStack, and eventually the request will get here.
        """
        return self._undoStack

    def parts(self):
        """Returns a list of parts associated with the document."""
        return self._parts

    def assemblies(self):
        """Returns a list of assemblies associated with the document."""
        return self._assemblies

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def addToSelection(self, obj, value):
        self._selectionDict[obj] = value
        self._selectedChangedDict[obj] = value
    # end def
    
    def removeFromSelection(self, obj):
        if obj in self._selectionDict:
            del self._selectionDict[obj]
            self._selectedChangedDict[obj] = (False, False)
    # end def
    
    def addStrandToSelection(self, strand, value):
        sS = strand.strandSet()
        if sS in self._selectionDict:
            self._selectionDict[sS][strand] = value
        else:
            self._selectionDict[sS] = { strand : value }
        self._selectedChangedDict[strand] = value
    # end def
    
    def removeStrandFromSelection(self, strand):
        sS = strand.strandSet()
        if sS in self._selectionDict:
            temp = self._selectionDict[sS]
            if strand in temp:
                del temp[strand]
                if len(temp) == 0:
                    del self._selectionDict[sS]
            self._selectedChangedDict[strand] = (False, False)
    # end def
    
    def selectionDict(self):
        return self._selectionDict
    # end def
    
    def isModelSelected(self, obj):
        return obj in self._selectionDict
    # end def
    
    def isModelStrandSelected(self, strand):
        sS = strand.strandSet()
        if sS in self._selectionDict:
            if strand in self._selectionDict[sS]:
                return True
            else:
                return False
        else:
            return False
    # end def
    
    def getSelectedValue(self, obj):
        """
        obj is an objects to look up
        it is prevetted to be in the dictionary 
        """
        return self._selectionDict[obj]
        
    def getSelectedStrandValue(self, strand):
        """
        strand is an objects to look up
        it is prevetted to be in the dictionary 
        """
        return self._selectionDict[strand.strandSet()][strand]
    # end def
            
    def sortedSelectedStrands(self, strandSet):
        # outList = self._selectionDict[strandSet].keys()
        # outList.sort(key=Strand.lowIdx)
        outList = self._selectionDict[strandSet].items()
        getLowIdx = lambda x: Strand.lowIdx(itemgetter(0)(x))
        outList.sort(key=getLowIdx)
        return outList
    # end def
    
    def determineStrandSetBounds(self, selectedStrandList, strandSet):
        minLowDelta = strandSet.partMaxBaseIdx()
        minHighDelta = strandSet.partMaxBaseIdx()  # init the return values
        sSDict = self._selectionDict[strandSet]
        # get the StrandSet index of the first item in the list
        sSIdx = strandSet._findIndexOfRangeFor(selectedStrandList[0][0])[2]
        sSList = strandSet._strandList
        lenSSList = len(sSList)
        maxSSIdx = lenSSList-1
        i = 0
        for strand, value in selectedStrandList:
            while strand != sSList[sSIdx]:
                # incase there are gaps due to double xovers
                ssIdx += 1
            # end while
            idxL, idxH = strand.idxs()
            if value[0]:    # the end is selected
                if sSIdx > 0:
                    lowNeighbor = sSList[sSIdx-1]
                    if lowNeighbor in sSDict:
                        valueN = sSDict[lowNeighbor]
                        # we only care if the low neighbor is not selected
                        temp = minLowDelta  if valueN[1] else idxL - lowNeighbor.highIdx() - 1
                    # end if
                    else: # not selected
                        temp = idxL - lowNeighbor.highIdx() - 1
                    # end else
                else:
                    temp = idxL - 0
                # end else
                if temp < minLowDelta:
                    minLowDelta = temp
                # end if
                # check the other end of the strand
                if not value[1]:
                    temp = idxH - idxL -1
                    if temp < minHighDelta:
                        minHighDelta = temp
            # end if
            if value[1]:
                if sSIdx < maxSSIdx:
                    highNeighbor = sSList[sSIdx+1]
                    if highNeighbor in sSDict:
                        valueN = sSDict[highNeighbor]
                        # we only care if the low neighbor is not selected
                        temp = minHighDelta if valueN[1] else highNeighbor.lowIdx() - idxH -1
                    # end if
                    else: # not selected
                        temp = highNeighbor.lowIdx() - idxH - 1
                    # end else
                else:
                    temp = strandSet.partMaxBaseIdx() - idxH
                # end else
                if temp < minHighDelta:
                    minHighDelta = temp
                # end if
                # check the other end of the strand
                if not value[0]:
                    temp = idxH - idxL - 1
                    if temp < minLowDelta:
                        minLowDelta = temp
            # end if
            # increment counter
            sSIdx += 1
        # end for
        return (minLowDelta, minHighDelta)
    # end def
    
    def getSelectionBounds(self):
        minLowDelta = -1
        minHighDelta = -1
        for strandSet in self._selectionDict.iterkeys():
            selectedList = self.sortedSelectedStrands(strandSet)
            tempLow, tempHigh = self.determineStrandSetBounds(selectedList, strandSet)
            if tempLow < minLowDelta or minLowDelta < 0:
                minLowDelta = tempLow
            if tempHigh < minHighDelta or minHighDelta < 0:
                minHighDelta = tempHigh
        # end for Mark train bus to metro
        return (minLowDelta, minHighDelta)
    # end def
    
    # def operateOnStrandSelection(self, method, arg, both=False):
    # 
    # # end def
    
    def resizeSelection(self, delta, useUndoStack=True):
        if useUndoStack:
            self.undoStack().beginMacro("Resize Selection")
        for strandSetDict in self._selectionDict.itervalues():
            for strand, value in strandSetDict.iteritems():
                idxL, idxH = strand.idxs()
                idxL = idxL+delta if value[0] else idxL
                idxH = idxH+delta if value[1] else idxH
                Strand.resize(strand, (idxL,idxH), useUndoStack)
            # end for
        # end for
        if useUndoStack:
            self.undoStack().endMacro()
    # end def
    
    def updateSelection(self):
        """
        do it this way in the future when we have a better signaling architecture between views
        """
        # self.documentSelectedChangedSignal.emit(self._selectedChangedDict)
        """
        For now, individual objects need to emit signals
        """
        for obj, value in self._selectedChangedDict.iteritems():
            obj.selectedChangedSignal.emit(obj, value)
        # end for
        self._selectedChangedDict = {}
        # for sS in self._selectionDict:
        #     print self.sortedSelectedStrands(sS)
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def addHoneycombPart(self):
        """
        Create and store a new DNAPart and instance, and return the instance.
        """
        dnapart = None
        if len(self._parts) == 0:
            dnapart = HoneycombPart(document=self)
            self._addPart(dnapart)
        return dnapart

    def addSquarePart(self):
        """
        Create and store a new DNAPart and instance, and return the instance.
        """
        dnapart = None
        if len(self._parts) == 0:
            dnapart = SquarePart(document=self)
            self._addPart(dnapart)
        return dnapart

    def removeAllParts(self):
        """Used to reset the document. Not undoable."""
        for part in self._parts:
            part.remove(useUndoStack=False)
    # end def

    def removePart(self, part):
        self._parts.remove(part)

    ### PUBLIC SUPPORT METHODS ###
    def setController(self, controller):
        """Called by DocumentController setDocument method."""
        self._controller = controller

    ### PRIVATE SUPPORT METHODS ###
    def _addPart(self, part, useUndoStack=True):
        """Add part to the document via AddPartCommand."""
        c = self.AddPartCommand(self, part)
        util.execCommandList(self, [c], desc="Add part", useUndoStack=useUndoStack)
        return c.part()

    ### COMMANDS ###
    class AddPartCommand(QUndoCommand):
        """
        Undo ready command for deleting a part.
        """
        def __init__(self, document, part):
            QUndoCommand.__init__(self)
            self._doc = document
            self._part = part

        def part(self):
            return self._part

        def redo(self):
            if len(self._doc._parts) == 0:
                self._doc._parts.append(self._part)
                self._part.setDocument(self._doc)
                self._doc.documentPartAddedSignal.emit(self._part)

        def undo(self):
            self._part.setDocument(None)
            self._doc._parts.remove(self._part)
            self._part.partRemovedSignal.emit(self._part)
