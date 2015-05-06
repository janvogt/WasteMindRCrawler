#!/usr/bin/env python3

"""Crawl streetgeometries from OSM

Using http://overpass-api.de/api/"""

__author__ = "Jan Vogt"
__copyright__ = "Copyright 2015, Jan Vogt"
__email__ = "jan.vogt@me.com"
__license__ = "GPLv3"

from overpy import Overpass
from itertools import chain
from multiline import Multiline
from line import Line
from uuid import uuid4


class RegionCrawler:
#     osmScript = """<osm-script output="json" timeout="25">
#   <id-query into="searchArea" ref="3601970193" type="area"/>
#   <union into="_">
#     <query into="_" type="node">
#       <has-kv k="highway" modv="" v=""/>
#       <area-query from="searchArea" into="_" ref=""/>
#     </query>
#     <query into="_" type="way">
#       <has-kv k="highway" modv="" v=""/>
#       <area-query from="searchArea" into="_" ref=""/>
#     </query>
#     <query into="_" type="relation">
#       <has-kv k="highway" modv="" v=""/>
#       <area-query from="searchArea" into="_" ref=""/>
#     </query>
#   </union>
#   <print e="" from="_" geometry="skeleton" limit="" mode="body" n="" order="id" s="" w=""/>
#   <recurse from="_" into="_" type="down"/>
#   <print e="" from="_" geometry="skeleton" limit="" mode="skeleton" n="" order="quadtile" s="" w=""/>
# </osm-script>"""
    osmScript="""area[name="{}"][boundary=administrative]->.a;
way(area.a)[highway][name];
(._;>;);out;"""
    @classmethod
    def getStreets(cls, region):
        data = cls.osmScript.format(region)
        result = Overpass().query(data)
        nodes = {n.id: (n.lat, n.lon) for n in result.get_nodes()}
        multiline = Multiline()
        for way in result.get_ways():
            l = Line()
            for nId in way._node_ids:
                l.addPoint(*nodes[nId])
            multiline.addLine(l)
        return multiline

if __name__ == "__main__":
    import sys
    if 2 > len(sys.argv):
        print("Usage: ./{} region >> streetfile.csv".format(sys.argv[0]))
    else:
        print('{},"{}","{}"'.format(uuid4(), sys.argv[1], RegionCrawler.getStreets(sys.argv[1]).getWKT()))
