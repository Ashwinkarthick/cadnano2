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
util.qtWrapImport('QtGui', globals(), [ 'QUndoCommand' ])
util.qtWrapImport('QtCore', globals(), [ 'pyqtSignal', 'QObject' ])

def rangeIntersection(firstRange, secondRange):
    ff, fl = firstRange
    sf, sl = secondRange
    if ff >= fl:
        return [0, 0]
    if sf >= sl:
        return [0, 0]
    l, r = max(ff, sf), min(fl, sl)
    if l >= r:
        return [0, 0]
    return [l, r]

class RangeSet(QObject):
    """
    Represents a set of objects (rangeItems or RIs) that each conceptually
    occupy a contiguous subset of the integers under the additional constraints
    1) no two items in the set overlap (occupy an identical integer)
    2) any two adjacent items a, b st canMergeRangeItems(a,b) == True upon
       insertion of the last one to be inserted will be merged.

    The default implementation allows 'metadata' to be attached to each range,
    effectively turning RangeSet into a dictionary where assigning a range of
    keys (for i in range(10): myDict[i] = someVal) is cheap (the equivalent
    using RangeSet would be 'myRangeSet.addRange((0, 10, someVal))'.)
    """
    logger = None
    # Parameters are the pythonic range of modified indices.
    # Participation in a merge doesn't count as modification.
    # the object is a tuple holding a pythonic range of indices that could
    # have been modified.
    indicesModifiedSignal = pyqtSignal(object)
    def __init__(self):
        QObject.__init__(self)
        self.ranges = []
        self.lastGottenRangeIdx = None

    ############################### Invariants ###########################
    def assertConsistency(self):
        """
        Raises an exception if the receiver's invariants
        are not maintained
        """
        for i in range(len(self.ranges)):
            f, l = self.idxs(self.ranges[i])
            assert(f < l)  # All ranges contain an index
        for i in range(len(self.ranges)-1):
            # Naming convention:
            # {l:left, r:right}{f:firstIdx, l:afterLastIdx}
            lf, ll = self.idxs(self.ranges[i])
            rf, rl = self.idxs(self.ranges[i + 1])
            if ll > rf:
                # Ranges are sorted, don't overlap
                for j in range(*rangeIntersection([0, len(self.ranges)], [i - 3, i + 3])):
                    print "self.ranges[%i]: %s"%(j, self.ranges[j])                
                print "Problem between items at idx %i, %i (out of order)"\
                      %(i, i + 1)
                assert(False)  
            if ll == rf:
                # Adjacent ranges containing the same metadata
                # MUST be merged
                if self.canMergeRangeItems(self.ranges[i], self.ranges[i + 1]):
                    for j in range(*rangeIntersection([0, len(self.ranges)], [i - 3, i + 3])):
                        print "self.ranges[%i]: %s"%(j, self.ranges[j])
                    print "Problem between items at idx %i, %i (can be merged, not merged)"\
                          %(i, i + 1)
                    assert(False)

    ############################### Framework ###########################
    # If you want a RangeSet that stores something other than tuples of
    # integers representing ranges of indexes, these are the methods to override
    def idxs(self, rangeItem):
        """
        Returns (firstIdx, afterLastIdx) simplified representation of the
        rangeItem passed in.
        """
        return rangeItem[0:2]

    def mergeRangeItems(self, rangeItemA, rangeItemB, undoStack):
        """
        If a subclass needs to support undo, it should push whatever it does
        here onto undoStack (iff undoStack is not None). It can also just return
        an entirely new object in which case undo will be handled automatically.
        """
        al, ar = self.idxs(rangeItemA)
        bl, br = self.idxs(rangeItemB)
        return (min(al, bl), max(ar, br), rangeItemB[2])

    def changeRangeForItem(self, rangeItem, newStartIdx, newAfterLastIdx, undoStack):
        """
        Changes the range corresponding to rangeItem.
        Careful, this isn't a public method. It gets called to notify a subclass
        of a change, not to effect the change itself.

        If a subclass needs to support undo, it should push whatever it does
        here onto undoStack (iff undoStack is not None). It can also just return
        an entirely new object in which case undo will be handled automatically.
        """
        oldStartIdx, oldAfterLastIdx = self.idxs(rangeItem)
        unionStartIdx = min(oldStartIdx, newStartIdx)
        unionAfterLastIdx = max(oldAfterLastIdx, newAfterLastIdx)
        return (newStartIdx, newAfterLastIdx, rangeItem[2])

    def splitRangeItem(self, rangeItem, splitStart, afterSplitEnd, keepLeft, undoStack):
        """
        When a range is inserted into the middle of another range (and no
        merging can occur) the existant range is split into two endpoints
        and the newly inserted range is sandwiched inbetween. This method
        returns the endpoints.
              [NewRange)
         [ExistingRange------)
         [Exi)[NewRange)[----)  Sandwich
         [Exi)          [----)  What this function returns
        """
        md = rangeItem[2]  # Preserve metadata
        return [(rangeItem[0], splitStart, md),\
                (afterSplitEnd, rangeItem[1], md)]

    def willRemoveRangeItem(self, rangeItem):
        pass
    def willInsertRangeItem(self, rangeItem):
        pass
    def didRemoveRangeItem(self, rangeItem):
        pass
    def didInsertRangeItem(self, rangeItem):
        pass

    def itemRemovalWillBePushed(self, strand, useUndoStack, undoStack):
        """Called before the command that causes removal of self to be pushed
        to the undoStack is pushed (in contrast to willRemoveRangeItem which is
        called every time the undoStack decides to remove an item). This is the
        place to push side effects of removal onto the undo stack."""
        pass

    def boundsChanged(self):
        """
        Gets called whenever something in the write API causes the value
        returned by bounds() to change.
        """
        pass

    def canMergeRangeItems(self, rangeItemA, rangeItemB):
        aLeft, aRight = self.idxs(rangeItemA)
        bLeft, bRight = self.idxs(rangeItemB)
        assert(aLeft < aRight)
        assert(bLeft < bRight)
        if aRight < bLeft:
            return False
        if bRight < aLeft:
            return False
        return self.canMergeTouchingRangeItems(rangeItemA, rangeItemB)

    def canMergeTouchingRangeItems(self, rangeItemA, rangeItemB):
        """ Once it has been determined that two rangeItems are adjacent or
        overlapping, this method is called to see if there is something beyond
        the raw ranges that prevents items A and B from being merged. The
        default implementation only merges adjacent ranges if they have
        identical metadata. """
        return rangeItemA[2:] == rangeItemB[2:]

    def defaultUndoStack(self):
        return None

    ############################### Public Read API ###########################

    def get(self, idx, retvalOnIdxNotInSelf=None):
        """
        In the analogy to dict, rs.get is identical to rd.get.
        Returns the range at idx or retvalOnIndexNotInSelf if
        idx is not in any range of the receiver.
        """
        idx = self._idxOfRangeContaining(idx)
        if idx == None:
            return retvalOnIdxNotInSelf
        return self.ranges[idx]

    def __getitem__(self, idx):
        return nself.get(idx)

    def __contains__(self, intVal):
        """
        In the analogy to dict, checks to see if intVal is in the
        set of keys.
        """
        return self._idxOfRangeContaining(intVal) != None

    def bounds(self):
        """
        Returns a range tuple (lowestIdx, oneAfterHighestIdx) that would contain
        every range in the receiver.
        """
        if len(self.ranges) == 0:
            return (0, 0)
        ff, fl = self.idxs(self.ranges[0])
        lf, ll = self.idxs(self.ranges[-1])
        return (ff, ll)

    def containsAllInRange(rangeStart, afterRangeEnd):
        """
        Returns weather or not the receiver contains all i st
        rangeStart <= i < afterRangeEnd
        """
        idxRange = self._idxRangeOfRangesIntersectingRange(rangeStart, rangeEnd)
        previousLastIdx = None
        for i in range(*idxRange):
            l, r = self.idxs(self.ranges[i])
            if previousLastIdx == None:
                previousLastIdx = r
            else:
                if previousLastIdx != l:
                    return False
                previousLastIdx = r
        return True

    def containsAnyInRange(rangeStart, rangeEnd):
        idxRange = self._idxRangeOfRangesIntersectingRange(rangeStart, rangeEnd)
        return idxRange[1] - idxRange[0] > 0

    def rangeItemsTouchingRange(self, rangeStart, rangeEnd):
        rangeItemIndexRange = self._idxRangeOfRangesIntersectingRange(rangeStart, rangeEnd)
        return self.ranges[rangeItemIndexRange[0]:rangeItemIndexRange[1]]

    def __iter__(self):
        """
        Iterate over the range items in self.
        """
        return self.ranges.__iter__()

    ################################ Public Write API ############################
    def addRange(self, rangeItemToInsert, useUndoStack=True, undoStack=None, suppressCallsItem=None, keepLeft=True):
        """
        Adds rangeItem to the receiver, ensuring that the range given by
        self.idxs(rangeItem) does not overlap any other rangeItem in the receiver
        (this is enforced by deleting or truncating any rangeItems in the way)
        and tries to merge the newly inserted rangeItem with its neighbors.

        Note: "touching" ranges intersect or are adjacent to rangeItem.
        """
        
        firstIndex, afterLastIndex = self.idxs(rangeItemToInsert)
        if firstIndex >= afterLastIndex:
            return
        oldBounds = self.bounds()
        undoStack = self.beginCommand(useUndoStack,\
                                      undoStack,\
                                      'RangeSet.addRange')
        # middleRangeItemIdx: the index into self.ranges that one would insert a
        # range item if one wished to insert the range item into the space
        # celared by this removeRange command
        middleRangeItemIdx =  self.removeRange(firstIndex, afterLastIndex,\
                                               useUndoStack, undoStack,\
                                               suppressCallsItem, keepLeft)

        if middleRangeItemIdx > 0:
            leftRangeItemIdx = middleRangeItemIdx - 1
            leftRangeItem = self.ranges[leftRangeItemIdx]
            if self.canMergeRangeItems(leftRangeItem, rangeItemToInsert):
                mergedRangeItm = self.mergeRangeItems(leftRangeItem,\
                                                     rangeItemToInsert,\
                                                     undoStack)
                firstReplacedRangeItemIdx = leftRangeItemIdx
                itemToInsert = mergedRangeItm
            else:
                firstReplacedRangeItemIdx = middleRangeItemIdx
                itemToInsert = rangeItemToInsert
        else:
            firstReplacedRangeItemIdx = 0
            itemToInsert = rangeItemToInsert

        if middleRangeItemIdx < len(self.ranges):
            # The range that will be to the right of the inserted range
            # because the range to be inserted hasn't been inserted yet
            rightRangeItm = self.ranges[middleRangeItemIdx]
            if self.canMergeRangeItems(itemToInsert, rightRangeItm):
                mergedRangeItm = self.mergeRangeItems(itemToInsert,\
                                                     rightRangeItm,\
                                                     undoStack)
                afterLastReplacedRangeItemIdx = middleRangeItemIdx + 1
                itemToInsert = mergedRangeItm
            else:
                afterLastReplacedRangeItemIdx = middleRangeItemIdx
        else:
            afterLastReplacedRangeItemIdx = middleRangeItemIdx
        com = self.ReplaceRangeItemsCommand(self,\
                                            firstReplacedRangeItemIdx,\
                                            afterLastReplacedRangeItemIdx,\
                                            [itemToInsert],\
                                            suppressCallsItem)
        self.endCommand(undoStack, com)

    def removeRange(self, firstIndex, afterLastIndex, useUndoStack=True,\
                    undoStack=None, suppressCallsItem=None, keepLeft=True):
        """
        Called by VStrand.clearStrand().

        Update the ranges such that the region from [firstIndex:afterLastIndex]
        is empty. If the pre-existing ranges extend past that region, then
        they need to be updated by truncation.

        Returns middleIdx: the index into self.ranges that one would insert a
        range item if one wished to insert the range item into the space
        celared by this removeRange command. Used e.g. for xover insertion.
        """
        if firstIndex >= afterLastIndex:
            return
        oldBounds = self.bounds()
        undoStack = self.beginCommand(useUndoStack,\
                                      undoStack,\
                                      'RangeSet.removeRange')
        intersectingIdxRange = self._idxRangeOfRangesIntersectingRange(firstIndex,
                                                               afterLastIndex)
        replacementRanges = []
        # (first Index (into self.ranges) of an Touching Range)
        firstIIR, afterLastIIR = intersectingIdxRange
        # print "\tRemoveRange: %s[%i:%i]"%(self.ranges, firstIIR, afterLastIIR)
        if afterLastIIR == firstIIR:
            if useUndoStack: undoStack.endMacro()
            return firstIIR
        firstIR = self.ranges[firstIIR]
        firstIRL, firstIRAr = self.idxs(firstIR)
        if firstIRL < firstIndex:
            if firstIRAr > afterLastIndex:
                replacementRanges = self.splitRangeItem(firstIR,\
                                                        firstIndex,\
                                                        afterLastIndex,\
                                                        keepLeft,\
                                                        undoStack)
                # middleIdx: the index into self.ranges that one would insert a
                # range item if one wished to insert the range item into the space
                # celared by this removeRange command
                middleIdx = firstIIR + len(replacementRanges) - 1
            else:
                newItem = self.changeRangeForItem(firstIR,\
                                                  firstIRL,\
                                                  firstIndex,\
                                                  undoStack)
                replacementRanges.append(newItem)
                middleIdx = firstIIR + len(replacementRanges)
        else:
            middleIdx = firstIIR + len(replacementRanges)
        lastIR = self.ranges[afterLastIIR - 1]
        lastIRL, lastIRAr = self.idxs(lastIR)
        if lastIRAr > afterLastIndex and lastIRL >= firstIndex:
            newItem = self.changeRangeForItem(lastIR,\
                                              afterLastIndex,\
                                              lastIRAr,\
                                              undoStack)
            replacementRanges.append(newItem)
        com = self.ReplaceRangeItemsCommand(self,\
                                            firstIIR,\
                                            afterLastIIR,\
                                            replacementRanges,\
                                            suppressCallsItem)
        for ri in com.risToRemove:
            ri.removalWillBePushed(useUndoStack, undoStack)
        self.endCommand(undoStack, com)
        return middleIdx

    def resizeRangeAtIdx(self, idx, newFirstIndex, newAfterLastIdx, useUndoStack=True, undoStack=None):
        """
        Finds the largest contiguous range of indices in the receiver that includes
        idx and changes it.
        """
        assert(isinstance(idx, (int, long)))
        undoStack = self.beginCommand(useUndoStack,\
                                      undoStack,\
                                      'RangeSet.resizeRangeAtIdx')
        rangeItemToResize = self.get(idx)
        oldL, oldAR = self.idxs(rangeItemToResize)
        self.removeRange(oldL, oldAR,\
                         useUndoStack=useUndoStack, undoStack=undoStack,\
                         suppressCallsItem=rangeItemToResize)
        newRangeItem = self.changeRangeForItem(rangeItemToResize,\
                                               newFirstIndex,\
                                               newAfterLastIdx,\
                                               undoStack)
        # Caveat: newRangeItem might == rangeItemToResize
        self.addRange(newRangeItem,\
                      useUndoStack=useUndoStack, undoStack=undoStack,\
                      suppressCallsItem=rangeItemToResize)
        if undoStack != None:
            undoStack.endMacro()

    def rangesNearIdx(self, idx):
        """ Returns a tuple of range items relative to the range item at idx
        (rangeItemBeforeIdx, rangeItemAtIdx, rangeItemAfterIdx)
        where rangeItem{Before,After}Idx is None if the range at idx is
        the first or last range, respectively. rangeItemAtIdx can be None."""
        rangeItemIdx = self._idxOfRangeContaining(idx,\
                                         returnTupledIdxOfNextRangeOnFail=True)
        ranges = self.ranges
        if isinstance(rangeItemIdx, (int, long)):
            rangeItemAtIdx = ranges[rangeItemIdx]
            lIdx = rangeItemIdx - 1
            rIdx = rangeItemIdx + 1
        else:
            rangeItemAtIdx = None
            rangeItemIdx = rangeItemIdx[0]
            lIdx = rangeItemIdx - 1
            rIdx = rangeItemIdx
        rangeItemAfterIdx = ranges[rIdx] if rIdx < len(ranges) else None
        rangeItemBeforeIdx = ranges[lIdx] if lIdx >= 0 else None
        return (rangeItemBeforeIdx, rangeItemAtIdx, rangeItemAfterIdx)

    ################################ Private Write API #########################
    def beginCommand(self, useUndoStack, undoStack, commandDescription):
        """Called as a prefix to every public mutation method. Ensures uniform
        handling of the useUndoStack+undoStack variables. Returns the
        undoStack that the mutator method should use."""
        self.lastGottenRangeIdx = None  # Clear cache
        if useUndoStack:
            if undoStack == None: undoStack = self.undoStack()
            assert(undoStack != None)
            undoStack.beginMacro(commandDescription)
            return undoStack
        else:
            return None

    def endCommand(self, undoStack, commands):
        """Called at the end of every public mutation method"""
        # Sanitize commands
        if type(commands) not in (list, tuple):
            commands = (commands,)
        commands = filter(lambda x: x != None, commands)
        # Now commands is an iterable of QUndoCommand instances
        if undoStack != None:
            map(undoStack.push, commands)
            undoStack.endMacro()
        else:
            for c in commands:
                c.redo()

    class ReplaceRangeItemsCommand(QUndoCommand):
        def __init__(self, rangeSet, firstIdx, afterLastIdx, replacementRIs, suppressCallsItem):
            QUndoCommand.__init__(self)
            self.rangeSet = rangeSet
            self.firstIdx = firstIdx
            self.afterLastIdx = afterLastIdx
            self.replacementRIs = replacementRIs
            ranges = rangeSet.ranges
            lowerBoundsOfModifiedIdxs = []
            upperBoundsOfAfterModifiedIdxs = []
            if afterLastIdx - firstIdx > 0:
                upperBoundsOfAfterModifiedIdxs.append(\
                    rangeSet.idxs(ranges[afterLastIdx - 1])[1]   )
                lowerBoundsOfModifiedIdxs.append(\
                    rangeSet.idxs(ranges[0])[0]   )
            if replacementRIs:
                upperBoundsOfAfterModifiedIdxs.append(\
                    rangeSet.idxs(replacementRIs[-1])[1]  )
                lowerBoundsOfModifiedIdxs.append(\
                    rangeSet.idxs(replacementRIs[0])[0]   )
            if lowerBoundsOfModifiedIdxs and upperBoundsOfAfterModifiedIdxs:
                self.modifiedIdxRange = (min(lowerBoundsOfModifiedIdxs),\
                                         max(upperBoundsOfAfterModifiedIdxs))
            else:
                self.modifiedIdxRange = (0, 0)
            # Resizing a rangeItem is internally done with a removal command
            # and an insertion command. We don't want to call willRemove and
            # didInsert while we are doing that (just changeRangeForItem) so
            # we need to manually suppress those calls for the object being
            # removed / changeRanged / added. This is the item to which we
            # suppress willRemove and didInsert calls.
            self.suppressCallsItem = suppressCallsItem
            self.replacedRIs = rangeSet.ranges[self.firstIdx:self.afterLastIdx]
            replacedSet = set(id(ri) for ri in self.replacedRIs)
            replacementSet = set(id(ri) for ri in self.replacementRIs)
            # Figure out who gets notifications
            risToRemove = list(filter(lambda ri: id(ri) not in replacementSet,\
                                      self.replacedRIs))
            try:
                risToRemove.remove(suppressCallsItem)
            except ValueError:
                pass
            risToInsert = list(filter(lambda ri: id(ri) not in replacedSet,\
                                      self.replacementRIs))
            try:
                risToInsert.remove(suppressCallsItem)
            except ValueError:
                pass
            self.risToRemove, self.risToInsert = risToRemove, risToInsert
        def redo(self):
            rangeSet = self.rangeSet
            rangeArr, oldBounds = rangeSet.ranges, rangeSet.bounds()
            # Now actually perform the actions
            map(rangeSet.willRemoveRangeItem, self.risToRemove)
            map(rangeSet.willInsertRangeItem, self.risToInsert)
            rangeArr[self.firstIdx:self.afterLastIdx] = self.replacementRIs
            map(rangeSet.didInsertRangeItem, self.risToInsert)
            map(rangeSet.didRemoveRangeItem, self.risToRemove)
            if rangeSet.bounds() != oldBounds: rangeSet.boundsChanged()
            rangeSet.indicesModifiedSignal.emit(self.modifiedIdxRange)
            if rangeSet.logger != None:
                rangeSet.assertConsistency()
        def undo(self):
            assert(self.replacedRIs != None)  # Must redo before undo
            rangeSet = self.rangeSet
            oldBounds = rangeSet.bounds()
            replacedSet = set(id(ri) for ri in self.replacedRIs)
            replacementSet = set(id(ri) for ri in self.replacementRIs)
            suppressCallsItem = self.suppressCallsItem
            lastIdx = self.firstIdx + len(self.replacementRIs)
            map(rangeSet.willRemoveRangeItem, self.risToInsert)
            map(rangeSet.willInsertRangeItem, self.risToRemove)
            self.rangeSet.ranges[self.firstIdx:lastIdx] = self.replacedRIs
            map(rangeSet.didInsertRangeItem, self.risToRemove)
            map(rangeSet.didRemoveRangeItem, self.risToInsert)
            if rangeSet.bounds() != oldBounds: rangeSet.boundsChanged()
            rangeSet.indicesModifiedSignal.emit(self.modifiedIdxRange)
            if rangeSet.logger != None:
                rangeSet.assertConsistency()

    ################################ Private Read API ##########################
    def _idxOfRangeContaining(self, intVal, returnTupledIdxOfNextRangeOnFail=False):
        """
        Returns the index in self.ranges of the range
        containing intVal or None if none does.
        """
        assert(isinstance(intVal, (int, long)))
        if not self.ranges:
            if returnTupledIdxOfNextRangeOnFail:
                return (0,)
            return None

        # ------------- Amortize sequential or repeated access -----------------
        lastGottenRangeIdx = self.lastGottenRangeIdx
        if lastGottenRangeIdx != None:
            try:
                lgrL, lgrR = self.idxs(self.ranges[lastGottenRangeIdx])
                if lgrL <= intVal < lgrR:
                    return lastGottenRangeIdx
                nextRangeItem = self.ranges[lastGottenRangeIdx + 1]
                nextLgrL, nextLgrR = self.idxs(nextRangeItem)
                if lgrR <= intVal < nextLgrL:
                    if returnTupledIdxOfNextRangeOnFail:
                        return (lastGottenRangeIdx + 1,)
                    else:
                        return None
                if nextLgrL <= intVal < nextLgrR:
                    ret = lastGottenRangeIdx + 1
                    self.lastGottenRangeIdx = ret
                    return ret
            except IndexError:
                pass
        self.cacheMissed = True  # For the amortization unit test
        # ------------------ Can cut this block without changing return val ----

        # m <= the index of any range containing
        # intVal, M >= the index of any range containing
        # intVal.
        m, M = 0, len(self.ranges)-1
        while m <= M:
            mid = (m+M)/2
            rangeItem = self.ranges[mid]
            l, r = self.idxs(rangeItem)
            if not isinstance(intVal, (int, long)):
                print "!!!intVal: %s "%(intVal) + util.trace(5)
            if r <= intVal:
                m = mid + 1
            elif l > intVal:
                M = mid - 1
            else:  # v and r[mid][0] <= intVal < r[mid][1]
                self.lastGottenRangeIdx = mid
                return mid
        if returnTupledIdxOfNextRangeOnFail:
            # The tuple is an indicator that the search failed
            self.lastGottenRangeIdx = m
            return (m,)
        return None

    def _idxRangeOfRangesIntersectingRange(self, rangeStart, rangeEnd):
        """
        Returns a range [first, afterLast) of indices into self.ranges,
        such that every rangeItem in self.ranges[first:afterLast] has
        a nonempty intersection with [rangeStart, rangeEnd)
        """
        if rangeStart >= rangeEnd:
            return [0, 0]  # Empty range
        idx = self._idxOfRangeContaining(rangeStart,\
                                         returnTupledIdxOfNextRangeOnFail=True)
        lenRanges = len(self.ranges)
        if not isinstance(idx, (int, long)):
            # idx is a tuple containing an integer indexing in ranges
            # to the first range touching [rangeStart, infinity)
            # or len(ranges)+1 because one couldn't be found
            assert(isinstance(idx, (list, tuple)))
            idx = idx[0]
        if idx >= lenRanges:
            return [lenRanges, lenRanges]  # Empty range
        # idx now refers to the location in self.ranges of the first
        # range touching [rangeStart, infinity)
        lastIdx = idx
        while True:
            if lastIdx >= lenRanges:
                return [idx, lastIdx]
            f, l = self.idxs(self.ranges[lastIdx])
            if f >= rangeEnd:
                return [idx, lastIdx]
            lastIdx += 1
        assert(False)

    def _invalidateCaches(self):
        pass
    
    ############# Slow but sure methods for unit testing ##############
    
    def _slowIdxOfRangeContaining(self, intVal, returnTupledIdxOfNextRangeOnFail=False):
        for i in range(len(self.ranges)):
            rangeItem = self.ranges[i]
            l, r = self.idxs(rangeItem)
            if l <= intVal < r:
                return i
            if l > intVal and returnTupledIdxOfNextRangeOnFail:
                return (i,)
        if returnTupledIdxOfNextRangeOnFail:
            return (len(self.ranges),)
        return None

    def _slowIdxRangeOfRangesTouchingRange(self, rangeStart, rangeEnd):
        if rangeStart >= rangeEnd:
            return [0,0]
        firstIdx = None
        for i in range(len(self.ranges)):
            rangeItem = self.ranges[i]
            f, l = self.idxs(rangeItem)
            leftOfTarget = l <= rangeStart
            rightOfTarget = f >= rangeEnd
            if not leftOfTarget and firstIdx == None:
                firstIdx = i
            if rightOfTarget:
                if firstIdx == None:
                    firstIdx = i
                return [firstIdx, i]
        if firstIdx == None:
            firstIdx = len(self.ranges)
        return [firstIdx, len(self.ranges)]
        