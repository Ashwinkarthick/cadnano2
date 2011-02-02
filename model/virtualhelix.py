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


class VirtualHelix(object):
    """Stores staple and scaffold routing information."""
    def __init__(self, number, canvasSize):
        super(VirtualHelix, self).__init__()
        self._number = number
        self._canvasSize = canvasSize
        self._staple = []
        self._scaffold = []

    def simpleRep(self,encoder):
        """Returns a representation in terms of simple JSON-encodable types
        or types that implement simpleRep"""
        ret = {'.class': "DNAPart"}
        ret['number'] = self._number
        ret['canvasSize'] = self._canvasSize
        ret['staple'] = self._staple
        ret['scaffold'] = self._scaffold
        return ret

    @classmethod
    def fromSimpleRep(cls, rep):
        """Instantiates one of the parent class from the simple
        representation rep"""
        ret = VirtualHelix()
        ret._number = rep['number']
        ret._canvasSize = rep['canvasSize']
        ret._staple = rep['staple']
        ret._scaffold = rep['scaffold']
        return ret

    def resolveSimpleRepIDs(self,idToObj):
        raise NotImplementedError

    def number(self):
        """return VirtualHelix number"""
        return self._number
