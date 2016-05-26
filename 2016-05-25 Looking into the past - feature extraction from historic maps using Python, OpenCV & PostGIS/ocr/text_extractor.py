# -*- coding: utf-8 -*-

"""text_extractor pull text characters from an image

Usage:
  text_extractor.py

Options:
  -h --help Show this screen

"""

from __future__ import division

import csv
import sys
import os
import time
import uuid

import cv2
import numpy as np
import glob

import math

import fiona
import rasterio

from collections import OrderedDict
from fiona.crs import from_epsg
from shapely.geometry import mapping, Point, box


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

    roundness = (4 * (enclosed_area / math.pi)) / math.pow(max_diameter, 2)

    return roundness


def get_contour_properties(cnt, as_dict=True):
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

    if as_dict:
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
    else:
        contour_properties = [
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

    return contour_properties


def retain_contour(contour_properties, thresholds):
    retain = False

    this_area = contour_properties["area"]
    this_h = contour_properties["h"]
    this_aspect_ratio = contour_properties["aspect_ratio"]
    this_roundness = contour_properties["roundness"]
    this_solidity = contour_properties["solidity"]

    threshold_area = thresholds["area"]
    threshold_h_lower = thresholds["h_lower"]
    threshold_h_upper = thresholds["h_upper"]
    threshold_aspect_ratio = thresholds["aspect_ratio"]
    threshold_roundness = thresholds["roundness"]
    threshold_solidity = thresholds["solidity"]

    area_threshold_met = False
    h_threshold_met = False
    aspect_ratio_threshold_met = False
    roundness_threshold_met = False
    solidity_threshold_met = False

    if this_area < threshold_area:
        area_threshold_met = True

    if (this_h > threshold_h_lower) and (this_h < threshold_h_upper):
        h_threshold_met = True

    if this_aspect_ratio < threshold_aspect_ratio:
        aspect_ratio_threshold_met = True

    if this_roundness > threshold_roundness:
        roundness_threshold_met = True

    if this_solidity < threshold_solidity:
        solidity_threshold_met = True

    if area_threshold_met and h_threshold_met and aspect_ratio_threshold_met and roundness_threshold_met and solidity_threshold_met:
        retain = True

    return retain


def tidy(path_to_geocrud="/home/james/geocrud/adrc"):
    for f in glob.glob(os.path.join(path_to_geocrud, "*")):
        os.remove(f)


def run_batch_extractions(batch_file):
    if os.path.exists(batch_file):
        with open(batch_file, "r") as inpf:
            jobs = csv.reader(inpf, delimiter=",", quotechar='"')
            for job in jobs:
                input_image = job[0]
                max_contour_area = int(job[1])
                max_contour_envelope_area = int(job[2])
                aspect_ratio = float(job[3])
                gblur = job[4]
                erode = job[5]
                extract_text(input_image, max_contour_area, max_contour_envelope_area, aspect_ratio, gblur, erode)


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

        shp_fname = os.path.join("/home/james/geocrud/adrc", "".join([base_outfname, "_", geom_type.lower(), "_features.shp"]))

        print("writing contours to shapefile...")

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


def extract_text(input_image,
                 max_contour_area=1000,
                 max_contour_envelope_area=1500,
                 aspect_ratio=2.0,
                 gblur="True",
                 erode="True"):
    """

    These are Gina`s default values for the params

    :param input_image:
    :param max_contour_area: controls rejection of contours
    :param max_contour_envelope_area: controls rejection of contours
    :param aspect_ratio: controls rejection of contours
    :param gblur: apply gaussian blur
    :param erode: apply erosion filter
    :return:
    """
    print("Hey remember, we`ve turned off most of the script! :)")

    job_uuid = str(uuid.uuid4())
    base_output_path = "/home/james/geocrud/adrc/"

    print("processing %s" % input_image)
    fname_timestamp = time.strftime("%Y%m%d-%H%M%S")

    # Load map – change path and filename
    # cv2.imread(filename) : loads an image from a file - returns an array/matrix
    im = cv2.imread(input_image)

    # im.copy() : copies one array to another
    im2 = im.copy() #keep a copy
    im3 = im.copy()
    #print "input image..."

    # cv2.imshow(winname, image) : display an image in the specified window
    #cv2.imshow("1 Input Image", im)

    # cv2.waitKey(delay in ms) : wait for a key event
    #cv2.waitKey(0)


    ############################ PRE-PROCESSING ##############################
    # Convert to greyscale
    processed_image = cv2.cvtColor(im,cv2.COLOR_RGB2GRAY)
    #cv2.imshow("2 Greyscaled", processed_image)
    #cv2.waitKey(0)

    # Apply Gaussian Blur - Increase in case of dotted background
    if gblur == "True":
        processed_image= cv2.GaussianBlur(processed_image,(5,5),0)
        #cv2.imshow("3 GBlur Applied", processed_image)
        #cv2.waitKey(0)

    # Apply Otsu's threshold and invert the colors of the image - digits white on black background
    (thresh, processed_image) = cv2.threshold(processed_image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    #cv2.imshow("4 Thresholded", processed_image)
    #cv2.waitKey(0)

    if erode == "True":
        # Define Kernel Size and apply erosion filter
        element = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        processed_image=cv2.erode(processed_image,element)

    blank=processed_image.copy()
    blank2=blank.copy()
    processed_image_b=processed_image.copy()

    #print "erosion filter applied..."
    #cv2.imshow("5 Erosion Filter applied", processed_image)
    #cv2.waitKey(0)

    out_fname = "".join([base_output_path,
                         # job_uuid,
                         # "_",
                         # str(max_contour_area),
                         # "_",
                         # str(max_contour_envelope_area),
                         # "_",
                         # str(aspect_ratio),
                         "img_passed_to_feature_extraction.tif"])

    cv2.imwrite(out_fname, processed_image)

    ############################ FEATURE DETECTION ##############################
    # Contour tracing - Detect all contours with no hierarchy
    image, contours, hierarchy = cv2.findContours(processed_image,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

    #################### JRCC - SHOW ALL Contours #############################
    font = cv2.FONT_HERSHEY_COMPLEX

    # draw mbr of every contour
    id = 0
    num_retained = 0
    num_dropped = 0
    lower_area_threshold = 0
    contour_features = []
    final_contours = []
    contours_retain=[]

    # thresholds to decide if we retain the contour
    thresholds = {
        "area": 5000,
        "h_lower": 20,
        "h_upper": 100,
        "aspect_ratio": 1.5,
        "roundness": 0.1,
        "solidity": 0.8
    }

    base_outfname = os.path.splitext(os.path.split(input_image)[-1])[0]
    #out_fname = os.path.join("/home/james/geocrud/adrc", "".join([base_outfname, "_contour_properties.csv"]))
    #with open(out_fname, "w") as outpf:
    #    my_writer = csv.writer(outpf, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    #    my_writer.writerow(["id", "x", "y", "w", "h", "area", "perimeter", "is_convex", "angle_of_rotation", "aspect_ratio", "extent", "solidity", "compactness", "roundness"])
    for cnt in contours:
        this_contour_properties = get_contour_properties(cnt)

        x = this_contour_properties["x"]
        y = this_contour_properties["y"]
        w = this_contour_properties["w"]
        h = this_contour_properties["h"]
        # hw = h/w
        # wh = w/h
        # area = this_contour_properties["area"]
        # perimeter = this_contour_properties["perimeter"]
        # is_convex = this_contour_properties["is_convex"]
        # angle_of_rotation = this_contour_properties["angle_of_rotation"]
        # aspect_ratio = this_contour_properties["aspect_ratio"]
        # extent = this_contour_properties["extent"]
        # solidity = this_contour_properties["solidity"]
        # compactness = this_contour_properties["compactness"]
        # roundness = this_contour_properties["roundness"]

        if retain_contour(this_contour_properties, thresholds):
            cv2.rectangle(im2, (x, y), (x + w, y+h), (0, 255, 0), 1)
            #cv2.putText(im2, str(id), (x, y+h), cv2.FONT_HERSHEY_PLAIN, 2, [0,0,255])
            contours_retain.append(cnt)
            num_retained += 1
        else:
            num_dropped += 1

        #if area > lower_area_threshold:
            #cv2.rectangle(im2, (x, y), (x + w, y+h), (0, 255, 0), 1)
            #cv2.putText(im2, str(id), (x, y+h), cv2.FONT_HERSHEY_PLAIN, 2, [0,0,255])
            #contour_features.append([id, x, y, w, h])
            #my_writer.writerow([id, w, h, hw, wh, area, perimeter, is_convex, angle_of_rotation, aspect_ratio, extent, solidity, compactness, roundness])
            #final_contours.append(cnt)
            #num_retained += 1
        #else:
            #num_dropped += 1

        id += 1

    #dump_contours_to_shapefile(contour_features, input_image)

    #cv2.drawContours(im2, final_contours, -1, (255, 64, 0), 1)
    #cv2.drawContours(processed_image, final_contours, -1, (255, 64, 0), 1)
    #cv2.imwrite(out_fname, processed_image)

    #print "num contours retained", num_retained
    #print "num contours dropped", num_dropped

    cv2.imwrite("/home/james/geocrud/adrc/82877433_selected_contours.tif", im2)

    ###########################################################################

    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
    ###########################################################################
    # 050416 stop this part of the script running
    ###########################################################################

    cont = False

    if cont:
        contour_properties = [["contour_id", "h", "w", "area", "hw", "wh", "hxw", "x", "y"]]

        # display info about every contour and add a label to the displayed image
        contour_id = 1

        for cnt in contours:
            [x,y,w,h] = cv2.boundingRect(cnt)
            # cv2.contourArea(contour) : compute contour area
            contour_area = cv2.contourArea(cnt)

            hw = h/w
            wh = w/h

            hxw = h * w
            text_x = x
            text_y = y + h + 15

            contour_properties.append([contour_id, h, w, contour_area, hw, wh, hxw, x, y+h])

            #print input_image,contour_id, h, w, hw, wh, contour_area, hxw, x, y+h

            contour_id += 1

        csv_fname = "".join([base_output_path,
                             # job_uuid,
                             # "_",
                             # str(max_contour_area),
                             # "_",
                             # str(max_contour_envelope_area),
                             # "_",
                             # str(aspect_ratio),
                             "contour_properties.csv"])

        with open(csv_fname, "w") as outpf:
            c = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            c.writerows(contour_properties)

        out_fname = "".join([base_output_path,
                             # job_uuid,
                             # "_",
                             # str(max_contour_area),
                             # "_",
                             # str(max_contour_envelope_area),
                             # "_",
                             # str(aspect_ratio),
                             "all_contours.png"])

        # cv2.imwrite() : save image to a specified file
        cv2.imwrite(out_fname, im2)

        #print "All contours..."
        #cv2.imshow("All contours", im2)
        #cv2.waitKey(0)

        #################### End of jrcc ##########################################

        # Apply the first 4 rules for digit graphic separation
        contours_reject=[]
        for cnt in contours:
            [x,y,w,h] = cv2.boundingRect(cnt)
            if cv2.contourArea(cnt) < max_contour_area and h/w < aspect_ratio and w/h < aspect_ratio and h*w < max_contour_envelope_area:
                continue
            else:
                contours_reject.append(cnt)

        # Erase contours from the image
        cv2.drawContours(blank,contours_reject,-1,(0,0,0),-1)

        #print "Contours Erased..."
        #cv2.imshow("Contours Erased", blank)
        #cv2.waitKey(0)

        #blank2=blank.copy()
        image, contours, hierarchy = cv2.findContours(blank,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        contour_id = 1
        contours_retain=[]
        contours_reject=[]
        for cnt in contours:
            if cv2.contourArea(cnt)>50:
                contours_retain.append(cnt)
            else:
                contours_reject.append(cnt)
            contour_id += 1

        # Erase small contours from the image
        cv2.drawContours(blank2,contours_reject,-1,(0,0,0),-1)

        #TODO draw the full contour rather than it`s MBR
        #cv2.drawContours(im2, contours_retain, -1, (0,255,0), 2)
        #cv2.drawContours(im2, contours_retain, -1, (0,255,0), 2)
        #cv2.imwrite(out_fname, im2)



        #print "Small contours erased..."
        #cv2.imshow("Small Contours Erased", blank2)
        #cv2.waitKey(0)

    ############# Dealing with Touching Digits ##########################

    """
    Stavropoulou_Optical Character Recognition on Scanned Maps compressed.pdf p20

    num_cols - choice depends on the size of the touching characters and
    subsequently on the size of the font. After the white pixels have been
    counted for each column the characters are seperated in the column that
    has the minimum number of white pixels
    """

    # 070416 - from running against 82877433.tif large important letters
    # at the start of words are being incorrectly split by this part of
    # the process due to the w>2*num_cols+1 and w>1.2*h criteria

    deal_w_touching_digits = False

    if not deal_w_touching_digits:
        print("Hey, one more thing, we`ve turned off dealing with touching digits!")

    #print '.....Dealing with Touching Digits'
    bounding_list=[]
    digit_im_list=[]
    # Set the dimensions for resizing
    dim = (24, 42)

    # Specify the search number of columns for selecting cut column.
    num_cols=5

    for cnt in contours_retain:
        [x,y,w,h] = cv2.boundingRect(cnt) #finding bounding rectangle

        if deal_w_touching_digits:
            if w>2*num_cols+1:
                if w>1.2*h: #in case of fused characters
                    middle=int(round(w/2))
                    fused_character_im=blank2[y-1:y+h+1,x-1:x+w+1]
                    min_col=0
                    col_wh_pixels=[]
                    for i in range(middle-num_cols,middle+num_cols):
                        # examining all the middle columns
                        col=fused_character_im[:,i]
                        white_pixels=0
                        for j in range(len(col)):
                            if col[j]!=0:
                                white_pixels=white_pixels+1
                        col_wh_pixels.append(white_pixels)
                    min_index=col_wh_pixels.index(min(col_wh_pixels))
                    patch1=blank2[y-1:y+h+1,x-1:x+middle-num_cols+min_index]
                    resized1 = cv2.resize(patch1, dim, interpolation = cv2.INTER_AREA)
                    ret,patch1 = cv2.threshold(resized1,50,255,cv2.THRESH_BINARY)
                    #Repeat thresholding after interpolation
                    patch2=blank2[y-1:y+h+1,x+middle-num_cols+min_index:x+w+1]
                    resized2=cv2.resize(patch2, dim, interpolation = cv2.INTER_AREA)
                    ret,patch2 = cv2.threshold(resized2,50,255,cv2.THRESH_BINARY)
                    #Repeat thresholding after interpolation
                    digit_im_list.append(patch1)
                    digit_im_list.append(patch2)
                    bounding_list.append([x,y,w/2,h])
                    bounding_list.append([x+w/2,y,w/2,h])
                else:
                    patch=blank2[y-1:y+h+1,x-1:x+w+1]
                    resized = cv2.resize(patch, dim, interpolation = cv2.INTER_AREA)
                    ret,patch = cv2.threshold(resized,127,255,cv2.THRESH_BINARY)
                    #Repeat thresholding after interpolation
                    digit_im_list.append(patch)
                    bounding_list.append([x,y,w,h])
        else:
            # if we`re not dealing with touching digits do the default always
            # as later on the script makes use of data structures updated here
            patch=blank2[y-1:y+h+1,x-1:x+w+1]
            resized = cv2.resize(patch, dim, interpolation = cv2.INTER_AREA)
            ret,patch = cv2.threshold(resized,127,255,cv2.THRESH_BINARY)
            #Repeat thresholding after interpolation
            digit_im_list.append(patch)
            bounding_list.append([x,y,w,h])


    arr=np.array(bounding_list)

    # TODO - the aoi`s clip too tightly to the contour so we need to add a buffer


    # 250416 - what was I thinking when I implemented this?
    # for m in xrange(len(arr)):
    #     x1 = arr[m, 0]
    #     y1 = arr[m, 1]
    #     w  = arr[m, 2]
    #     h  = arr[m, 3]
    #     x2 = x1 + w
    #     y2 = y1 + h
    #
    #     # add a 1px buffer around the contour
    #     # errors will happen if the buffer extends beyond the extents of the image
    #     x1 = x1 - 10
    #     y1 = y1 - 10
    #     x2 = x2 + 10
    #     y2 = y2 + 10
    #
    #     aoi_fname = base_output_path + str(m) + ".png"
    #     cv2.imwrite(aoi_fname, processed_image_b[y1:y2, x1:x2])

    processed_image_c = cv2.cvtColor(processed_image_b, cv2.COLOR_GRAY2RGB)

    #id = 0

    #for m in xrange(len(arr)):
        #print m
        #cv2.rectangle(im3,(arr[m,0],arr[m,1]),(arr[m,0] + arr[m,2],arr[m,1]+arr[m,3]),(255,0,255),2)
        #cv2.rectangle(im3,(int(arr[m,0]),int(arr[m,1])),(int(arr[m,0]) + int(arr[m,2]),int(arr[m,1])+int(arr[m,3])),(255,0,255),2)
        #cv2.rectangle(processed_image_c,(int(arr[m,0]),int(arr[m,1])),(int(arr[m,0]) + int(arr[m,2]),int(arr[m,1])+int(arr[m,3])),(255,0,255),1)
        #cv2.putText(processed_image_c, str(id), (int(arr[m,0]),int(arr[m,1])), cv2.FONT_HERSHEY_PLAIN, 2, [0,0,255])
        #id += 1

    #cv2.imshow("Detected Features", im3)
    #cv2.waitKey(0)

    #out_fname = "".join([base_output_path,
    #                     job_uuid,
    #                     "_",
    #                     str(max_contour_area),
    #                     "_",
    #                     str(max_contour_envelope_area),
    #                     "_",
    #                     str(aspect_ratio),
    #                     "_final_contours.png"])

    #cv2.imwrite(out_fname, im3)

    #cv2.putText(processed_image_c, "Hello World", (10, 10), cv2.FONT_HERSHEY_PLAIN, 2, [255,0,0] )


    cv2.drawContours(processed_image_c, contours_retain, -1, (0,255,0), 2)


    out_fname = "".join([base_output_path,
                         # job_uuid,
                         # "_",
                         # str(max_contour_area),
                         # "_",
                         # str(max_contour_envelope_area),
                         # "_",
                         # str(aspect_ratio),
                         "img_passed_to_feature_extraction_w_contours.png"])

    cv2.imwrite(out_fname, processed_image_c)

    # write out the numpy arrays of the extracted features to a text file
    # in a seperate script we will classify these

    id = 0



    features = []
    for m in range(len(arr)):
        try:
            feature = digit_im_list[m]

            # ------------------------ 250416 ---------------------------------
            out_fname = "/home/james/geocrud/adrc/" + str(id) + "_sample.png"
            cv2.imwrite(out_fname, feature)
            # ------------------------ 250416 ---------------------------------

            #out_fname = "/home/james/geocrud/adrc/" + job_uuid + "_candidate_" + str(id) + ".png"
            #out_fname = "/home/james/geocrud/adrc/" + str(id) + ".png"
            #cv2.imwrite(out_fname, feature)
            reshaped_feature = feature.reshape((1, 1008))
            features.append(reshaped_feature)


            id += 1
        except Exception as ex:
            print(ex)


    ###########################################################################
    #TODO - so we can create a shapefile showing marked up locations we need
    #to dump location of candidates

    print("".join(["len(digit_im_list): ", str(len(digit_im_list))]))
    print("".join(["len(bounding_list): ", str(len(bounding_list))]))

    id = 0
    with open("/home/james/geocrud/adrc/candidate_locations.csv", "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        my_writer.writerow(["id", "x", "y", "w", "h"])
        for m in range(len(arr)):
            x, y, w, h = bounding_list[m]
            my_writer.writerow([id, x, y, w, h])
            id += 1

    candidates = np.empty((0, 1008))
    for feature in features:
        try:
            candidates = np.append(candidates, feature, 0)
        except Exception as ex:
            print(ex)

    np.savetxt(os.path.join(base_output_path[:-1], "candidates.data"), candidates)


def main():

    args = sys.argv

    """
    if len(args) == 7:
        input_image = args[1]
        max_contour_area = int(args[2])
        max_contour_envelope_area = int(args[3])
        aspect_ratio = float(args[4])
        gblur = args[5]
        erode = args[6]
        extract_text(input_image, max_contour_area, max_contour_envelope_area, aspect_ratio, gblur, erode)
    """

    if len(sys.argv) == 2:
        input_image = sys.argv[1]
        if os.path.exists(input_image):
            tidy()
            extract_text(input_image, gblur="False")

        #batch_file = sys.argv[1]
        #if os.path.exists(batch_file):
        #    run_batch_extractions(batch_file)
        #else:
        #    print("batch file not found, aborting...")
    #else:
    #    input_image = '/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif'
        #input_image = '/home/james/Desktop/adrc_aoi_samples/87212838_aoi.tif'



if __name__ == "__main__":
    main()
