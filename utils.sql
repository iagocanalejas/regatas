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

-- RETRIEVE RACES FOR A GIVEN CLUB
SELECT *
FROM race
WHERE exists(SELECT * FROM participant WHERE race_id = race.id AND club_id = 25) -- change here
--   AND extract(YEAR from date) >= 2015
--   AND extract(YEAR from date) <= 2015
ORDER BY date;

-- RETRIEVE TROPHIES/FLAGS WITH DIFFERENT LAPS
SELECT id,
       date,
       type,
       race_name,
       trophy_id,
       trophy_edition,
       flag_id,
       flag_edition,
       league_id,
       laps,
       lanes,
       town,
       gender,
       metadata
FROM race r
WHERE (SELECT count(DISTINCT lanes) -- change here (laps | lanes | town | organizer)
       FROM race r2
       WHERE r.gender = r2.gender
         AND r.type = r2.type
         AND (r.trophy_id = r2.trophy_id AND r.flag_id = r2.flag_id)) > 1
ORDER BY trophy_id, trophy_edition, flag_id, flag_edition;

-- RETRIEVE PARTICIPANTS OF TIME TRIAL RACES WITH MORE THAN 1 LANE
SELECT *
FROM participant p1
WHERE (SELECT type FROM race WHERE race.id = p1.race_id) = 'TIME_TRIAL'
  AND (SELECT count(DISTINCT lane) FROM participant p2 WHERE p2.race_id = p1.race_id) > 1
ORDER BY race_id;
