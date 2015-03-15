#!/usr/bin/env python3

"""Line class to represent an ordered set of coordinates

Provides facilities to export wkt coordinate strings"""

__author__ = "Jan Vogt"
__copyright__ = "Copyright 2015, Jan Vogt"
__email__ = "jan.vogt@me.com"
__license__ = "GPLv3"

class Line:
    def __init__(self):
        self.points = []
    def addPoint(self, lat, lng):
        self.points.append((lng, lat))
    def getWKT(self):
        return '({})'.format(','.join(map(lambda x: "{:f} {:f}".format(*x), self.points)))
    def __str__(self):
        return str(self.points)