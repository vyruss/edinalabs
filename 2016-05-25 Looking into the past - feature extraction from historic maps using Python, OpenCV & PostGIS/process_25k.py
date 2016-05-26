"""
    pull out groups of pixels for different features based on RGB values
    - does not cope with variations in brightness between different NLS map sheets
"""

import csv
import cv2
import glob
import numpy as np
import os
import string
import subprocess

from string import Template
from snaql.factory import Snaql

import pg_connection as u


def get_sample_regions(v_tablename, r_tablename):
    """
    :param v_tablename:
    :param r_tablename:
    :return: gid/ftype from the training_regions Pg table so we can go through them
    """

    sample_regions = None

    snaql_factory = Snaql(".", "sql")
    queries = snaql_factory.load_queries("adrc_queries.sql")

    if "myrasters.nls_" in r_tablename:
        raster_src = r_tablename[len("myrasters.nls_"):]

        sql = queries.get_training_regions(
            vector_name=v_tablename,
            raster_src=raster_src
        )

        rs = u.query_pg(db_connection_string, sql)
        sample_regions = [[int(x[0]), x[1]] for x in rs]

    return sample_regions


def query_raster_by_training_regions(r_tablename, v_tablename):
    """

    :param r_tablename:
    :param v_tablename:
    :return: dict of min/max BGR pixel values for training regions
    """

    results = {}

    band_lookup = {1:"R", 2:"G", 3:"B"}

    snaql_factory = Snaql(".", "sql")
    queries = snaql_factory.load_queries("adrc_queries.sql")

    sample_regions = get_sample_regions(v_tablename, r_tablename)

    for sr in sample_regions:
        sample_region = sr[0]

        results[sample_region] = {
            "src_raster":r_tablename,
            "ftype":sr[1],
            "min":{"B":None, "G":None, "R":None},
            "max":{"B":None, "G":None, "R":None}
        }

        for band in (1,2,3):
            sql = queries.get_zonal_statistics(
                band_id=band,
                vector_name=v_tablename,
                raster_name=r_tablename,
                sample_region_id=sample_region
            )

            rs = u.query_pg(db_connection_string, sql)

            if len(rs) > 0:
                for r in rs:
                    min_value = r[1]
                    max_value = r[2]
                    results[sample_region]["min"][band_lookup[band]] = min_value
                    results[sample_region]["max"][band_lookup[band]] = max_value

    return results


def results_to_csv(results, out_fname="/home/james/geocrud/zonal_stats.csv"):
    """

    :param results:
    :param out_fname:
    :return: None - writes the training data to a CSV file
    """
    if os.path.exists(out_fname):
        mode = "a"
        out_results = []
    else:
        mode = "w"
        out_results = [["sample_region", "raster_src", "ftype", "min_b", "min_g", "min_r", "max_b", "max_g", "max_r"]]

    for sample_region in results:
        raster_src = results[sample_region]["src_raster"]
        ft = results[sample_region]["ftype"]
        min_r = results[sample_region]["min"]["R"]
        min_g = results[sample_region]["min"]["G"]
        min_b = results[sample_region]["min"]["B"]
        max_r = results[sample_region]["max"]["R"]
        max_g = results[sample_region]["max"]["G"]
        max_b = results[sample_region]["max"]["B"]
        out_results.append([sample_region, raster_src, ft, min_b, min_g, min_r, max_b, max_g, max_r])

    with open(out_fname, mode) as outpf:
        my_writer = csv.writer(outpf, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        my_writer.writerows(out_results)


def sample_region_to_png(region_id, vector_table, raster_table, output_folder="/home/james/geocrud"):
    """

    dump the raster that falls within the region out as a png

    based on:

    http://petewarden.com/2013/08/31/how-to-save-an-image-to-disk-from-postgis/

    but first had to follow this

    http://gis.stackexchange.com/questions/142056/postgis-is-not-seeing-any-gdal-drivers

    to set in /etc/postgresql/9.3/main/environment which by default for security
    reasons are disabled

    POSTGIS_GDAL_ENABLED_DRIVERS=ENABLE_ALL
    POSTGIS_ENABLE_OUTDB_RASTERS=1

    :param region_id: the id of the polygon we want to crop the raster to
    :param vector_table: the table holding the polygon cookie cutters
    :param raster_table: the raster table we want to crop
    :param output_folder: where to dump the PNG, default is ~/geocrud
    :return: writes PNG(s)
    """
    base_output_fname = raster_table

    if "." in base_output_fname:
        base_output_fname = base_output_fname.replace(".","_")

    base_output_fname = base_output_fname + "_" + str(region_id)

    output_hex = os.path.join(output_folder, "".join([base_output_fname, ".hex"]))
    output_png = os.path.join(output_folder, "".join([base_output_fname, ".png"]))

    sql_t = Template("""\copy (SELECT encode(st_aspng(s.clipped_raster), 'hex') as png FROM (SELECT a.gid,st_clip(b.rast, a.geom,true) as clipped_raster FROM $v_tablename a, $r_tablename b WHERE a.gid = $region_id) s) TO '$output_hex'""")

    sql = sql_t.substitute(v_tablename=vector_table,
                           r_tablename=raster_table,
                           region_id=region_id,
                           output_hex=output_hex
                           )

    cmd_t = Template('''psql -c "$sql_to_run"''')
    cmd = cmd_t.substitute(sql_to_run=sql)
    print(cmd)
    subprocess.call(cmd, shell=True)

    cmd_t = Template("""xxd -p -r $input_hex > $output_png""")
    cmd = cmd_t.substitute(input_hex=output_hex, output_png=output_png)
    print(cmd)
    subprocess.call(cmd, shell=True)


def fetch_colour_boundaries(zonal_fname="/home/james/geocrud/zonal_stats.csv", restrict_to=None):
    """

    :param zonal_fname:
    :param restrict_to:
    :return: dict of aggregate colour boundaries, keyed on featurtype
    """

    boundaries = None

    if os.path.exists(zonal_fname):

        boundaries = {}

        with open(zonal_fname, "r") as inpf:
            c = 1
            my_reader = csv.reader(inpf, delimiter=",", quotechar='"')
            for r in my_reader:
                if c > 1:
                    sample_region = r[0]
                    raster_src = r[1]

                    if (restrict_to is None) or (restrict_to == raster_src):
                        ft = r[2]
                        min_b = int(float(r[3]))
                        min_g = int(float(r[4]))
                        min_r = int(float(r[5]))
                        max_b = int(float(r[6]))
                        max_g = int(float(r[7]))
                        max_r = int(float(r[8]))

                        if ft not in boundaries:
                            # ([min_b, min_g, min_r], [max_b, max_g, max_r])
                            boundaries[ft] = ([256, 256, 256], [0, 0, 0])

                        if min_b < boundaries[ft][0][0]:
                             boundaries[ft][0][0] = min_b

                        if min_g < boundaries[ft][0][1]:
                             boundaries[ft][0][1] = min_g

                        if min_r < boundaries[ft][0][2]:
                            boundaries[ft][0][2] = min_r

                        if max_b > boundaries[ft][1][0]:
                            boundaries[ft][1][0] = max_b

                        if max_g > boundaries[ft][1][1]:
                            boundaries[ft][1][1] = max_g

                        if max_r > boundaries[ft][1][2]:
                            boundaries[ft][1][2] = max_r
                c += 1

    return boundaries


def split_img_by_colour(image_to_split, colour_boundaries, output_path = "/home/james/geocrud"):
    """

    :param image_to_split:
    :param colour_boundaries:
    :param output_path:
    :return: split an image up based on colour boundaries
    """

    print(image_to_split)

    if os.path.exists(image_to_split):

        base_name =  os.path.splitext(os.path.split(image_to_split)[-1])[0]

        print("".join(["reading image...", image_to_split]))
        image = cv2.imread(image_to_split)

        #cv2.imshow("25K", image)
        #cv2.waitKey(0)

        #image= cv2.GaussianBlur(image,(3,3),0)
        #cv2.imshow("G_blurred", image)
        #cv2.waitKey(0)

        for feature in colour_boundaries:
            print("".join(["pulling out all pixels within colour boundaries for ", feature]))
            lower = np.array(colour_boundaries[feature][0], dtype="uint8")
            upper = np.array(colour_boundaries[feature][1], dtype="uint8")

            mask = cv2.inRange(image, lower, upper)
            output = cv2.bitwise_and(image, image, mask=mask)

            #cv2.imshow(feature, np.hstack([image, output]))
            #cv2.imshow(feature, output)
            #cv2.waitKey(0)

            processed_image = cv2.cvtColor(output, cv2.COLOR_RGB2GRAY)
            (thresh, processed_image) = cv2.threshold(processed_image, 0, 255, cv2.THRESH_OTSU)

            processed_image = cv2.medianBlur(processed_image, 3)
            #cv2.imshow("Median blur applied", processed_image)
            #cv2.waitKey(0)

            out_fname = base_name + "_extracted_" + feature + ".tif"
            out_fname = os.path.join(output_path, out_fname)
            cv2.imwrite(out_fname, processed_image)


def query_raster_by_vector(raster_table, vector_table):
    """

    drives the analysis

    :param raster_table:
    :param vector_table:
    :return:
    """
    my_raster_table = raster_table
    my_vector_table = vector_table

    results = query_raster_by_training_regions(r_tablename=my_raster_table,
                                                v_tablename=my_vector_table)

    if "myrasters.nls_" in my_raster_table:
        raster_src = my_raster_table[len("myrasters.nls_"):]

    results_to_csv(results)


def do_thresholding(input_image):
    im = cv2.imread(input_image)
    processed_image = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    (thresh, processed_image) = cv2.threshold(processed_image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    out_fname = "/home/james/geocrud/thresholded_" + os.path.split(input_image)[-1]
    cv2.imwrite(out_fname, processed_image)


def do_color_correction(input_image):
    pass
    # http://answers.opencv.org/question/16258/color-correction/


def split_to_hsv(input_image):
    im = cv2.imread(input_image)
    hsv_im = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv_im)
    out_fname = "/home/james/geocrud/h_" + os.path.split(input_image)[-1]
    cv2.imwrite(out_fname, h)

    out_fname = "/home/james/geocrud/s_" + os.path.split(input_image)[-1]
    cv2.imwrite(out_fname, s)

    out_fname = "/home/james/geocrud/v_" + os.path.split(input_image)[-1]
    cv2.imwrite(out_fname, v)

def main():
    """

    :return:
    """
    do_training = False
    classify_images = False
    dump_sample_region_footprints = True
    explore = False
    threshold = False

    vector_table = "myrasters.training_regions"

    raster_tables = [
        "myrasters.nls_25k_91578185",
    ]

    if do_training:
        # Having defined a set of training region polygons, find the min/max
        # values of BGR in each polygon to inform the classification process
        # creates a CSV file with these ranges

        print("Doing Training...")

        for raster_table in raster_tables:
            query_raster_by_vector(raster_table, vector_table)

    if classify_images:
        # use the training classes to seperate out the pixels in an image
        # training classes are read from the CSV

        print("Splitting Images...")

        images_to_classify = "/home/james/serviceDelivery/ADRC/NLS_Data/wetransfer-aa0da6/*.tif"

        print(images_to_classify)

        colour_boundaries = fetch_colour_boundaries()

        for fn in glob.glob(images_to_classify):
           split_img_by_colour(fn, colour_boundaries, output_path = "/home/james/geocrud")

        # use training data on a per-sheet basis

        # colour_boundaries = fetch_colour_boundaries(restrict_to="myrasters.nls_91578182")
        #
        # image_to_classify = "/home/james/serviceDelivery/ADRC/NLS_samples/25K_210316/wetransfer-aa0da6/91578182.tif"
        # split_img_by_colour(image_to_classify, colour_boundaries, output_path = "/home/james/geocrud")
        #
        # colour_boundaries = fetch_colour_boundaries(restrict_to="myrasters.nls_91578185")
        #
        # image_to_classify = "/home/james/serviceDelivery/ADRC/NLS_samples/25K_210316/wetransfer-aa0da6/91578185.tif"
        # split_img_by_colour(image_to_classify, colour_boundaries, output_path = "/home/james/geocrud")

    if dump_sample_region_footprints:
        # what fun, if desired we can write out a PNG showing the footprint of
        # each training region :)

        print("Dumping training footprints...")

        for raster_table in raster_tables:
            sample_regions = get_sample_regions(vector_table, raster_table)
            for sr in sample_regions:
                region_id = sr[0]
                sample_region_to_png(region_id, vector_table, raster_table, output_folder="/home/james/geocrud")

    if explore:
        images_to_classify = "/home/james/serviceDelivery/ADRC/NLS_samples/25K_210316/wetransfer-aa0da6/*.tif"

        for fn in glob.glob(images_to_classify):
            split_to_hsv(fn)

        # something else!
        #colour_boundaries = fetch_colour_boundaries(restrict_to="myrasters.nls_91578185")
        #print colour_boundaries

    if threshold:
        pass
        #do_thresholding(image_to_classify)


if __name__ == "__main__":
    db_host = "localhost"
    db_port = "5432"
    db_name = "james"
    db_user = "james"

    db_params = u.DatabaseConnectionParams(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user)

    db_connection_string = db_params.get_connection_string()

    if db_connection_string is not None:
        main()