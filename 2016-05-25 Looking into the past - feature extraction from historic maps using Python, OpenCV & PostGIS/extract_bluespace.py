#!/usr/bin/env python

"""
    given a thresholded image where foreground pixels correspond to water
    pulled from NLS 25K mapping identify stippled regions corresponding to
    bodies of inland water. Outputs the marked-up image with the locations
    of the water bodies plotted, a CSV file providing various properties of
    the extracted contours and a shapefile (based on the contours) which
    provides vectors of the extracted features. Currently the shapefiles just
    provides point or MBR footprints with more work required to write the
    full water body geometry

    although process seems to reliably identify closed water bodies, nature of
    the source maps means that in a significant number of cases water bodies
    in the thresholded image are not closed. The areal parts of rivers are also
    broken by crossing features such as roads. Method would need to be refined
    to take these into account
"""

import cv2
import csv
import numpy as np
import math
import os
import glob

import fiona
import rasterio

from collections import OrderedDict
from fiona.crs import from_epsg
from shapely.geometry import mapping, Point, box


def get_compactness(perimeter, area):
    # seems to yield values of 1 for a cirle
    # decreasing to 0 as the shape becomes less and less compact
    # which is the opposite of every other definition. WTF

    #compactness = math.sqrt(area) / (0.282 * perimeter)


    compactness = math.pow(perimeter, 2) / area

    return compactness


def get_compactness_from_roundness(cnt):
    # http://www.imagemet.com/WebHelp6/Default.htm#PnPParameters/Measure_Shape_Parameters.htm#Roundnes
    # compactness is a measure of how compact a feature is
    # except for a circle which will have a compactness of 1, all shapes will have a compactness factor
    # less than 1
    compactness = math.sqrt(get_roundness(cnt))

    return compactness


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


    try:
        roundness = (4 * (enclosed_area / math.pi)) / math.pow(max_diameter, 2)
    except ZeroDivisionError:
        roundness = None

    return roundness


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


def dump_hierarchy_to_csv(hierarchy):
    with open("/home/james/geocrud/hierarchy.csv", "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        for cnt in hierarchy[0]:
            my_writer.writerow(cnt)


def dump_contours_to_shapefile(contour_features, input_image, geom_type="Polygon"):
    """

    writes out a point/MBR proxy of passed contour features to a shapefile

    :param contour_features:
    :param input_image:
    :param geom_type:
    :return:
    """

    #TODO need to write out full geometry rather than just an MBR/point proxy
    #TODO need to be able to cope with contours that don`t form valid geometries


    if geom_type in ("Point", "Polygon"):
        base_outfname = os.path.splitext(os.path.split(input_image)[-1])[0]

        ds = rasterio.open(input_image)
        ds_affine = ds.affine

        schema_properties = OrderedDict([
            ("id", "int"),
            ("source", "str:25")
        ])

        my_schema = {
            "geometry": geom_type,
            "properties": schema_properties
        }

        my_driver = "ESRI Shapefile"
        my_crs = from_epsg(27700)

        shp_fname = os.path.join("/home/james/geocrud", "".join([base_outfname, "_", geom_type.lower(), "_features.shp"]))

        print("writing contours to shapefile...")
        print(shp_fname)

        with fiona.open(shp_fname, "w", driver=my_driver, crs=my_crs, schema=my_schema) as outpf:
            for cnt in contour_features:
                contour_id = cnt[0]
                contour_x = cnt[1]
                contour_y = cnt[2]
                contour_w = cnt[3]
                contour_h = cnt[4]

                ll_coord = ds_affine * (contour_x, (contour_y + contour_h))

                if geom_type == "Point":
                    feature_geom = Point(ll_coord)

                if geom_type == "Polygon":
                    ur_coord = ds_affine * ((contour_x+contour_w), (contour_y))
                    feature_geom = box(ll_coord[0], ll_coord[1], ur_coord[0], ur_coord[1])

                outpf.write({
                    "geometry": mapping(feature_geom),
                    "properties": {
                        "id": contour_id,
                        "source": base_outfname
                    }
                })


def extract(input_image, method="sub_contour_counting", write_shapefile=True):
    """
    :param input_image:
    :return:
    """

    print("".join(["processing ", input_image]))

    base_outfname = os.path.splitext(os.path.split(input_image)[-1])[0]

    im = cv2.imread(input_image)

    processed_image = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    processed_image = cv2.medianBlur(processed_image, 3)

    im2 = processed_image.copy()
    im3 = cv2.cvtColor(im2, cv2.COLOR_GRAY2RGB)
    im4 = im3.copy()

    if method == "sub_contour_counting":
        # identify water bodies as contours that contain 5 or more child contours
        # i.e. indv stipple marks
        contour_mode = cv2.RETR_TREE
        num_children_per_parent = None

        image, contours, hierarchy = cv2.findContours(processed_image, contour_mode, cv2.CHAIN_APPROX_SIMPLE)

        # find out the number of children that each parent has
        # the idea being that contours containing lots of stipples will have large
        # numbers of children and thus can be differentiated from other contours
        if contour_mode == cv2.RETR_TREE:
            num_children_per_parent = count_children(hierarchy)

        outer_ids = []

        print("finding stippled regions by sub contour counting...")

        if num_children_per_parent is not None:
            id = 0
            for cnt in contours:
                if id in num_children_per_parent:
                    number_of_children = num_children_per_parent[id]
                    if number_of_children >= 5:
                        outer_id = hierarchy[0][id][3]
                        outer_ids.append(outer_id)
                id += 1

        final_contours = []
        final_contour_properties = [["id", "compactness", "roundness"]]
        final_contour_features = []
        id = 0
        for cnt in contours:
            if id in outer_ids:
                final_contours.append(cnt)
                this_contour_properties = get_contour_properties(cnt)
                compactness = this_contour_properties["compactness"]
                roundness = this_contour_properties["roundness"]
                x = this_contour_properties["x"]
                y = this_contour_properties["y"]
                w = this_contour_properties["w"]
                h = this_contour_properties["h"]
                cv2.putText(im4, str(id), (x, y+h), cv2.FONT_HERSHEY_PLAIN, 2, [0,0,255])
                final_contour_properties.append([id, compactness, roundness])
                final_contour_features.append([id, x, y, w, h])
            id += 1

        if write_shapefile:
            dump_contours_to_shapefile(final_contour_features, input_image)

        print("writing marked-up image/contours properties file...")

        cv2.drawContours(im4, final_contours, -1, (255, 64, 0), 2)
        out_fname = os.path.join("/home/james/geocrud", "".join([base_outfname, "_final_contours.png"]))
        cv2.imwrite(out_fname, im4)

        out_fname = os.path.join("/home/james/geocrud", "".join([base_outfname, "_contour_properties.csv"]))
        with open(out_fname, "w") as outpf:
            my_writer = csv.writer(outpf, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            my_writer.writerows(final_contour_properties)

    if method == "stipple_grouping":
        # rather like we do with the hatch lines form water regions by forming
        # groups from individual stipple marks. Will be more compute intensive
        # but will not depend on the outer ring of the water body being a closed
        # loop and so will be more fault tolerant.

        # for now just dump them to a shapefile

        #TODO work out how (and where) we group stipples into regions

        print("dumping wee (stipple mark) contours to a shapefile...")

        shp_fname = os.path.join("/home/james/geocrud", "".join([base_outfname, "_stipple_points.shp"]))

        ds = rasterio.open(input_image)
        ds_affine = ds.affine

        schema_properties = OrderedDict([
            ("id", "int"),
            ("source", "str:25")
        ])

        my_schema = {
            "geometry": "Point",
            "properties": schema_properties
        }

        my_driver = "ESRI Shapefile"
        my_crs = from_epsg(27700)

        contour_mode = cv2.RETR_LIST
        image, contours, hierarchy = cv2.findContours(processed_image, contour_mode, cv2.CHAIN_APPROX_SIMPLE)

        #contours_retain = []

        id = 0
        with fiona.open(shp_fname, "w", driver=my_driver, crs=my_crs, schema=my_schema) as outpf:
            for cnt in contours:
                contour_properties = get_contour_properties(cnt)

                x = contour_properties["x"]
                y = contour_properties["y"]
                w = contour_properties["w"]
                h = contour_properties["h"]

                if contour_properties["area"] <= 5.0:
                    #contours_retain.append(cnt)
                    ll_coord = ds_affine * (x, (y + h))
                    ur_coord = ds_affine * ((x+w), (y))

                    min_x = ll_coord[0]
                    min_y = ll_coord[1]
                    max_x = ur_coord[0]
                    max_y = ur_coord[1]

                    avg_x = (min_x + max_x) / 2.0
                    avg_y = (min_y + max_y) / 2.0

                    feature_geom = Point(avg_x, avg_y)

                    outpf.write({
                        "geometry": mapping(feature_geom),
                        "properties": {
                            "id": id,
                            "source": base_outfname
                        }
                    })
                id += 1

        #input_image_height = im.shape[0]
        #input_image_width = im.shape[1]
        #blank_im = np.zeros((input_image_height, input_image_width,3), np.uint8)
        #cv2.drawContours(blank_im, contours_retain, -1, (255, 64, 0), 2)
        #out_fname = os.path.join("/home/james/geocrud/water", "".join([base_outfname, "_retained_contours.png"]))
        #cv2.imwrite(out_fname, blank_im)


def main():

    #for fn in glob.glob("/home/james/Desktop/thresholded_h/*.tif"):
    #    #extract(fn, method="stipple_grouping")
    #    extract(fn, method="sub_contour_counting")

    fn = "/home/james/serviceDelivery/ADRC/thresholded_h/h_91578182.tif"
    extract(fn, method="stipple_grouping")

    #extract("/home/james/Desktop/thresholded_h/h_91578212.tif", method="stipple_grouping")

if __name__ == "__main__":
    main()
