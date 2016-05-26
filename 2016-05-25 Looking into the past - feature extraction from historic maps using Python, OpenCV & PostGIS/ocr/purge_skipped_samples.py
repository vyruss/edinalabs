__author__ = 'james'

import csv
import os
import pprint
import string
import subprocess


def purge():

    kept_samples = [["training_sample","response"]]

    with open("/home/james/geocrud/adrc/training_samples.csv", "r") as inpf:
        samples_reader = csv.reader(inpf, delimiter=",")
        c = 1
        for r in samples_reader:
            if c > 1:
                path_to_sample = r[0]
                response = r[1]

                if response == "!":
                    os.remove(path_to_sample)
                else:
                    kept_samples.append([path_to_sample, response])
            c += 1

    with open("/home/james/geocrud/adrc/training_samples.csv", "w") as outpf:
        samples_writer = csv.writer(outpf, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        samples_writer.writerows(kept_samples)


def move_into_folders():
    """

    given e.g. /home/james/Desktop/unclassified.csv with records like

    sample response
    1.png A
    2.png B
    3.png !

    create a folder called A
    move 1.png to folder A
    create a folder called B
    move 2.png to folder B
    ignore 3.png

    /home/james/Desktop/unclassified.csv manually edited to mark the response
    for every sample

    ND = skip/crud/wtf etc

    :return:
    """

    d = {}

    with open("/home/james/Desktop/unclassified.csv", "r") as inpf:
        samples_reader = csv.reader(inpf, delimiter=",")
        c = 1
        for r in samples_reader:
            if c > 1:
                sample = r[0]
                response = r[1]
                if response != "!":
                    if response == "&":
                        response = "AMP"
                    if response in d:
                        d[response].append(sample)
                    else:
                        d[response] = [sample]
            c += 1

    for response in sorted(d.keys()):
        if not os.path.exists(os.path.join("/home/james/Desktop/training_sample_sets", response)):
            cmd = "mkdir " + os.path.join("/home/james/Desktop/training_sample_sets", response)
            subprocess.call(cmd, shell=True)
            #print cmd

        for sample in d[response]:
            cmd = "mv " + os.path.join("/home/james/Desktop/training_sample_sets/OTHER", sample) + " " + os.path.join("/home/james/Desktop/training_sample_sets", response, sample)
            subprocess.call(cmd, shell=True)
            #print cmd

    # with open("/home/james/Desktop/training_samples.csv", "r") as inpf:
    #     samples_reader = csv.reader(inpf, delimiter=",")
    #     c = 1
    #     for r in samples_reader:
    #         if c > 1:
    #             sample = r[0]
    #             response = r[1]
    #             if response == "!":
    #                 cmd = "cp " + os.path.join("/home/james/geocrud/adrc", sample) + " " + os.path.join("/home/james/Desktop/training_sample_sets/OTHER", sample)
    #                 subprocess.call(cmd, shell=True)
    #         c += 1

        #print response, len(d[response])


def build_csv_from_folders():
    """

    create a CSV file with:

    sample response
    /path_to/1.png A
    /path_to/2.png B

    from /home/james/Desktop/training_sample_sets

    which we need for

    https://redmine.edina.ac.uk/projects/adcr-s/wiki/Update_September_2015

    prepare_training_samples_from_csv.py

    :return:
    """

    with open("/home/james/Desktop/training_samples_080416.csv", "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        my_writer.writerow(["sample", "response"])

        for root, dirs, files in os.walk("/home/james/Desktop/training_sample_sets"):
            for fn in files:
                sample = os.path.join(root, fn)
                response = os.path.split(root)[-1]
                if os.path.exists(os.path.join(root, sample)):
                    my_writer.writerow([sample, response])

if __name__ == "__main__":
    build_csv_from_folders()
    #move_into_folders()



