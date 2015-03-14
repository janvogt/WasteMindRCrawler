#!usr/bin/env python3

"""Crawl streetgeometries from OSM

Using http://overpass-api.de/api/"""

__author__ = "Jan Vogt"
__copyright__ = "Copyright 2015, Jan Vogt"
__email__ = "jan.vogt@me.com"
__license__ = "GPLv3"

from overpy import Overpass
from itertools import chain

class Street:
    def __init__(self, name, line):
        self.name = name
        self.lines = [line]
    def addLine(self, line):
        self.lines.append(line)
    def getWKT(self):
        if len(self.lines) > 1:
            return 'MULTILINESTRING({})'.format(','.join(map(lambda x: x.getWKT(), self.lines)))
        else:
            return 'LINESTRING' + self.lines[0].getWKT()
    def __str__(self):
        return ('Street(name="%s" wkt="%s")' % (self.name, self.getWKT()))


class Line:
    def __init__(self):
        self.points = []
    def addPoint(self, lat, lng):
        self.points.append((lat, lng))
    def getWKT(self):
        return '({})'.format(','.join(map(lambda x: str(float(x)), chain(*self.points))))
    def __str__(self):
        return str(self.points)

class StreetCrawler:
    osmScript = """<?xml version="1.0" encoding="UTF-8"?>
<osm-script timeout="1800" element-limit="2073741824">
    <union>
      <query type="way">
        <has-kv k="highway" v="motorway"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="trunk"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="primary"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="secondary"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="tertiary"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="residential"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="unclassified"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="living_street"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="pedestrian"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="service"/>
        <has-kv k="service" v="parking_aisle" modv="not"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="tertiary"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="residential"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="motorway_link"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="trunk_link"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="primary_link"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="secondary_link"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="residential_link"/>
        <bbox-query {0}/>
      </query>
      <query type="way">
        <has-kv k="highway" v="tertiary_link"/>
        <bbox-query {0}/>
      </query>
    </union>
    <union>
      <item/>
      <recurse type="down"/>
    </union>
    <print/>
</osm-script>"""
    freiburgBB = 's="47.9169" w="7.6676" n="48.0524" e="7.9327"'
    @classmethod
    def getStreets(cls):
        data = cls.osmScript.format(cls.freiburgBB)
        result = Overpass().query(data)
        nodes = {n.id: (n.lat, n.lon) for n in result.get_nodes()}
        streets = {}
        for way in result.get_ways():
            try:
                name = way.tags['name']
                l = Line()
                for nId in way._node_ids:
                    l.addPoint(*nodes[nId])
                try:
                    streets[name].addLine(l)
                except KeyError:
                    streets[name] = Street(name, l)
            except KeyError:
                continue
        return streets

if __name__ == "__main__":
    streets = StreetCrawler.getStreets()
    for s in streets.values():
        print(s)