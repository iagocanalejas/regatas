-- RETRIEVE RACES FILTERING BY DATASOURCE & YEAR
SELECT id,
       date,
       race_name,
       trophy_id,
       trophy_edition,
       flag_id,
       flag_edition,
       league_id,
       laps,
       lanes,
       town,
       type,
       gender,
       metadata
FROM race
WHERE extract(YEAR FROM date) = 2015
  AND metadata -> 'datasource' @> '[{"datasource_name": "abe"}]';

-- RETRIEVE TROPHIES/FLAGS WITH DIFFERENT LAPS
SELECT id,
       date,
       race_name,
       trophy_id,
       trophy_edition,
       flag_id,
       flag_edition,
       league_id,
       laps,
       lanes,
       town,
       type,
       gender,
       metadata
FROM race r
WHERE (SELECT count(distinct laps)
       FROM race r2
       WHERE r.gender = r2.gender
         AND (r.trophy_id = r2.trophy_id OR r.flag_id = r2.flag_id)) > 1
ORDER BY trophy_id, trophy_edition, flag_id, flag_edition;

-- TODO: command to find same trophy/flag races with different laps/lanes/towns
