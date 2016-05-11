CREATE TABLE earnings (
    median DECIMAL(8,3),
    area   VARCHAR);

CREATE TABLE house (
    median INTEGER,
    const  VARCHAR);

CREATE TABLE simd (
    vigintile INTEGER,
    zone      VARCHAR,
    const     VARCHAR);

CREATE TABLE results_const (
    const     VARCHAR,
    con2011   NUMERIC(3,1),
    lab2011   NUMERIC(3,1),
    ld2011    NUMERIC(3,1),
    snp2011   NUMERIC(3,1),
    ind2011   NUMERIC(3,1),
    other2011 NUMERIC(3,1),
    con2016   NUMERIC(3,1),
    lab2016   NUMERIC(3,1),
    ld2016    NUMERIC(3,1),
    snp2016   NUMERIC(3,1),
    ind2016   NUMERIC(3,1),
    other2016 NUMERIC(3,1));

CREATE TABLE results_region (
    region    VARCHAR,
    lab2011   NUMERIC(3,1),
    snp2011   NUMERIC(3,1),
    ld2011    NUMERIC(3,1),
    con2011   NUMERIC(3,1),
    gre2011   NUMERIC(3,1),
    margo2011 NUMERIC(3,1),
    lab2016   NUMERIC(3,1),
    snp2016   NUMERIC(3,1),
    ld2016    NUMERIC(3,1),
    con2016   NUMERIC(3,1),
    gre2016   NUMERIC(3,1),
    margo2016 NUMERIC(3,1));


CREATE OR REPLACE VIEW council_earnings AS
SELECT co.*, median
FROM district_borough_unitary_region co
JOIN earnings ON "CODE" = area;

CREATE OR REPLACE VIEW const_house AS
SELECT cr.*, median
FROM scotland_and_wales_const_region cr
JOIN house ON "CODE" = const;

CREATE OR REPLACE VIEW const_simd AS
WITH foo AS (SELECT const, count(zone) AS simd
             FROM simd
             WHERE vigintile <= 3 -- top 15% most deprived
             GROUP BY const)
SELECT cr.*, foo.simd
FROM scotland_and_wales_const_region cr
JOIN foo ON "CODE" = const;

CREATE OR REPLACE VIEW res_const AS
SELECT *
FROM scotland_and_wales_const_region
JOIN results_const ON "CODE" = const;

CREATE OR REPLACE VIEW res_region AS
SELECT *
FROM scotland_and_wales_region_region
JOIN results_region ON "CODE" = region;
