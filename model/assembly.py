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
assembly.py

Created by Nick Conway on 2011-01-19.
"""

from collections import defaultdict
from idbank import IdBank

# from PyQt4.QtCore import QObject
import util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QObject'] )



class Assembly(QObject):
    """
    """
    def __init__(self, parent=None):
        super(Assembly,self).__init__()
        """
        this is gonna be a list of non-specific attributes for an assembly
        self.object_instances = defaultdict(list)  # default dictionary as a list?
        """
        self.parent = parent    # or parent hash?
        self.node_type = "assembly"
        self.color = 0
        self.annotation = ""
        
        #self.instance_id_bank = IdBank()    # generate instances of themselves
                
        # this contains instances of this specific assembly, and other views
        # like: self.instances[id] = [treeNode] 
        self.instances = {}
        
        self.part_children = {}
        self.mate_children = {}
        
        # other views
    # end def
# end class

class AssemblyInstance(Assembly):
    def __init__(self, name, obj_id, parent=None):
        pass
    # end def
# end class
