#!/usr/bin/python

import fiona
import glob
import os
import rasterio
import subprocess


from fiona.crs import from_epsg
from shapely.geometry import mapping, Polygon
from string import Template

__author__ = 'james'

"""
    clip out a 1x1 km aoi at the centre of all tiff files in some directory
"""


def clip_raster(raster, mask, out_fname):
    """
    clip a raster to the extents of a shapefile via gdalwarp

    :param raster:
    :param mask:
    :param out_fname:
    :return:
    """
    gdal_t = Template("""gdalwarp -q -cutline $mask -crop_to_cutline -of GTiff $srcRaster $outFileName""")
    gdal_cmd = gdal_t.substitute(mask=mask, srcRaster=raster, outFileName=out_fname)
    subprocess.call(gdal_cmd, shell=True)


def get_poly_from_mbr_coords(min_x, min_y, max_x, max_y):
    """
    create a Shapely polygon from a set of mbr coords

    :param min_x:
    :param min_y:
    :param max_x:
    :param max_y:
    :return:
    """
    poly = Polygon([(min_x, min_y),
                    (max_x, min_y),
                    (max_x, max_y),
                    (min_x, max_y),
                    (min_x, min_y)
                    ])

    return poly


def get_poly_from_raster_extents(filename):
    """
    get a shapely polygon describing the extent of a raster using rasterio

    :param filename:
    :return:
    """
    ds = rasterio.open(filename)

    ul = ds.affine * (0, 0)
    lr = ds.affine * (ds.width, ds.height)

    min_x = ul[0]
    min_y = lr[1]
    max_x = lr[0]
    max_y = ul[1]

    poly = get_poly_from_mbr_coords(min_x, min_y, max_x, max_y)

    return poly


def polygon_to_shapefile(polygon, out_fname, buffered_centrepoint=False):
    """
    generate a shapefile representing the extents or an aoi of a raster

    :param raster:
    :param out_fname:
    :param buffered_centrepoint:
    :return:
    """

    my_schema = {
        "geometry": "Polygon",
        "properties": {
            "id": "int",
            "name": "str"
            },
    }

    my_driver = "ESRI Shapefile"

    # for mi fiona will write correct format depending on
    # if we specify output file as .mif or .tab
    #my_driver = "MapInfo File"

    my_crs = from_epsg(27700)

    with fiona.open(out_fname, "w", driver=my_driver, crs=my_crs, schema=my_schema) as c:

        if buffered_centrepoint:
            centroid = polygon.centroid
            buffered_aoi = centroid.buffer(500.0)
            buffered_aoi_envelope = buffered_aoi.envelope
            poly = buffered_aoi_envelope

        id = 1
        name = ""

        c.write({
            "geometry": mapping(poly),
            "properties": {
                "id": id,
                "name": name
            }
        })


def main():

    base_output_path = "/home/james/geocrud/adrc"

    for f in glob.glob("/home/james/serviceDelivery/ADRC/NLS_samples/*.tif"):

       sheet_name = os.path.splitext(os.path.split(f)[1])[0]
       aoi_shp = os.path.join(base_output_path, (sheet_name + "_aoi.shp"))
       clipped_raster = os.path.join(base_output_path, (sheet_name + "_aoi.tif"))

       raster_extents = get_poly_from_raster_extents(f)

       polygon_to_shapefile(raster_extents, aoi_shp, buffered_centrepoint=True)

       clip_raster(f, aoi_shp, clipped_raster)

    # base_output_path = "/home/james/geocrud/adrc"
    #
    # src_image = "/home/james/Desktop/adrc_aoi_samples/87212838_aoi.tif"
    # aoi_regions = ([],
    #                [],
    #                [])
    #
    # id = 1
    # for aoi in aoi_regions:
    #     poly = get_poly_from_mbr_coords(aoi[0], aoi[1], aoi[2], aoi[3])
    #     mask = os.path.join(base_output_path, "".join(["aoi_", str(id),".shp"]))
    #     out_fname=os.path.join(base_output_path, "".join(["aoi_", str(id),".tif"]))
    #     polygon_to_shapefile(poly,mask, buffered_centrepoint=False)
    #     clip_raster(src_image, mask, out_fname)


if __name__ == "__main__":
    main()
