# -*- coding: utf-8 -*-
'''
$ Date:
$ Author:
$ Purpose:
June 2014
Georgia Stavropoulou
This python script is designed to perform feature extraction on maps
with ultimate purpose the development of a library of digits. The
algorithm detects and extracts contours from the map based on some
criteria of height-width analogy and contour area. Preprocessing
steps may need to be altered depending on the quality of the map.
File Name: library_development.py
'''

import cv2
import numpy as np
import matplotlib.pyplot as plt
import pickle
import sys
import os
import csv
import math

key_codes = {1048624:"0",
             1048625:"1",
             1048626:"2",
             1048627:"3",
             1048628:"4",
             1048629:"5",
             1048630:"6",
             1048631:"7",
             1048632:"8",
             1048633:"9",
             1048673:"a",
             1048674:"b",
             1048675:"c",
             1048676:"d",
             1048677:"e",
             1048678:"f",
             1048679:"g",
             1048680:"h",
             1048681:"i",
             1048682:"j",
             1048683:"k",
             1048684:"l",
             1048685:"m",
             1048686:"n",
             1048687:"o",
             1048688:"p",
             1048689:"q",
             1048690:"r",
             1048691:"s",
             1048692:"t",
             1048693:"u",
             1048694:"v",
             1048695:"w",
             1048696:"x",
             1048697:"y",
             1048698:"z"
}


def get_key_from_cv_keycode(keycode):
    key_pressed = None
    if keycode in key_codes:
        key_pressed = key_codes[keycode]

    return key_pressed


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


def get_rotated_rec(cnt):
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    angle_of_rotation = rect[2]
    box = np.int0(box)

    return box, angle_of_rotation


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


def build_training_library(input_image, run_interactively=True):
    # TODO the script should take these as params, rather than these defaults
    #max_contour_area = 1000
    #max_contour_envelope_area = 1500
    #aspect_ratio = 2.0

    # thresholds to decide if we retain the contour
    thresholds = {
        "area": 5000,
        "h_lower": 20,
        "h_upper": 100,
        "aspect_ratio": 1.5,
        "roundness": 0.1,
        "solidity": 0.8
    }

    base_output_path = "/home/james/geocrud/adrc"

    # Load map – change path and filename
    im = cv2.imread(input_image)
    im2 = im.copy() #keep a copy
    # TODO scale the displayed image to a fixed size window, otherwise it fills the screen

    resized_src_im = cv2.resize(im, (400, 400), interpolation = cv2.INTER_AREA)

    if run_interactively:
        cv2.imshow("1 Input Image", resized_src_im)
        cv2.waitKey(0)
    else:
        dumped_images = [["training_sample","response"]]
        id = 1

    print("pre-processing...")

    ############################ PRE-PROCESSING ##############################
    # Convert to greyscale
    processed_image = cv2.cvtColor(im,cv2.COLOR_RGB2GRAY)
    #cv2.imshow("2 Greyscaled", processed_image)
    #cv2.waitKey(0)

    # Apply Gaussian Blur - Increase in case of dotted background
    processed_image= cv2.GaussianBlur(processed_image,(5,5),0)
    #cv2.imshow("3 GBlur Applied", processed_image)
    #cv2.waitKey(0)

    # Apply Otsu's threshold and invert the colors of the image - digits white on black background
    (thresh, processed_image) = cv2.threshold(processed_image, 0, 255,
    cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    #cv2.imshow("4 Thresholded", processed_image)
    #cv2.waitKey(0)

    # Define Kernel Size and apply erosion filter
    element = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    processed_image=cv2.erode(processed_image,element)
    blank=processed_image.copy()
    #cv2.imshow("5 Erosion Filter applied", processed_image)
    #cv2.waitKey(0)

    ############################ FEATURE DETECTION ##############################
    # Contour tracing - Detect all contours with no hierarchy
    _, contours, hierarchy = cv2.findContours(processed_image,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    # Apply the first 4 rules for digit graphic separation
    contours_retain=[]
    contours_reject=[]
    # for cnt in contours:
    #     [x,y,w,h] = cv2.boundingRect(cnt)
    #     if cv2.contourArea(cnt)< max_contour_area and h/w < aspect_ratio and w/h < aspect_ratio and h*w < max_contour_envelope_area:
    #         continue
    #     else:
    #         contours_reject.append(cnt)

    print("going through contours...")

    for cnt in contours:
        this_contour_properties = get_contour_properties(cnt)
        if retain_contour(this_contour_properties, thresholds):
            contours_retain.append(cnt)
        else:
            contours_reject.append(cnt)

    print("".join(["number of retained contours: ", len(contours_retain)]))
    print("".join(["number of rejected contours: ", len(contours_reject)]))
    print("erasing rejected contours...")

    # Erase contours from the image
    cv2.drawContours(blank,contours_reject,-1,(0,0,0),-1)

    #cv2.imshow("Contours Erased", blank)
    #cv2.waitKey(0)

    blank2=blank.copy()
    _, contours,hierarchy = cv2.findContours(blank,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

    #contours_retain=[]
    #contours_reject=[]
    #for cnt in contours:
    #    if cv2.contourArea(cnt)>50:
    #        contours_retain.append(cnt)
    #    else:
    #        contours_reject.append(cnt)

    # Erase small contours from the image
    cv2.drawContours(blank2,contours_reject,-1,(0 ,0,0),-1)

    print("erased rejected contours...")

    #cv2.imshow("Small Contours Erased", blank2)
    #cv2.waitKey(0)

    ############# Dealing with Touching Digits ##########################

    # 070416 - from running against 82877433.tif large important letters
    # at the start of words are being incorrectly split by this part of
    # the process due to the w>2*num_cols+1 and w>1.2*h criteria

    deal_w_touching_digits = False

    if not deal_w_touching_digits:
        print("Hey, one more thing, we`ve turned off dealing with touching digits!")

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

    for m in range(len(arr)):
        cv2.rectangle(im2,(arr[m,0],arr[m,1]),(arr[m,0] + arr[m,2],arr[m,1]+
    arr[m,3]),(255,0,255),2)

    #cv2.imshow("Detected Features", im2)
    #cv2.waitKey(0)

    #plt.imshow(im2)
    #plt.title('Segmented images')
    #plt.show()

    ######################## Library Development ###############################
    # TODO reinstate acceptance of numbers as well as characters
    keys = [i for i in range(1048673, 1048699)]
    captured_keys = []
    samples=[]
    responses=[]
    num=0

    if run_interactively:
        print("Press A to Z to assign to the image this response")
        print("Press any other keyboard button to reject the image")
        print("Press escape to stop the process")

    # Iterate through all the segmented images
    for i in range(len(digit_im_list)):
        sample = digit_im_list[i]
        reshaped_sample = sample.reshape((1,1008))

        if run_interactively:
            cv2.imshow(str(i)+' of:' + str(len(digit_im_list)) + ', slc:' + str(num), sample )
            key = cv2.waitKey(0)
            # TODO hide/close the displayed feature
            if key in keys:
                key_pressed = get_key_from_cv_keycode(key)
                # sub-images are 24x42 = 1008
                # so data is reshaped to 1x1008
                print("".join([key_pressed, " recorded as response: ", key]))
                samples.append(reshaped_sample)
                responses.append(key)
                captured_keys.append(key)
                num += 1
            else:
                if key == 1048603:
                    break
        else:
            out_fname = "/home/james/geocrud/adrc/" + str(id) + "_sample.png"
            cv2.imwrite(out_fname, sample)
            dumped_images.append([out_fname, "!"])
            id += 1

    if run_interactively:
        my_samples = np.empty((0, 1008))
        for sample in samples:
            try:
                my_samples = np.append(my_samples, sample, 0)
            except Exception as ex:
                print(ex)

        # save the array of thresholded samples - the training data to a text file
        np.savetxt(os.path.join(base_output_path, "training_samples.data"), my_samples)

        # save the array of responses (what each sample represents) to text file
        responses = np.array(responses, np.float32)
        responses = responses.reshape((responses.size, 1))
        np.savetxt(os.path.join(base_output_path, "training_responses.data"), responses)

        # unclear what is being pickled, so replaced by writing the arrays
        # to a text file. Presumably the reason for the pickling is that
        # there are performance issues with writing/reading text files

        #train_set=[selected_im,responses]
        #save the library
        #pkl_file = open('/home/james/Desktop/Library_file.pkl', 'w')
        #pkl_file = open('/home/james/Desktop/Testset_file.pkl', 'w')
        #pickle.dump(train_set, pkl_file)
        #pkl_file.close()

        for key in sorted(key_codes):
            if key > 1048633:
                key_frequency = captured_keys.count(key)
                if key_frequency == 0:
                    print("".join(["Warning! - training data for", key_codes[key], "was not captured!"]))

        # check the distribution of digits in the library
        #count=[0]*10
        #for i in xrange(len(responses)):
        #    count[responses[i]]=count[responses[i]]+1
        #print count

    if not run_interactively:
        with open("/home/james/geocrud/adrc/training_samples.csv", "w") as outpf:
            samples_writer = csv.writer(outpf, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            samples_writer.writerows(dumped_images)

        print("ALL standardised training images dumped")
        print("create CSV describing these and then run")
        print("prepare_training_samples_from_csv.py")


def main():
    # input_image = '/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif'
    # input_image = "/home/james/Desktop/adrc_aoi_samples/82877484_aoi.tif"

    if len(sys.argv) == 3:
        input_image = sys.argv[1]
        run_iactive = sys.argv[2]

        print(input_image)
        print(run_iactive)

        if os.path.exists(input_image):
            if run_iactive == 'True':
                build_training_library(input_image)
            else:
                build_training_library(input_image, run_interactively=False)
        else:
            print("Aborted - image not found")
    else:
        print("Useage library_development.py <input_image> <run_interactive>")

if __name__ == "__main__":
    main()



