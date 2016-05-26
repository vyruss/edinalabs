#!/usr/bin/python

"""
    to experiment with ml generate synthetic features, the geometry of which
    we have complete control over
"""

import csv
import cv2
import glob
import itertools
import numpy as np
import os
import shutil
import subprocess


def tidy(basepath):
    for f in glob.glob(os.path.join(basepath, "*")):
        try:
            os.remove(f)
        except OSError:
            shutil.rmtree(f)


def create_image(id, elements_to_draw, output_folder):
    assert len(elements_to_draw) > 0
    assert os.path.exists(output_folder)

    canvas = np.zeros((42, 24, 3), dtype = "uint8")
    fg = (255, 255, 255)

    for e in elements_to_draw:
        cv2.rectangle(canvas, (e[0], e[1]), (e[2], e[3]), fg, -1)

    cv2.imwrite(os.path.join(output_folder, ".".join([str(id), "png"])), canvas)


class SyntheticData:
    """
        models a 24x42 image made up
        from 12 'cells' that we can
        turn on to produce different
        patterns

        [A][B]
        [C][D]
        [E][F]
        [G][H]
        [I][J]
        [K][L]

        self.shapes are cv vertices
    """

    def __init__(self):
        self.shapes = {
            "A":[0,0,11,6],
            "B":[12,0,24,6],
            "C":[0,7,11,13],
            "D":[12,7,24,13],
            "E":[0,14,11,20],
            "F":[12,14,24,20],
            "G":[0,21,11,27],
            "H":[12,21,24,27],
            "I":[0,28,11,34],
            "J":[12,28,24,34],
            "K":[0,35,11,41],
            "L":[12,35,24,41]
        }

    def get_elements(self, elements_wanted):
        assert len(elements_wanted) > 0

        elements = []

        for label in elements_wanted:
            if label in self.shapes:
                elements.append(self.shapes[label])

        return elements


def generate_synthetic_samples(element_set):
    assert len(element_set) > 0

    output_folder = "/home/james/geocrud/synthetic/samples"
    tidy(output_folder)

    sd = SyntheticData()

    id = 1

    for element in element_set:
        elements_to_draw = sd.get_elements(element)
        create_image(id, elements_to_draw, output_folder)
        id += 1

    images_to_cv_data(output_folder, "candidates.data")


def generate_synthetic_training(training_patterns):

    assert len(training_patterns) > 0

    output_folder = "/home/james/geocrud/synthetic/training"
    tidy(output_folder)

    sd = SyntheticData()

    id = 1

    labels = {}

    for training_pattern in training_patterns:
        label = training_pattern[0]
        pattern = training_pattern[1]
        elements_to_draw = sd.get_elements(pattern)
        create_image(id, elements_to_draw, output_folder)
        labels[".".join([str(id), "png"])] = label
        id += 1

    #elements_to_draw = sd.get_elements("ACEGIK")
    #create_image(1, elements_to_draw, output_folder)

    #elements_to_draw = sd.get_elements("BDFHJL")
    #create_image(2, elements_to_draw, output_folder)

    #elements_to_draw = sd.get_elements("ABCDEF")
    #create_image(3, elements_to_draw, output_folder)

    #elements_to_draw = sd.get_elements("GHIJKL")
    #create_image(4, elements_to_draw, output_folder)

    #labels = {
    #    "1.png": 1,
    #    "2.png": 2,
    #    "3.png": 3,
    #    "4.png": 4
    #}

    samples = np.empty((0, 1008))
    responses = []

    for fn in glob.glob(os.path.join(output_folder, "*.png")):
        if os.path.split(fn)[-1] in labels:
            im = cv2.imread(fn)
            im_b = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
            reshaped = im_b.reshape((1, 1008))
            samples = np.append(samples, reshaped, 0)
            responses.append(labels[os.path.split(fn)[-1]])

    np.savetxt(os.path.join(output_folder, "csv_training_samples.data"), samples)

    responses = np.array(responses, np.float32)
    responses = responses.reshape((responses.size, 1))
    np.savetxt(os.path.join(output_folder, "csv_training_responses.data"), responses)


def images_to_cv_data(path_to_images, ds_name):
    assert os.path.exists(path_to_images)

    samples = np.empty((0, 1008))

    for fn in glob.glob(os.path.join(path_to_images, "*.png")):
        im = cv2.imread(fn)
        im_b = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        reshaped = im_b.reshape((1, 1008))
        samples = np.append(samples, reshaped, 0)

    np.savetxt(os.path.join(path_to_images, ds_name), samples)


def do_classification():
    tidy("/home/james/geocrud/synthetic/classified")
    p_training_samples = "/home/james/geocrud/synthetic/training/csv_training_samples.data"
    p_training_responses = "/home/james/geocrud/synthetic/training/csv_training_responses.data"
    p_candidates = "/home/james/geocrud/synthetic/samples/candidates.data"
    p_classifications = "/home/james/geocrud/synthetic/classified"

    training_samples = np.loadtxt(p_training_samples, np.float32)
    training_responses = np.loadtxt(p_training_responses, np.float32)
    candidates = np.loadtxt(p_candidates, np.float32)

    k = 1
    knn_model = cv2.ml.KNearest_create()
    knn_model.train(training_samples, cv2.ml.ROW_SAMPLE, training_responses)
    retval, results, neighbours, distances = knn_model.findNearest(candidates, k)

    id = 1

    while id-1 < len(results):
        result_label = int(results[id-1])
        result_neighbours = neighbours[id-1]
        result_distances = distances[id-1]

        fn = "".join([str(id), ".png"])

        if not os.path.exists(os.path.join(p_classifications, str(result_label))):
            cmd = "mkdir " + os.path.join(p_classifications, str(result_label))
            subprocess.call(cmd, shell=True)

        new_fname = "".join([str(result_label), "_", str(id), ".png"])
        old = os.path.join("/home/james/geocrud/synthetic/samples", ".".join([str(id), "png"]))
        new = os.path.join(p_classifications, str(result_label), new_fname)
        shutil.copy(old, new)

        id += 1

    #TODO - explore how KNN is doing the classification

    # given
    # [1, 2, 4, 1, 21848400, 21848400, 43696800]
    # result_label = 1
    # result_neighbours = 2,4,1
    # result_distances = 21848400, 21848400, 43696800
    # i.e. result 1 has the highest distance?

    with open("/home/james/Desktop/results.csv", "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

        header = ["id"] + ["classified_as"] + \
            ["_".join(["neighbour", str(x+1)]) for x in range(0,k)] + \
            ["_".join(["distance", str(x+1)]) for x in range(0,k)]

        my_writer.writerow(header)

        id = 1
        while id-1 < len(results):
            result_label = int(results[id-1])
            result_neighbours = [int(x) for x in neighbours[id-1]]
            result_distances = [int(x) for x in distances[id-1]]
            out_rec = [id] + [result_label] + result_neighbours + result_distances
            my_writer.writerow(out_rec)
            id += 1


def main():
    # generate(make-up!) training data

    training_patterns = [
        [1, "ACEGIKL"],
        [1, "ACEGIKJ"],
        [1, "ACEGIKH"],
        [1, "ACEGIKF"],
        [2, "ABKL"],
        [2, "CDIJ"],
        [2, "ABEF"],
        [3, "AL"],
        [3, "BK"],
        [3, "AK"],
        [3, "BL"],
        [4, "ACDEHIJL"],
        [4, "ACDEGIJK"],
        [4, "BCDFGIJK"],
        [4, "BCDFHIJL"],
        [5, "ABCDEF"],
        [5, "GHIJKL"],
        [5, "CDEFGH"],
        [5, "EFGHIJ"],
        [6, "ACE"],
        [6, "HJL"],
        [6, "BDF"],
        [6, "GIK"]
    ]

    generate_synthetic_training(training_patterns)

    # generate samples to classify

    # so we can generate every permutation
    element_set = []
    #for i in itertools.combinations("ABCDEFGHIJKL", 6):
    #    elements = "".join(i)
    #    element_set.append(elements)

    # or not
    element_set = [
        "ACEGIKL",
        "AL",
        "HJL",
        "A"
    ]

    generate_synthetic_samples(element_set)

    # do classification based on the training data
    do_classification()


if __name__ == "__main__":
    main()