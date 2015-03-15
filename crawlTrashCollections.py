#!/usr/bin/env python

"""Crawls the Waste calendar from Freiburg

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
import csv
from calendar import Calendar
from datetime import date as Date
from datetime import timedelta as Timedelta
from itertools import chain, repeat
import sys

class AwsRow:
    days = {'Mo': 0, 'Di': 1, 'Mi': 2, 'Do': 3, 'Fr': 4, 'Sa': 5, 'So': 6}
    evenOffset = {'u': Timedelta(0), 'g': Timedelta(7)}
    week = Timedelta(7)
    twoWeek = Timedelta(14)
    offsets = {'2015-01-01': '2015-01-02',
               '2015-01-02': '2015-01-03',
               '2015-01-06': '2015-01-07',
               '2015-01-07': '2015-01-08',
               '2015-01-08': '2015-01-09',
               '2015-01-09': '2015-01-10',
               '2015-02-16': '2015-02-17',
               '2015-02-17': '2015-02-18',
               '2015-02-18': '2015-02-19',
               '2015-02-19': '2015-02-20',
               '2015-02-20': '2015-02-21',
               '2015-04-03': '2015-04-02',
               '2015-04-06': '2015-04-07',
               '2015-04-07': '2015-04-08',
               '2015-04-08': '2015-04-09',
               '2015-04-09': '2015-04-10',
               '2015-04-10': '2015-04-11',
               '2015-05-01': '2015-05-02',
               '2015-05-14': '2015-05-15',
               '2015-05-15': '2015-05-16',
               '2015-05-25': '2015-05-26',
               '2015-05-26': '2015-05-27',
               '2015-05-27': '2015-05-28',
               '2015-05-28': '2015-05-29',
               '2015-05-29': '2015-05-30',
               '2015-06-04': '2015-06-05',
               '2015-06-05': '2015-06-06',
               '2015-12-21': '2015-12-19',
               '2015-12-22': '2015-12-21',
               '2015-12-23': '2015-12-22',
               '2015-12-24': '2015-12-23',
               '2015-12-25': '2015-12-24'}
    def __init__(self):
        self.street = ''
        self.yardWaste = ''
        self.residualWaste = ''
        self.bioWaste = ''
        self.greenBinAndYellowBag = ''
        self.geoId = ''
    def __str__(self):
        return "AwsRow(street=\"%s\", yardWaste=\"%s\", residualWaste=\"%s\", bioWaste=\"%s\", greenBinAndYellowBag=\"%s\")" % \
            (self.street, self.yardWaste, self.residualWaste, self.bioWaste, self.greenBinAndYellowBag)
    def __setattr__(self, name, value):
        self.__dict__[name] = re.sub('\s+', ' ', value).strip()
    def getCSV(self):
        return '\n'.join('"{}","{}",{}'.format(typ, date, self.geoId) for typ, date in chain(
                zip(repeat('yard_waste'), self.iterMultibleByDayMonthString(self.yardWaste, 2015)),
                zip(repeat('other'), self.iterWeeklyByDayString(self.residualWaste, 2015)),
                zip(repeat('organic'), self.iterWeeklyByDayString(self.bioWaste, 2015)),
                zip(repeat('paper'), self.iterBiweeklyByDayWeekString(self.greenBinAndYellowBag, 2015)),
                zip(repeat('plastic'), self.iterBiweeklyByDayWeekString(self.greenBinAndYellowBag, 2015))))

    @classmethod
    def _getRealIsodate(cls, isodate):
        try:
            return cls.offset[isodate]
        except KeyError:
            return isodate

    @classmethod
    def iterWeeklyByDayString(cls, day, year):
        try:
            date = cls._getFirstDateForWeekDay(year, cls.days[day])
        except KeyError:
            return
        while date.year == year:
            yield date
            date += cls.week
    @classmethod
    def iterMultibleByDayMonthString(cls, daymonth, year):
        dates = daymonth.split(' ')
        for date in dates:
            match = re.match('(\d{2}).(\d{2}).', date)
            if not match:
                return
            day, month = match.group(1, 2)
            yield Date(year, int(month), int(day))
    @classmethod
    def iterBiweeklyByDayWeekString(cls, dayweek, year):
        dayweekArr = dayweek.split('/')
        if len(dayweekArr) == 1:
            yield from cls.iterWeeklyByDayString(dayweekArr[0], year)
            return
        try:
            date = cls._getFirstDateForWeekDay(year, cls.days[dayweekArr[0]])
        except KeyError:
            return
        date += cls.evenOffset[dayweekArr[1]]
        while date.year == year:
            yield date
            date += cls.twoWeek
    @staticmethod
    def _getFirstDateForWeekDay(year, day):
        date = Date(year, 1, 1)
        return date + Timedelta((7 - date.weekday()) % 7 + day)
    @staticmethod
    def getCSVHeader():
        return 'type,date,location_id'

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

class Street:
    def __init__(self, name, uuid, row, header):
        self.name = name
        self.uuid = uuid
        self.row = row
        self.header = header
    def getCSV(self):
        return '{},"{}","{}"'.format(*self.row)
    @classmethod
    def getStreetsDictFromCSV(cls, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            rows = iter(csv.reader(f))
            header = next(rows)
            fields = {'location_id': header.index('location_id'), 'name': header.index('name')}
            return {cls.normalizeName(row[fields['name']]): Street(row[fields['name']], row[fields['location_id']], row, header) for row in csv.reader(f)}
    def __str__(self):
        return self.name + ' ' + self.uuid
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

if __name__ == '__main__':
    if(4 > len(sys.argv)):
        print('Usage: ./{} streets_file events_output used_streets_output'.format(sys.argv[0]))
        exit()
    streets = Street.getStreetsDictFromCSV(sys.argv[1])
    collectionsF, streetsF = sys.argv[2], sys.argv[3]
    try:
        rows = AwsCrawler.getRows()
    except URLError:
        print('Failed to download data')
    else:
        usedStreets = {}
        with open(collectionsF, 'x') as f:
            f.write(AwsRow.getCSVHeader() + '\n')
            for row in rows:
                try:
                    street = streets[Street.normalizeName(row.street)]
                    row.geoId = street.uuid
                    usedStreets[street.uuid] = street
                    # print('Match: ' + street.name + ' & ' + row.street)
                except KeyError:
                    pass
                    # print('Not found: ' + Street.normalizeName(row.street))
                f.write(row.getCSV() + '\n')
        with open(streetsF, 'x') as f:
            f.write(Street.getCSVHeader() + '\n')
            for street in usedStreets.values():
                f.write(street.getCSV() + '\n')
