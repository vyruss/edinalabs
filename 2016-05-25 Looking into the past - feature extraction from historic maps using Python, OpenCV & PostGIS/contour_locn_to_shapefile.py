import csv
import fiona
import rasterio

from collections import OrderedDict
from fiona.crs import from_epsg
from shapely.geometry import mapping, Point, box


def create_shapefile_from_csv(geometry_type="Polygon"):

    if geometry_type in ("Polygon", "Point", "Centroid"):
        csv_fn = "/home/james/geocrud/adrc/candidate_locations.csv"
        classifications_fn = "/home/james/Desktop/classifications_by_id.csv"
        img_fn = "/home/james/serviceDelivery/ADRC/NLS_samples/82877397.tif"
        shp_fn = "/home/james/Desktop/candidate_locations_" + geometry_type.lower() + ".shp"

        ds = rasterio.open(img_fn)
        ds_affine = ds.affine

        schema_properties = OrderedDict(
            [
                ("id", "int"),
                ("x", "int"),
                ("y", "int"),
                ("w", "int"),
                ("h", "int")
            ])

        my_schema = {
            "geometry": geometry_type,
            "properties": schema_properties
        }

        if geometry_type == "Centroid":
            my_schema["geometry"] = "Point"

        my_driver = "ESRI Shapefile"
        my_crs = from_epsg(27700)

        with open(csv_fn, "r") as inpf:
            with fiona.open(shp_fn, "w", driver=my_driver, crs=my_crs, schema=my_schema) as outpf:
                my_reader = csv.reader(inpf)
                c = 1
                for r in my_reader:
                    if c > 1:
                        id = int(r[0])
                        x = int(r[1])
                        y = int(r[2])
                        w = int(r[3])
                        h = int(r[4])

                        ul_coord = ds_affine * (x, y)
                        ll_coord = ds_affine * ((x), (y+h))
                        ur_coord = ds_affine * ((x+w), y)

                        if geometry_type == "Point":
                            feature_geom = Point(ur_coord)

                        if geometry_type == "Polygon":
                            #ur_coord = ds_affine * ((x+w), (y-h))
                            feature_geom = box(ll_coord[0], ll_coord[1], ur_coord[0], ur_coord[1])

                        if geometry_type == "Centroid":
                            ur_coord = ds_affine * ((x+w), (y-h))
                            bbox = box(ll_coord[0], ll_coord[1], ur_coord[0], ur_coord[1])
                            feature_geom = bbox.centroid

                        outpf.write({
                            "geometry": mapping(feature_geom),
                            "properties": {
                            "id": id,
                            "x": x,
                            "y": y,
                            "w": w,
                            "h": h
                            }
                        })

                    c += 1

def main():
    create_shapefile_from_csv(geometry_type="Polygon")
    #create_shapefile_from_csv(geometry_type="Centroid")
    #create_shapefile_from_csv(geometry_type="Point")

if __name__ == "__main__":
    main()



