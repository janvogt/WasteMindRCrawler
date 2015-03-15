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
from datetime import date as Date
from datetime import timedelta as Timedelta
from itertools import chain, repeat
from uuid import uuid4
import sys
from street import Street

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
    def getCSV(self, count):
        return '\n'.join('{},"{}","{}",{}'.format(uuid4(), typ, date, self.geoId) for typ, date in chain(
                zip(repeat('yard_waste'), self.iterMultibleByDayMonthString(self.yardWaste, Date.today(), count)),
                zip(repeat('other'), self.iterWeeklyByDayString(self.residualWaste, Date.today(), count)),
                zip(repeat('organic'), self.iterWeeklyByDayString(self.bioWaste, Date.today(), count)),
                zip(repeat('paper'), self.iterBiweeklyByDayWeekString(self.greenBinAndYellowBag, Date.today(), count)),
                zip(repeat('plastic'), self.iterBiweeklyByDayWeekString(self.greenBinAndYellowBag, Date.today(), count))))

    @classmethod
    def _getRealIsodate(cls, isodate):
        try:
            return cls.offset[isodate]
        except KeyError:
            return isodate

    @classmethod
    def iterWeeklyByDayString(cls, day, dateBegin, count=0):
        try:
            date = cls._getNextDateForWeekday(dateBegin, cls.days[day])
        except KeyError:
            return
        n = 0
        while n < count or count == 0:
            yield date
            n += 1
            date += cls.week
    @classmethod
    def iterMultibleByDayMonthString(cls, daymonth, dateBegin, count=0):
        datesStr = daymonth.split(' ')
        year = dateBegin.year
        dates = []
        for dateStr in datesStr:
            match = re.match('(\d{2}).(\d{2}).', dateStr)
            if not match:
                continue
            day, month = match.group(1, 2)
            dates.append(Date(year, int(month), int(day)))
        n = 0
        if len(dates) == 0:
          return
        dates.sort()
        while True:
            for date in dates:
                date = Date(year, int(date.month), int(date.day))
                if date < dateBegin:
                    continue
                yield date
                n += 1
                if count != 0 and n >= count:
                    return
            year += 1
    @classmethod
    def iterBiweeklyByDayWeekString(cls, dayweek, dateBegin, count=0):
        dayweekArr = dayweek.split('/')
        if len(dayweekArr) == 1:
            yield from cls.iterWeeklyByDayString(dayweekArr[0], dateBegin, count)
            return
        try:
            date = cls._getNextDateForWeekday(dateBegin, cls.days[dayweekArr[0]])
        except KeyError:
            return
        date += cls.evenOffset[dayweekArr[1]]
        n = 0
        while n < count or count == 0:
            yield date
            n += 1
            date += cls.twoWeek
    @staticmethod
    def _getNextDateForWeekday(dateBegin, day):
        return dateBegin + Timedelta((7 - dateBegin.weekday()) % 7 + day)
    @staticmethod
    def getCSVHeader():
        return 'event_id,type,date,location_id'

class AwsCrawler:
    typeMap = {'Straße': 'street',
           'Schnitt gut': 'yardWaste',
           'Restmüll tonne': 'residualWaste',
           'Bio tonne': 'bioWaste',
           'Grüne Tonne Gelber Sack gerade/ungerade Kalenderwoche': 'greenBinAndYellowBag'}
    alphabet = 'abcdefghijklmnopqrstuvwxzyäöüß'
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
    if(5 != len(sys.argv)):
        print('Usage: ./{} streets_file events_output used_streets_output NcollectionsFromToday'.format(sys.argv[0]))
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
                f.write(row.getCSV(int(sys.argv[4])) + '\n')
        with open(streetsF, 'x') as f:
            f.write(Street.getCSVHeader() + '\n')
            for street in usedStreets.values():
                f.write(street.getCSV() + '\n')
