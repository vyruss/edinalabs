Looking into the past - feature extraction from historic maps using Python, OpenCV and PostGIS.
===============================================================================================

ADRC-S
------

* Administrative Data Research Centre Scotland
* part of the Administrative Data Research Network (ADRN)
* An ESRC Data Investment
* 12 ADRC-S Work Packages
* EDINA working on WP5 - Provision of Geocoding and Georeferencing tools

Administrative Data
-------------------

* Data Linkage

What, Why and with whom we are actually doing
---------------------------------------------

* Who - Prof(s) Chris Dibben and Jamie Pearce from UoE GeoSciences
* What - Building geospatial layers from historic maps
* Why - Effects of past environmental conditions on (longitudinal) population cohorts

* Train - where did I run in the past (causing air pollution from my coal fired boilers)
* Urban - did past populations live in predominantly urban or rural locale
* Industry - where were particular types of industry located
* Greenspace and Bluespace - Parks and Water

How are we doing this
---------------------

* UoE MSc Student`s (Gina) Disseration on OCR of maps / automatic geo-registration
* Computer Vision
* Extend OCR from [0-9] to [a-z][A-Z]
* Extract other types of non-textual information from (historic) maps - Vector Features

Environment
-----------

* Python(3) - the latest and greatest
* Virtualenv - create isolated environment
* PyCharm Community Edition IDE - PEP8 / git integration / various plug-ins
* Ubuntu 16.04
* OpenCV - Image Processing and Computer Vision
* PostgreSQL (9.5)
* PostGIS (2.2) - (geospatial) data store and (spatial) analysis engine for vector and raster data
* QGIS 
* (a bit of) ArcGIS / ArcScan

Python Libraries used / we will encounter
-----------------------------------------

* numpy - numpy array sit`s at the heart of everything

* cv2 (OpenCV3) - python interface to OpenCV

* shapely 

* fiona ([vector] File Input Output Not Analysis?)
** more pythonic interface to GDAL-OGR
** use to create shapefiles etc

* rasterio (Raster Input Output)
** when manipulate (geospatial) rasters in cv2, cv2 treats data as any other type of image
** use rasterio affine functions to map pixel coordinates to geospatial coordinates 
* development of shapely; fiona; rasterio all led by Sean Gilles (now of mapbox). Each does 1 thing well. Interoperate nicely.

* assuming PostGIS, if you add in a map renderer like mapnik, then this lot gives you everything
  needed to do geographic data analysis (raster and vector), data conversion, data management and map automation :)
  
* Snaql - "Raw (S)QL queries in Python without pain"

Historic Maps
-------------

* Provided by Chris@NLS
* High quality (large) full colour scans
* Mainly be looking at 2 map series
* 25 inch
* 25K

OpenCV Flowline
---------------

* Load image
* Change colorspace
* Do low-level image processing
 for example, blurring to remove high frequency noise
* Threshold 
 into binary foreground/background image
* Identify candidate features - Contour Tracing
 rather like a contour on a barometric chart or a topographic map, contour marks a change boundary
 on a binary foreground/background image, contours mark change between foreground and background
 contours form linear sequences of coordinates
 cv2 has different options for contour description which we can exploit
 shape / (hierarchial) relationship with one another
* Filter / Classify candidate features
 e.g. select contours which are a particular size/shape
 use ML to assign labels to particular regions of the image occupied by the contour
* Form higher level features from candidates
 build upwards - group points into lines, group lines into regions (polygons)
* Create geospatial layer

Example 1 - Bluespace
---------------------

Py / SQL code examples

Example 2 - Text & Symbols
--------------------------

Py / SQL code examples

Example 3 - Urban Areas
-----------------------

Py / SQL code examples

More information
----------------

* pyimagesearch
* OpenCV docs (Python interface docs are better in version 3 than 2!)
* lots of books e.g. on Packt
