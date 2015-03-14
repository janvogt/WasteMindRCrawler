#!/usr/bin/env python3

"""Crawls the Waste calender from Freiburg

Uses the undocumented Endpoint using www.abfallwirtschaft-freiburg.de/_intern/search.php?strasse=xxx"""

__author__ = "Jan Vogt"
__copyright__ = "Copyright 2015, Jan Vogt"
__email__ = "jan.vogt@me.com"
__license__ = "GPLv3"

import  html.parser

class AwsRow:
    def __init__(self):
        self.street = ''
        self.yardWaste = ''
        self.residualWaste = ''
        self.bioWaste = ''
        self.greenBinAndYellowBag = ''

if __name__ == '__main__':
    print('hallo')