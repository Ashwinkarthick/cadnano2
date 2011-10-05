# Copyright 2011 Autodesk, Inc.  All rights reserved.
#
# The MIT License
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
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

from controllers.mayacontrollers.mayaObjectManager import Mom
from controllers.itemcontrollers.strand.stranditemcontroller import StrandItemController
from model.enum import StrandType
from model.enum import LatticeType

import maya.OpenMayaUI as mui
import maya.OpenMaya as mo
import maya.cmds as cmds
import util

util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QColor'])

"""
solidrootitem.py
Created by Simon Breslav on 2011-10-05.
"""

class StrandItem(QObject):
    """
    StrandItem is the strand item in the SolidView. 
    """
    def __init__(self, id, modelStrand, virtualHelixItem):
        """The parent should be a VirtualHelixItem."""
        super(StrandItem, self).__init__(virtualHelixItem)
        self._modelStrand = modelStrand
        self._virtualHelixItem = virtualHelixItem
        self._controller = StrandItemController(self, modelStrand)
        mayaNodeInfo = ()
        if(modelStrand.strandSet().isScaffold()):
            mayaNodeInfo = self.createMayaHelixNodes(virtualHelixItem.x(),
                                                     virtualHelixItem.y(),
                                      modelStrand.oligo().color(),
                                      StrandType.Scaffold,
                                      id)
        else:
            mayaNodeInfo = self.createMayaHelixNodes(virtualHelixItem.x(),
                                                     virtualHelixItem.y(),
                                      modelStrand.oligo().color(),
                                      StrandType.Staple,
                                      id)
        #self.onStrandDidMove(strand)
        m = Mom()
        m.cnToMaya[ modelStrand ] = mayaNodeInfo
        m.mayaToCn[ mayaNodeInfo[2] ] = modelStrand
        m.mayaToCn[ mayaNodeInfo[0] ] = modelStrand
    # end def

    ### SLOTS ###
    def strandResizedSlot(self):
        """strandResizedSlot"""
        print "solidview.StrandItem.strandResizedSlot", self._modelStrand.idxs()
        id = self._virtualHelixItem.partItem().strandMayaID(self._modelStrand)
        cylinderName = "HalfCylinderHelixNode%s" % id
        # XXX - [SB] why is there +1 in 2nd component of idxs?
        endpoints = self._modelStrand.idxs()
        totalNumBases = self._virtualHelixItem.vhelix().part().maxBaseIdx()
        cmds.setAttr("%s.startBase" % cylinderName,
                             endpoints[0])
    
        cmds.setAttr("%s.endBase" % cylinderName,
                             endpoints[1] - 1)
        cmds.setAttr("%s.totalBases" % cylinderName, int(totalNumBases))

    def sequenceAddedSlot(self, oligo):
        """sequenceAddedSlot"""
        print "solidview.StrandItem.sequenceAddedSlot"

    def sequenceClearedSlot(self, oligo):
        """sequenceClearedSlot"""
        print "solidview.StrandItem.sequenceClearedSlot"
    # end def

    def strandRemovedSlot(self, strand):
        id = self._virtualHelixItem.partItem().strandMayaID(strand)
        #print "SolidHelix:onStrandWillBeRemoved %s" % id
        transformName = "DNAShapeTransform%s" % id
        mom = Mom()
        mom.removeIDMapping(id, strand)
        
        if cmds.objExists(transformName):
            cmds.delete(transformName)

        self._virtualHelixItem.StrandIDs().remove(id)
        self._virtualHelixItem.partItem().deleteStrandMayaID(strand)

        #print strand
        self._modelStrand = None
        self._controller.disconnectSignals()
        self._controller = None
        print "solidview.StrandItem.sequenceClearedSlot"
    # end def

    def strandDestroyedSlot(self, strand):
        print "solidview.StrandItem.strandDestroyedSlot"
    # end def

    def strandXover3pCreatedSlot(self, strand):
        print "solidview.StrandItem.strandXover3pCreatedSlot"
    # end def

    def strandXover3pRemovedSlot(self, strand):
        print "solidview.StrandItem.strandXover3pRemovedSlot"
    # end def

    def oligoAppeareanceChangedSlot(self, oligo):
        print "solidview.StrandItem.oligoAppeareanceChangedSlot"
    # end def

    def oligoSequenceAddedSlot(self, oligo):
        print "solidview.StrandItem.oligoSequenceAddedSlot"
    # end def

    def oligoSequenceClearedSlot(self, oligo):
        print "solidview.StrandItem.oligoSequenceClearedSlot"
    # end def

    def strandHasNewOligoSlot(self, strand):
        print "solidview.StrandItem.strandHasNewOligoSlot"
    # end def

    def strandDecoratorCreatedSlot(self, strand):
        print "solidview.StrandItem.strandDecoratorCreatedSlot"
    # end def

    def createMayaHelixNodes(self, x, y, colorname, strandType, id):
        cylinderName = "HalfCylinderHelixNode%s" % id
        transformName = "DNAShapeTransform%s" % id
        meshName = "DNACylinderShape%s" % id
        shaderName = "DNAStrandShader%s" % id

        cmds.createNode("transform", name=transformName)
        cmds.setAttr("%s.rotateX" % transformName, 90)
        cmds.setAttr("%s.translateX" % transformName, x)
        cmds.setAttr("%s.translateY" % transformName, y)
        cmds.createNode("mesh", name=meshName, parent=transformName)

        cmds.createNode("spHalfCylinderHelixNode", name=cylinderName)
        cmds.connectAttr("%s.outputMesh" % cylinderName,
                         "%s.inMesh" % meshName)

        # XXX - [SB] This should go away and we will ask the model for
        # the right numbers...
        if self._virtualHelixItem.partItem().type() == LatticeType.Honeycomb:
            cmds.setAttr("%s.rotation" % cylinderName, 34.286)
            cmds.setAttr("%s.rotationOffset" % cylinderName, 30)
            cmds.setAttr("%s.parity" % cylinderName, self._virtualHelixItem.isEvenParity())
        elif self._virtualHelixItem.partItem().type() == LatticeType.Square:
            cmds.setAttr("%s.rotation" % cylinderName, 33.75)
            cmds.setAttr("%s.rotationOffset" % cylinderName, 240)
            cmds.setAttr("%s.parity" % cylinderName, self._virtualHelixItem.isEvenParity())
        else:
            raise NotImplementedError

        cmds.setAttr("%s.strandType" % cylinderName, strandType)
        color = QColor(colorname)
        colorval = "%d_%d_%d" % (color.red(), color.green(), color.blue())
        shaderName = "DNAStrandShader%d_%d_%d" % (color.red(),
                                                  color.green(),
                                                  color.blue())
        if not cmds.objExists(shaderName):
            # Shader does not exist create one
            cmds.shadingNode('lambert', asShader=True, name=shaderName)
            cmds.sets(n="%sSG" % shaderName, r=True, nss=True, em=True)
            cmds.connectAttr("%s.outColor" % shaderName,
                             "%sSG.surfaceShader" % shaderName)
            cmds.setAttr("%s.color" % shaderName,
                         color.redF(), color.greenF(), color.blueF(),
                         type="double3")
            cmds.sets(meshName, forceElement="%sSG" % shaderName)
        else:
            #shader exist connect
            cmds.sets(meshName, forceElement="%sSG" % shaderName)
            
        return (cylinderName, transformName, meshName)



