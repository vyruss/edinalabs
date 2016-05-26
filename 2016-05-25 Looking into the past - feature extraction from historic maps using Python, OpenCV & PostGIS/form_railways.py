#!/usr/bin/python

"""

do like we do in other cases, try and form groups from primitives by in this
case searching for primitives within some distance of one another and which
minimise change in azimuth

for a point find the distance and azimuth from that point to the 5 nearest
neighbours of that point.

SELECT
b.gid,
st_distance(a.geom, b.geom) as n_distance,
degrees(st_azimuth(a.geom, b.geom)) as n_orientation
FROM
(
 SELECT gid, geom
 FROM rail.points_91578182
 WHERE gid = 214
) a,
rail.points_91578182 b
WHERE b.gid != a.gid
ORDER BY a.geom <-> b.geom
LIMIT 5;

as it stands this is not useful. We need to compare this_azimuth with
prev_azimuth i.e. calculate delta and pick the neighbour that minimises change
in delta from prev

suspect things will break down at junctions where multiple lines converge...

"""

import os
import pickle
import string

from collections import OrderedDict

from shapely.wkt import loads
from shapely.geometry import mapping, LineString

import fiona
from fiona.crs import from_epsg

import pg_connection


def write_geometries(force_refresh=False):
    if force_refresh or (not os.path.exists("/home/james/Desktop/geometries.data")):
        print("writing neighbour geometries...")
        db_host = "localhost"
        db_port = "5432"
        db_name = "james"
        db_user = "james"

        db_params = pg_connection.DatabaseConnectionParams(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user)

        db_connection_string = db_params.get_connection_string()

        table_name = "rail.points_91578182"

        if db_connection_string is not None:
            sql_t = string.Template(
                """SELECT gid,st_astext(geom) FROM $srcTableName"""
            )

            sql = sql_t.substitute(srcTableName=table_name)

            rs = pg_connection.query_pg(sql, db_connection_string)

            d = {}

            for r in rs:
                gid = r[0]
                wkt = r[1]
                d[gid] = wkt

            with open("/home/james/Desktop/geometries.data", "wb") as outpf:
                pickle.dump(d, outpf)


def find_and_write_neighbours(force_refresh=False, debug=False):
    if force_refresh or (not os.path.exists("/home/james/Desktop/neighbours.data")):
        print("querying Pg for neighbours...")

        db_host = "localhost"
        db_port = "5432"
        db_name = "james"
        db_user = "james"

        db_params = pg_connection.DatabaseConnectionParams(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user)

        db_connection_string = db_params.get_connection_string()

        table_name = "rail.points_91578182"

        if db_connection_string is not None:
            sql_t = string.Template(
                """SELECT gid FROM $srcTableName"""
            )

            sql = sql_t.substitute(srcTableName=table_name)

            rs = pg_connection.query_pg(sql, db_connection_string)

            gids = [x[0] for x in rs]

            sql_t = string.Template(
                """SELECT
                a.gid,
                b.gid,
                st_distance(a.geom, b.geom) as n_distance,
                degrees(st_azimuth(a.geom, b.geom)) as n_orientation
                FROM
                (
                 SELECT gid, geom
                 FROM $srcTableName
                 WHERE gid = $gid
                ) a,
                $srcTableName b
                WHERE b.gid != a.gid
                ORDER BY a.geom <-> b.geom
                LIMIT 5"""
            )

            d = {}

            for gid in gids:
                sql = sql_t.substitute(
                    srcTableName=table_name,
                    gid=gid
                )

                rs = pg_connection.query_pg(
                    sql,
                    db_connection_string
                )

                neighbours = {}

                for r in rs:
                    neighbour_id = r[1]
                    distance = r[2]
                    orientation = r[3]
                    neighbours[neighbour_id] = [distance, orientation]

                d[gid] = neighbours

            with open("/home/james/Desktop/neighbours.data", "wb") as outpf:
                pickle.dump(d, outpf)


def group(start_gid, stop_gid, debug=False):
    status_ok = True
    if debug:
        print("In debug mode, so processing will stop artificially")
    allocated = None
    fn = "/home/james/Desktop/neighbours.data"
    if os.path.exists(fn):
        d = None

        with open(fn, "rb") as inpf:
            d = pickle.load(inpf)

        if d is not None:
            allocated = [start_gid]
            current_gid = start_gid

            cycles = 1

            if debug:
                # when we are in debug mode, cap iterations
                cycle_limit = 150
            else:
                cycle_limit = 0

            while (stop_gid not in allocated) and cycles < cycle_limit:
                if debug:
                    if cycles == cycle_limit:
                        print("oops (stuck in infinite loop) - thus execution artificially halted :p")
                        print(cycles)
                        status_ok = False
                min_distance = 1000000
                next_gid = None
                neighbours = d[current_gid]
                for neighbour_id in neighbours:
                    if neighbour_id not in allocated:
                        neighbour = neighbours[neighbour_id]
                        if debug:
                            print(current_gid, "-->", neighbour_id)
                        n_distance = neighbour[0]
                        n_orientation = neighbour[1]
                        if n_distance < min_distance:
                            min_distance = n_distance
                            next_gid = neighbour_id

                if next_gid is not None:
                    if debug:
                        print("".join(["for ", current_gid, " picked ", next_gid]))
                    if next_gid not in allocated:
                        allocated.append(next_gid)
                    if debug:
                        print(allocated)
                    current_gid = next_gid
                cycles += 1

    return allocated, status_ok


def linestrings_to_shapefile(linestrings, shp_fname):
    schema_properties = OrderedDict(
        [
            ("gid", "int")
        ]
    )

    my_schema = {
        "geometry": "LineString",
        "properties": schema_properties
    }

    my_driver = "ESRI Shapefile"
    my_crs = from_epsg(27700)

    with fiona.open(shp_fname, "w", driver=my_driver, crs=my_crs, schema=my_schema) as outpf:
        for gid in linestrings:
            linestring = linestrings[gid]

            outpf.write({
                "geometry": mapping(linestring),
                "properties": {
                    "gid": gid
                }
            })


def fetch_geometries():
    geometries = None

    if os.path.exists("/home/james/Desktop/geometries.data"):
        with open("/home/james/Desktop/geometries.data") as inpf:
            geometries = pickle.load(inpf)

    return geometries


def form_railway(start_gid, stop_gid, debug=False):
    geometries = fetch_geometries()

    if geometries is not None:
        allocated, status_ok = group(start_gid, stop_gid, debug)

        if status_ok:
            print("writing railwayline shapefile...")
            linestrings = {}
            points = []

            for gid in allocated:
                wkt = loads(geometries[gid])
                points.append(wkt)

            ls = LineString(points)
            linestrings = {1: ls}

            shp_fname = "".join(
                [
                    "/home/james/Desktop/railway_",
                    str(start_gid),
                    "_to_",
                    str(stop_gid),
                    ".shp"
                ]
            )

            linestrings_to_shapefile(linestrings, shp_fname)


def main():
    find_and_write_neighbours()
    write_geometries()
    start_gid = 88
    stop_gid = 119
    form_railway(start_gid, stop_gid, debug=True)

if __name__ == "__main__":
    main()