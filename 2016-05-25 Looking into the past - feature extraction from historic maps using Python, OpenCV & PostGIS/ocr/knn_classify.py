#!/usr/bin/python

__author__ = 'james'

import csv
import cv2
import numpy as np
import opencv_utils as ocu
import os
import shutil
import subprocess
import glob
import pprint


def tidy(basepath):
    for f in glob.glob(os.path.join(basepath, "*")):
        try:
            os.remove(f)
        except OSError:
            shutil.rmtree(f)


def do_classification():
    path_to_training_samples_data = "/home/james/Desktop/csv_training_samples.data"
    path_to_training_responses_data = "/home/james/Desktop/csv_training_responses.data"
    path_to_candidates_data = "/home/james/geocrud/adrc/candidates.data"
    path_to_candidates_images = "/home/james/geocrud/adrc"

    training_samples = np.loadtxt(path_to_training_samples_data, np.float32)
    training_responses = np.loadtxt(path_to_training_responses_data, np.float32)
    candidates = np.loadtxt(path_to_candidates_data, np.float32)

    # create a new KNN model and train it based on our samples/responses

    #knn_model = cv2.KNearest()
    #knn_model.train(training_samples, training_responses)

    # In OpenCV 3 API has changed considerably...
    knn_model = cv2.ml.KNearest_create()
    knn_model.train(training_samples, cv2.ml.ROW_SAMPLE, training_responses)

    # TODO - experiment with difft values of k, number of nearest neighbours

    # Again, OpenCV(3) API has changed so now .findNearest
    retval, results, neighbours, distances = knn_model.findNearest(candidates, 5)

    rl = ocu.ResponseLookup()

    id = 0

    classifications_by_id = []

    for result in np.nditer(results):
        result_label = rl.get_response_from_code(int(result))
        classifications_by_id.append([id, result_label])

        # rename the images of the candidate features by prefixing their
        # filename with what they were classified as, that way we can
        # easily pore through the directory contents to see how well the
        # classification got on

        # also move them into a sub-directory with the classname to make it
        # even easier to pore through the results

        base_output_path = "/home/james/Desktop/classified"

        fname = "".join([str(id), "_sample.png"])

        if os.path.exists(os.path.join(path_to_candidates_images, fname)):
            if not os.path.exists(os.path.join(base_output_path, result_label)):
                cmd = "mkdir " + os.path.join(base_output_path, result_label)
                subprocess.call(cmd, shell=True)

            new_fname = "".join([result_label, "_", str(id), ".png"])
            old = os.path.join(path_to_candidates_images, fname)
            new = os.path.join("/home/james/Desktop/classified", result_label, new_fname)
            shutil.copy(old, new)
        id += 1


    with open("/home/james/Desktop/classifications_by_id.csv", "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        my_writer.writerow(["id", "classified_as"])
        my_writer.writerows(classifications_by_id)


def main():
    print("purging old classifications...")
    tidy("/home/james/Desktop/classified")

    print("doing new classification...")
    do_classification()

    #TODO - seems to be getting terrible results, need CM to see how terrible!

    # create a confusion matrix
    # build input for confusion.py
    # based on /home/james/Desktop/classification.log


if __name__ == "__main__":
    main()




