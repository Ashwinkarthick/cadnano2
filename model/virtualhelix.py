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
from math import modf
from random import Random
import re, sys, os
from exceptions import AttributeError, IndexError
from itertools import product, imap, repeat
from cadnano import app, ignoreEnv

from .enum import LatticeType, Parity, StrandType, BreakType
from .enum import Crossovers, EndType
from .base import Base
from views import styles
from rangeset import RangeSet
from vstrand import VStrand
from vbase import VBase
import strand

import util

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QObject', 'pyqtSignal', 'QTimer'] )
util.qtWrapImport('QtGui', globals(), [ 'QUndoCommand', 'QUndoStack', \
                                        'QColor'] )

class VirtualHelix(QObject):
    """Stores staple and scaffold routing information."""
    prohibitSingleBaseCrossovers = True
    if os.environ.get('CADNANO_NO_THOUGHTPOLICE', False) and not ignoreEnv():
        prohibitSingleBaseCrossovers = False

    basesModifiedSignal = pyqtSignal()
    dimensionsModifiedSignal = pyqtSignal()

    def __init__(self, numBases=21, idnum=0, incompleteArchivedDict=None):
        """
        numBases=21, 
        idnum=0, 
        incompleteArchivedDict is from the decoder
        """
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
        self.vScaf = VStrand(self)
        self.vStap = VStrand(self)
        self.vScaf._setVHelix(self)
        self.vStap._setVHelix(self)
        # As is the floatingXoverBase if there is one
        self.floatingXoverBase = None

        """
        This is for inserts and skips. A dictionary for inserts and skips is
        added for inserts and skips of the form { index: count }
        + count indicates insert
        - count indicates skip
        """
        
        # unused
        self._stapleInserts = {}
        
        if incompleteArchivedDict != None and incompleteArchivedDict.get('inserts'):
            self._scaffoldInserts = dict((int(k), v) for k,v in incompleteArchivedDict['inserts'].iteritems())
        elif incompleteArchivedDict != None and incompleteArchivedDict.get('loops'):
            self._scaffoldInserts = dict((int(k), v) for k,v in incompleteArchivedDict['loops'].iteritems())
        else:
            self._scaffoldInserts  = {}
            
        # For VirtualHelix that don't live inside a part (maybe they were
        # created in a script) this holds the undo stack.
        self._privateUndoStack = None
        # numBases is a simulated property that corresponds to the
        # length of _stapleBases and _scaffoldBases
        if incompleteArchivedDict:
            numBases = len(re.split('\s+',\
                                    incompleteArchivedDict['staple'])) - 1
        self.setNumBases(numBases, notUndoable=True)
        
        self._sequenceForScafCache = None
        self._sequenceForStapCache = None

        self._isSeqBlank = True

    ######################################################################
    ######################## New Model Quarantine ########################
    ######################################################################
    def scaf(self, idx=None):
        if idx == None:
            return self.vScaf
        else:
            return VBase(self.vScaf, idx)

    def stap(self, idx=None):
        if idx == None:
            return self.vStap
        else:
            return VBase(self.vStap, idx)

    def model1String(self):
        """ Same as __repr__ but uses the new model"""
        scaf = '%-2iScaffold: ' % self.number() + self.scaf().model1String()
        stap = '%-2iStaple:   ' % self.number() + self.stap().model1String()
        return scaf + '\n' + stap

    def chk(self):
        """ Check the new model vs the old model (TEMPORARY) """
        oldModelStr = repr(self)
        newModelStr = self.model1String()
        if oldModelStr != newModelStr:
            print "MISMATCH old, new"
            print oldModelStr
            print newModelStr

    def vStrand(self, strandType):
        """A hack that returns the vStrand corresponding to strandType.
        You should use vhelix.vScaf and vhelix.vStap to communicate with the
        strands directly."""
        if strandType == StrandType.Scaffold:
            return self.vScaf
        elif strandType == StrandType.Staple:
            return self.vStap
        else:
            raise IndexError("%s is not Scaffold=%s or Staple=%s" % \
                         (strandType, StrandType.Scaffold, StrandType.Staple))

    def vStrandScaf(self):
        return self.vScaf

    def vStrandStap(self):
        return self.vStap

    ######################################################################
    ######################## End New Model Quarantine ####################
    ######################################################################

    def resetSequenceCache(self):
        self._sequenceForScafCache = None
        self._sequenceForStapCache = None
    # end def

    def assertConsistent(self):
        for strandType in (StrandType.Scaffold, StrandType.Staple):
            for b in self._strand(strandType):
                if b._neighbor3p():
                    neighbor = b._neighbor3p()
                    if not neighbor._neighbor5p() == b:
                        print "Doubly Linked List broken at VH %i, %s strand, base %i, 3p"\
                              %(self.number(),\
                                "scaf" if strandType == StrandType.Scaffold else "stap",\
                                b._n)
                    correctNeighborForCoords = neighbor._vhelix._strand(neighbor._strandtype)[neighbor._n]
                    if neighbor != correctNeighborForCoords:
                        print "3p neighbor of base at VH %i, %s strand, base %i is\
                               not the base it claims to be"\
                               %(self.number(),\
                                 "scaf" if strandType == StrandType.Scaffold else "stap",\
                                 b._n)
                # end if b._neighbor3p()
                if b._neighbor5p():
                    neighbor = b._neighbor5p()
                    if not neighbor._neighbor3p() == b:
                        print "Doubly Linked List broken at VH %i, %s strand, base %i, 5p"\
                              %(self.number(),\
                                "scaf" if strandType == StrandType.Scaffold else "stap",\
                                b._n)
                    correctNeighborForCoords = neighbor._vhelix._strand(neighbor._strandtype)[neighbor._n]
                    if neighbor != correctNeighborForCoords:
                        print "5p neighbor of base at VH %i, %s strand, base %i is\
                               not the base it claims to be"\
                               %(self.number(),\
                                 "scaf" if strandType == StrandType.Scaffold else "stap",\
                                 b._n)

    def __str__(self):
        return 'vh%i' % self.number()

    def __repr__(self):
        """
        Returns ASCII representation of the contents of this virtualhelix,
        connected to the updated model.
        """
        # scaf = '%-2iScaffold: ' % self.number() + \
        #                     ' '.join((str(b) for b in self._scaffoldBases))
        # stap = '%-2iStaple:   ' % self.number() + \
        #                         ' '.join((str(b) for b in self._stapleBases))
        scaf = '%-2iScaffold: ' % self.number() + self.scaf().model1String()
        stap = '%-2iStaple:   ' % self.number() + self.stap().model1String()
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

    def palette(self):
        if self.part():
            return self.part().palette()
        return styles.default_palette

    def numBases(self):
        assert(len(self._stapleBases) == len(self._scaffoldBases))
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
                                         oldNB-1, newNumBases)
            c1 = self.ClearStrandCommand(self, StrandType.Staple,\
                                         oldNB-1, newNumBases)
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

    def strandDrawn5To3(self, vstrand):
        isScaf = vstrand == self.vScaf
        isEven = (self._number%2) == 0
        return isEven == isScaf

    def directionOfStrandIs5to3(self, strandtype):
        """
        Even scaffold strands and odd staple strands are displayed
        in the 5' to 3' direction (left to right in the view).
        """
        isScaf = strandtype == StrandType.Scaffold
        isEven = (self._number%2) == 0
        return isEven == isScaf

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
            raise IndexError("%s is not Scaffold=%s or Staple=%s" % \
                         (strandType, StrandType.Scaffold, StrandType.Staple))

    def _insert(self, strandType):
        """The returned insert list should be considered privately
        mutable"""
        return self._scaffoldInserts
        # if strandType == StrandType.Scaffold:
        #     return self._scaffoldInserts
        # elif strandType == StrandType.Staple:
        #     return self._stapleInserts
        # else:
        #     raise IndexError("%s is not Scaffold=%s or Staple=%s" % \
        #                  (strandType, StrandType.Scaffold, StrandType.Staple))

    def insert(self, strandType):
        """
        This insert method returns the scaffold inserts as is and then 
        check the staple strand for a presense of a base 
        before indicating a insert
        """
        if strandType == StrandType.Scaffold:
            return self._scaffoldInserts
        elif strandType == StrandType.Staple:
            ret = {}
            for index, insertsize in self._scaffoldInserts.iteritems():
                if self.hasBaseAt(strandType, index):
                    ret[index] = insertsize
            return ret
        else:
            raise IndexError("%s is not Scaffold=%s or Staple=%s" % \
                         (strandType, StrandType.Scaffold, StrandType.Staple))

    ############################## Access to Bases ###########################
    def indexOfRightmostNonemptyBase(self):
        """
        During reduction of the number of bases in a part,
        the first click removes empty bases from the right hand
        side of the part (red left-facing arrow). This method
        is used on each vhelix by the part to determine the
        numBases that will effect such a reduction.
        """
        # ret = -1
        #  for strandType in (StrandType.Scaffold, StrandType.Staple):
        #      strand = self._strand(strandType)
        #      for i in range(len(strand)):
        #          if not strand[i].isEmpty():
        #              ret = max(ret, i)
        #  return ret
        filtScaffold = max(map(lambda b: b._n if not b.isEmpty() else -1, \
                                            self._strand(StrandType.Scaffold)))
        filtStaple = max(map(lambda b: b._n if not b.isEmpty() else -1, \
                                            self._strand(StrandType.Staple)))
        return max(filtScaffold, filtStaple)

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

    def hasEmptyAt(self, strandType, index):
        base = self._baseAt(strandType, index)
        if not base:
            return False
        else:
            return base.isEmpty()

    def getDragBound(self, strandType, index):
        base = self._baseAt(strandType, index)
        if not base:
            return False
        if base.isEnd() == 5:
            # keep checking natural 5' neighbor until we hit something
            while True:
                nat5 = base._natNeighbor5p()
                if nat5 == None:  # ran out of neighbors
                    break
                if not nat5.isEmpty():  # hit non-empty base
                    break
                base = nat5
        elif base.isEnd() == 3:
            # keep checking natural 3' neighbor until we hit something
            while True:
                nat3 = base._natNeighbor3p()
                if nat3 == None:  # ran out of neighbor
                    break
                if not nat3.isEmpty():  # hit non-empty base
                    break
                base = nat3
        else:
            print "!"
        return base._n

    def hasInsertOrSkipAt(self, strandType, index):
        """
        check for key "index" in the insert dictionary based on strandtype
        returns 0 if no insert or skip and returns the length of the skip
        otherwise
        """
        # For now, inserts and skips are only in the scaffold
        if index in self._insert(StrandType.Scaffold):
        # if index in self._insert(strandType):
            return self._insert(StrandType.Scaffold)[index]
        else:
            return 0

    # def getEndpoints(self, strandType):
    #     """docstring for getEndpoints"""
    #     ends3, ends5 = [], []
    #     strand = self._strand(strandType)
    #     for i in range(len(strand)):
    #         b = strand[i]
    #         if b.is5primeEnd():
    #             ends5.append(i)
    #         if b.is3primeEnd():
    #             ends3.append(i)
    #     return (ends3, ends5)
        
    def getEndpoints(self, strandType):
        """docstring for getEndpoints"""
        strand = self._strand(strandType)
        ends3 = map(lambda b: b._n, filter(lambda b: b.is3primeEnd(), strand))
        ends5 = map(lambda b: b._n, filter(lambda b: b.is5primeEnd(), strand))
        return (ends3, ends5)
    # end def

    # def getSegmentsAndEndpoints(self, strandType):
    #     """Returns a list of segments, endpoints of self in the format
    #     ([(startIdx, endIdx), ...],
    #      [3pEndIdx1, 3pEndIdx2, ...], 
    #      [5pEndIdx1, ...])
    #     where startIdx and endIdx can be 1.5, 2.5 etc (multiply by base
    #     width to see where to draw the lines)"""
    #     segments, ends3, ends5 = [], [], []
    #     strand = self._strand(strandType)
    #     i, s = 0, None
    #     curColor = None
    #     # s is the start index of the segment
    #     # segColor is the color of the current segment
    #     for i in range(len(strand)):
    #         b = strand[i]
    #         
    #         #Segments
    #         if b._connectsToNatL():
    #             if curColor and b.getColor() and\
    #                curColor.name() != b.getColor().name():
    #                 # print "<B1 %s %s>"%(curColor.name(), b.getColor().name())
    #                 segments.append((s,i))
    #                 s = i
    #                 curColor = b.getColor()
    #             if s==None:
    #                 s = i
    #                 curColor = b.getColor()
    #             else:
    #                 pass
    #         else: # not connected to base on left
    #             if s==None:
    #                 pass
    #             else:
    #                 # print "<B2>"
    #                 segments.append((s,i))
    #                 s = None
    #         if b._connectsToNatR():
    #             if s==None:
    #                 s = i+.5
    #                 curColor = b.getColor()
    #             else:
    #                 pass
    #         else: # not connected to base on right
    #             if s==None:
    #                 pass
    #             else:
    #                 # print "<B3>"
    #                 segments.append((s,i+.5))
    #                 s = None
    #         #Endpoints
    #         if b.is5primeEnd():
    #             ends5.append(i)
    #         if b.is3primeEnd():
    #             ends3.append(i)
    #     return (segments, ends3, ends5)
        
    def getSegmentsAndEndpoints(self, strandType):
        """Returns a list of segments, endpoints of self in the format
        ([(startIdx, endIdx), ...],   # These "indexes" are floats
         [3pEndIdx1, 3pEndIdx2, ...], 
         [5pEndIdx1, ...])
        where startIdx and endIdx can be 1.5, 2.5 etc (multiply by base
        width to see where to draw the lines)"""
    
        strand = self._strand(strandType)
        s = [-1]
        curColor = None
        # s is the start index of the segment
        # segColor is the color of the current segment
        def segmentGet(b, s, curColor):
            ret = None
            #Segments
            if b._connectsToNatL():
                if curColor and b.getColor() and \
                   curColor.name() != b.getColor().name():
                    # print "<B1 %s %s>"%(curColor.name(), b.getColor().name())
                    ret = (s[0], b._n)
                    s[0] = b._n
                    curColor = b.getColor()
                if s[0] == -1:
                    s[0] = b._n
                    curColor = b.getColor()
                else:
                    pass
            else: # not connected to base on left
                if s[0] == -1:
                    pass
                else:
                    # print "<B2>"
                    ret = (s[0], b._n)
                    s[0] = -1
            if b._connectsToNatR():
                if s[0] == -1:
                    s[0] = b._n + .5
                    curColor = b.getColor()
                else:
                    pass
            else: # not connected to base on right
                if s[0] == -1:
                    pass
                else:
                    # print "<B3>"
                    ret = (s[0], b._n + .5)
                    s[0] = -1
            return ret
        # end def
        segments = filter(lambda x: True if x != None else False, \
                    map(lambda b: segmentGet(b, s, curColor), strand) \
                    )
        ends3 = map(lambda b: b._n, filter(lambda b: b.is3primeEnd(), strand) )
        ends5 = map(lambda b: b._n, filter(lambda b: b.is5primeEnd(), strand) )
        return (segments, ends3, ends5)
    # end def

    def get3PrimeXovers(self, strandType):
        """
        Returns a tuple of tuples of the form 
        ((fromVH, fromIdx), (toVH, strandType, toIdx))
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
                    ret.append(( (self, base._n),\
                                 (base._3pBase.vhelix(),\
                                  base._3pBase._strandtype,\
                                  base._3pBase._n) ))
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
        # hue = 47 * idx + 31 * self.number()
        # return QColor.fromHsl(hue % 256, 255, 128)
        # print "colorOfBase", idx, c.name(), self._stapleBases[idx].getColor()
        return self._strand(strandType)[idx].getColor()

    def shouldHighlight(self, strandType, idx):
        return self._strand(strandType)[idx]._shouldHighlight

    def sequenceForVirtualStrand(self, strandType):
        if strandType == StrandType.Scaffold:
            if self._sequenceForScafCache != None:
                return self._sequenceForScafCache
            seq = "".join([b.sequence()[0] for b in self._strand(strandType)])
            self._sequenceForScafCache = seq
        else: #Staple Strand
            if self._sequenceForStapCache != None:
                return self._sequenceForStapCache
            seq = "".join([b.lazy_sequence()[0] for b in self._strand(strandType)])
            self._sequenceForStapCache = seq
        return seq

    def sequenceForInsertAt(self, strandType, idx):
        if strandType == StrandType.Scaffold:
            return self._strand(strandType)[idx].sequenceOfInsert()
        else:
            return self._strand(strandType)[idx].lazy_sequenceOfInsert()

    def _basesConnectedTo(self, strandType, idx):
        """
        Private because it returns a set of Base objects.
        Returns [] if the base at strandType, idx is empty.
        """
        ret = []
        try:
            base = self._strand(strandType)[idx]
        except TypeError:
            print idx
            util.trace(10)
            raw_input()
            sys.exit(1)
        # Back track to the 5' end
        startBase = base
        while base._hasNeighbor5p():
            base = base._neighbor5p()
            if base == startBase:
                break
        startBase = base
        # Move forward through the linked list,
        # adding bases to the (not linked) list
        # we will return
        if not base.isEmpty():
            ret.append(base)
        while base._hasNeighbor3p():
            neighbor = base._neighbor3p()
            if neighbor == startBase:
                break
            ret.append(neighbor)
            base = neighbor
        return ret

    def numBasesConnectedTo(self, strandType, idx):
        """
        Returns [] if the base at strandType, idx is empty.
        """
        ret = 0
        try:
            base = self._strand(strandType)[idx]
        except TypeError:
            print idx
            util.trace(10)
            raw_input()
            sys.exit(1)
        # Back track to the 5' end
        startBase = base
        while base._hasNeighbor5p():
            base = base._neighbor5p()
            if base == startBase:
                break
        startBase = base
        # Move forward through the linked list,
        # adding bases to the (not linked) list
        # we will return
        if not base.isEmpty():
            ret += (1 + self.hasInsertOrSkipAt(StrandType.Scaffold, base._n))
        while base._hasNeighbor3p():
            neighbor = base._neighbor3p()
            if neighbor == startBase:
                break
            ret += (1 + self.hasInsertOrSkipAt(StrandType.Scaffold, base._n))
            base = neighbor
        return ret

    def fivePEndOfSegmentThrough(self, strandType, idx):
        bases = self._basesConnectedTo(strandType, idx)
        if bases:
            return (bases[0]._vhelix, bases[0]._strandtype, bases[0]._n)
        else:
            return None

    def undoStack(self):
        if self._privateUndoStack != None:
            return self._privateUndoStack
        if self.part() != None:
            return self.part().undoStack()
        if self._privateUndoStack == None:
            #print "Creating detached undo stack for %s" % self
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
    def connectsToNat5p(self, strandType, idx):
        return self._strand(strandType)[idx]._connectsToNat5p()
    def connectsToNat3p(self, strandType, idx):
        return self._strand(strandType)[idx]._connectsToNat3p()
    def connectsToNatR(self, strandType, idx):
        return self._strand(strandType)[idx]._connectsToNatR()
    def connectsToNatL(self, strandType, idx):
        return self._strand(strandType)[idx]._connectsToNatL()

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
    def setHasBeenModified(self):
        if self.part():
            self.part().modifiedVHSet.add(self)
        else:
            self.basesModifiedSignal.emit()
        return self

    def emitBasesModifiedIfNeeded(self):
        part = self.part()
        if part:
            if part.basesModifySilently:
                return
            # for vh in list(self.part().modifiedVHSet):
            #     vh.basesModifiedSignal.emit()
            map(lambda vh: vh.basesModifiedSignal.emit(), list(self.part().modifiedVHSet))
            part.modifiedVHSet.clear()
            part._recalculateStrandLengths()
            part.modificationCondition.acquire()
            part.modificationCondition.notifyAll()
            part.modificationCondition.release()
        else:
            self.basesModifiedSignal.emit()

    def beginCommand(self, useUndoStack, undoStack, strng):
        """undoStack overrides the default undoStack if it is not None"""
        if useUndoStack:
            if undoStack == None:
                undoStack = self.undoStack()
            assert(undoStack != None)
            undoStack.beginMacro(strng)
        else:
            undoStack = None
        # Acquire lock on part
        part = self.part()
        if part != None:
            part.lock.acquireWrite()
        return undoStack

    def endCommand(self, undoStack, commands, police=False, additionalAffectedBases=None):
        """ Shared command (not to be confused with UndoCommand) suffix"""
        # We allow the caller to pass a single command or multiple commands in
        # a tuple. For the benefit of the code below, we regularize the argument
        # into a tuple.
        if type(commands) not in (list, tuple):
            commands = (commands,)
        # c is the command
        if undoStack != None:
            # for c in commands:
            #     if c != None:
            #         undoStack.push(c)
            map(lambda c: undoStack.push(c) if c != None else None, commands)
            if police:  # Check for inconsistencies, fix one-base Xovers, etc
                self.thoughtPolice(undoStack)
        else:
            if police:  # Check for inconsistencies, fix one-base Xovers, etc
                self.thoughtPolice(undoStack)
            # for c in commands:
            #     if c != None:
            #         c.redo()
            map(lambda c: c.redo() if c != None else None, commands)
        if additionalAffectedBases != None and police:
            affectedVH = set()
            for b in additionalAffectedBases:
                affectedVH.add(b._vhelix)
            for vh in affectedVH:
                if vh != self:
                    vh.thoughtPolice(undoStack)
        if undoStack != None:
            undoStack.endMacro()
        self.resetSequenceCache()
        part = self.part()
        if part != None:
            part.lock.release()

    def connectStrand(self, strandType, startIndex, endIndex, useUndoStack=True,
                      undoStack=None, police=True, color=None, speedy=False):
        """
        Connects sequential bases on a single strand, starting with
        startIndex and ending with etdIndex (inclusive)
        Sets {s.n, (s+1).np, ..., (e-2).np, (e-1).np, e.p}
        """
        undoStack = self.beginCommand(useUndoStack, undoStack, "Extend strand")
        strand = self._strand(strandType)
        vstrand = self.vStrand(strandType)
        #vstrand.connectStrand(startIndex, endIndex,\
        #                      useUndoStack=useUndoStack, undoStack=undoStack)
        startIndex, endIndex = int(startIndex), int(endIndex)
        startIndex = util.clamp(startIndex, 0, len(strand) - 1)
        endIndex = util.clamp(endIndex, 0, len(strand) - 1)
        c = self.ConnectStrandCommand(self, strandType, startIndex, endIndex,\
                                      color=color, speedy=speedy)
        self.endCommand(undoStack, c, police)
        
    def clearAllStrands(self):
        for strandType in (StrandType.Scaffold, StrandType.Staple):
            # print "clearing", strandType
            for idx in range(len(self._strand(strandType))):
                # print idx
                if self.hasBaseAt(strandType, idx):
                    rightBreakIdx = leftBreakIdx = idx
                    while leftBreakIdx > 1:
                        if self.hasCrossoverAt(strandType, leftBreakIdx-1):
                            if self.hasStrandAt(strandType, idx):
                                self.removeXoversAt(strandType, leftBreakIdx-1)
                            break
                        if self.hasEndAt(strandType, leftBreakIdx-1):
                            break
                        leftBreakIdx -= 1
                    while rightBreakIdx < self.numBases():
                        if self.hasCrossoverAt(strandType, rightBreakIdx):
                            if self.hasStrandAt(strandType, idx):
                                self.removeXoversAt(strandType, rightBreakIdx)
                            break
                        if self.hasEndAt(strandType, rightBreakIdx) and rightBreakIdx != idx:
                            break
                        rightBreakIdx += 1
                    # end while
                    # print "executing clear"
                    # print leftBreakIdx, rightBreakIdx
                    self.clearStrand(strandType, leftBreakIdx, rightBreakIdx, useUndoStack=True)
                # end if
            # end for
        # end for
    # end def

    def legacyClearStrand(self, strandType, startIndex, endIndex,\
                    useUndoStack=True,undoStack=None, colorL=None, colorR=None,\
                    police=True, undoDesc="Clear strand"):
        startIndex += -.5 if startIndex < endIndex else .5
        endIndex += .5 if startIndex < endIndex else -.5
        self.clearStrand(strandType, startIndex, endIndex, useUndoStack,\
                         undoStack, colorL, colorR, police, undoDesc)

    def clearStrand(self, strandType, startIndex, endIndex, useUndoStack=True,\
                    undoStack=None, colorL=None, colorR=None, police=True,\
                    undoDesc="Clear Strand"):
        undoStack = self.beginCommand(useUndoStack, undoStack, "Clear strand")
        vstrand = self.vStrand(strandType)
        #vstrand.clearStrand(strandType, startIndex,\
        #                    useUndoStack=useUndoStack, undoStack=undoStack)
        strand = self._strand(strandType)
        startIndex = util.clamp(startIndex, 0, len(strand))
        startIndex = int(startIndex*2.)/2.
        endIndex = util.clamp(endIndex, 0, len(strand))
        endIndex = int(endIndex*2.)/2.

        c = self.ClearStrandCommand(self, strandType, startIndex, endIndex,\
                                    colorL=colorL, colorR=colorR)

        self.endCommand(undoStack, c, police)

    def installXoverFrom3To5(self, strandType, fromIndex, toVhelix, toIndex,\
           useUndoStack=True, undoStack=None, endToTakeColorFrom=3,\
           speedy=False, police=True):
        """
        The from base must provide the 3' pointer, and to must provide 5'.

        The speedy option is for the importer in json_io which doesn't want
        to deal with colors, segment lengths, etc at every intermediate
        stage of the loading process (which calls installXover... for
        *all* of its connections).
        """
        undoStack = self.beginCommand(useUndoStack, undoStack, "Install XOver")
        c = self.Connect3To5Command(strandType, self, fromIndex, toVhelix,\
                                    toIndex, endToTakeColorFrom, speedy=speedy)
        targetBase = toVhelix._strand(StrandType.Scaffold)[0]
        self.endCommand(undoStack, c, police, (targetBase,))

    def removeConnectedStrandAt(self, strandType, idx, useUndoStack=True,\
                                undoStack=None):
        undoStack = self.beginCommand(useUndoStack,\
                                      undoStack, "removeConnectedStrandAt")
        bases = self._basesConnectedTo(strandType, idx)
        c = self.RemoveBasesCommand(bases)
        self.endCommand(undoStack, c, additionalAffectedBases=bases)

    def removeXoversAt(self, strandType, idx, newColor=None,\
                       useUndoStack=True, undoStack=None):
        undoStack = self.beginCommand(useUndoStack, undoStack, "removeXoversAt")
        base = self._strand(strandType)[idx]
        if base._hasCrossoverL():
            base._vhelix.clearStrand(strandType, idx, idx + 0.5, undoStack=undoStack)
        if base._hasCrossoverR():
            base._vhelix.clearStrand(strandType, idx + 0.5, idx + 1, undoStack=undoStack)
        self.endCommand(undoStack, None)

    def removeXoverTo(self, strandType, fromIndex, toVhelix, toIndex,\
                      useUndoStack=True, undoStack=None, endToKeepColor=3,\
                      newColor=None):
        undoStack = self.beginCommand(useUndoStack, undoStack, "removeXoverTo")
        strand = self._strand(strandType)
        fromBase = strand[fromIndex]
        toBase = toVhelix._strand(strandType)[toIndex]
        if fromBase._3pBase != toBase or fromBase != toBase._5pBase:
            raise IndexError("Crossover does not exist to be removed.")
        c = self.Break3To5Command(strandType, self, fromIndex,\
                                  endToKeepColor=endToKeepColor,\
                                  newColor=newColor)
        self.endCommand(undoStack, c)

    def installInsert(self, strandType, index, insertsize, useUndoStack=True,\
                    undoStack=None, speedy=False):
        """
        Main function for installing inserts and skips
        -1 is a skip, +N is a insert
        
        The tool was designed to allow installation only on scaffold, 
        however to allow updating from inserts drawn on staples, we make this tool
        StrandType agnostic
        """
        undoStack = self.beginCommand(useUndoStack, undoStack, "installInsert")
        d = None
        if strandType == StrandType.Scaffold and self._isSeqBlank == False:
            d = self.ApplySequenceCommand(self, StrandType.Scaffold, index, " ")
        c = self.InsertCommand(self, strandType, index, insertsize)
        self.endCommand(undoStack, (d, c))

    def applyColorAt(self, color, strandType, index, useUndoStack=True,\
                     undoStack=None):
        """Determine the connected strand that passes through
        (self, strandType, index) and apply color to every base
        in that strand. If color is none, pick a (bright) random
        color and apply it to every base in that strand"""
        undoStack = self.beginCommand(useUndoStack, undoStack, "applyColorAt")
        bases = self._basesConnectedTo(strandType, index)
        if color == None:
            color = self.palette()[0]
        c = self.ApplyColorCommand(bases, color)
        self.endCommand(undoStack, c)

    def applySequenceAt(self, strandType, index, seqStr, useUndoStack=True,\
                        undoStack=None):
        """
        Finds the 5' end of the oligo going through strandType,index and
        assigns a character of seqStr to every base, traveling towards the
        3' end
        """
        undoStack = self.beginCommand(useUndoStack,\
                                      undoStack,\
                                      "applySequenceAt")
        c = self.ApplySequenceCommand(self, strandType, index, seqStr)
        self.endCommand(undoStack, c)
        self.emitBasesModifiedIfNeeded()

    def floatingXover(self):
        """
        Return the receiver's floating xover in the format:
        ((fromVH, fromStrand, fromIdx), toPt)
        or, if there isn't a floating xover, return
        None
        """
        if self.floatingXoverBase != None:
            fb = self.floatingXoverBase
            return ((fb._vhelix, fb._strandtype, fb._n),\
                    fb.floatingXoverDestination())
        return None

    def setFloatingXover(self, strandType=None, fromIdx=None, toPoint=None):
        """The floating crossover is a GUI hack that is the
        temporary crossover shown while the user is using the
        force tool (pencil tool right click) that has a 3' end
        wherever the user clicked / is dragging from and ends
        beneath the mouse."""
        if self.part():
            if strandType==None or fromIdx==None or toPoint==None:
                self.part().updateFloatingXover.emit(None, None)
            else:
                self.part().updateFloatingXover.emit((self, strandType, fromIdx),
                                                     toPoint)
        if self.floatingXoverBase != None:
            self.floatingXoverBase._floatingXoverDestination = None
            self.floatingXoverBase = None
        if strandType==None or fromIdx==None or toPoint==None:
            self.setHasBeenModified()
            self.emitBasesModifiedIfNeeded()
            return
        newXoverBase = self._strand(strandType)[fromIdx]
        newXoverBase._floatingXoverDestination = toPoint
        self.floatingXoverBase = newXoverBase
        self.setHasBeenModified()
        self.emitBasesModifiedIfNeeded()

    def autoDragToBoundary(self, strandType, idx):
        """docstring for autoDragToBound"""
        dragBound = self.getDragBound(strandType, idx)
        if idx != dragBound:
            self.connectStrand(strandType, idx, dragBound)

    def autoDragAllBreakpoints(self, strandType):
        """Called by dnapart, extends all breakpoints as far as
        they could have manually been dragged in the interface."""
        ends3, ends5 = self.getEndpoints(strandType)
        strand = self._strand(strandType)
        for idx in sorted(ends3 + ends5):
            self.autoDragToBoundary(strandType, idx)

    ################ Private Base Modification API ###########################
    # The Notification Responsibilities of a Command
    #   1) Call vh.setHasBeenModified() on every VirtualHelix that is modified.
    #      Judiciously use this method, since all it really does is add the VH
    #      it is called on to a list of dirty VH in the dnapart.
    #   2) Call vh.emitBasesModifiedIfNeeded() when you are done with a command.
    #      This actually emits the signals (this way, Base can automatically
    #      decide which VH were dirtied yet a command that affects 20 bases doesn't
    #      result in 20 duplicate basesModifiedSignal signals being emitted)

    def thoughtPolice(self, undoStack):
        """
        Make sure that self obeys certain limitations,
        force it to if it doesn't. This currently amounts
        to looking for single base crossovers and making
        a connection so that they are no longer single base
        crossovers.
        """
        if self.prohibitSingleBaseCrossovers:
            for strandType in (StrandType.Scaffold, StrandType.Staple):
                strand = self._strand(strandType)
                # speeding up function to enable map
                def thoughtPolice_sub(b):
                    hasNeighborL = b._hasNeighborL()
                    hasNeighborR = b._hasNeighborR()
                    hasXoverL = b._hasCrossoverL()
                    hasXoverR = b._hasCrossoverR()
                    if hasXoverL and not hasNeighborR:
                        self.connectStrand(strandType, b._n, b._n+1,\
                                           police=False, undoStack=undoStack)
                    if hasXoverR and not hasNeighborL:
                        self.connectStrand(strandType, b._n-1, b._n,\
                                           police=False, undoStack=undoStack)
                # end def
                map(thoughtPolice_sub, strand)
    # end def

    def isSeqBlank(self):
        return self._isSeqBlank
    # end def

    def updateLengthsFrom5pEnds(self):
        """After a file load, bases have an incorrect value for
        base._shouldHighlight. This method fixes that for all bases in strands
        that have a 5' end on self."""
        _, _, scaf5 = self.getSegmentsAndEndpoints(StrandType.Scaffold)
        _, _, stap5 = self.getSegmentsAndEndpoints(StrandType.Staple)
        scaf, stap = self._scaffoldBases, self._stapleBases
        part = self.part()
        for baseNum in scaf5:
            part.modifiedBaseSet.add(scaf[baseNum])
        for baseNum in stap5:
            part.modifiedBaseSet.add(stap[baseNum])
        part._recalculateStrandLengths()

    class ApplySequenceCommand(QUndoCommand):
        def __init__(self, vh, strandType, idx, seqStr):
            """
            Applies seqStr to the oligo connected to (strandType, idx),
            applying the first... [FIX]
            """
            QUndoCommand.__init__(self)
            self._vh = vh
            self._strandType = strandType
            self._idx = idx
            self._seqStr = seqStr
            if seqStr == ' ':
                self._isSeqBlank = True
            else:
                self._isSeqBlank = False
                
        def redo(self):
            vh = self._vh
            self._isOldSeqBlank = vh._isSeqBlank
            vh._isSeqBlank = self._isSeqBlank
                
            bases = vh._basesConnectedTo(StrandType.Scaffold, self._idx)
            charactersUsedFromSeqStr = 0
            self.oldBaseStrs = oldBaseStrs = []
            startBase = vh._strand(StrandType.Scaffold)[self._idx]
            startBaseComplement = vh._strand(StrandType.Staple)[self._idx]
            scafBasesInBase = vh.hasInsertOrSkipAt(StrandType.Scaffold, startBase._n)
            stapBasesInBase = vh.hasInsertOrSkipAt(StrandType.Staple, startBase._n)
            if stapBasesInBase and self._strandType == StrandType.Staple:
                # We are applying to a staple insert
                startBase = vh._strand(StrandType.Staple)[self._idx]
                self.oldInsertSeq = startBase._sequence
                if not startBase._sequence:
                    startBase._sequence = " "
                startBase._sequence = startBase._sequence[0] + self._seqStr
                seqLen = len(self._seqStr)
                if seqLen==0:
                    del vh._insert(startBase._strandtype)[startBase._n]
                else:
                    vh._insert(startBase._strandtype)[startBase._n] = seqLen
                # vh.setHasBeenModified()
                # vh.emitBasesModifiedIfNeeded()
                # return
            else:
                # We use this variable to determine if we 
                # need to undo an application to an asymmetrical
                # insert or a strand application, so it always
                # must be present
                self.oldInsertSeq = None
            # We aren't applying to a insert, so we must insert through
            # the entire strand and apply to each pair of complementary
            # bases
            for i in range(len(bases)):
                b = bases[i]
                b._vhelix.resetSequenceCache()
                stap_b = b._vhelix._strand(StrandType.Staple)[b._n]
                numBasesInB = b._vhelix.hasInsertOrSkipAt(StrandType.Scaffold, b._n)+1
                oldBaseStrs.append((b._sequence, stap_b._sequence))
                numBasesToUse = numBasesInB
                if numBasesToUse == 0:
                    seq = " "
                elif charactersUsedFromSeqStr + numBasesToUse <= len(self._seqStr):
                    seq = self._seqStr[charactersUsedFromSeqStr:charactersUsedFromSeqStr+numBasesToUse]
                    charactersUsedFromSeqStr += numBasesToUse
                else:
                    partialSeq = self._seqStr[charactersUsedFromSeqStr:]
                    charactersUsedFromSeqStr = len(self._seqStr)
                    seq = partialSeq.ljust(numBasesToUse)
                
                # if self._strandType == StrandType.Scaffold:
                b._sequence = seq
                # if not stap_b._sequence:
                #     stap_b._sequence = " "
                # stap_b._sequence = util.rcomp(seq)

                
            vh.setHasBeenModified()
            vh.emitBasesModifiedIfNeeded()

        def undo(self):
            vh = self._vh
            vh._isSeqBlank = self._isOldSeqBlank
            
            scafBases = vh._basesConnectedTo(StrandType.Scaffold, self._idx)
            #stapBases = vh._basesConnectedTo(StrandType.Staple, self._idx)
            startBase = vh._strand(StrandType.Scaffold)[self._idx]
            #startBaseComplement = vh._strand(StrandType.Staple)[self._idx]
            scafBasesInBase = vh.hasInsertOrSkipAt(StrandType.Scaffold, startBase._n)
            #stapBasesInBase = vh.hasInsertOrSkipAt(StrandType.Staple, startBase._n)
            
            
            if self.oldInsertSeq != None:
                startBase._sequence = self.oldInsertSeq
                vh.resetSequenceCache()
                vh.setHasBeenModified()
                vh.emitBasesModifiedIfNeeded()
                return
            for i in range(len(scafBases)):
                scafB = scafBases[i]
                scafB._vhelix.resetSequenceCache()
                scafBseq = self.oldBaseStrs[i][0]
                #if self._strandType == StrandType.Scaffold:
                scafB._sequence = scafBseq
                
                # stapB = scafB._vhelix._strand(StrandType.Staple)[scafB._n]
                # stapBseq = self.oldBaseStrs[i][1]
                #stapB._sequence = stapBseq
            # end for
            vh.resetSequenceCache()
            vh.setHasBeenModified()
            vh.emitBasesModifiedIfNeeded()


    class ApplyColorCommand(QUndoCommand):
        def __init__(self, bases, color):
            super(VirtualHelix.ApplyColorCommand, self).__init__()
            self._bases = list(bases)
            if color==None and len(self._bases):
                b = self._bases[0]
                newHue = 199*b._vhelix.number() +\
                         131*int(b._strandtype) +\
                         151*b._n
                color = QColor()
                color.setHsv(newHue%256, 255, 255)
            self._newColor = color

        def redo(self):
            nc = self._newColor
            
            # see commit 54e8b1c48bab8ec2776f for slow version
            
            # fast version below
            self._oldColors = map(Base._setColor, self._bases, repeat(nc, len(self._bases)))
            # shouldn't have to worry about 'b._vhelix' being 'None'
            temp = map(VirtualHelix.setHasBeenModified, (b._vhelix for b in self._bases))
            # temp = filter(lambda b: True if b._vhelix != None else False, self._bases)
            if len(temp) > 0: # check to see if has elements and emit signal
                temp[0].emitBasesModifiedIfNeeded()

        def undo(self):
            oc = self._oldColors
            
            # see commit 54e8b1c48bab8ec2776f for slow version
            
            # fast version below
            bases = reversed(self._bases)
            map(Base._setColor, bases, reversed(oc))
            # shouldn't have to worry about 'b._vhelix' being 'None'
            temp = map(VirtualHelix.setHasBeenModified, (b._vhelix for b in bases))
            # temp = filter(lambda b: True if b._vhelix != None else False, bases)
            if len(temp) > 0: # check to see if has elements and emit signal
                temp[0].emitBasesModifiedIfNeeded()


    class InsertCommand(QUndoCommand):
        def __init__(self, virtualHelix, strandType, index, insertsize):
            super(VirtualHelix.InsertCommand, self).__init__()
            self._vh = virtualHelix
            self._strandType = strandType
            self._index = index
            self._insertsize = insertsize
            self._oldInsertsize = None

        def redo(self):
            if self._vh.hasStrandAt(self._strandType, self._index):
                insert = self._vh._insert(self._strandType)
                self._oldInsertsize = 0
                if self._insertsize != 0: # if we are not removing the insert
                    if self._index in insert:
                        self._oldInsertsize = insert[self._index]
                    # end if
                    insert[self._index] = self._insertsize # set the model
                else: # trying to set the insert to zero so get rid of it! 
                    if self._index in insert:
                        self._oldInsertsize = insert[self._index]
                        del insert[self._index]
                    # end if
                # end else
                # length recalculation highlighting
                part = self._vh.part()
                if part and self._vh.hasBaseAt(StrandType.Staple, self._index):
                    part.modifiedBaseSet.add(self._vh._stapleBases[self._index])
                self._vh.setHasBeenModified()
                self._vh.emitBasesModifiedIfNeeded()

        def undo(self):
            if self._vh.hasStrandAt(self._strandType, self._index):
                insert = self._vh._insert(self._strandType)
                assert(self._oldInsertsize != None)  # Must redo/apply before undo
                if self._oldInsertsize != 0: # if we are not removing the insert
                    insert[self._index] = self._oldInsertsize
                else: 
                    if self._index in insert:
                        del insert[self._index]
                    # end if
                # end else
                # length recalculation highlighting
                part = self._vh.part()
                if part and self._vh.hasBaseAt(StrandType.Staple, self._index):
                    part.modifiedBaseSet.add(self._vh._stapleBases[self._index])
                self._vh.setHasBeenModified()
                self._vh.emitBasesModifiedIfNeeded()


    class RemoveBasesCommand(QUndoCommand):
        def __init__(self, bases):
            super(VirtualHelix.RemoveBasesCommand, self).__init__()
            self.bases = list(bases)
        def redo(self):
            ol = self._oldLinkage = []
            vh = None
            # for b in self.bases:
            #     ol.append(b._set3Prime(None))
            #     ol.append(b._set5Prime(None))
            #     vh = b._vhelix
            # if vh:
            #     vh.emitBasesModifiedIfNeeded()
            
            # fast version of the above
            olA = map(lambda b: b._set3Prime(None), self.bases)
            olB = map(lambda b: b._set5Prime(None), self.bases)
            self._oldLinkage = map(list(zip(olA,olB)))
            temp = filter(lambda b: True if b._vhelix != None else False, self._bases)
            if len(temp) > 0:
                temp[0]._vhelix.emitBasesModifiedIfNeeded()
        def undo(self):
            ol = self._oldLinkage
            vh = None
            # for b in reversed(self.bases):
            #     b._unset5Prime(None, ol.pop())
            #     b._unset3Prime(None, ol.pop())
            #     vh = b._vhelix
            # if vh:
            #     vh.emitBasesModifiedIfNeeded()
            
            # fast version of the above
            bases = reversed(self.bases)
            olB = map(lambda b: b._unset5Prime(ol.pop()), bases)
            olA = map(lambda b: b._unset3Prime(ol.pop()), bases)
            temp = filter(lambda b: True if b._vhelix != None else False, self._bases)
            if len(temp) > 0:
                temp[0]._vhelix.emitBasesModifiedIfNeeded()


    class ConnectStrandCommand(QUndoCommand):
        def __init__(self, virtualHelix, strandType, startIndex, endIndex, color=None, speedy=False):
            super(VirtualHelix.ConnectStrandCommand, self).__init__()
            self._vh = virtualHelix
            self._strandType = strandType
            self._startIndex = startIndex
            self._endIndex = endIndex
            self._oldLinkage = None
            self._colorSubCommand = None
            self._explicitColor = color
            self._speedy = speedy

        def redo(self):
            # Sets {s.n, (s+1).np, ..., (e-2).np, (e-1).np, e.p}
            # st s, s+1, ..., e-1, e are connected
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage = []
            firstIdx = min(self._startIndex, self._endIndex)
            stopIdx = max(self._startIndex, self._endIndex)
            if self._vh.directionOfStrandIs5to3(self._strandType):
                for i in range(firstIdx, stopIdx):
                    ol.append(strand[i]._set3Prime(strand[i + 1]))
            else:
                for i in range(firstIdx, stopIdx):
                    ol.append(strand[i]._set5Prime(strand[i + 1]))
            if not self._speedy or self._strandType != StrandType.Scaffold:
                # Now ensure all connected bases have the same color
                # which gets taken from the startIndex base
                if self._explicitColor == None:
                    color = strand[self._startIndex].getColor()
                else:
                    color = self._explicitColor
                bases = self._vh._basesConnectedTo(self._strandType, self._startIndex)
                self._colorSubCommand = VirtualHelix.ApplyColorCommand(bases, color)
                self._colorSubCommand.redo()
            self._vh.resetSequenceCache()
            self._vh.emitBasesModifiedIfNeeded()

        def undo(self):
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage
            firstIdx = min(self._startIndex, self._endIndex)
            stopIdx = max(self._startIndex, self._endIndex)
            assert(ol != None)  # Must redo/apply before undo
            if self._vh.directionOfStrandIs5to3(self._strandType):
                for i in range(stopIdx - 1, firstIdx - 1, -1):
                    strand[i]._unset3Prime(strand[i + 1],\
                                           *ol[i - firstIdx])
                # end for
            # end if
            else:
                for i in range(stopIdx - 1, firstIdx - 1, -1):
                    strand[i]._unset5Prime(strand[i + 1],\
                                           *ol[i - firstIdx])
                # end for
            # end else
            if self._strandType != StrandType.Scaffold:
                self._colorSubCommand.undo()
            self._vh.resetSequenceCache()
            self._vh.emitBasesModifiedIfNeeded()

    class ClearStrandCommand(QUndoCommand):
        def __init__(self, virtualHelix, strandType, startIndexF, endIndexF, colorL=None, colorR=None):
            super(VirtualHelix.ClearStrandCommand, self).__init__()
            self._vh = virtualHelix
            self._strandType = strandType
            self._startIndexF = min(startIndexF, endIndexF)
            self._endIndexF = max(startIndexF, endIndexF)
            self._oldLinkage = None
            self._colorL = colorL
            self._colorR = colorR
    
        def redo(self):
            # See docs/virtualhelix.pdf for a description of
            # how each parameter is used.
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage = []
            potentialNewEndpoints = []
            insertDict = self._vh._insert(self._strandType)
            self.erasedInsertDictItems = {}
            startIdxF = min(self._startIndexF, self._endIndexF)
            endIdxF = max(self._startIndexF, self._endIndexF)
            startFrac, startIdx = modf(startIdxF)
            endFrac, endIdx = modf(endIdxF)
            startIdx, endIdx = int(startIdx), int(endIdx)
            # We break every clear operation into two stages:
            # clearing edges (A, C) and clearing segments (B)
            #      |-----------|   clearStrand(, 1.5, 4.5)
            # <,> <,> <,> <,> <,> <,> <,> <,>
            #       A B B B B C
            # "Emptying" corresponds to B type clears.
            # We start with an overly wide application of B
            # and narrow it if possible.
            firstBaseToEmpty = startIdx
            lastBaseToEmpty = endIdx
            # clearedStartR = there is an A
            # clearedEndL = there is a C
            self.clearedStartR, self.clearedEndL = False, False
            if startFrac > .25:
                if startFrac < .75:
                    # startFrac in (.25, .75)
                    self.clearedStartR = True
                    startBase = strand[startIdx]
                    # Take care of A
                    potentialNewEndpoints.extend((startBase, startBase._RBase()))
                    ol.append(startBase._setR(None))
                    firstBaseToEmpty += 1
                else:
                    # startFrac in [.75, 1]
                    firstBaseToEmpty += 1
            else:   # startFrac in [0, .25]
                pass
            if endFrac < .75:
                if endFrac > .25:
                    # endFrac in (.25, .75)
                    # We put of clearing until after
                    # we clear the Bs so that our
                    # list of new endpoints is in order
                    self.clearedEndL = True
                    lastBaseToEmpty -= 1
                else:
                    # endFrac in [0, .25]
                    lastBaseToEmpty -= 1
            else:   # endFrac in [.75, 1]
                pass
            # Take care of the Bs
            self.firstBaseToEmpty = firstBaseToEmpty
            self.lastBaseToEmpty = lastBaseToEmpty
            for i in range(firstBaseToEmpty, lastBaseToEmpty + 1):
                base = strand[i]
                potentialNewEndpoints.extend((base, base._LBase()))
                ol.append(base._setL(None))
                potentialNewEndpoints.extend((base, base._RBase()))
                ol.append(base._setR(None))
            if self.clearedEndL:
                endBase = strand[endIdx]
                # Take care of C
                potentialNewEndpoints.extend((endBase, endBase._LBase()))
                ol.append(endBase._setL(None))
            # Now determine which bases were left completely empty
            # by this clear operation that weren't empty before.
            # All bases that we could possibly have left empty that
            # weren't emptied before (indices are inclusive)
            firstEmptiedBase = startIdx
            lastEmptiedBase = endIdx
            # We might not have entirely emptied the first and last
            # bases, so we discard them if necessary from our list
            if not strand[firstEmptiedBase].isEmpty():
                firstEmptiedBase += 1
            if lastEmptiedBase >= len(strand):
                lastEmptiedBase -= 1
            elif not strand[lastEmptiedBase].isEmpty():
                lastEmptiedBase -= 1
            # Now that we know which bases got emptied, clear the
            # inserts and sequences on those bases
            self.firstEmptiedBase = firstEmptiedBase
            assert(firstEmptiedBase >= 0)
            self.lastEmptiedBase = lastEmptiedBase
            assert(lastEmptiedBase < len(strand))
            self.erasedSequenceItems = []    
            for i in range(firstEmptiedBase, lastEmptiedBase+1):
                if insertDict.get(i, None) != None:
                    self.erasedInsertDictItems[i] = insertDict[i]
                    del insertDict[i]
                    if self._vh.part() and \
                            self._vh.hasBaseAt(StrandType.Staple, i):
                        self._vh.part().modifiedBaseSet.add(\
                                        self._vh._stapleBases[i])
                self.erasedSequenceItems.append(strand[i]._sequence)
                strand[i]._sequence = " "
            
            # Our list of potential endpoints has tons of duplicates
            # and empty bases in it. First, remove the empty bases.
            # Clearly, an empty base can't be an endpoint because
            # neither of its pointers is linked to another base.
            isEndpt = lambda x: x!=None and x.isEnd()
            # potentialNewEndpoints = list(filter(isEndpt, potentialNewEndpoints))
            # newEndpts = []
            # Deduplicate, taking advantage of the fact that the
            # list of endpoints will be in order
            # if len(potentialNewEndpoints):
            #     newEndpts = [potentialNewEndpoints[0]]
            #     for pe in potentialNewEndpoints[1:]:
            #         if pe != newEndpts[-1]:
            #             newEndpts.append(pe)
            
            # speed up the above code block, 'set' uniqifies, deduplicates fast
            newEndpts = potentialNewEndpoints = list(set(filter(isEndpt, potentialNewEndpoints)))
                
            
            # print "New endpoints: [%s] [%s] <%s | %s>"%(" ".join(str(b._n)
            # for b in potentialNewEndpoints), " ".join(str(b._n) for b in newEndpts),
            # self._colorL.name() if self._colorL else "-", self._colorR.name()
            # if self._colorR else "-")
            
            # Could filter out endpoints leading to the same set of
            # connected bases if that becomes a performance issue
            # but I don't anticipate it
            if self._strandType != StrandType.Scaffold:
                colorSubCommands = []
                for i in range(len(newEndpts)):
                    e = newEndpts[i]
                    bases = e._vhelix._basesConnectedTo(e._strandtype, e._n)
                    # None corresponds to a pseudorandom color
                    color = None
                    if i==0 and self._colorL!=None:
                        color = self._colorL
                    elif i==len(newEndpts)-1 and self._colorR!=None:
                        color = self._colorR
                    c = VirtualHelix.ApplyColorCommand(bases, color)
                    c.redo()
                    colorSubCommands.append(c)
                # end for
                if len(potentialNewEndpoints) > 0:
                    if self._colorL:
                        bases = self._vh._basesConnectedTo(self._strandType, potentialNewEndpoints[0]._n)
                        c = VirtualHelix.ApplyColorCommand(bases, self._colorL)
                        c.redo()
                        colorSubCommands.append(c)
                    if self._colorR:
                        bases = self._vh._basesConnectedTo(self._strandType, potentialNewEndpoints[-1]._n)
                        c = VirtualHelix.ApplyColorCommand(bases, self._colorR)
                        c.redo()
                        colorSubCommands.append(c)
                # end if
                self.colorSubCommands = colorSubCommands
            # end if
            self._vh.resetSequenceCache()
            self._vh.emitBasesModifiedIfNeeded()
    
        def undo(self):
            strand = self._vh._strand(self._strandType)
            ol = self._oldLinkage
            assert(ol != None)  # Must redo/apply before undo
            startIdxF = min(self._startIndexF, self._endIndexF)
            endIdxF = max(self._startIndexF, self._endIndexF)
            startFrac, startIdx = modf(startIdxF)
            endFrac, endIdx = modf(endIdxF)
            startIdx, endIdx = int(startIdx), int(endIdx)
            # If this assert raises an exception, undo() got called without
            # redo() being called first
            if self._strandType != StrandType.Scaffold:
                assert(hasattr(self, 'colorSubCommands'))
                # for c in reversed(self.colorSubCommands):
                #     c.undo()
                map(lambda c: c.undo(), reversed(self.colorSubCommands))
                del self.colorSubCommands
            # end if
            insertDict = self._vh._insert(self._strandType)
            for k, v in self.erasedInsertDictItems.iteritems():
                insertDict[k] = v
                if self._vh.part() and \
                        self._vh.hasBaseAt(StrandType.Staple, k):
                    self._vh.part().modifiedBaseSet.add(\
                                    self._vh._stapleBases[k])

            # for i in reversed(range(self.firstEmptiedBase, self.lastEmptiedBase+1)):
            #     strand[i]._sequence = self.erasedSequenceItems.pop()
            for b in reversed(strand[self.firstEmptiedBase: self.lastEmptiedBase+1]):
                b._sequence = self.erasedSequenceItems.pop()
            
            if self.clearedEndL:
                endBase = strand[endIdx]
                endBase._unsetL(None, *ol.pop())
            
            # for i in reversed(range(self.firstBaseToEmpty, self.lastBaseToEmpty + 1)):
            #     base = strand[i]
            #     base._unsetR(None, *ol.pop())
            #     base._unsetL(None, *ol.pop())
            temp = reversed(strand[self.firstBaseToEmpty:self.lastBaseToEmpty + 1])
            def unsetRL_sub(base, ol):
                base._unsetR(None, *ol.pop())
                base._unsetL(None, *ol.pop())
            map(lambda b: unsetRL_sub(b, ol), temp)
            
            if self.clearedStartR:
                startBase = strand[startIdx]
                startBase._unsetR(None, *ol.pop())
            self._vh.resetSequenceCache()
            self._vh.emitBasesModifiedIfNeeded()

    class Connect3To5Command(QUndoCommand):
        def __init__(self, strandType, fromHelix, fromIndex, toHelix, toIndex, endToTakeColorFrom=3, speedy=False):
            super(VirtualHelix.Connect3To5Command, self).__init__()
            self._strandType = strandType
            self._fromHelix = fromHelix
            self._fromIndex = fromIndex
            self._toHelix = toHelix
            self._toIndex = toIndex
            self._colorEnd = endToTakeColorFrom
            self._speedy = speedy

        def redo(self):
            vh, strandType = self._fromHelix, self._strandType
            fromIdx, toIdx = self._fromIndex, self._toIndex
            fromB = vh._strand(strandType)[fromIdx]
            toB = self._toHelix._strand(strandType)[toIdx]
            old3p = fromB._3pBase
            old5p = toB._5pBase
            self._undoDat = fromB._set3Prime(toB)
            if self._speedy:
                self._colorCommand = False
                self._colorCommand1 = False
                self._colorCommand2 = False
                return
            if self._colorEnd == 3:
                color = vh.colorOfBase(strandType, fromIdx)
            elif self._colorEnd == 5:
                color = self._toHelix.colorOfBase(strandType, toIdx)
            else:
                assert(False)
            # Ensure that the newly joined strand is all one color
            bases = vh._basesConnectedTo(strandType, fromIdx)
            c = VirtualHelix.ApplyColorCommand(bases, color)
            c.redo()
            self._colorCommand = c
            
            # If we had to split a strand to make the crossover, give
            # the resulting segment a random color
            self._colorCommand1 = None
            if old3p!=None:
                bases1 = old3p._vhelix._basesConnectedTo(old3p._strandtype, old3p._n)
                color1 = vh.palette()[0]
                c1 = VirtualHelix.ApplyColorCommand(bases1, color1)
                c1.redo()
                self._colorCommand1 = c1
            self._colorCommand2 = None
            if old5p != None:
                bases2 = old5p._vhelix._basesConnectedTo(old5p._strandtype, old5p._n)
                color2 = vh.palette()[1]
                c2 = VirtualHelix.ApplyColorCommand(bases2, color2)
                c2.redo()
                self._colorCommand2 = c2
            vh.emitBasesModifiedIfNeeded()

        def undo(self):
            fromB = self._fromHelix._strand(self._strandType)[self._fromIndex]
            toB = self._toHelix._strand(self._strandType)[self._toIndex]
            assert(self._undoDat)  # Must redo/apply before undo
            fromB._unset3Prime(toB, *self._undoDat)
            if self._colorCommand != False:
                self._colorCommand.undo()
            if self._colorCommand1:
                self._colorCommand1.undo()
            if self._colorCommand2:
                self._colorCommand2.undo()
            self._fromHelix.emitBasesModifiedIfNeeded()

    class Break3To5Command(QUndoCommand):
        def __init__(self, strandType, vhelix, index, endToKeepColor=3, newColor=None):
            super(VirtualHelix.Break3To5Command, self).__init__()
            self._strandType = strandType
            self._base = vhelix._strand(strandType)[index]
            self._endToKeepColor = endToKeepColor
            self._colorCommand = None
            if newColor==None:
                newColor = vhelix.palette()[0]
            self._newColor = newColor

        def redo(self):
            threeB = self._base
            self._old3pBase = fiveB = threeB._3pBase
            threeB._set3Prime(None)
            if threeB and self._endToKeepColor==5:
                color = self._newColor
                bases = threeB._vhelix._basesConnectedTo(threeB._strandtype, threeB._n)
                c = VirtualHelix.ApplyColorCommand(bases, color)
                c.redo()
                self._colorCommand = c
            elif fiveB and self._endToKeepColor==3:
                color = self._newColor
                bases = fiveB._vhelix._basesConnectedTo(fiveB._strandtype, fiveB._n)
                c = VirtualHelix.ApplyColorCommand(bases, color)
                c.redo()
                self._colorCommand = c
            threeB._vhelix.emitBasesModifiedIfNeeded()

        def undo(self):
            assert(self._old3pBase)
            base = self._base
            base._set3Prime(self._old3pBase)
            base._vhelix.emitBasesModifiedIfNeeded()
            if self._colorCommand:
                self._colorCommand.undo()

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
                del vh._stapleBases[newNumBases:]
                del vh._scaffoldBases[newNumBases:]
            assert(vh.numBases() == newNumBases)
            vh.dimensionsModifiedSignal.emit()

        def undo(self):
            self.redo(actuallyUndo=True)

    ################################ Crossovers ##############################
    
    def potentialCrossoverList(self, facingRight, vStrandFrom):
        """Returns a list of [(fromVBase, toVBase)] tuples of potential
        crossovers
        facingRight means 
        facingLeft means
        """
        ret = []  # LUT = Look Up Table
        vh = self
        part = vh.part()
        luts = (part.scafL, part.scafR, part.stapL, part.stapR)
        isStaple = vStrandFrom.isStap()
        
        # these are the list of crossover points simplified
        lut = luts[int(facingRight) + 2 * int(isStaple)]

        neighbors = vh.neighbors()
        for p in range(len(neighbors)):
            neighbor = neighbors[p]
            if not neighbor:
                continue
            for i, j in product(range(0, vh.numBases(), part.step), lut[p]):
                index = i + j
                vstrandTo = neighbor.vStrandStap() if isStaple else neighbor.vStrandScaf()
                if index < vh.numBases():
                    frVB = vStrandFrom.get(index)
                    toVB = vstrandTo.get(index)
                    # if frVB != None and toVB != None:
                        # return tuple (VBase, VBase) using the __call__ method in VStrand
                    ret.append((vStrandFrom(index), vstrandTo(index)))
        return ret


    def isaXover(self, fromIndex, toVH, toIndex, strandType):
        """
        Always from 3 prime to 5 prime
        """
        strandFrom = self._strand(strandType)
        strandTo = toVH._strand(strandType)
        if strandFrom[fromIndex].get3pBase() == strandTo[toIndex] and \
            strandFrom[fromIndex] == strandTo[toIndex].get5pBase():
            return True
        else:
            return False

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
        if fromIndex >= self.numBases() or\
           toIndex >= neighbor.numBases():
            return False
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
        numBases = self.numBases()
        strdir = "5->3" if self.directionOfStrandIs5to3(strandType) else "3->5"
        strand = self._strand(strandType)
        return "(%s) " % (strdir) + " ".join(str(b) for b in strand)

    def fillSimpleRep(self, sr):
        """Fills sr with a representation of self in terms
        of simple types (strings, numbers, objects, and arrays/dicts
        of objects that also implement fillSimpleRep)"""
        sr['.class'] = "VirtualHelix"
        sr['tentativeHelixID'] = self.number()  # Not used (just for readability)
        stapleStrand = self._strand(StrandType.Staple)
        sr['staple'] = self.encodeStrand(StrandType.Staple)
        sr['stapleColors'] = " ".join(str(b.getColor().name()) for b in stapleStrand)
        scaffoldStrand = self._strand(StrandType.Scaffold)
        sr['scafld'] = self.encodeStrand(StrandType.Scaffold)
        sr['scafldColors'] = " ".join(str(b.getColor().name()) for b in scaffoldStrand)
        # only encode scaffold inserts for version 1.5
        # sr['loops'] = dict((str(k), v) for k,v in self._scaffoldInserts.iteritems())
        sr['inserts'] = dict((str(k), v) for k,v in self._scaffoldInserts.iteritems())

    # First objects that are being unarchived are sent
    # ClassNameFrom.classAttribute(incompleteArchivedDict)
    # which has only strings and numbers in its dict and then,
    # sometime later (with ascending finishInitPriority) they get
    # finishInitWithArchivedDict, this time with all entries
    finishInitPriority = 1.0  # AFTER DNAParts finish init

    def getRangesAndXoversFromString(self, baseStrList):
        """
        Decodes the string representation of each base in baseStrList
        and returns a tuple containing the ranges, left-xovers, and 
        right-xovers.
        """
        ranges, xoL, xoR = [], [], []
        for i in range(len(baseStrList)):
            base = baseStrList[i]
            if not base in ["_,_", "<,>"]:  # start or end of range
                ranges.append(i)
                if not base in ["<,_", "_,>"]:  # crossover
                    l, r = re.split(',', base)
                    lm = re.match(r"(\d+):(\d+)", l)
                    rm = re.match(r"(\d+):(\d+)", r)
                    if lm != None:
                        xoL.append((i, int(lm.group(1)), int(lm.group(2))))
                    if rm != None:
                        xoR.append((i, int(rm.group(1)), int(rm.group(2))))
        assert(len(ranges) % 2 == 0)
        return (ranges, xoL, xoR)

    def finishInitWithArchivedDict(self, completeArchivedDict):
        """
        Initialization of the virtualhelix is completed as follows:
        
        1. Parse the scaf and stap strings into ranges and xover positions
        by calling getRangesAndXoversFromString()
        2. Call connectStrand for each of the ranges
        3. Send crossover locations to the part for addition on finalizeImport
        4. Apply color information
        """
        # 1
        scaf = re.split('\s+', completeArchivedDict['scafld'])
        stap = re.split('\s+', completeArchivedDict['staple'])
        scafDir, scaf = scaf[0], scaf[1:]
        stapDir, stap = stap[0], stap[1:]
        assert(len(scaf) == len(stap) and len(stap) == self.numBases())
        scafRanges, scafXoL, scafXoR = self.getRangesAndXoversFromString(scaf)
        stapRanges, stapXoL, stapXoR = self.getRangesAndXoversFromString(stap)

        # 2
        for i in range(0, len(scafRanges), 2):
            startIdx, endIdx = scafRanges[i:i+2]
            self.scaf().connectStrand(startIdx, endIdx, useUndoStack=False)
        for i in range(0, len(stapRanges), 2):
            startIdx, endIdx = stapRanges[i:i+2]
            self.stap().connectStrand(startIdx, endIdx, useUndoStack=False)

        # 3
        if scafDir == "(5->3)":  # stapDir == (3->5)
            for frIdx, toNum, toIdx in scafXoL:  # scaf frVBase is 3'L xover
                self._part.importXover(\
                       StrandType.Scaffold, self._number, frIdx, toNum, toIdx)
            for frIdx, toNum, toIdx in stapXoR:  # stap frVBase is 3'R xover
                self._part.importXover(\
                         StrandType.Staple, self._number, frIdx, toNum, toIdx)
        else:  # scafDir == (3<-5), stapDir = (5->3)
            for frIdx, toNum, toIdx in scafXoR:  # scaf frVBase is 3'R xover
                self._part.importXover(\
                       StrandType.Scaffold, self._number, frIdx, toNum, toIdx)
            for frIdx, toNum, toIdx in stapXoL:  # stap frVBase is 3'L xover
                self._part.importXover(\
                         StrandType.Staple, self._number, frIdx, toNum, toIdx)

        # 4
        # Give bases the proper colors
        # scafColors = re.split('\s+', completeArchivedDict['scafldColors'])
        # # for i in range(len(scaf)):
        # #     self._scaffoldBases[i]._setColor(QColor(scafColors[i]))
        # map(Base._setColor, self._scaffoldBases, imap(QColor, scafColors))

        # stapColors = re.split('\s+', completeArchivedDict['stapleColors'])
        # # for i in range(len(stap)):
        # #     self._stapleBases[i]._setColor(QColor(stapColors[i]))
        # map(Base._setColor, self._stapleBases, imap(QColor, stapColors))
