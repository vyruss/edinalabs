# trying to understand what cv hierarchies actuallly are and how they work
# under different modes

[next, previous, first_child, parent]
or [h_next, h_prev, v_next, v_prev]

next denotes next contour at the same hierarchial level
previous denotes previous contour at the same hierarchial level
first_child denotes its first child contour
parent denotes index of its parent contour

if there is no child or parent, that field is taken as -1

mode = RETR_LIST
----------------

[[[ 1 -1 -1 -1]   i = 0 
  [ 2  0 -1 -1]   i = 1
  [ 3  1 -1 -1]   i = 2
  [ 4  2 -1 -1]   i = 3
  [ 5  3 -1 -1]   i = 4
  [-1  4 -1 -1]]] i = 5
  
retrieves ALL contours but does NOT create any parent-child relations
all contours belong to the same hierarchy level

so first_child/parent are always -1  

so for contour with index = 0
 next is contour with index = 1
 previous = -1 (there is no prev)
 
so for contour with index = 4
 next is contour with index = 5 (since in RETR_LIST there is no hierarchy)
 previous = 3
 
so for contour with index = 5
 next = -1 (there is no next)
 previous = 4
 
mode = RETR_EXTERNAL
--------------------

[[[ 1 -1 -1 -1]    i = 0
  [-1  0 -1 -1]]]  i = 1
  
returns only extreme outer contours, all child contours are left behind

so for contour with index = 0
 next is contour with index = 1
 previous = -1 (there is no prev) 
  
mode = RETR_CCOMP
-----------------
  
[[[ 1 -1 -1 -1]    i = 0
  [ 2  0 -1 -1]    i = 1
  [ 3  1 -1 -1]    i = 2  
  [ 5  2  4 -1]    i = 3
  [-1 -1 -1  3]    i = 4
  [-1  3 -1 -1]]]  i = 5
  
retrieves all contours and arranges them to a 2 level hierarchy
 external contours of the object (its external boundary) are placed in hierarchy 1
 contours of holes inside object are placed in hierarchy 2
 if any object inside it, its placed in hierarchy 1 only, and it`s hole in hierarchy2
 
Given an image of a big white zero on a black background - outer circle of zero would
be in first hierarchy and inner circle of zero would be in second hierarchy

mode = RETR_TREE
----------------
  
[[[ 5 -1  1 -1]
  [-1 -1  2  0]
  [ 3 -1 -1  1]
  [ 4  2 -1  1]
  [-1  3 -1  1]
  [-1  0 -1 -1]]]
  
SIMPLE EXAMPLE

RETR_LIST

[[[ 1 -1 -1 -1]
  [ 2  0 -1 -1]
  [ 3  1 -1 -1]
  [ 4  2 -1 -1]
  [-1  3 -1 -1]]]

RETR_EXTERNAL

[[[ 1 -1 -1 -1]
  [-1  0 -1 -1]]]
  
RETR_CCOMP

[[[ 2 -1  1 -1]   i = 0
  [-1 -1 -1  0]   i = 1
  [ 3  0 -1 -1]   i = 2
  [-1  2  4 -1]   i = 3
  [-1 -1 -1  3]]] i = 4 
  
RETR_TREE
  
[[[ 2 -1  1 -1]    i = 0
  [-1 -1 -1  0]    i = 1
  [-1  0  3 -1]    i = 2
  [-1 -1  4  2]    i = 3
  [-1 -1 -1  3]]]  i = 4

  


 
 

  
