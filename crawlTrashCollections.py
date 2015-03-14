#!/usr/bin/env python

"""Crawls the Waste calender from Freiburg

Uses the undocumented Endpoint using www.abfallwirtschaft-freiburg.de/_intern/search.php?strasse=xxx"""

__author__ = "Jan Vogt"
__copyright__ = "Copyright 2015, Jan Vogt"
__email__ = "jan.vogt@me.com"
__license__ = "GPLv3"

from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import quote
from lxml import etree
import re


class AwsRow:
    def __init__(self):
        self.street = ''
        self.yardWaste = ''
        self.residualWaste = ''
        self.bioWaste = ''
        self.greenBinAndYellowBag = ''

    def __str__(self):
        return "AwsRow(street=\"%s\", yardWaste=\"%s\", residualWaste=\"%s\", bioWaste=\"%s\", greenBinAndYellowBag=\"%s\")" % \
            (self.street, self.yardWaste, self.residualWaste, self.bioWaste, self.greenBinAndYellowBag)

    def __setattr__(self, name, value):
        self.__dict__[name] = re.sub('\s+', ' ', value).strip()

from collections import defaultdict

class AwsCrawler:
    typeMap = {'Straße': 'street',
           'Schnitt gut': 'yardWaste',
           'Restmüll tonne': 'residualWaste',
           'Bio tonne': 'bioWaste',
           'Grüne Tonne Gelber Sack gerade/ungerade Kalenderwoche': 'greenBinAndYellowBag'}
    alphabet = 'abcdefghijklmnopqrstuvwxzyäöüß'
    offsets = {'01-01-2015': '01-02-2015',
               '01-02-2015': '01-03-2015',
               '01-06-2015': '01-07-2015',
               '01-07-2015': '01-08-2015',
               '01-08-2015': '01-09-2015',
               '01-09-2015': '01-10-2015',
               '02-16-2015': '02-17-2015',
               '02-17-2015': '02-18-2015',
               '02-18-2015': '02-19-2015',
               '02-19-2015': '02-20-2015',
               '02-20-2015': '02-21-2015',
               '04-03-2015': '04-02-2015',
               '04-06-2015': '04-07-2015',
               '04-07-2015': '04-08-2015',
               '04-08-2015': '04-09-2015',
               '04-09-2015': '04-10-2015',
               '04-10-2015': '04-11-2015',
               '05-01-2015': '05-02-2015',
               '05-14-2015': '05-15-2015',
               '05-15-2015': '05-16-2015',
               '05-25-2015': '05-26-2015',
               '05-26-2015': '05-27-2015',
               '05-27-2015': '05-28-2015',
               '05-28-2015': '05-29-2015',
               '05-29-2015': '05-30-2015',
               '06-04-2015': '06-05-2015',
               '06-05-2015': '06-06-2015',
               '12-21-2015': '12-19-2015',
               '12-22-2015': '12-21-2015',
               '12-23-2015': '12-22-2015',
               '12-24-2015': '12-23-2015',
               '12-25-2015': '12-24-2015'}
    @classmethod
    def getRows(cls):
        """Throws URLError if download fails"""
        AwsRows = []
        for letter in cls.alphabet:
            with urlopen("http://www.abfallwirtschaft-freiburg.de/_intern/search.php?strasse=%s" % quote(letter)) as resp:
                respStr = resp.read().decode('utf-8')
                tree = etree.HTML(respStr)
                if None == tree:
                    continue
                table = tree.find('body/table/tbody')
                if None == table:
                    continue
                rows = iter(table)
                header = [cls.typeMap[' '.join(col.itertext())] for col in next(rows)]
                for row in rows:
                    awsRow = AwsRow()
                    for (i, col) in enumerate(row):
                        setattr(awsRow, header[i], ' '.join(col.itertext()))
                    AwsRows.append(awsRow)
        return AwsRows

if __name__ == '__main__':
    try:
        for row in AwsCrawler.getRows():
            print(row)
    except URLError:
        print('Failed to download data')