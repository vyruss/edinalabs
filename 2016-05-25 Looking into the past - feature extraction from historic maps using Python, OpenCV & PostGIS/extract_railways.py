from __future__ import division

import csv
import os

import cv2

import contour_utils


def extract(min_area=50, max_area=200):
    # 090516 - new plan, try and use the outputs of process_25k for the black
    # SBuilding features, as these seperate out railways as well

    # e.g. /home/james/geocrud/91578185_extracted_SBuilding.png & 91578182_extracted_SBuilding.png

    input_image = "/home/james/geocrud/91578182_extracted_SBuilding.tif"
    im = cv2.imread(input_image)
    p_im = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    p_im_rgb = cv2.cvtColor(p_im, cv2.COLOR_GRAY2RGB)

    contour_mode = cv2.RETR_LIST
    image, contours, hierarchy = cv2.findContours(p_im, contour_mode, cv2.CHAIN_APPROX_SIMPLE)

    contour_properties = [["contour_id", "x", "y", "w", "h", "area", "perimeter", "is_convex", "angle_of_rotation", "aspect_ratio", "extent", "solidity", "compactness", "roundness"]]

    contour_id = 1
    for cnt in contours:

        retain_contour = False

        cp = contour_utils.get_contour_properties(cnt)
        x = cp["x"]
        y = cp["y"]
        w = cp["w"]
        h = cp["h"]
        area = cp["area"]
        perimeter = cp["perimeter"]
        is_convex = cp["is_convex"]
        angle_of_rotation = cp["angle_of_rotation"]
        aspect_ratio = cp["aspect_ratio"]
        extent = cp["extent"]
        solidity = cp["solidity"]
        compactness = cp["compactness"]
        roundness = cp["roundness"]

        if area > min_area:
            if area < max_area:
                retain_contour = True

        if retain_contour:
            contour_properties.append(
                [
                    contour_id,
                    x,
                    y,
                    w,
                    h,
                    area,
                    perimeter,
                    is_convex,
                    angle_of_rotation,
                    aspect_ratio,
                    extent,
                    solidity,
                    compactness,
                    roundness
                ]
            )

        contour_id += 1

    csv_fname = os.path.join(
        "/home/james/geocrud/railways",
        "".join([os.path.splitext(os.path.split(input_image)[1])[0], "_contour_properties.csv"])
    )

    with open(csv_fname, "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        my_writer.writerows(contour_properties)

    shp_fname = os.path.join(
        "/home/james/geocrud/railways",
        "".join([os.path.splitext(os.path.split(input_image)[1])[0], "_contour_properties.shp"])
    )

    shp_fname_pt = os.path.join(
        "/home/james/geocrud/railways",
        "".join([os.path.splitext(os.path.split(input_image)[1])[0], "_contour_properties_points.shp"])
    )

    src_image="/home/james/serviceDelivery/ADRC/NLS_samples/25K_210316/wetransfer-aa0da6/91578182.tif"
    contour_utils.contour_properties_csv_to_shapefile(csv_fname, src_image, shp_fname, geometry_type="Polygon")

    contour_utils.contour_properties_csv_to_shapefile(csv_fname, src_image, shp_fname_pt, geometry_type="Point")


def main():
    extract()


if __name__ == "__main__":
    main()

