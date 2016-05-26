"""
    OpenCV(3) demo
"""

import cv2
import contour_utils
import os


def main():
    if os.path.exists("images/simple.png"):

        print("How many squares have a hole?")

        # load image from file
        im = cv2.imread("images/simple.png")
        cv2.imshow("Input Image", im)
        cv2.waitKey(0)

        # convert image from RGB to Grayscale
        gs = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Greyscaled", gs)
        cv2.waitKey(0)

        # blur the image using the median filter
        blurred = cv2.medianBlur(gs, 5)
        cv2.imshow("Blurred", blurred)
        cv2.waitKey(0)

        # threshold the image
        (T, thresh) = cv2.threshold(blurred, 155, 255, cv2.THRESH_BINARY_INV)
        cv2.imshow("Thresholded", thresh)
        cv2.waitKey(0)

        # convert the thresholded image back from Grayscale to RGB
        # so we can use colour to highlight regions of interest
        p_im = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)

        # find contours in the thresholded binary image
        image, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # draw all extracted contours in blue
        cv2.drawContours(p_im, contours, -1, (255, 0, 0), 2)

        # draw the id of every contour in green and output various properties of each contour
        idx = 0
        for cnt in contours:
            this_contour_properties = contour_utils.get_contour_properties(cnt)
            c_width = this_contour_properties["w"]
            c_height = this_contour_properties["h"]
            c_locn_x = this_contour_properties["x"]
            c_locn_y = this_contour_properties["y"]
            c_area = this_contour_properties["area"]
            c_perimeter = this_contour_properties["perimeter"]
            c_roundness = this_contour_properties["roundness"]
            cv2.putText(p_im, str(idx), (c_locn_x, (c_locn_y + c_height + 15)), cv2.FONT_HERSHEY_PLAIN, 1, [0, 255 , 0])
            print("Contour %s has area of %s" % (idx, c_area))
            idx += 1

        # display the image showing all the extracted contours
        cv2.imshow("Find all contours", p_im)
        cv2.waitKey(0)

        # find which contours have children (1 or more sub-contours)
        num_children = contour_utils.count_children(hierarchy)

        filtered_contours = []
        number_of_squares_with_hole = 0

        idx = 0
        for cnt in contours:
            if idx in num_children:
                number_of_squares_with_hole += 1
                filtered_contours.append(cnt)
            idx += 1

        print("%s squares have a hole" % number_of_squares_with_hole)

        cv2.drawContours(p_im, filtered_contours, -1, (0, 0, 255), 2)
        cv2.imshow("Select squares with hole", p_im)
        cv2.waitKey(0)

if __name__ == "__main__":
    main()