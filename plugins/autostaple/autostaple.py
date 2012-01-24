import util, cadnano
import heapq
from model.strandset import StrandSet
from model.enum import StrandType
from model.parts.part import Part
def breakStaples(part, settings):
    for o in list(part.oligos()):
        if not o.isStaple():
            continue
        breakStaple(o, settings)

# Scoring functions takes an incremental breaking solution (IBS, see below)
# which is a linked list of breakpoints (nodes) and calculates the score
# (edge weight) of the staple that would lie between the last break in
# currentIBS and proposedNextNode. Lower is better.
def tgtLengthStapleScorer(currentIBS, proposedNextBreakNode, settings):
    """ Gives staples a better score for being
    closer to settings['tgtStapleLen'] """
    tgtStapleLen = settings.get('tgtStapleLen', 35)
    lastBreakPosInOligo = currentIBS[2][0]
    proposedNextBreakPos = proposedNextBreakNode[0]
    stapleLen = proposedNextBreakPos - lastBreakPosInOligo
    # Note the exponent. This allows Djikstra to try solutions
    # with fewer length deviations first. If you don't include
    # it, most paths that never touch a leaf get visited, decreasing
    # efficiency for long proto-staples. Also, we want to favor solutions
    # with several small deviations from tgtStapleLen over solutions with
    # a single larger deviation.
    return abs(stapleLen - tgtStapleLen)**3

def breakStaple(oligo, settings):
    # We were passed a super-long, highly suboptimal staple in the
    # oligo parameter. Our task is to break it into more reasonable staples.
    # We create a conceptual graph which represents breakpoints as
    # nodes. Each edge then represents a staple (bounded by two breakpoints
    # = nodes). The weight of each edge is an optimality score, lower is
    # better. Then we use Djikstra to find the most optimal way to break
    # the super-long staple passed in the oligo parameter into smaller staples
    # by finding the minimum-weight path from "starting" nodes to "terminal"
    # nodes.        
        
    # The minimum number of bases after a crossover
    stapleScorer = settings.get('stapleScorer', tgtLengthStapleScorer)
    minStapleLegLen = settings.get('minStapleLegLen', 2)
    minStapleLen = settings.get('minStapleLen', 30)
    maxStapleLen = settings.get('maxStapleLen', 40)
        
    # First, we generate a list of valid breakpoints = nodes. This amortizes
    # the search for children in the inner loop of Djikstra later. Format:
    # node in nodes := (
    #   pos,        position of this break in oligo
    #   strand,     strand where the break occurs
    #   idx,        the index on strand where the break occurs
    #   isTerminal) True if this node can represent the last break in oligo
    nodes = possibleBreakpoints(oligo, settings)
    lengthOfNodesArr = len(nodes)
    
    # Each element of heap represents an incremental breakpoint solution (IBS)
    # which is a linked list of nodes taking the following form:
    # (totalWeight,   # the total weight of this list is first for automaic sorting
    #  prevIBS,       # the tuple representing the break before this (or None)
    #  node,          # the tuple from nodes representing this break
    #  nodeIdxInNodeArray)
    # An IBS becomes a full breakpoint solution iff
    #    Its first node is an initial node (got added during "add initial nodes")
    #    Its last node is a terminal node (got flagged as such in possibleBreakpoints)
    # Djikstra says: the first full breakpoint solution to be visited will be the optimal one
    heap = []
    firstStrand = oligo.strand5p()
    
    # Add everything on the firstStrand as an initial break
    # for i in xrange(len(nodes)):
    #     node = nodes[i]
    #     pos, strand, idx, isTerminal = node
    #     if strand != firstStrand:
    #         break
    #     newIBS = (0, None, node, i)
    #     heapq.heappush(heap, newIBS)
    
    # Just add the existing endpoint as an initial break
    newIBS = (0, None, nodes[0], 0)
    heap.append(newIBS)
    
    # nodePosLog = []
    while heap:
        # Pop the min-weight node off the heap
        curIBS = heapq.heappop(heap)
        curTotalScore, prevIBS, node, nodeIdxInNodeArr = curIBS
        if node[3]:  # If we popped a terminal node, we win
            # print "Full Breakpt Solution Found"
            return performBreaks(oligo.part(), curIBS)
        # Add its children (set of possible next breaks) to the heap
        nodePos = node[0]
        nextNodeIdx = nodeIdxInNodeArr + 1
        while nextNodeIdx < lengthOfNodesArr:
            nextNode = nodes[nextNodeIdx]
            nextNodePos = nextNode[0]
            proposedStrandLen = nextNodePos - nodePos
            if minStapleLen <= proposedStrandLen <= maxStapleLen:
                # nodePosLog.append(nextNodePos)
                nextStapleScore = tgtLengthStapleScorer(curIBS, nextNode, settings)
                newChildIBS = (curTotalScore + nextStapleScore,\
                               curIBS,\
                               nextNode,\
                               nextNodeIdx)
                heapq.heappush(heap, newChildIBS)
            elif proposedStrandLen > maxStapleLen:
                break
            nextNodeIdx += 1
    # print nodePosLog
    # print "No Breakpt Solution Found"

def performBreaks(part, fullBreakptSoln):
    """ fullBreakptSoln is in the format of an IBS (see breakStrands).
    This function performs the breaks proposed by the solution. """
    util.beginSuperMacro(part, desc="Auto-Break")
    breakList, oligo = [], None  # Only for logging purposes
    if fullBreakptSoln != None:  # Skip the first breakpoint
        fullBreakptSoln = fullBreakptSoln[1]
    while fullBreakptSoln != None:
        curNode = fullBreakptSoln[2]
        fullBreakptSoln = fullBreakptSoln[1]  # Walk up the linked list
        if fullBreakptSoln == None:  # Skip last breakpoint
            break
        pos, strand, idx, isTerminal = curNode
        if strand.isDrawn5to3():
            idx -= 1 # Our indices correspond to the left side of the base
        strand.split(idx, updateSequence=False)
        breakList.append(curNode)  # Logging purposes only
    # print 'Breaks for %s at: %s'%(oligo, ' '.join(str(p) for p in breakList))
    util.endSuperMacro(part)

def possibleBreakpoints(oligo, settings):
    """ Returns a list of possible breakpoints (nodes) in the format:
    node in nodes := (             // YOU CANNOT UNSEE THE SADFACE :P
      pos,        position of this break in oligo
      strand,     strand where the break occurs
      idx,        the index on strand where the break occurs
      isTerminal) True if this node can represent the last break in oligo"""
    
    # The minimum number of bases after a crossover
    minStapleLegLen = settings.get('minStapleLegLen', 2)
    minStapleLen = settings.get('minStapleLen', 30)
    maxStapleLen = settings.get('maxStapleLen', 40)
    
    nodes = []
    strand = firstStrand = oligo.strand5p()
    isLoop = strand.connection5p() != None
    pos, idx = 0, 0  # correspond to pos, idx above
    while True:
        nextStrand = strand.connection3p()
        isTerminalStrand = nextStrand in (None, firstStrand)
        if strand.isDrawn5to3():
            idx, maxIdx = strand.lowIdx(), strand.highIdx() + 1
            if strand != firstStrand:
                idx += minStapleLegLen
                pos += minStapleLegLen
            if not isTerminalStrand:
                maxIdx -= minStapleLegLen
            while idx <= maxIdx:
                isTerminalNode = isTerminalStrand and idx == maxIdx
                nodes.append((pos, strand, idx, isTerminalNode))
                idx += 1
                pos += 1
            pos += minStapleLegLen - 1
        else:
            minIdx, idx = strand.lowIdx(), strand.highIdx() + 1
            if strand != firstStrand:
                idx -= minStapleLegLen
                pos += minStapleLegLen
            if not isTerminalStrand:
                minIdx += minStapleLegLen
            while idx >= minIdx:
                isTerminalNode = isTerminalStrand and idx == minIdx
                nodes.append((pos, strand, idx, isTerminalNode))
                idx -= 1
                pos += 1
            pos += minStapleLegLen - 1
        strand = nextStrand
        if isTerminalStrand:
            break
    # if nodes:  # dump the node array to stdout
    #     print ' '.join(str(n[0])+':'+str(n[2]) for n in nodes) + (' :: %i'%oligo.length()) + repr(nodes[-1])
    return nodes
    
def autoStaple(part):
    """Autostaple does the following:
    1. Clear existing staple strands by iterating over each strand
    and calling RemoveStrandCommand on each. The next strand to remove
    is always at index 0.
    2. Create temporary strands that span regions where scaffold is present.
    3. Determine where actual strands will go based on strand overlap with
    prexovers.
    4. Delete temporary strands and create new strands.
    """
    epDict = {}  # keyed on StrandSet
    cmds = []

    # clear existing staple strands
    for vh in part.getVirtualHelices():
        stapSS = vh.stapleStrandSet()
        for strand in stapSS:
            c = StrandSet.RemoveStrandCommand(stapSS, strand, 0)  # rm
            cmds.append(c)
    util.execCommandList(part, cmds, desc="Clear staples")
    cmds = []

    # create strands that span all bases where scaffold is present
    for vh in part.getVirtualHelices():
        segments = []
        scafSS = vh.scaffoldStrandSet()
        for strand in scafSS:
            lo, hi = strand.idxs()
            if len(segments) == 0:
                segments.append([lo, hi])  # insert 1st strand
            elif segments[-1][1] == lo - 1:
                segments[-1][1] = hi  # extend
            else:
                segments.append([lo, hi])  # insert another strand
        stapSS = vh.stapleStrandSet()
        epDict[stapSS] = []
        for i in range(len(segments)):
            lo, hi = segments[i]
            epDict[stapSS].extend(segments[i])
            c = StrandSet.CreateStrandCommand(stapSS, lo, hi, i)
            cmds.append(c)
    util.execCommandList(part, cmds, desc="Add tmp strands", useUndoStack=False)
    cmds = []

    # determine where xovers should be installed
    for vh in part.getVirtualHelices():
        stapSS = vh.stapleStrandSet()
        is5to3 = stapSS.isDrawn5to3()
        potentialXovers = part.potentialCrossoverList(vh)
        for neighborVh, idx, strandType, isLowIdx in potentialXovers:
            if strandType != StrandType.Staple:
                continue
            if isLowIdx and is5to3:
                strand = stapSS.getStrand(idx)
                neighborSS = neighborVh.stapleStrandSet()
                nStrand = neighborSS.getStrand(idx)
                if strand == None or nStrand == None:
                    continue
                # check for bases on both strands at [idx-1:idx+3]
                if strand.lowIdx() < idx and strand.highIdx() > idx + 1 and\
                   nStrand.lowIdx() < idx and nStrand.highIdx() > idx + 1:
                    epDict[stapSS].extend([idx, idx+1])
                    epDict[neighborSS].extend([idx, idx+1])

    # clear temporary staple strands
    for vh in part.getVirtualHelices():
        stapSS = vh.stapleStrandSet()
        for strand in stapSS:
            c = StrandSet.RemoveStrandCommand(stapSS, strand, 0)
            cmds.append(c)
    util.execCommandList(part, cmds, desc="Rm tmp strands", useUndoStack=False)
    cmds = []

    util.beginSuperMacro(part, desc="Auto-Staple")

    for stapSS, epList in epDict.iteritems():
        assert (len(epList) % 2 == 0)
        epList = sorted(epList)
        ssIdx = 0
        for i in range(0, len(epList),2):
            lo, hi = epList[i:i+2]
            c = StrandSet.CreateStrandCommand(stapSS, lo, hi, ssIdx)
            cmds.append(c)
            ssIdx += 1
    util.execCommandList(part, cmds, desc="Create strands")
    cmds = []

    # create crossovers wherever possible (from strand5p only)
    for vh in part.getVirtualHelices():
        stapSS = vh.stapleStrandSet()
        is5to3 = stapSS.isDrawn5to3()
        potentialXovers = part.potentialCrossoverList(vh)
        for neighborVh, idx, strandType, isLowIdx in potentialXovers:
            if strandType != StrandType.Staple:
                continue
            if (isLowIdx and is5to3) or (not isLowIdx and not is5to3):
                strand = stapSS.getStrand(idx)
                neighborSS = neighborVh.stapleStrandSet()
                nStrand = neighborSS.getStrand(idx)
                if strand == None or nStrand == None:
                    continue
                part.createXover(strand, idx, nStrand, idx, updateOligo=False)

    c = Part.RefreshOligosCommand(part)
    cmds.append(c)
    util.execCommandList(part, cmds, desc="Assign oligos")
    cmds = []
    util.endSuperMacro(part)
# end def

cadnano.app().breakStaples = breakStaples
