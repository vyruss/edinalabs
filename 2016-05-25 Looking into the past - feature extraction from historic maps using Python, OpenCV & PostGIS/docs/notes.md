82877361_subarea.tif sample region

using default values for 

contourArea = < max_contour_area (1000)
contourArea = > 50
h/w = <2
w/h = <2
h*w = < max_contour_envelope_area (1500)

States
------

- contour of letter found and accepted
- contour of letter found but rejected
- contour of letter found BUT a sub-region(s)
- no contour of letter found

Classification
--------------

Paper Mill
!P - contour of letter found but rejected : 381
 - area = 649.5 
 - h = 40
 - w = 42
 - h/w = 0.952 ok
 - w/h = 1.05 ok
 - h*w = 1680 fail as > 1500
 
a - contour of letter found and accepted
p - contour of letter found BUT a sub-region(s) 
e - contour of letter found BUT a sub-region(s) 
r - no contour of letter found

M - contour of letter found BUT a sub-region(s)
i - contour of letter found and accepted
ll - contour of letter found and accepted BUT 2 letters fused 

Water of
W - contour of letter found BUT a sub-region(s)
a - contour of letter found and accepted : 351
!t - contour of letter found but rejected : 353
 - area = 324.5
 - h = 47
 - w = 23
 - h/w = 2.043 fail as >2
 - w/h = 0.489 ok
 - h*w = 1081 ok
e - contour of letter found and accepted : ?
r - no contour of letter found

o - contour of letter found BUT a sub-region(s)
f - contour of letter found BUT a sub-region(s) 

Iron Works
I - contour of letter found and accepted : ?
r - contour of letter found and accepted : ?
o - contour of letter found and accepted : ?
n - no contour of letter found 

W - contour of letter found and accepted : 87 + 85
o - contour of letter found and accepted : ?
r - contour of letter found and accepted : 78
k - contour of letter found and accepted : 83
s - contour of letter found and accepted : 77

100215
------

compare results of these runs

(batched)

# defaults values - fails to capture the P of Paper and t of Water
"/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif",1000,1500,2.0

# increase max contour envelope area - now captures P of paper, keep aspect ration at 2.0
"/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif",1000,1700,2.0 

# keep default contour envelope area, increase aspect ration to 2.1
# now captures t of Water but fails to capture P of paper
"/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif",1000,1500,2.1

# increase both max contour area and aspect ration
# captures both P of Paper and t of Water
"/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif",1000,1700,2.1

# so you might thing if use these values of max contour area and aspect ration would get same
# results when running against the full image?
# nope - probably because the the

the full image

"/home/james/serviceDelivery/ADRC/NLS_samples/82877361.tif",1000,1700,2.1

# in the image passed to the contour finder, t of Water is fused to another region
# the P of Paper looks ok though, so why has it not been found with the same params
# as in the sub region? - because the thresholding is different across the whole
# image than in the smaller sub region...

# the contour associated with the P in the full image
contour_id  h   w	area	hw	wh	hxw
72089	    42	44	725	    0	1	1848 

# the contour associates with the P in the sub image
contour_id  h   w	area	hw	wh	hxw
381	        40	42	649.5	0	1	1680

# can see what the problem is, in the full image the mbr of the contour
# corresponding to P has got bigger so it falls beyond the threshold
# hxw > 1700 and therefore the contour is dropped...

# since the structuring params are the same the only things that is difft
# between doing processing on the sub image compared with the full image
# is the thresholding - the reason it`s difft is because otsu is based on
# consideration of the image as a whole which will obviously be different
# between the small image and the whole image.

# the issue with this is that we are going to have problems coming up with
# size params as each image will be thresholded in isolation...

# if we up max_contour_envelope_area to 2000 and rerun against the full image, P is now identified

100615
------
------

so

/home/james/serviceDelivery/code/adrc/python/text_extractor.py big_one.csv

works on "/home/james/serviceDelivery/ADRC/NLS_samples/82877385.tif"

and dumps 1000s of extracted sub-images to

/home/james/geocrud/adrc

giving either <id>_src_<job_uuid>.png or <id>_thresh_<job_uuid>.png
these are the 1000s of primitives pulled by the current script from the full NLS sheet scan.
The b&w <id>_thresh_<job_uuid>.png ones are the ones we are interested in since these have been pulled from the threshold image according to the size/shape rules.

I`ve then manually eyeballed these and copied the <id>_thresh_<job_uuid>.png`s that are letter B like to

/home/james/serviceDelivery/Bees

[todo]
- how do we determine programatically (recognition) what it is about a primitive that determines it`s a B rather than just another character or not a character at all. On the basis that once this has been done we can start stringing the characters together to build up words and thus placenames etc.

 - Gina implemented 4 recognition methods:
  - Template matching with Pearson Correlation Coefficient as the descriptor
  - Contour matching with Hu Moments (of the contours) as the descriptor
   - advantage over template matching is that hu moments are invariant to transformations like
     rotation and scaling and therefore the method can be used for cases of multi-oriented and
     multi-size characters
   - in both template and contour matching the template image that gives the highest correlation coefficient value or has the most similar Hu moments with the original segmented image is identified as the closest match  
   
  - K-Nearest Neighbour matching with Distance of Pixel Values as the descriptor
   - statistical method that compares an unknown pattern to a set of patterns that have already been labelled during the training stage
   - classification measures the distance between pixel values of the input image and the templates
    - !!! this makes the method sensitive to translations, rotations and scaling !!!
  
  - Artificial Neural Networks with Pixel Values as the descriptor
  
  - Gina`s results (performance of difft recognition methods):
   - template matching and K-Nearest Neighbour performed best
   - ANN performed almost as well as template matching and KNN
   - contour matching performed poorly
    - because hu moments are rotation invariant so cannot tell difference
      between rotated 6 and 9 characters (and also unstable for other
      numbers as well)
   - !!!recommendation - despite template matching being as accurate as 
        KNN, one-by-one comparison with the templates is very time consuming
        and therefore KNN is the method to go for.
    
  
[todo] what do we need to do to similarly implement these recognition methods?

  !!! the binary thresholded primitives need to be the same size if we`re going to be doing comparisons !!!
  
  !!! after indv digits are recognized they have to be connected with their neighbouring digits in order to form the multi-digit numbers that they represent. Gina implemented a method that searches in the close area of each digit for other recognized digits - when two characters are to be connected, their sizes must be similar. Therefore in her method only digits with approximately the same dimensions are connected in a string of digits !!!
  

- given 1 image from /home/james/serviceDelivery/Bees what do we need to do to be able to find this self-same image again or find other images which are similar under /home/james/serviceDelivery/Bees or disimilar?

- so assume we have actually tagged 1 of these primitives as the letter B, do we know where this portion of the image actually lies in geographic space?

- can we employ some search against a word dictionary to fill in the gaps of extracted characters?

120615
------

Hit a stumbling block of understanding what we pass to cv2.KNearest.train()

Understand from my noddy knn.py example that we pass an array of training data and an array of labels
 which is simple to understand when dealing with a simple 1 dimensional array of numbers
  what I don`t understand is how we do the same when each data point in the training data is a sub-region (patch) of the image
  that represents a candidate letter within the image
  
  been using library_development.py to create pkl files which are then loaded by tester.py but keep getting this kind of thing:
  
  "train data must be floating-point matrix in function cvCheckTrainData"
  
  look at this again(!)
  
  http://stackoverflow.com/questions/9413216/simple-digit-recognition-ocr-in-opencv-python
  
230615
------

that helped.
Modified Gina`s stuff to write the numpy arrays to text files rather than pickling
the bit I had missed is that each extracted candidate region is decomposed from a "grid" to 1 massive "row"
and these are then fed to the classifier

a flowline is:

(
 all outputs are being dumped/read from /home/james/geocrud/adrc
 each .data file is just a text representation of a numpy array
 it`s probably inefficient to be manipulating text files, which is why gina probably opted for the pickling
)

1. library_development.py (interactively creates training_samples.data & training_responses.data)
2. text_extractor.py (automatically produces candidates.data & dumps each candidate sub image as well as info about contours etc)
3. knn_classify.py (automatically builds a KNN classifier model from training_samples.data & training_responses.data & classifies candidates.data)

at the moment I`ve been running so that training_samples.data = candidates.data which tests the process works (I think!) but does not do anything useful

with run of knn_classify.py (where training_samples.data = candidates.data), for k in

knn_model.find_nearest(candidates, k=1)

if k = 1 then all the candidates match the training samples (not very useful)
if k = 3 then the matches are less good (as there are more class overlaps and things are misclassified)
 if build up larger training sets will this help?

/home/james/serviceDelivery/ADRC/NLS_samples/*.tif are geotiff`s (based on what gdalinfo says)

240615
------

take a 1x1 km extract from some file in /home/james/serviceDelivery/ADRC/NLS_samples/*.tif
and build up a training set

take a different 1x1km extract from either a different region of the same file or from a completly different file

[todo]

used clip_out_test_regions.py to extract a 1x1km AOI from each of the /home/james/serviceDelivery/ADRC/NLS_samples/*.tif files
these are at /home/james/Desktop/adrc_aoi_samples

note the text density varies widely across these!
use one to build up the training set
then run the extraction/classification against a different one and see what kind of results we get

300615
------

improved workflow

library_development.py 

is now ran like this:

./library_development.py /home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif True
./library_development.py /home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/82877361_subarea.tif False


True means it runs interactively and as previously it displays each candidate sample after which we hit a button on the keyboard
 after it has ran interactively it displays info about which letter no sample has been provided for

False means it just dumps all standardised candidates to the disk with a csv with these contents:
 (did this as it`s quicker to reject things by poring over the contents of a folder...)
"training_sample","response"
"/home/james/geocrud/adrc/1_sample.png","!"
"/home/james/geocrud/adrc/2_sample.png","!"

we then need to look at the dumped candidate images and fill in the response column of the CSV with a-z
records with the default value of ! still present will be skipped in the next step

and then run prepare_training_samples_from_csv.py

which will generate the training_samples.data & training_responses.data from the CSV
! means the sample will be skipped

as a test I interactively ran library_development.py against 82877361_subarea.tif
I then ran it non-interactively, ran prepare_training_samples_from_csv.py 
and then ran knn_classify.py with training data from interactive, test data from prepare_training_samples_from_csv.py
which matches 1 for 1, thus showing that the features are being represented correctly between each of the various scripts

- we know that the images are geotiff`s, thus we know the position of one extracted feature and it`s position relative to other features
 - (for experimentation) when text_extractor.py runs it now inserts x/y into the contours_properties.csv
  - use rasterio/fiona to get the geolocation of the source raster and create a point shapefile for every contour position
   - contour_locn_to_shapefile.py

----
 
[todo] 

try (non-interactively!)

/home/james/Desktop/adrc_aoi_samples/82877484_aoi.tif as training image
/home/james/Desktop/adrc_aoi_samples/87212838_aoi.tif as image to capture from

- parameters need further experimentation
- the character isolation criteria is entirely based on size/shape/aspect ration of contours
 - is their other criteria that would improved this 
  - what makes a letter different from a tree
   - if we can find a tree then we know it might instead be a letter
    - are there other such features?
    
    
140715
------

at the moment we don`t do this but I guess we will need to make a distinction in the training data between a lower
and upper class character since e.g. a is quite a different shape to A.

At the moment training_samples.csv should only contain 0-9|a-z

did this:

/home/james/Desktop/adrc_aoi_samples/82877484_aoi.tif as training image

/home/james/Desktop/adrc_aoi_samples/87212838_aoi.tif as image to capture from

For experimentation purposes I`ve been using z to represent those christmas tree type features
these are clearly not letters but if we can always spot these then we can exclude them from the
set of candidates that could be characters.

{{todo}} 

process is still a bit painful but sequence is as follows:

run library_development.py (non-interactively)
 producing: training_samples.csv
then edit training_samples.csv and mark up with characters, leaving those to be skipped as !
then run purge_skipped_samples.py (it will purge images marked by ! and rewrite the training_samples.csv file)
then run prepare_training_samples_from_csv.py (based on the just modified training_samples.csv file)
 producing: csv_training_samples.data csv_training_responses.data
  these then need copied to Desktop
then purge contents of /home/james/geocrud
then run text_extractor.py
then copy candidates.data to Desktop
then run knn_classify.py
then edit classification_results.csv and assign the actual class against each predicted class
then run confused.py against classification_results.csv to generate a confusion matrix

- need to evaluate results

https://en.wikipedia.org/wiki/Confusion_matrix

from confusion matrix derive a table of confusion for each class (character)

e.g. for "s"

true positive - actual s candidates that were correctly classified as being an s
false positive - other candidates that were incorrectly classifed as being an s
false negatives - actual s candidates that were incorrectly classifeld as being something other than an s
true negatives - all the remaining candidates that were correctly classified as not being an s


- /home/james/geocrud/*_all_contours.png vs as /home/james/geocrud/*_final_contours.png shows since we are STILL using the default params MANY of the letters are not making it through to the classification stage

{{todo}}

repeat this whole process with modified parmas for feature size etc
 do things improve?
 
160715
------

not convinced the reported values of hw & wh in the _contours_properties.csv are legit as they are all being rounded 

python(2) integer division floors the result to the nearest integer
is this actually an issue?
 we`re only doing division to compute h/w and w/h and comparing these against an aspect ratio of 2 
 if concerned we should add

 #from __future__ import division 
 
 at the start of text_extractor.py
 
200715
------

OK, so the "tooling" pretty much works in that we have a complete flowline to build up library and do feature classification
in a blind image

BUT fundamentally there are STILL issues with extracting the candidates owing to not being able to adequately seperate the
characters from the rest of the map or from one another

SO need to go back to the start and attempt to refine the "tooling" and the choice of params based on the AOI`s that I captured manually back at the start here:

/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/regions

so for example doing:

(run with default params)

james@dlib-ngunnawal:~/serviceDelivery/code/adrc/python$ ./text_extractor.py /home/james/Desktop/24.tif 1000 1500 2.0 True True

is still pretty far from where we need to be :(

ISSUES that remain:
 - param choice - default params are optimised for digit capture, we need to characterise better the range of character size in inputs to inform param choice
 - characters that either overun backdrop line or are so close that they bleed into these when a blur filter is applied
 - for characters can have different size in the same word so the mbr of one may overun the neigbour so need tome ways of subtracting the one from the other, assuming this is not what the stuff that the fused characters does already!
 - look at furher things we can do to remove features we don`t care about:
  - digits
  - trees - so those xmas trees(!), what about the other types - if the same symbol is always used can we detect them and remove them
  - field boundaries / lines
   - so looking at things the other way - can we extract non-text another way and then deal with text as we`re doing here?
   
final_research_paper_GStavropoulou.pdf:

"the problem is that fused characters have analogies that do not 
correpsond to one individual character and thus are eliminated from 
the process if the applied rules are too strict"

"for cases of rotated characters the minimum-bounding box is detected 
and the analogies are calculated based on this rectangular

...the segmented image is then rotated and resized in order to pass the 
recognition process." (?)

Classification Methods

I Template Matching

II Contour Matching - compares hu moments of candidates with those of 
templates. Hu moments are invariant to transformations like rotation 
and scaling making it useful for cases of multi-oriented and 
multi-sized characters 

III KNN Nearest Neighbour - measures the distance between the pixel 
values of the input image and templates used. BUT this makes the 
method sensitive to translations, rotations and scaling.  

IV ANN

KNN was used, was this because dealing with rotation was not an issue 
when dealing with digits as opposed to characters?

---

"After the individual digits are recognized, they have to be connected 
with their neighbouring digits in order to form the multi-digit 
numbers that they represent... an algorithmic method was implemented 
that searches in the close area of each digit for other recognized 
digits... when two characters are to be connected, their sizes must be 
similar. Therefore in the proposed methods only digits with of 
approximately the same dimensions are connected in a string of digits."

"Results

- even though specific rules of contour area and width-height ratios 
were followed, many elements of the map were defined as digits and 
were passed in the process of recognition - cases of alphabetical 
characters and map symbols that occur on the map and have the same 
analogies as the digits

- another problem were the fused characters that were not successfully 
seperated in the pre-processing ... these pairs of digits were 
rejected from the algorithm and never passed to the recognition process

"one of the most challenging problems for developing an OCR algorithm 
is the seperation of touching characters or the segmentation of 
characters that are connected with image graphics."

methods for seperation of touching characters are based on connected 
component analysis - the analysis of the connected pixel area

touching characters generally have an aspect ratio (w/h) larger than 
that of single isolated characters... based on this from the remaining 
contours in the image only those that have a bounding box width 1.2 
times larger than the height were addressed as touching characters

the ration of 1.2 times larger than the height was found to work 
better with the fonts used in the sample maps as it does not affect 
indx digits with width slightly larger than their height

 - this rule poses a restriction to the useage of the algorithm on 
 rotated characters or digits, as in these cases the aspect ratio 
 might be equal to those of rotated characters
 
digits appear to form mostly one-digit or two-digit numbers. Therefore 
the developed algorithm tackles only 2 touching digits.

the algorithm is applied on the middle columns of pixels in the area 
of the touching characters and searches for the local minimum vertical 
thickness of white pixels, the point where the characters are possibly 
connected

- the number of columns that the algorithm is implemented on depends 
on the size of the touching characters and therefore on the size of 
the font

Post-Processing - grouping of individual digits (into strings)

the groupings of the symbols into strings is based on the symbols 
location in the document; symbols that are found to be sufficiently 
close are grouped together

for individual digits, detect those digits that form a multi-digit 
number and merge them together

search in the neighbourhood of each digit for other digits with 
similar size

algorithm initially detects the digits that could be first in a string 
of consecutive digits, by searching in the region left of it for other 
similar digits

BUT method employed is only suitable for numbers in horizontal or 
vertical form and does not solve the cases of rotated strings of 
numbers. Therefore to connect the individual digits in OS maps a 
different method has to be applied.

220715
------

for letters picked out (all except 45!) here:

/home/james/serviceDelivery/ADRC/NLS_samples/TestRegion/QGIS/manually_marked_up_industrial_sites.qgs

this will run each letter extract (as opposed to the whole image) 
through text_extractor.py and dump to stdout 

print input_image, contour_id, h, w, hw, wh, contour_area, hxw, x, y+h

james@dlib-ngunnawal:~/serviceDelivery/code/adrc/python$ for i in {1..44}; do ./text_extractor.py /home/james/geocrud/regions/$i.tif 1000 1500 2.0 True True; done | grep -v ^processing

and then shove into pg using csvkit (which rocks!)

so we can see the range of letter size we are encountering and how 
this differs from the defaults assumed by the script as was designed
to pull out digits.

SELECT input_img, image_id, c_id, h, w, hw, wh, c_area, hxw, x, y, letter
FROM public.adrc_letters_properties
ORDER BY image_id;

so for "Wellington"

(SELECT image_id, max(h) as max_h
FROM public.adrc_letters_properties
WHERE image_id >= 1 and image_id <= 10
GROUP BY image_id
ORDER BY max_h ASC
LIMIT 1)
UNION ALL
(SELECT image_id, max(h) as max_h
FROM public.adrc_letters_properties
WHERE image_id >= 1 and image_id <= 10
GROUP BY image_id
ORDER BY max_h DESC
LIMIT 1)

image_id;max_h
5;25
1;42

so max height varies from 42 for ucase "W" at start to 25 for lcase 
"i" half-way through

so max hxw varies from 2184 for same ucase "W" to 250 for same lcase 
"i"

yet

so max hw varies from 6 for "l" 3 chars in to 0.96 for "n" at end
and max wh varies from 1.23 for ucase "W" at start to 0.40 for "l" 3 
chars in

280715
------

on ML

http://www.r2d3.us/visual-intro-to-machine-learning-part-1/

170915
------

so where to now?

1) Finish investigating size characteristics of the text we want to extract to guide our parameter choice

# for each of the 44 sample letters picked out above display the properties of the largest contour
# associated with each

VIEW - select * from adrc_letters_properties_of_max_contour;

dump out and analyse in a spreadsheet

adrc_letters_properties_of_max_contour.ods

?

2) What is involved in pulling non-textual information from the image

fundamentally there are STILL issues with extracting the candidates owing to not being able to adequately seperate the
characters from the rest of the map or from one another

Inverting the current problem where letters overrun background features, looking at what is involved in pulling non-textual features e.g. linear features from the map as these seem to be of interest and if we are able to isolate these reliably then this would aid the text extraction process since we can just extract them from the image prior to doing the OCR, maybe.

Pull all linework from the image as vectors

Peform spatial analysis on the vectors to identify lines which form hatches
 - i.e. lines that are parallel and within distance of other lines
  - draw an envelope / convex hull around the end points of these to

Having ran hatched_regions/./group_lines.py
  
SELECT distinct group_id,count(*)
FROM public.vectorised_polyline_simple
WHERE group_id > 0
GROUP BY group_id
HAVING count(*) > 5
ORDER BY group_id ASC;

/* generate convext hulls from the aggregate start/end point of each group */

SELECT s.group_id,st_convexhull(st_collect(s.all_start_points, s.all_end_points)) as geom
FROM
(
 SELECT
 group_id,
 st_collect(st_startpoint(geom)) as all_start_points,
 st_collect(st_endpoint(geom)) as all_end_points
 FROM public.vectorised_polyline_simple
 WHERE group_id IN 
 (
  SELECT group_id
  FROM public.vectorised_polyline_simple
  WHERE group_id > 0
  GROUP BY group_id
  HAVING COUNT(*) > 4
 )
 GROUP BY group_id
) s;

/* generate concave hulls from the aggregate start/end point of each group and calculate areal extent */

SELECT ss.group_id,ss.geom,st_area(ss.geom)
FROM
(
SELECT s.group_id,st_concavehull(st_collect(s.all_start_points, s.all_end_points),0.99) as geom
FROM
(
SELECT
group_id,
st_collect(st_startpoint(geom)) as all_start_points,
st_collect(st_endpoint(geom)) as all_end_points
FROM public.vectorised_polyline_simple
WHERE group_id IN 
(
SELECT group_id
FROM public.vectorised_polyline_simple
WHERE group_id > 0
GROUP BY group_id
HAVING COUNT(*) > 4
)
GROUP BY group_id
) s
) ss;

/*

SELECT 
st_extent(a.geom) AS total_extent,
sum(sss.parea) AS total_grp_area
FROM public.vectorised_polyline_simple a,
(
SELECT ss.group_id,ss.geom,st_area(ss.geom) as p_area
FROM
(
SELECT s.group_id,st_concavehull(st_collect(s.all_start_points, s.all_end_points),0.99) as geom
FROM
(
SELECT
group_id,
st_collect(st_startpoint(geom)) as all_start_points,
st_collect(st_endpoint(geom)) as all_end_points
FROM public.vectorised_polyline_simple
WHERE group_id IN 
(
SELECT group_id
FROM public.vectorised_polyline_simple
WHERE group_id > 0
GROUP BY group_id
HAVING COUNT(*) > 4
)
GROUP BY group_id
) s
) ss
) sss;

/* this returns the wrong answer as area of total ds seems too small for some reason
 * but this is what I hand in mind. So generate a polygon for each set of grouped lines
 * (more precise that generating a single polygon covering all lines), aggregate the
 * area of the ground covered by these and divide by the total area of the ground to
 * give a proportion of the ground that is covered by hatching and thus since this is
 * our proxy the proportion of "urban-ness"
**/ 

SELECT
(sum(sss.p_area) / st_area(st_extent(a.geom))) as prop_urban
FROM public.vectorised_polyline_simple a,
(
SELECT ss.group_id,ss.geom,st_area(ss.geom) as p_area
FROM
(
SELECT s.group_id,st_concavehull(st_collect(s.all_start_points, s.all_end_points),0.99) as geom
FROM
(
SELECT
group_id,
st_collect(st_startpoint(geom)) as all_start_points,
st_collect(st_endpoint(geom)) as all_end_points
FROM public.vectorised_polyline_simple
WHERE group_id IN 
(
SELECT group_id
FROM public.vectorised_polyline_simple
WHERE group_id > 0
GROUP BY group_id
HAVING COUNT(*) > 4
)
GROUP BY group_id
) s
) ss
) sss;

  
Outcome of the meeting with Chris + Chris on 160915
---------------------------------------------------

Seemed happy enough with what we are doing wrt to OCR of text / extracting other types of info from the map

Need to crack on with developing the training library
 Remember as well as size, font, weight also need to take account of cAsE...
  Would there be any benefit to us farming out the creation of the training library - getting others to eyeball and mark up samples
   paying folk to do this on amazon mechanical turk
     
To be honest we have pretty much overlooked the issue of rotation

Are there general OCR principles / best practices to cope with broken letters / lines through letters

By blue-space they mean rivers, lochs etc

If the hatched areas as proxy for urbanisation works could we combine with text extraction to decriminate between industrial and residential
 Are there other ways of descriminating industrial from urban - block size/shape/orientation
 
As well as extracting urban block, extract water and wooded areas (on basis that xmas tree symbols are readily extractable) and build up historic land-use maps to give a course measure of the landuse in the past
 
JRCC understanding is that JPearce when creating their historic greenspace maps work backwards from the current greenspace map doing subtraction of features - map differencing. Is there any scope for us to automate bits of this?
 Need to look at the greenspace data
 
I don`t need to attend the retreat - yay!
JR as "CI" does :)

150116
------

TODO

- need to normalise candidate regions by correcting rotation
 - unless the criteria we are using to compare candidates with training data is invarient to rotation
 
- can we actually implement  the hatched area detection without ArcScan using opencv?
 - line detection using
 
260116
------

We met Chris Dibben/Zhiqiang Feng at Farr Institute.
Zhiqiang`s minutes from the meeting are:

Updating progress and discussing plans of moving ahead.
So far capturing urban forms is quite promising, Text recognition is still a problem. 
Actions:
JR: send ZF the briefing document describing JC’s work so far.
JR: fill research fish, setting up milestones and completing other relevant outputs.
JC: carry out further work on urban form identification. Also explore feasibility of distinguishing residential/industrial landuse.
JC: Explore feasibility of capturing street names/locations from maps.
ZF: keep touch with JR/JC on work progress.
Next meeting 7th March, 3pm Drummond Street.



JC: carry out further work on urban form identification. Also explore feasibility of distinguishing residential/industrial landuse.
JC: Explore feasibility of capturing street names/locations from maps.

above added to redmine for tracking purposes

030216
------

# the geometries need to be single linestrings, so need to do:

SELECT AddGeometryColumn('adrc', 'big_thresholded_lines', 'new_geom', 27700, 'LINESTRING', 2);
UPDATE adrc.big_thresholded_lines SET new_geom = st_geometryn(geom, 1);
ALTER TABLE adrc.big_thresholded_lines RENAME COLUMN geom to old_geom;
ALTER TABLE adrc.big_thresholded_lines RENAME COLUMN new_geom to geom;
CREATE INDEX big_thresholded_lines_spidx ON adrc.big_thresholded_lines USING GIST ( geom );
UPDATE adrc.big_thresholded_lines SET group_id = 0;

# the table needs to have an azimuth column

ALTER TABLE adrc.big_thresholded_lines ADD COLUMN azimuth double precision;

# azimuth is referenced from north and is positive clockwise
# these will give difft results S----E  E----S 
# so vary choice by comparing dist of start/end point to origin
# presumably in some cases this will not work?

UPDATE adrc.big_thresholded_lines
SET azimuth = 
CASE 
 WHEN st_distance(st_setsrid(st_point(0,0), 27700), st_startpoint(geom)) < st_distance(st_setsrid(st_point(0,0), 27700), st_endpoint(geom))
 THEN degrees(st_azimuth(st_startpoint(geom),st_endpoint(geom)))
 ELSE degrees(st_azimuth(st_endpoint(geom),st_startpoint(geom)))
END;

# post-processing analysis in Pg

# pull out all groups of lines where group membership is >= some threshold e.g. 5

SELECT *
INTO adrc.big_thresholded_lines_selection_4
FROM adrc.big_thresholded_lines a
WHERE a.group_id in
(
 SELECT s.group_id
 FROM
 (
  SELECT DISTINCT group_id,count(*)
  FROM adrc.big_thresholded_lines
  WHERE group_id > 0
  GROUP BY group_id
  HAVING count(*) > 3
 )
 s
);

CREATE INDEX big_thresholded_lines_selection_4_spidx
ON adrc.big_thresholded_lines_selection_4
USING GIST (geom);


040216
------

used opencv to threshold:

/home/james/serviceDelivery/ADRC/NLS_samples/82877205.tif

ran gdal_translate to create a tif world files from the 82877205.tif geotiff for the thresholded file

in arctoolbox created a binary raster from the (with tfw) thresholded file 

in arccatalog created an empty polyline to hold the lines that arcscan will produce

in arcmap ran arcscan against the binary raster (it took ~30 mins) inserting lines into the empty polyline

arscan cannot be automated using native arcgis tools (i.e. geoprocessing/python scripts), so might be able to
do this using a windows automation tool like AutoIt by simulating mouse clicks/key presses/filling out forms etc

dumped the polylines out as a shapefile and loaded into Pg

did the above to create a linestring column / add azimuth column

ran group_lines.py - this took from 15:33:16 to 22:38:16 to group 210640 lines i.e. 7 hours

given the time involved will this scale (under the current approach)
highly likely the line grouping part can be speeded up but the need to use ArcScan going to be the bottleneck
 not sure how realistic it is to be able to replicate what ArcScan does using OpenCV
 
having grouped the lines:

SELECT group_id, st_convexhull(st_collect(geom)) as geom
FROM adrc.big_thresholded_lines_selection_4
GROUP BY group_id;

create a fishnet

SELECT ST_Collect(cells.geom)
FROM adrc.st_createfishnet(3, 3, 1000, 1000,325806,676166) AS cells;

200316
------


Since we`ve installed opencv 3 using:

http://www.pyimagesearch.com/2015/06/22/install-opencv-3-0-and-python-2-7-on-ubuntu/

we`ve done so using a virtualenv
so we`ll need to do our work in this project (copying the existing stuff over)

210316
------

http://hslpicker.com/

Hue - what colour? (shade of colour and where colour is found in the colour spectrum)
Saturation - how much colour? (how pure hue is with respect to a white reference)
 e.g. a color that is all red and no white is fully saturated
 if add some white to the red, the result becomes more pastel and color shifts from red to pink
 the hue is still red but has become less saturated
Value - how bright? (a relative description of how much light is coming from the color)
 e.g. a red car appears bright during the day but looks duller at night as less ambient light
 is reflected

(H)ue (S)aturation (V)alue 
= 
(H)ue (S)aturation (L)ightness
=
(H)ue (S)aturation (B)rightness

H+S gives colour information
V just gives lighting intensity

Using HSV we can remove V (intensity) and then don`t have to deal with large
variations of illumination

so can threshold only on H+S

(in GIMP)

H : degrees from 0 to 360
S : % 0 to 100 i.e. a pure red that has no white is 100% saturated
V : % 0 to 100 the amount of light illuminating a color. High value - looks bright, low value - looks dark


(in opencv)
 
BGR [0-255][0-255][0-255]
HSV [0-179][0-255][0-255]

So to convert H from GIMP to OpenCV / 2

Hue wraps round


/home/james/serviceDelivery/ADRC/NLS_samples/25K_210316/wetransfer-aa0da6

91578185.tif Pg myrasters.nls_91578185 (a)
vs
91578182.tif Pg myrasters.nls_91578182 (b)

b is more washed out than a
so the same road changes from a bright orange in a to a washed out orange in b
whilst buildings in a are a darker greenish grey whereas in b they are a much lighter grey

so BGR thresholds are sheet dependent and those computed for 1 sheet won`t apply to another sheet

need to look at using HSV instead as I think that will allow us to remove brightness and isolate based on Hue and Saturation
maybe..

so can we seperate features based purely on HS (and exclude V)?

230316
------

how exciting we can dump rasters out of Pg as PNG 

OK, fun over(!), back to work...

we got to:

/home/james/new_adrc/process_25k.py

250316
------

One workaround would be rather than aggregating the colour boundaries across all
map sheets to have colour boundaries per sheet. Creating the training data would
be painful though. Instead if we could guarantee that a feature that is present in
OSMM existed at the time of NLS 25K data (i.e. it is older than 1940) we could use
such a feature as a training region. So as an extreme example we could use the 50K
gaz to find a castle and use this to find a castle polygon on the OSMM?

280316
------

see https://www.planet.com/pulse/color-correction/

color correction is the process of adjusting raw image data so
that the resulting picture looks realistic

color correction - 3 aspects
 - brightness (the overall level of light in an image)
 - contrast (the relative light levels of adjacent areas)
 - color balancing (adjusting the overall hue of an image)
 
brightness and contrast together can be considered tonal
adjustments

Step 1 - adjust levels
Step 2 - find something white, for a point of reference, and
then set the relative maximum levels of the RGB channels so
that the surface that should be white is white, i.e. white is
255 255 255

290316
------

use process_25k.py split_to_hsv() to split RGB image into HSV components
 ~/Desktop/h_*.tif
 threshold the H (hue) component
  0 - 15 = Water Areas (holds for all images)
   doing the thresholding in GIMP
    we should though do the same using cv
     #TODO - come up with feature extraction process to identify the stipled regions
     
from ~/Desktop/h_91578185.tif (hue thresholded from 0-15 to pull out water areas)
 can we isolate Hailes Quarry (at extreme LL)?


300316
------

in experimentation there are some water bodies that don`t extract as perfect rings
can we use contour approximation / convex hulls as described here to cope with
"bad" shapes:

http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_imgproc/py_contours/py_contour_features/py_contour_features.html

050416
------

# grouping stiples:

http://workshops.boundlessgeo.com/postgis-intro/knn.html

Use KNN distance bounding-box operators to find closest stipple point to
another stipple point

seems to be quicker to construct the geom on the fly rather than pulling it
from the table

i.e. 12ms

12ms * 1007916 records = 12094992 = 3.35hrs
doing alternative way seems to take 35 days :)

select
 gid, st_distance(ST_SetSRID(ST_Point(323424.152710864,674394.234738909),27700), geom)
from adrc.nls_25k_stipple_points
where gid != 137669
order by
geom <-> ST_SetSRID(ST_Point(323424.152710864,674394.234738909),27700)
limit 1

# back to text extraction

having extracted the hatched areas, could we "subtract" these from the image
 to help with isolating text?
 
060416
------

further revisting text extraction, modified new_adrc/text_extractor.py to dump
mbr of contours as shapefile and contours properties as a csv file. (there must
be an easier way of doing this) Then (in Pg) joined the two and dumped a 
shapefile back out. This way we can (more easily than in Py):
 - plot the contour mbr features against the image with the full contours drawn
 - interrogate each contour
 - make selections / query the contours
 - select indv or groups of contours of interest (since we know id`s we can use
   these as part of future processing)
   

nls_82877433_contour_mbrs_selected_060416 is a selectionset formed according to
this criteria:

"AREA" < 5000
AND "H"  > 20
AND "H"  < 100
AND "ASPECTR" < 1.5
AND "ROUND_M" > 0.1
AND "SOLIDITY" < 0.8

somewhere between 060416 and 250416 (!)
---------------------------------------

we modified ~/new_adrc/library_development.py to include the new shape descriptors
and ran it non-interactively against /home/james/serviceDelivery/ADRC/NLS_samples/82877433.tif
with the above 6 thresholds producing the 24x42 png`s @ ~/geocrud/adrc

we then classified ALL of these (with the help of purge_skipped_samples.py)
producing ~/Desktop/training_sample_sets

which we reference in ~/Desktop/training_samples_080416.csv

250416
------

What we need to do at 80% over the next 6 weeks:

look @ everything but priorities are:

#15754 - discriminate between industrial and residential buildings
#15755 - extract railways
#15756 - investigate broader green space areas
 - OCR tree symbols
 - stippled open space areas
  - how universal (or not is the stippling of open space areas)

+

- revisit OCR process (to assist with #15754)
- revisit the color seperation process
 - find reference regions on (each) map sheet which we know should be a
   particular colour and then perform enhancement on a per-sheet basis
   to normalise all colours on that sheet. Reference regions could be
   features on the map that have persisted from the past through to the
   present day
   - using reference regions to calibrate (correct) images seems to be a
     common practice...
     - color balance / contrast
      - use reference with known optical property to estimate scene
        illuminant
        
        
  - http://mathematica.stackexchange.com/questions/77235/white-balance-correction-with-mathematica
   - histogram mean colour balance
    - transform the histogram of each colour channel to the same common mean
   - white area mean balanced colors


IPython / Jupyter
-----------------

@ /home/james
james@dlib-ngunnawal:~$ source py3dev/bin/activate
(py3dev)james@dlib-ngunnawal:~$ jupyter notebook
under folder py3dev click on jupyter_test.ipynb

250416
------

So back to doing something with ~/Desktop/training_sample_sets (see above)

as per https://redmine.edina.ac.uk/projects/adcr-s/wiki/Update_September_2015

need to run:
 
#TODO - modify text_extractor.py [dont think it produces the std 24x42 pngs] 
 it does now as *_sample.png images
  though we actually need to confirm what is being passed around internally

#TODO - modify prepare_training_samples_from_csv.py
 done  

#TODO - revisit knn_classify.py (other classifiers) 
 done - in move to opencv 3 a load of the API calls changed
  we did a classification where the training_data = candidates so not much of a test...
   but we need to check the tooling (still) works
    so ~/Desktop/classified/oak_2375.png = ~/geocrud/adrc/2375_sample.png
    
#TODO 

- create confusion matrix process
 - try modifying KNN params
- repeat above for unseen image
 - can we reliably pull off oak/xmas trees
 
260416
------

an alternative to digitising training regions would be to use seed pixels - a pixel
is selected that is representative of the surrounding area, then according to 
stats, pixels with similar spectral characteristics that are contiguous to the seed
pixel are selected and become the training samples

280416
------

~/Desktop/training_sample_sets was created from /home/james/serviceDelivery/ADRC/NLS_samples/82877433.tif

pick another /home/james/serviceDelivery/ADRC/NLS_samples/*.tif image (with lots of trees!) as an unseen image and try classifying based on the training set
 use 82877397.tif (new town etc)

290416
------

as a side, could we write a QGIS plugin/web-based tool to roll up the training-data collection?

100516
------

Extracting Railways

a) On the 25k railways are shown as alternating black/white dashed lines. When we run
process_25k.py to pull out black pixels corresponding to Special Buildings, it also
pulls out the black dashes using in railway lines.

b) extract_railways.py just finds all contours in (a) that have area between 50 and 200
   and creates a point shapefile with all the properties of that contour.
   
c) form_railways has a DashGrouper class that subclasses the LineGrouper class that
   we use to form groups of lines corresponding to hatched building regions
   
   the thinking being that we are doing the same kind of process
   
#TODO - when we form_railways by extending the line by adding a new point group
        membership is based on orientation of the line being similar to the last
        segment which was added. What do we do at the start or when we need to
        start forming a new group? - relying on manually setting the start candidate
        is not going to work...
       
 
 
 







 
 


    
   
   
   
  
 
 
 
 
 


  
 






  

  












 
 









   
     

     
     
      
 



















 



