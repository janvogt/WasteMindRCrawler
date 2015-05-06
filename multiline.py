#!/usr/bin/env python3

"""Multiline Class to represent an multiline geometry

Implements support functions for importing and exporting from WKT"""

__author__ = "Jan Vogt"
__copyright__ = "Copyright 2015, Jan Vogt"
__email__ = "jan.vogt@geops.de"
__license__ = "GPLv3"

class Multiline:
    def __init__(self, wkt=None):
        self.lines = None if wkt else []
        # import from WKT
        # until that:
        self.wkt = wkt
    def addLine(self, line):
        if not self.wkt:
            self.lines.append(line)
        else:
            raise
    def getWKT(self):
        if not self.lines:
            return self.wkt
        if len(self.lines) > 1:
            self.wkt = 'MULTILINESTRING({})'.format(','.join(map(lambda x: x.getWKT(), self.lines)))
        else:
            self.wkt = 'LINESTRING' + self.lines[0].getWKT()
        self.lines = None
        return self.wkt
    def __str__(self):
        return 'Multiline(wkt="{}", lines="{}")'.format(self.wkt, self.lines)