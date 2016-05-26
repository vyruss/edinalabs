#!/usr/bin/python

__author__ = 'james'

import csv
import cv2
import numpy as np
import os

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

def invert_dictionary(dict):
    dict_inv = {}
    for k in dict:
        dict_inv[key_codes[k]] = k

    return dict_inv


def generate_response_lookup(path_to_samples="/home/james/Desktop/training_sample_sets"):
    """
       generate a dict which maps a unique int to every response
    :return:
    """

    response_lookup = {}

    id = 1

    for i in sorted(os.listdir(path_to_samples)):
        response_lookup[i] = id
        id += 1

    with open("/home/james/Desktop/response_lookup.csv", "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        my_writer.writerows(response_lookup.items())

    return response_lookup


def write_training_arrays_to_text():

    # we need to map letter entered in spreadsheet back to keycode
    # so invert the dictionary
    key_codes_inv = invert_dictionary(key_codes)

    base_output_path = "/home/james/Desktop"

    samples = np.empty((0, 1008))
    responses = []

    with open("/home/james/Desktop/training_samples_080416.csv", "r") as inpf:
        samples_reader = csv.reader(inpf, delimiter=",")
        c = 1
        for r in samples_reader:
            if c > 1:
                path_to_sample = r[0]
                response = r[1]

                if response != "!":
                    try:
                        sample = cv2.imread(path_to_sample)
                        sample_b = cv2.cvtColor(sample,cv2.COLOR_RGB2GRAY)

                        reshaped_sample = sample_b.reshape((1, 1008))
                        samples = np.append(samples, reshaped_sample, 0)
                    except Exception as ex:
                        print(ex)
                    responses.append(key_codes_inv[response])
            c += 1

    # save the array of thresholded samples - the training data to a text file
    np.savetxt(os.path.join(base_output_path, "csv_training_samples.data"), samples)

    # save the array of responses (what each sample represents) to text file
    responses = np.array(responses, np.float32)
    responses = responses.reshape((responses.size, 1))
    np.savetxt(os.path.join(base_output_path, "csv_training_responses.data"), responses)


def write_training_arrays_to_text_2():

    # not really key codes but rather a dict assigining a unique id to
    # every unique response instance
    key_codes = generate_response_lookup()

    # 250416 - if we are doing things non-interactively, why do we care about keycodes...
    # so we will just write the response for the sample directly

    # we need to map letter entered in spreadsheet back to keycode
    # so invert the dictionary
    #key_codes_inv = invert_dictionary(key_codes)

    base_output_path = "/home/james/Desktop"

    samples = np.empty((0, 1008))
    responses = []

    with open("/home/james/Desktop/training_samples_080416.csv", "r") as inpf:
        samples_reader = csv.reader(inpf, delimiter=",")
        c = 1
        for r in samples_reader:
            if c > 1:
                path_to_sample = r[0]
                response = r[1]

                if response in key_codes:
                    try:
                        responses.append(key_codes[response])
                        sample = cv2.imread(path_to_sample)
                        sample_b = cv2.cvtColor(sample,cv2.COLOR_RGB2GRAY)

                        reshaped_sample = sample_b.reshape((1, 1008))
                        samples = np.append(samples, reshaped_sample, 0)
                    except Exception as ex:
                        print(ex)
                else:
                    print("n")

                    #responses.append(key_codes_inv[response])

            c += 1

    # save the array of thresholded samples - the training data to a text file
    np.savetxt(os.path.join(base_output_path, "csv_training_samples.data"), samples)

    # save the array of responses (what each sample represents) to text file

    responses = np.array(responses, np.float32)
    responses = responses.reshape((responses.size, 1))
    np.savetxt(os.path.join(base_output_path, "csv_training_responses.data"), responses)


def main():
    #write_training_arrays_to_text()
    write_training_arrays_to_text_2()


if __name__ == "__main__":
    main()