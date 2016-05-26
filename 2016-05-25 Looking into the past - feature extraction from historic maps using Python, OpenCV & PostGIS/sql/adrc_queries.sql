{% sql 'get_training_regions', note='query to retrieve the gid`s of the captured training regions' %}
    SELECT gid,ftype
    FROM {{vector_name}}
    WHERE raster_src='{{raster_src}}'
{% endsql %}
{% sql 'get_zonal_statistics', note='query to do a vector on raster overlay by training region' %}
    SELECT sss.gid,min(sss.value),max(sss.value)
    FROM
    (
     SELECT ss.*
     FROM
     (
      SELECT s.gid,(st_valuecount(s.clipped_raster, {{band_id}},true)).*
      FROM
      (
       SELECT a.gid,st_clip(b.rast, a.geom,true) as clipped_raster
       FROM
       {{vector_name}} a,
       {{raster_name}} b
       WHERE a.gid = {{sample_region_id}}
      ) s
     ) ss
     WHERE ss.value > 0
     ORDER BY COUNT DESC
     LIMIT 10
    ) sss
    GROUP BY sss.gid
{% endsql %}
{% sql 'get_neighbour', note='query to find the next neigbouring line' %}
    SELECT b.gid
    FROM {{srcTableName}} a, {{srcTableName}} b
    WHERE a.gid = {{id}}
    AND st_dwithin(st_lineinterpolatepoint(a.geom, 0.5),b.geom, {{searchDistance}})
    AND st_disjoint(a.geom, b.geom)
    AND abs(a.azimuth - b.azimuth) < {{searchAngleDelta}}
    AND a.gid != b.gid
    AND (
     (
      (st_x(st_endpoint(a.geom)) - st_x(st_startpoint(a.geom)))
      *
      (st_y(st_lineinterpolatepoint(b.geom, 0.5)) - st_y(st_startpoint(a.geom)))
     ) -
     (
      (st_y(st_endpoint(a.geom)) - st_y(st_startpoint(a.geom)))
      *
      (st_x(st_lineinterpolatepoint(b.geom, 0.5)) - st_x(st_startpoint(a.geom)))
     )
     ) {{searchDirection}} 0
    AND b.group_id = 0
{% endsql %}
{% sql 'get_ungrouped_lines', note='query to find the gids of all ungrouped lines' %}
    SELECT gid FROM {{table_name}} WHERE group_id = 0
{% endsql %}
{% sql 'drop_table', note='drops the _selection_4 table' %}
    DROP TABLE IF EXISTS {{table_name}} CASCADE"
{% endsql %}
{% sql 'select_groups_into_new_table', note='create new table from grouped lines' %}
    SELECT *
    INTO {{destTableName}}
    FROM {{srcTableName}} a
    WHERE a.group_id in
    (
     SELECT s.group_id
     FROM
     (
      SELECT DISTINCT group_id,count(*)
      FROM {{srcTableName}}
      WHERE group_id > 0
      GROUP BY group_id
      HAVING count(*) > 3
     )
    s
    )
{% endsql %}
{% sql 'set_group_id', note='sets the group id for a given gid' %}
    UPDATE {{tableName}}
    SET group_id = {{groupId}}
    WHERE gid = {{gid}}
{% endsql %}
{% sql 'reset_groups', note='set the group_id of all lines to 0' %}
    UPDATE {{table_name}} SET group_id = 0
{% endsql %}