__author__ = 'james'

import csv
import os
import glob

# TODO having create a confusion matrix, create a table of confusion...

def write_confusion_matrix(classification_results_fname, output_path):
    """

    create as a csv a confusion matric of actual class vs predicted class
    each column represents the instances in a predicted class
    each row represents the instances in an actual class
    all correct predictions are located in the diagonal of the matrix so
    it`s easy to visually inspect the matric for errors as these will fall
    outside the diagonal


    :param classification_results_fname:
    :param output_path:
    :return:
    """
    classifications = {}

    with open(classification_results_fname) as inpf:
        my_reader = csv.reader(inpf, delimiter="\t")
        c = 1
        for r in my_reader:
            if c > 1:
                predicted_class = r[2]
                actual_class = r[3]

                if actual_class in classifications:
                    classifications[actual_class].append(predicted_class)
                else:
                    classifications[actual_class] = [predicted_class]
            c += 1

    # skip those marked with ! which is indicative of an extracted feature
    # which we can`t determine what it`s actual class should be
    actuals = sorted([x for x in classifications.keys() if x != '!'])

    all_predictions = [[''] + actuals]

    for actual_class in actuals:
        predictions = [actual_class]
        for predicted_class in actuals:
            c = classifications[actual_class].count(predicted_class)
            if c > 0:
                predictions.append(c)
            else:
                predictions.append(0)
        all_predictions.append(predictions)

    with open(os.path.join(output_path, "confusion_matrix.csv"), "w") as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        my_writer.writerows(all_predictions)


def get_classification_results():
    classifications = {}
    training_data = {}

    for fn in glob.glob("/home/james/Desktop/classified/*.png"):
        head,tail = os.path.splitext(os.path.split(fn)[-1])
        prediction, image_id = head.split("_")
        classifications[int(image_id)] = prediction

    with open("/home/james/Desktop/training_samples_080416.csv", "r") as inpf:
        my_reader = csv.reader(inpf)
        c = 1
        for r in my_reader:
            if c > 1:
                fn = r[0]
                known_response = r[1]
                head,tail = os.path.splitext(os.path.split(fn)[-1])
                image_id = head.replace("_sample", "")
                training_data[int(image_id)] = known_response
            c += 1

    the_missing = 0

    predicted_vs_actual = []

    for id in classifications:
        predicted_class = classifications[id]
        if id in training_data:
            actual_class = training_data[id]
            predicted_vs_actual.append([id, predicted_class, actual_class])
        else:
            the_missing += 1

    print(predicted_vs_actual)


def main():

    #path_to_classification_results = "/home/james/geocrud/adrc/classification_results.csv"
    #output_path = "/home/james/Desktop"

    #write_confusion_matrix(path_to_classification_results, output_path)

    get_classification_results()


if __name__ == "__main__":
    main()
