import csv
import math

from collections import OrderedDict

import cv2
import numpy as np

import fiona
from fiona.crs import from_epsg
import rasterio
from shapely.geometry import mapping, Point, box


def get_rotated_rec(cnt):
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    angle_of_rotation = rect[2]
    box = np.int0(box)

    return box, angle_of_rotation


def get_roundness(cnt):
    # roundness describes a shapes resemblance to a circle
    # roundness approaches 1 the close a shape resembles a circle
    # http://www.imagemet.com/WebHelp6/Default.htm#PnPParameters/Measure_Shape_Parameters.htm#Roundnes
    # http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_imgproc/py_contours/py_contour_features/py_contour_features.html

    enclosed_area = cv2.contourArea(cnt)

    # min enclosing circle is the smallest circle enclosing all points of the shape
    (x, y), radius = cv2.minEnclosingCircle(cnt)
    center = (int(x), int(y))
    radius = int(radius)
    max_diameter = 2 * radius

    roundness = (4 * (enclosed_area / math.pi)) / math.pow(max_diameter, 2)

    return roundness


def get_compactness_from_roundness(cnt):
    # http://www.imagemet.com/WebHelp6/Default.htm#PnPParameters/Measure_Shape_Parameters.htm#Roundnes
    # compactness is a measure of how compact a feature is
    # except for a circle which will have a compactness of 1, all shapes will have a compactness factor
    # less than 1
    compactness = math.sqrt(get_roundness(cnt))

    return compactness


def get_contour_properties(cnt):
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    perimeter = cv2.arcLength(cnt, True)

    # # a convex polygon has no indents in any edges
    # # a concave polygon has an indent in at least one edge
    is_convex = cv2.isContourConvex(cnt)

    rotated_rectangle, angle_of_rotation = get_rotated_rec(cnt)
    aspect_ratio = float(w/h)
    rect_area = w*h
    extent = float(area)/rect_area

    chull = cv2.convexHull(cnt)
    chull_area = cv2.contourArea(chull)

    try:
        solidity = float(area)/chull_area
    except ZeroDivisionError:
        solidity = None

    compactness = get_compactness_from_roundness(cnt)
    roundness = get_roundness(cnt)

    contour_properties = {
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "area": area,
        "perimeter": perimeter,
        "is_convex": is_convex,
        "angle_of_rotation": angle_of_rotation,
        "aspect_ratio": aspect_ratio,
        "extent": extent,
        "solidity": solidity,
        "compactness": compactness,
        "roundness": roundness
    }

    return contour_properties


def retain_contour(properties_of_contour, min_area_threshold=500, min_roundness_threshold=0.1, max_aspect_ratio_threshold=1.5):
    retain = False

    area = properties_of_contour[0]
    perimeter = properties_of_contour[1]
    is_convex = properties_of_contour[2]
    angle_of_rotation = properties_of_contour[3]
    aspect_ratio = properties_of_contour[4]
    extent = properties_of_contour[5]
    solidity = properties_of_contour[6]
    compactness = properties_of_contour[7]
    roundness = properties_of_contour[8]

    if area >= min_area_threshold:
        if roundness > min_roundness_threshold:
            if aspect_ratio < max_aspect_ratio_threshold:
                retain = True

    return retain


def count_children(hierarchy):
    d = {}

    for cnt in hierarchy[0]:
        parent = cnt[3]

        if parent != -1:
            if parent in d:
                d[parent] += 1
            else:
                d[parent] = 1

    return d


def contour_properties_csv_to_shapefile(csv_fname="", src_image="", shp_fname="", geometry_type="Polygon"):

    if geometry_type in ("Polygon", "Point", "Centroid"):
        ds = rasterio.open(src_image)
        ds_affine = ds.affine

        schema_properties = OrderedDict(
            [
                ("id", "int"),
                ("x", "int"),
                ("y", "int"),
                ("w", "int"),
                ("h", "int"),
                ("area", "float"),
                ("perim", "float"),
                ("convex", "str"),
                ("rotation", "float"),
                ("aratio", "float"),
                ("extent", "float"),
                ("solidity", "float"),
                ("compact", "float"),
                ("round", "float")
            ])

        my_schema = {
            "geometry": geometry_type,
            "properties": schema_properties
        }

        if geometry_type == "Centroid":
            my_schema["geometry"] = "Point"

        my_driver = "ESRI Shapefile"
        my_crs = from_epsg(27700)

        with open(csv_fname, "r") as inpf:
            with fiona.open(shp_fname, "w", driver=my_driver, crs=my_crs, schema=my_schema) as outpf:
                my_reader = csv.reader(inpf)
                c = 1
                for r in my_reader:
                    if c > 1:
                        id = int(r[0])
                        x = int(r[1])
                        y = int(r[2])
                        w = int(r[3])
                        h = int(r[4])
                        area = float(r[5])
                        perim = float(r[6])
                        convex = r[7]
                        rotation = float(r[8])
                        aratio = float(r[9])
                        extent = float(r[10])

                        try:
                            solidity = float(r[11])
                        except ValueError:
                            solidity = None

                        compact = float(r[12])
                        round = float(r[13])

                        ul_coord = ds_affine * (x, y)
                        ll_coord = ds_affine * ((x), (y+h))
                        ur_coord = ds_affine * ((x+w), y)

                        if geometry_type == "Point":
                            geometry_type = "Centroid"
                            #feature_geom = Point(ur_coord)

                        if geometry_type == "Polygon":
                            feature_geom = box(ll_coord[0], ll_coord[1], ur_coord[0], ur_coord[1])

                        if geometry_type == "Centroid":
                            bbox = box(ll_coord[0], ll_coord[1], ur_coord[0], ur_coord[1])
                            feature_geom = bbox.centroid

                        outpf.write({
                            "geometry": mapping(feature_geom),
                            "properties": {
                            "id": id,
                            "x": x,
                            "y": y,
                            "w": w,
                            "h": h,
                            "area": area,
                            "perim": perim,
                            "convex": convex,
                            "rotation": rotation,
                            "aratio": aratio,
                            "extent": extent,
                            "solidity": solidity,
                            "compact": compact,
                            "round": round,
                            }
                        })

                    c += 1