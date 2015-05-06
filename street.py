#!/usr/bin/env python3

"""Street Class to represent an (uu)id-ed street with name and geometry

Implements support functions for importing and exporting from CSV and name matching"""

__author__ = "Jan Vogt"
__copyright__ = "Copyright 2015, Jan Vogt"
__email__ = "jan.vogt@me.com"
__license__ = "GPLv3"

from uuid import uuid4
from multiline import Multiline
import re
import csv

class Street:
    def __init__(self, nameOrRow, lineOrFields):
        if isinstance(nameOrRow, str):
            self.name = nameOrRow
            self.uuid = uuid4()
            self.multiline = Multiline()
            self.addLine(lineOrFields)
        else:
            self.name = nameOrRow[lineOrFields['name']]
            self.uuid = nameOrRow[lineOrFields['id']]
            self.multiline = Multiline(nameOrRow[lineOrFields['geometry']])
    def addLine(self, line):
        self.multiline.addLine(line)
    def getWKT(self):
        return self.multiline.getWKT()
    def getCSV(self):
        return '{},"{}","{}"'.format(self.uuid, self.name, self.getWKT())
    def __str__(self):
        return 'Street(name="{}", multiline="{}", uuid="{}")'.format(self.name, self.multiline, self.uuid)
    @classmethod
    def getStreetsDictFromCSV(cls, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            rows = iter(csv.reader(f))
            header = next(rows)
            fields = {'id': header.index('location_id'), 'name': header.index('name'), 'geometry': header.index('geometry')}
            return {cls.normalizeName(row[fields['name']]): Street(row, fields) for row in csv.reader(f)}
    @staticmethod
    def normalizeName(name):
        normalized = name.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss').replace('*', '').replace(' ab ', '').replace('-', ' ').replace('ç', 'c')
        normalized = re.sub('\(.*?\)', '', normalized)
        normalized = re.match('.\D+', normalized).group(0).strip()
        normalized = re.sub('((?<=\w)strasse)|(-str(?!\w))|( str(?!\w))|(-strasse)|(str(?!\w))', ' strasse', normalized)
        normalized = re.sub('((?<=\w)weg)|(-weg)', ' weg', normalized)
        normalized = re.sub('((?<=\w)gasse)|(-gasse)', ' gasse', normalized)
        normalized = re.sub('((?<=\w)gaessle)|(-gaessle)', ' gaessle', normalized)
        normalized = re.sub('((?<=\w)platz)|(-platz)', ' platz', normalized)
        normalized = re.sub('((?<=\w)steige)|(-steige)', ' steige', normalized)
        normalized = re.sub('((?<=\w)ring)|(-ring)', ' ring', normalized)
        normalized = re.sub('((?<!\w)st\.\s)|((?<!\w)sankt\s)', 'sankt ', normalized)
        return normalized
    @staticmethod
    def getCSVHeader():
        return 'location_id,name,geometry'