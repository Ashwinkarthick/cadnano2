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
virtualhelix.py
Created by Jonathan deWerd on 2011-01-26.
"""
import sys
from exceptions import AttributeError, IndexError
from itertools import product
from .enum import LatticeType, Parity, StrandType, BreakType
from .enum import Crossovers, EndType
from PyQt4.QtCore import pyqtSignal, QObject, QTimer
from PyQt4.QtGui import QUndoCommand, QUndoStack, QColor
from .base import Base
from util import *
from cadnano import app
import ui.styles as styles
import re


class VirtualHelix(QObject):
    """Stores staple and scaffold routing information."""
    basesModified = pyqtSignal()
    dimensionsModified = pyqtSignal()

    def __init__(self, numBases=21, idnum=0, incompleteArchivedDict=None):
        super(VirtualHelix, self).__init__()
        # Row, col are always owned by the parent part;
        # they cannot be specified in a meaningful way
        # for a detached helix (part==None). Only dnaparts
        # get to modify these.
        self._row = None
        self._col = None
        # If self._part exists, it owns self._number
        # in that only it may modify it through the
        # private interface. The public interface for
        # setNumber just routes the call to the parent
        # dnapart if one is present. If self._part == None
        # the vhelix owns self._number and may modify it.
        self._number = idnum
        # Attaching to a part via setPart gives the part ownership of
        # the above three properties (it asks part to set them,
        # self should no longer modify _row, _col, or _number)
        self._part = None
        # The base arrays are owned entirely by virtualhelix
        self._stapleBases = []
        self._scaffoldBases = []
        # As is the floatingXoverBase if there is one
        self.floatingXoverBase = None
        
        """
        This is for loops and skips.
        a dictionary for loops and skips is added
        for loops and skips
        of the form { index: count }
        + count indicates loop 
        - count indicates skip
        """
        self._stapleLoops = {}
        self._scaffoldLoops = {}
        
        # setSandboxed(True) gives self a private undo stack
        # in order to insulate undo/redo on the receiver
        # from global undo/redo (so that if a haywire tool
        # using undo() and redo() to give a live preview of
        # tho tool's effect calls undo() a million times it
        # doesn't make the document disappear). setSandboxed(False)
        # then clears _privateUndoStack at which point self
        # goes back to using the part / document undo stack.
        self._privateUndoStack = None
        self._sandboxed = False
        # numBases is a simulated property that corresponds to the
        # length of _stapleBases and _scaffoldBases
        if incompleteArchivedDict:
            numBases = len(re.split('\s+',\
                                    incompleteArchivedDict['staple'])) - 1
        self.setNumBases(numBases, notUndoable=True)
        
        # During a single UndoCommand, many basesModified signals can be generated.
        # basesModifiedVHs stores a set of VH that will hasBeenModified
        # upon a call to emitBasesModifiedIfNeeded.
        self.basesModifiedVHs = set()
        
    def __repr__(self):
        return 'vh%i' % self.number()

    def __str__(self):
        scaf = '%-2iScaffold: ' % self.number() + \
                            ' '.join((str(b) for b in self._scaffoldBases))
        stap = '%-2iStaple:   ' % self.number() + \
                                ' '.join((str(b) for b in self._stapleBases))
        return scaf + '\n' + stap

    def part(self):
        return self._part

    def _setPart(self, newPart, coords, num):
        """Should only be called by dnapart. Use dnapart's
        addVirtualHelixAt to add a virtualhelix to a dnapart."""
        (self._row, self._col) = coords
        if self._part and self._part.getVirtualHelix(coords):
            self._part.addVirtualHelixAt(coords, None)
        self._number = num
        self._part = newPart
        self.setNumBases(newPart.numBases(), notUndoable=True)
        # Command line convenience for -i mode
        if app().v != None:
            app().v[self.number()] = self

    def numBases(self):
        return len(self._stapleBases)

    def setNumBases(self, newNumBases, notUndoable=False):
        newNumBases = int(newNumBases)
        assert(newNumBases >= 0)
        oldNB = self.numBases()
        if self.part():
            assert(self.part().numBases() == newNumBases)
        if newNumBases == oldNB:
            return
        if newNumBases > oldNB:
            c = self.SetNumBasesCommand(self, newNumBases)
            if notUndoable:
                c.redo()
            else:
                self.undoStack().push(c)
        if newNumBases < oldNB:
            c0 = self.ClearStrandCommand(self, StrandType.Scaffold,\
                                         newNumBases, oldNB)
            c1 = self.ClearStrandCommand(self, StrandType.Staple,\
                                         newNumBases, oldNB)
            c2 = self.SetNumBasesCommand(self, newNumBases)
            if notUndoable:
                c0.redo()
                c1.redo()
                c2.redo()
            else:
                u = self.undoStack()
                u.beginMacro("Changing the number of bases")
                u.push(c0)
                u.push(c1)
                u.push(c2)
                u.endMacro()

    def number(self):
        """return VirtualHelix number"""
        return self._number
    
    def setNumber(self, newNumber):
        if self.part():
            self.part().renumberVirtualHelix(self, newNumber)
        else:
            self._number = newNumber
    
    # Why two setNumber commands? Because we're faced with
    # a bit of a connundrum. We want
    # 1) part() to control numbering when there is a part().
    #    Not all numbers are valid for all row, col coords (parity),
    #    numbers must be unique in a part, etc, etc. This code
    #    depends on the specifics of the dnapart, and so it
    #    ought to reside in the part.
    # 2) a VirtualHelix without a part to be able to keep track
    #    of a number. 
    # 3) asking a part for its number to be fast. We do it a
    #    lot, so doing a reverse lookup is unseemly.
    # How do we accomplish these goals?
    # 1) We declare that dnapart has the final say on numbers.
    #    it's the master copy. If a VH's self._number disagrees
    #    with the dnapart, the VH is wrong (there is always EXACTLY
    #    one "gold" copy of any data). Parts assign new numbers
    #    to VHs when the VHs are added to them, and they recycle
    #    numbers for deleted VHs.
    # 2) We add a self._number variable to the VH to keep track of
    #    a number when a VH has no part, with the proviso that this
    #    ivar is meaningless when there is a self.part().
    # 3) In times when we have a part, we save self._number from
    #    uselessness by making it a cache for reverse lookups of
    #    the number for a specific VH.
    # So, why two setNumber commands? What is the main question 
    # facing any user of an API? "How do I do x." This is answered
    # by searching for a relevant method name. Once such a method
    # name is found, the next question is "will calling this method
    # suffice?" Wary of caches (implicit or explicit) that need updating,
    # buffers that need flushing, and invariants that must be maintained,
    # this question often has a very complicated answer. A very simple
    # way to make an API user friendly is to ensure that the answer
    # is "Yes" for *ALL* public methods.
    #   No underscore => A caller is only responsible for is calling the method.
    #   underscore    => The caller has to do other voodoo to get the
    #                    suggested result (invalidate caches, flush buffers,
    #                    maintain invariants, pet watchdogs, etc)
    # So, in particular:
    #   setNumber will ask the part to validate the new number,
    #     maintain the numbering system responsible for quickly
    #     assigning numbers to now helices, emit notifications,
    #     and assure that the newNumber isn't already in use by
    #     another VH. If the receiver has no part(), self._number
    #     is a gold copy of the numbering data and can be simply
    #     updated. The user doesn't need to worry about any of this.
    #     In a command line script with no part(), the VH will
    #     use its new number without question, and inside the GUI
    #     changes will automagically appear in the interface.
    #   _setNumber JUST updates the cached value of self._number if
    #     self has a part. It could be skipped, but then DNAPart
    #     would have to touch the ivar self._number directly, which
    #     is mildly bad karma.
    def _setNumber(self, newNumber):
        self._number = newNumber

    def selected(self):
        return self in self.part().selection()

    # dnapart owns its selection, so look there for related
    # event emission
    def setSelected(self, willBeSelected):
        currentSelection = self.part().selection()
        selected = self in currentSelection
        needsSelecting = willBeSelected and not selected
        needsDeselectig = not willBeSelected and selected
        if needsSelecting:
            # We're modifying part()'s selection
            # object beneath it. I won't tell it
            # if you don't. Safety would demand
            # selection() returns a copy.
            currentSelection.append(self)
        elif needsDeselectig:
            currentSelection.remove(self)
        self.part().setSelection(currentSelection)

    def coord(self):
        return (self._row, self._col)

    def evenParity(self):
        """
        returns True or False
        """
        if self._part:
            return self._part.virtualHelixParityEven(self)
        else:
            return self._number % 2 == 0

    def directionOfStrandIs5to3(self, strandtype):
        """
        method to determine 5' to 3' or 3' to 5'
        """
        if self.evenParity() and strandtype == StrandType.Scaffold:
            return True
        elif not self.evenParity() and strandtype == StrandType.Staple:
            return True
        else:
            return False
    # end def

    def row(self):
        """return VirtualHelix helical-axis row"""
        return self._row

    def col(self):
        """return VirtualHelix helical-axis column"""
        return self._col

    def _strand(self, strandType):
        """The returned strand should be considered privately
        mutable"""
        if strandType == StrandType.Scaffold:
            return self._scaffoldBases
        elif strandType == StrandType.Staple:
            return self._stapleBases
        else:
            raise IndexError("%s is not Scaffold=%s or Staple=%s"%(strandType, StrandType.Scaffold, StrandType.Staple))
            
    def _loop(self, strandType):
        """The returned loop list should be considered privately
        mutable"""
        if strandType == StrandType.Scaffold:
            return self._scaffoldLoops
        elif strandType == StrandType.Staple:
            return self._stapleLoops
        else:
            raise IndexError("%s is not Scaffold=%s or Staple=%s"%(strandType, StrandType.Scaffold, StrandType.Staple))

    ############################## Access to Bases ###########################
    def hasBaseAt(self, strandType, index):
        """Returns true if a base is present at index on strand strandtype."""
        base = self._baseAt(strandType, index)
        if not base:
            return False
        else:
            return not base.isEmpty()

    def validatedBase(self, strandType, index, raiseOnErr=False):
        """Makes sure the basespec (strandType,index) is valid
        and raises or returns (None, None) according to raiseOnErr if
        it isn't valid"""
        if strandType != StrandType.Scaffold and \
                                            strandType != StrandType.Staple:
            if raiseOnErr:
                raise IndexError("Base (strand:%s index:%i) Not Valid" % \
                                                        (strandType, index))
            return (None, None)
        index = int(index)
        if index < 0 or index > self.numBases() - 1:
            if raiseOnErr:
                raise IndexError("Base (strand:%s index:%i) Not Valid" % \
                                                        (strandType, index))
            return (None, None)
        return (strandType, index)

    def _baseAt(self, strandType, index, raiseOnErr=False):
        strandType, index = \
                self.validatedBase(strandType, index, raiseOnErr=raiseOnErr)
        if strandType == None:
            return None
        return self._strand(strandType)[index]

    def hasCrossoverAt(self, strandType, index):
        """docstring for hasScafCrossoverAt"""
        base = self._baseAt(strandType, index)
        if not base:
            return False
        else:
            return base.isCrossover()

    def hasStrandAt(self, strandType, index):
        """A strand base is a base that is connected to
        other bases on both sides (possibly over a staple)"""
        base = self._baseAt(strandType, index)
        if not base:
            return False
        else:
            return base.isStrand()
    
    def hasEndAt(self, strandType, index):
        base = self._baseAt(strandType, index)
        if not base:
            return False
        else:
            return base.isEnd()
        
    def hasLoopAt(self, strandType, index):
        """
        check for key "index" in the loop dictionary based on strandtype
        returns 0 if no loop or skip and returns the length of the skip
        otherwise
        """
        if index in self._loop(strandType):
            return self._loop(strandType)[index]
        else:
            return 0

    def getSegmentsAndEndpoints(self, strandType):
        """Returns a list of segments, endpoints of self in the format
        ([(startIdx, endIdx), ...],
         [3pEndIdx1, 3pEndIdx2, ...], 
         [5pEndIdx1, ...])
        where startIdx and endIdx can be 1.5, 2.5 etc (multiply by base
        width to see where to draw the lines)"""
        segments, ends3, ends5 = [], [], []
        strand = self._strand(strandType)
        i, s = 0, None
        # s is the start index of the segment
        for i in range(len(strand)):
            b = strand[i]
            
            #Segments
            if b._hasSubSegmentL():
                if s==None:
                    s = i
                else:
                    pass
            else: # not connected to base on left
                if s==None:
                    pass
                else:
                    segments.append((s,i))
                    s = None
            if b._hasSubSegmentR():
                if s==None:
                    s = i+.5
                else:
                    pass
            else: # not connected to base on right
                if s==None:
                    pass
                else:
                    segments.append((s,i+.5))
                    s = None
            
            #Endpoints
            if b.is5primeEnd():
                ends5.append(i)
            if b.is3primeEnd():
                ends3.append(i)

        return (segments, ends3, ends5)

    def get3PrimeXovers(self, strandType):
        """
        Returns a tuple of tuples of the form 
        ((fromVH, fromIdx), (toVH, toIdx))
        or, in the case of a floating crossover,
        ((fromVH, fromIdx), toQPoint)
        """
        ret = []
        strand = self._strand(strandType)
        i, s = 0, None
        for base in strand:
            if base.is3primeXover():
                floatDest = base.floatingXoverDestination()
                if floatDest:
                    ret.append(((self, base._n), floatDest))
                else:
                    ret.append(((self, base._n),\
                        (base._3pBase.vhelix(), base._3pBase._n)))
        return ret

    def getXover(self, strandType, idx):
        """
        Takes an index and returns a tuple of the FROM (3p) end helix and
        the vhelix and index it points to on the TO (5p) end.
        """
        strand = self._strand(strandType)
        if strand[idx].is3primeXover():
            return ((self, idx),\
                    (strand[idx]._3pBase.vhelix(), strand[idx]._3pBase._n))
        else:  # it's a 5-prime Xover end, reverse it
            return ((strand[idx]._5pBase.vhelix(), strand[idx]._5pBase._n),\
                    (self, idx))
    # end def

    def colorOfBase(self, strandType, idx):
        if strandType == StrandType.Scaffold:
            return styles.bluestroke
            # return QColor(44, 51, 141)
        # hue = 47 * idx + 31 * self.number()
        # return QColor.fromHsl(hue % 256, 255, 128)
        c = QColor(self._stapleBases[idx].getColor())
        # print "colorOfBase", idx, c.name(), self._stapleBases[idx].getColor()
        return c
    
    def _basesConnectedTo(self, strandType, idx):
        strand = self._strand(strandType)
        bases = set()
        treeTips = [strand[idx]]
        while len(treeTips):
            b = treeTips.pop()
            if b in bases:
                continue
            else:
                bases.add(b)
                treeTips.append(b._3pBase)
                treeTips.append(b._5pBase)
        return bases
            
    def sandboxed(self):
        return self._sandboxed

    def setSandboxed(self, sb, mustNotShareStack=False):
        """Set True to give the receiver a temporary undo stack
        that will be deleted upon set False. Since tools can be
        made live by repeatedly pushing and popping undo commands,
        it occasionally happens that a bug pops many things off the
        undo stack. The temporary undo stack prevents excessive popping
        from reverting the document to a blank state."""
        if sb and self._privateUndoStack:
            if mustNotShareStack:
                assert(False)  # Caller needed a private undo stack; we couldn't provide one
            else:
                print "WARNING: attempting to sandbox a vh that already has an undo stack!"
        if sb and not self._privateUndoStack:
            self._sandboxed = True
            if not self._privateUndoStack:
                self._privateUndoStack = QUndoStack()
        elif not sb:
            if self._sandboxed:
                self._sandboxed = False
                self._privateUndoStack = None

    def undoStack(self):
        if self._privateUndoStack != None:
            return self._privateUndoStack
        if self.part() != None:
            return self.part().undoStack()
        if self._privateUndoStack == None:
            print "Creating detached undo stack for %s" % self
            self._privateUndoStack = QUndoStack()
        return self._privateUndoStack
    
    ################# New-Style Accessors ###################
    # A neighbor base is one that is connected to the base represented
    # by self through a phosphate linkage. These accessors let you get them
    def neighbor5p(self, strandType, idx):
        b = self._strand(strandType)[idx]._neighbor5p()
        return (b._vhelix, b._strandtype, b._n)
    def neighbor3p(self, strandType, idx):
        b = self._strand(strandType)[idx]._neighbor3p()
        return (b._vhelix, b._strandtype, b._n)
    # Although different strands are oriented different ways inside the gui,
    # R and L always represent the bases to the right and left of the receiver
    # in the GUI
    def neighborR(self, strandType, idx):
        b = self._strand(strandType)[idx]._neighborR()
        return (b._vhelix, b._strandtype, b._n)
    def neighborL(self, strandType, idx):
        b = self._strand(strandType)[idx]._neighborL()
        return (b._vhelix, b._strandtype, b._n)
    
    # Test for the presence of neghbors
    def hasNeighbor5p(self, strandType, idx):
        return self._strand(strandType)[idx]._hasNeighbor5p()
    def hasNeighbor3p(self, strandType, idx):
        return self._strand(strandType)[idx]._hasNeighbor3p()
    def hasNeighborR(self, strandType, idx):
        return self._strand(strandType)[idx]._hasNeighborR()
    def hasNeighborL(self, strandType, idx):
        return self._strand(strandType)[idx]._hasNeighborL()
    
    # A segment is a connection between a base and its neighbor
    # base on the same strand
    def hasSubSegment5p(self, strandType, idx):
        return self._strand(strandType)[idx]._hasSubSegment5p()
    def hasSubSegment3p(self, strandType, idx):
        return self._strand(strandType)[idx]._hasSubSegment3p()
    def hasSubSegmentR(self, strandType, idx):
        return self._strand(strandType)[idx]._hasSubSegmentR()
    def hasSubSegmentL(self, strandType, idx):
        return self._strand(strandType)[idx]._hasSubSegmentL()
    
    # A crossover is a connection between a base and a base
    # that isn't its neighbor on the same strand
    def hasCrossover5p(self, strandType, idx):
        return self._strand(strandType)[idx]._hasCrossover5p()
    def hasCrossover3p(self, strandType, idx):
        return self._strand(strandType)[idx]._hasCrossover3p()
    def hasCrossoverR(self, strandType, idx):
        return self._strand(strandType)[idx]._hasCrossoverR()
    def hasCrossoverL(self, strandType, idx):
        return self._strand(strandType)[idx]._hasCrossoverL()
    

    ################## Public Base Modification API #########
    """
    Overview: the bases in a virtualhelix can be modified
    with the public methods, which under the hood just validate
    their arguments and push
    undo commands (of a similar name to the public methods)
    that call private methods (often of exactly the same name
    as the public methods except for a prefixed underscore).
    Outside World -> doSomething() -> DoSomethingUndoCommand ->
        _doSomething() -> Private API
    or Outside World -> doSomething() -> DoSomethingUndoCommand -> Private API
    """
    def hasBeenModified(self):
        if self.part():
            self.part().basesModifiedVHs.add(self)
        else:
            self.basesModified.emit()
    
    def emitBasesModifiedIfNeeded(self):
        if self.part():
            for vh in self.part().basesModifiedVHs:
                vh.basesModified.emit()
            self.part().basesModifiedVHs.clear()
        else:
            self.basesModified.emit()
        #self.part().virtualHelixAtCoordsChanged.emit(*self.coord())
        
    def connectStrand(self, strandType, startIndex, endIndex, macro=True, undoStack=None):
        """
        Connects sequential bases on a single strand, starting with
        startIndex and ending with etdIndex (inclusive)
        Sets {s.n, (s+1).np, ..., (e-2).np, (e-1).np, e.p}
        """
        strand = self._strand(strandType)
        endIndex, startIndex = int(max(startIndex, endIndex)),\
                                        int(min(startIndex, endIndex))
        startIndex = clamp(startIndex, 0, len(strand) - 1)
        endIndex = clamp(endIndex, 0, len(strand) - 1)
        if undoStack==None:
            undoStack = self.undoStack()
        if macro:
            undoStack.beginMacro("Connect Strand")
        c = self.ConnectStrandCommand(self, strandType, startIndex, endIndex)
        undoStack.push(c)
        if macro:
            self.thoughtPolice(undoStack)  # Check for inconsistencies, fix one-base Xovers, etc
            undoStack.endMacro()

    def clearStrand(self, strandType, startIndex, endIndex, macro=True, undoStack=None):
        endIndex, startIndex = int(max(startIndex, endIndex)),\
                                        int(min(startIndex, endIndex))
        strand = strandType == StrandType.Scaffold and \
            self._scaffoldBases or self._stapleBases
        startIndex = clamp(startIndex, 1, len(strand)-1)
        endIndex = clamp(endIndex, 1, len(strand)-1)
        if undoStack==None:
            undoStack = self.undoStack()
        if macro:
            undoStack.beginMacro("Clear Strand")
        c = self.ClearStrandCommand(self, strandType, startIndex, endIndex)
        undoStack.push(c)
        if macro:
            self.thoughtPolice(undoStack)  # Check for inconsistencies, fix one-base Xovers, etc
            undoStack.endMacro()

    def installXoverFrom3To5(self, strandType, fromIndex, toVhelix, toIndex, macro=True, undoStack=None):
        """
        The from base must provide the 3' pointer, and to must provide 5'.
        """
        if undoStack==None:
            undoStack = self.undoStack()
        if macro:
            undoStack.beginMacro("Install 3-5 Xover")
        c = self.Connect3To5Command(strandType, self, fromIndex, toVhelix,\
                                    toIndex)
        undoStack.push(c)
        if macro:
            self.thoughtPolice(undoStack)  # Check for inconsistencies, fix one-base Xovers, etc
            toVhelix.thoughtPolice(undoStack=undoStack)
            undoStack.endMacro()
    
    def removeXoversAt(self, strandType, idx):
        fromBase = self._strand(strandType)[idx]
        for toBase in (fromBase._3pBase, fromBase._5pBase):
            if toBase==None:
                continue
            if toBase._vhelix != self:
                self.removeXoverTo(strandType, idx, toBase._vhelix, toBase._n)

    def removeXoverTo(self, strandType, fromIndex, toVhelix, toIndex, macro=True, undoStack=None):
        strand = self._strand(strandType)
        fromBase = strand[fromIndex]
        toBase = toVhelix._strand(strandType)[toIndex]
        if fromBase._5pBase == toBase:
            fromBase, toBase = toBase, fromBase
        if fromBase._3pBase != toBase or fromBase != toBase._5pBase:
            raise IndexError("Crossover does not exist to be removed.")
        if undoStack==None:
            undoStack = self.undoStack()
        if macro:
            undoStack.beginMacro("Remove Xover")
        c = fromVH.Break3To5Command(strandType, fromVH, fromIndex)
        undoStack.push(c)
        if macro:
            self.thoughtPolice(undoStack)  # Check for inconsistencies, fix one-base Xovers, etc
            toVhelix.thoughtPolice(undoStack=undoStack)
            undoStack.endMacro()
        
    def installLoop(self, strandType, index, loopsize):
        """
        Main function for installing loops and skips
        -1 is a skip, +N is a loop
        """
        c = self.LoopCommand(self, strandType, index, loopsize)
        self.undoStack().push(c)
    # end def

    def applyColorAt(self, colorName, strandType, index):
        """docstring for applyColorAt"""
        strand = self._strand(strandType)
        startBase = strand[index]
        # traverse to 5' end
        base = startBase
        while not base.is5primeEnd():
            base.setColor(colorName)
            base = base.get5pBase()  # advance to next
            if base == startBase:  # check for circular path
                return
        base.setColor(colorName)  # last 5' base
        # traverse to 3' end
        if not startBase.is3primeEnd():
            base = startBase.get3pBase()  # already processed startBase
            while not base.is3primeEnd():
                base.setColor(colorName)
                base = base.get3pBase()  # advance to next
            base.setColor(colorName)  # last 3' base
        self.emitBasesModifiedIfNeeded()

    def setFloatingXover(self, strandType=None, fromIdx=None, toPoint=None):
        """The floating crossover is a GUI hack that is the
        temporary crossover shown while the user is using the
        force tool (pencil tool right click) that has a 3' end
        wherever the user clicked / is dragging from and ends
        beneath the mouse."""
        if self.floatingXoverBase:
            self.floatingXoverBase._floatingXoverDestination = None
            self.floatingXoverBase = None
        if strandType==None or fromIdx==None or toPoint==None:
            self.hasBeenModified()
            self.emitBasesModifiedIfNeeded()
            return
        newXoverBase = self._strand(strandType)[fromIdx]
        newXoverBase._floatingXoverDestination = toPoint
        self.floatingXoverBase = newXoverBase
        self.hasBeenModified()
        self.emitBasesModifiedIfNeeded()

    ################ Private Base Modification API ###########################
    # The Notification Responsibilities of a Command
    #   1) Call vh.hasBeenModified() on every VirtualHelix that is modified.
    #      Judiciously use this method, since all it really does is add the VH
    #      it is called on to a list of dirty VH in the dnapart.
    #   2) Call vh.emitBasesModifiedIfNeeded() when you are done with a command.
    #      This actually emits the signals (this way, Base can automatically
    #      decide which VH were dirtied yet a command that affects 20 bases doesn't
    #      result in 20 duplicate basesModified signals being emitted)
    
    def thoughtPolice(self, undoStack):
        """Make sure that self obeys certain limitations, force it to if it doesn't"""
        for strandType in (StrandType.Scaffold, StrandType.Staple):
            strand = self._strand(strandType)
            for i in range(len(strand)):
                b = strand[i]
                hasNeighborL = b._hasNeighborL()
                hasNeighborR = b._hasNeighborR() 
                hasXoverL = b._hasCrossoverL()
                hasXoverR = b._hasCrossoverR()
                if hasXoverL and not hasNeighborR:
                    self.connectStrand(strandType, i, i+1, macro=False, undoStack=undoStack)
                if hasXoverR and not hasNeighborL:
                    self.connectStrand(strandType, i-1, i, macro=False, undoStack=undoStack)
    
    class LoopCommand(QUndoCommand):
        def __init__(self, virtualHelix, strandType, index, loopsize):
            super(VirtualHelix.LoopCommand, self).__init__()
            self._vh = virtualHelix
            self._strandType = strandType
            self._index = index
            self._loopsize = loopsize
            self._oldLoopsize = None

        def redo(self):
            if self._vh.hasStrandAt(self._strandType, self._index):
                loop = self._vh._loop(self._strandType)
                self._oldLoopsize = 0
                if self._loopsize != 0: # if we are not removing the loop
                    if self._index in loop:
                        self._oldLoopsize = loop[self._index]
                    # end if
                    loop[self._index] = self._loopsize # set the model
                else: # trying to set the loop to zero so get rid of it! 
                    if self._index in loop:
                        self._oldLoopsize = loop[self._index]
                        del loop[self._index]
                    # end if
                # end else
                self._vh.hasBeenModified()
                self._vh.emitBasesModifiedIfNeeded()

        def undo(self):
            if self._vh.hasStrandAt(self._strandType, self._index):
                loop = self._vh._loop(self._strandType)
                assert(self._oldLoopsize != None)  # Must redo/apply before undo
                if self._oldLoopsize != 0: # if we are not removing the loop
                    loop[self._index] = self._oldLoopsize
                else: 
                    if self._index in loop:
                        del loop[self._index]
                    # end if
                # end else
                self._vh.hasBeenModified()
                self._vh.emitBasesModifiedIfNeeded()

    class ConnectStrandCommand(QUndoCommand):
        def __init__(self, virtualHelix, strandType, startIndex, endIndex):
            super(VirtualHelix.ConnectStrandCommand, self).__init__()
            self._vh = virtualHelix
            self._strandType = strandType
            self._startIndex = startIndex
            self._endIndex = endIndex
            self._oldLinkage = None

        def redo(self):
            # Sets {s.n, (s+1).np, ..., (e-2).np, (e-1).np, e.p}
            # st s, s+1, ..., e-1, e are connected
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage = []
            if self._vh.directionOfStrandIs5to3(self._strandType):
                for i in range(self._startIndex, self._endIndex):
                    ol.append(strand[i]._set3Prime(strand[i + 1]))
            else:
                for i in range(self._startIndex, self._endIndex):
                    ol.append(strand[i]._set5Prime(strand[i + 1]))
            self._vh.emitBasesModifiedIfNeeded()

        def undo(self):
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage
            assert(ol != None)  # Must redo/apply before undo
            if self._vh.directionOfStrandIs5to3(self._strandType):
                for i in range(self._endIndex - 1, self._startIndex - 1, -1):
                    strand[i]._unset3Prime(strand[i + 1],\
                                           *ol[i - self._startIndex])
            else:
                for i in range(self._endIndex - 1, self._startIndex - 1, -1):
                    strand[i]._unset5Prime(strand[i + 1],\
                                           *ol[i - self._startIndex])
            self._vh.emitBasesModifiedIfNeeded()

    class ClearStrandCommand(QUndoCommand):
        def __init__(self, virtualHelix, strandType, startIndex, endIndex):
            super(VirtualHelix.ClearStrandCommand, self).__init__()
            self._vh = virtualHelix
            self._strandType = strandType
            self._startIndex = startIndex
            self._endIndex = endIndex
            self._oldLinkage = None

        def redo(self):
            # Clears {s.n, (s+1).np, ..., (e-1).np, e.p}
            # Be warned, start index and end index become endpoints
            # if this is called in the middle of a connected strand
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage = []
            if self._vh.directionOfStrandIs5to3(self._strandType):
                for i in range(self._startIndex - 1, self._endIndex):
                    leftBase, rightBase = strand[i], strand[i+1]
                    # Clear i.next
                    ol.append(leftBase._set3Prime(None))
                    # Clear (i+1)prev
                    ol.append(rightBase._set5Prime(None))
            else:
                for i in range(self._startIndex - 1, self._endIndex):
                    leftBase, rightBase = strand[i], strand[i+1]
                    # Clear i.next
                    ol.append(leftBase._set5Prime(None))
                    # Clear (i+1).prev
                    ol.append(rightBase._set3Prime(None))
            self._vh.emitBasesModifiedIfNeeded()

        def undo(self):
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage
            assert(ol != None)  # Must redo/apply before undo
            if self._vh.directionOfStrandIs5to3(self._strandType):
                for i in range(self._endIndex - 1, self._startIndex - 2, -1):
                    strand[i+1]._unset5Prime(None, *ol.pop())
                    strand[i]._unset3Prime(None, *ol.pop())
            else:
                for i in range(self._endIndex - 1, self._startIndex - 2, -1):
                    strand[i+1]._unset3Prime(None, *ol.pop())
                    strand[i]._unset5Prime(None, *ol.pop())
            self._vh.emitBasesModifiedIfNeeded()

    class Connect3To5Command(QUndoCommand):
        def __init__(self, strandType, fromHelix, fromIndex, toHelix, toIndex):
            super(VirtualHelix.Connect3To5Command, self).__init__()
            self._strandType = strandType
            self._fromHelix = fromHelix
            self._fromIndex = fromIndex
            self._toHelix = toHelix
            self._toIndex = toIndex

        def redo(self):
            fromB = self._fromHelix._strand(self._strandType)[self._fromIndex]
            toB = self._toHelix._strand(self._strandType)[self._toIndex]
            self._undoDat = fromB._set3Prime(toB)
            self._fromHelix.emitBasesModifiedIfNeeded()

        def undo(self):
            fromB = self._fromHelix._strand(self._strandType)[self._fromIndex]
            toB = self._toHelix._strand(self._strandType)[self._toIndex]
            assert(self._undoDat)  # Must redo/apply before undo
            fromB._unset3Prime(toB, *self._undoDat)
            self._fromHelix.emitBasesModifiedIfNeeded()

    class Break3To5Command(QUndoCommand):
        def __init__(self, strandType, vhelix, index):
            super(VirtualHelix.Break3To5Command, self).__init__()
            self._strandType = strandType
            self._base = vhelix._strand(strandType)[index]

        def redo(self):
            base = self._base
            self._old3pBase = base._3pBase
            base._set3Prime(None)
            base._vhelix.emitBasesModifiedIfNeeded()

        def undo(self):
            assert(self._old3pBase)
            base = self._base
            base._set3Prime(self._old3pBase)
            base._vhelix.emitBasesModifiedIfNeeded()

    class SetNumBasesCommand(QUndoCommand):
        def __init__(self, vhelix, newNumBases):
            super(VirtualHelix.SetNumBasesCommand, self).__init__()
            self.vhelix = vhelix
            self.newNumBases = newNumBases

        def redo(self, actuallyUndo=False):
            vh = self.vhelix
            if actuallyUndo:
                newNumBases, oldNB = self.oldNumBases, self.newNumBases
            else:
                self.oldNumBases = vh.numBases()
                newNumBases, oldNB = self.newNumBases, self.oldNumBases
            if vh.part():
                # If we are attached to a dnapart we must obey its dimensions
                assert(vh.part().numBases() == newNumBases)
            if newNumBases > oldNB:
                for n in range(oldNB, newNumBases):
                    vh._stapleBases.append(Base(vh, StrandType.Staple, n))
                    vh._scaffoldBases.append(Base(vh, StrandType.Scaffold, n))
            else:
                del vh._stapleBases[oldNB:-1]
                del vh._scaffoldBases[oldNB:-1]
            vh.dimensionsModified.emit()

        def undo(self):
            self.redo(actuallyUndo=True)

    ################################ Crossovers ##############################
    def potentialCrossoverList(self, facingRight, strandType):
        """Returns a list of [neighborVirtualHelix, index] potential
        crossovers"""
        ret = []  # LUT = Look Up Table
        part = self._part
        luts = (part.scafL, part.scafR, part.stapL, part.stapR)

        # these are the list of crossover points simplified
        lut = luts[int(facingRight) +\
                   2 * int(strandType == StrandType.Staple)]

        neighbors = self.neighbors()
        for p in range(len(neighbors)):
            neighbor = neighbors[p]
            if not neighbor:
                continue
            for i, j in product(range(0, self.numBases(), part.step), lut[p]):
                index = i + j
                ret.append([neighbor, index])
        return ret

    def crossoverAt(self, strandType, fromIndex, neighbor, toIndex):
        return

    def scaffoldBase(self, index):
        """docstring for scaffoldBase"""
        return self._scaffoldBases[index]

    def stapleBase(self, index):
        """docstring for stapleBase"""
        return self._stapleBases[index]
    
    def possibleNewCrossoverAt(self, strandType, fromIndex, neighbor, toIndex):
        """
        Return true if scaffold could crossover to neighbor at index.
        Useful for seeing if potential crossovers from potentialCrossoverList
        should be presented as points at which new a new crossover can be
        formed.
        """
        fromB = self._strand(strandType)[fromIndex]
        toB = neighbor._strand(strandType)[toIndex]
        if fromB.isCrossover() or toB.isCrossover():
            return False
        else:
            if strandType == StrandType.Scaffold:
                return  not self.scaffoldBase(fromIndex).isEmpty() and \
                    not neighbor.scaffoldBase(toIndex).isEmpty()
            else:
                return  not self.stapleBase(fromIndex).isEmpty() and \
                    not neighbor.stapleBase(toIndex).isEmpty()

    def getLeftScafPreCrossoverIndexList(self):
        return self.potentialCrossoverList(False, StrandType.Scaffold)

    def getRightScafPreCrossoverIndexList(self):
        return self.potentialCrossoverList(True, StrandType.Scaffold)

    def getLeftStapPreCrossoverIndexList(self):
        return self.potentialCrossoverList(False, StrandType.Staple)

    def getRightStapPreCrossoverIndexList(self):
        return self.potentialCrossoverList(True, StrandType.Staple)

    def neighbors(self):
        """The part (which controls helix layout) decides who
        the virtualhelix's neighbors are. A list is returned,
        possibly containing None in some slots, so that
        neighbors()[i] corresponds to the neighbor in direction
        i (where the map between directions and indices is defined
        by the part)"""
        return self._part.getVirtualHelixNeighbors(self)

    #################### Archiving / Unarchiving #############################
    # A helper method; not part of the archive protocol
    def encodeStrand(self, strandType):
        strand = self._strand(strandType)
        numBases = self.numBases()
        strdir = "5->3" if self.directionOfStrandIs5to3(strandType) else "3->5"
        return "(%s) " % (strdir) + " ".join(str(b) for b in strand)

    def fillSimpleRep(self, sr):
        """Fills sr with a representation of self in terms
        of simple types (strings, numbers, objects, and arrays/dicts
        of objects that also implement fillSimpleRep)"""
        sr['.class'] = "VirtualHelix"
        sr['tentativeHelixID'] = self.number()  # Not used... for readability
        sr['staple'] = self.encodeStrand(StrandType.Staple)
        sr['scafld'] = self.encodeStrand(StrandType.Scaffold)

    # First objects that are being unarchived are sent
    # ClassNameFrom.classAttribute(incompleteArchivedDict)
    # which has only strings and numbers in its dict and then,
    # sometime later (with ascending finishInitPriority) they get
    # finishInitWithArchivedDict, this time with all entries
    finishInitPriority = 1.0  # AFTER DNAParts finish init

    def finishInitWithArchivedDict(self, completeArchivedDict):
        scaf = re.split('\s+', completeArchivedDict['scafld'])[1:]
        stap = re.split('\s+', completeArchivedDict['staple'])[1:]
        # Did the init method set the number of bases correctly?
        assert(len(scaf) == len(stap) and len(stap) == self.numBases())
        for i in range(len(scaf)):
            self._scaffoldBases[i].setConnectsFromString(scaf[i])
            self._stapleBases[i].setConnectsFromString(stap[i])
