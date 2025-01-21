------------------------------------------------------------------------------------------------------------------------
-- RETRIEVE PARTICIPANTS OF TIME TRIAL RACES WITH MORE THAN 1 LANE
------------------------------------------------------------------------------------------------------------------------
SELECT *
FROM participant p
WHERE (SELECT type FROM race WHERE race.id = p.race_id) = 'TIME_TRIAL'  -- race is a time_trial
  AND (SELECT count(DISTINCT lane) FROM participant p2 WHERE p2.race_id = p.race_id) > 1  -- more than one lane found
  AND race_id NOT IN (SELECT id FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ilike '%PLAY%')) -- ignore play-offs
ORDER BY race_id;

------------------------------------------------------------------------------------------------------------------------
-- RETRIEVE PARTICIPANTS WITH NO LAPS
------------------------------------------------------------------------------------------------------------------------
SELECT p.*, r.metadata
FROM participant p JOIN race r ON p.race_id = r.id
WHERE p.laps = '{}'
  -- AND r.id not in (2189)
  AND NOT absent
  AND NOT retired
  AND NOT cancelled
  AND NOT EXISTS(SELECT 1 FROM penalty WHERE participant_id = p.id); -- ignore participants with penalties

------------------------------------------------------------------------------------------------------------------------
-- RETRIEVE TROPHIES/FLAGS WITH DIFFERENT LAPS/LANES/TOWNS/ORGANIZERS
------------------------------------------------------------------------------------------------------------------------
SELECT id,
       date,
       type,
       race_names,
       trophy_id,
       trophy_edition,
       flag_id,
       flag_edition,
       league_id,
       organizer_id,
       place_id,
       laps,
       lanes,
       gender,
       metadata
FROM race r
WHERE type != 'TIME_TRIAL'
  AND id NOT IN (SELECT id FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ilike '%PLAY%')) -- ignore play-offs
  AND (SELECT count(DISTINCT laps) -- change here (laps | lanes | place_id | organizer_id)
       FROM race r2
       WHERE r.gender = r2.gender
         AND r.type = r2.type
         AND ((r.place_id IS NULL AND r2.place_id IS NULL) OR r.place_id = r2.place_id)
         AND ((r.league_id IS NULL AND r2.league_id IS NULL) OR r.league_id = r2.league_id)
         AND ((r.trophy_id IS NULL AND r2.trophy_id IS NULL) OR r.trophy_id = r2.trophy_id)
         AND ((r.flag_id IS NULL AND r2.flag_id IS NULL) OR r.flag_id = r2.flag_id)
         AND r2.type != 'TIME_TRIAL') > 1
ORDER BY gender, trophy_id, trophy_edition, flag_id, flag_edition;

------------------------------------------------------------------------------------------------------------------------
-- RETRIEVE RACES WHERE THE NUMBER OF LANES IS DIFFERENT FROM THE EXPECTED NUMBER OF LANES (NUMBER OF PARTICIPANTS)
------------------------------------------------------------------------------------------------------------------------
SELECT id,
       date,
       type,
       cancelled,
       lanes,
       laps,
       race_names,
       trophy_id,
       trophy_edition,
       flag_id,
       flag_edition,
       league_id,
       place_id,
       gender,
       metadata
FROM race
WHERE (SELECT count(distinct lane) FROM participant WHERE race_id = race.id) != lanes  -- number of lanes is different from the number of different lanes
  AND id NOT IN (SELECT id FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ILIKE '%PLAY%')) -- ignore play-offs
  AND (SELECT count(p1.lane) FROM participant p1 WHERE race_id = race.id AND lane IS NOT NULL) > 1  -- ensure some participants have lane information
ORDER BY date;

------------------------------------------------------------------------------------------------------------------------
-- RETRIEVE RACES OF THE SAME LEAGUE/YEAR WITH DIFFERENT NUMBER OF PARTICIPANTS
------------------------------------------------------------------------------------------------------------------------
SELECT id,
       date,
       type,
       lanes,
       laps,
       race_names,
       trophy_id,
       trophy_edition,
       flag_id,
       flag_edition,
       league_id,
       place_id,
       gender,
       metadata
FROM race r
WHERE NOT r.cancelled
    AND league_id NOT IN (14, 15) -- ignore veteran leagues as they are a mess
    AND date NOT IN (SELECT date FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ilike '%PLAY%')) -- ignore races in play-off days
    AND (SELECT count(*) FROM participant WHERE race_id = r.id and not guest) -- number of participants in current race
        <> (SELECT max(cnt)
            FROM (SELECT COUNT(*) AS cnt, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY COUNT(*) DESC) AS seqnum
                FROM participant p JOIN race r1 ON p.race_id = r1.id
                WHERE NOT p.guest
                    AND r1.league_id = r.league_id
                    AND r1.gender = r.gender
                    AND EXTRACT(YEAR FROM r1.date) = EXTRACT(YEAR FROM r.date)
                    AND NOT r1.cancelled
                GROUP BY race_id
                ORDER BY cnt DESC) AS cs
            WHERE seqnum = 1)  -- maximum number of participants for a race matching year, league and gender
ORDER BY EXTRACT(YEAR FROM r.date) DESC, league_id, date;

------------------------------------------------------------------------------------------------------------------------
-- RETRIEVE RACES WHERE TWO PARTICIPANTS HAVE THE SAME TIME
------------------------------------------------------------------------------------------------------------------------
SELECT p1.club_id, p1.club_names, p1.laps[array_length(p1.laps, 1)], r.*
FROM race r
    JOIN participant p1 ON p1.race_id = r.id
WHERE EXISTS(
    SELECT 1
    FROM participant p2
    WHERE p1.laps <> '{}'
       AND EXTRACT(EPOCH FROM p1.laps[array_length(p1.laps, 1)]) > 0
       AND p2.race_id = r.id
       AND p2.id != p1.id
       AND to_char(p1.laps[array_length(p1.laps, 1)], 'MI:SS.MS') = to_char(p2.laps[array_length(p2.laps, 1)], 'MI:SS.MS')
)
ORDER BY r.id;

------------------------------------------------------------------------------------------------------------------------
-- RETRIEVE RACES WHERE ALL PARTICIPANTS MATCH AND HAVE THE SAME TIMES
------------------------------------------------------------------------------------------------------------------------
WITH race_data AS (
    -- Step 1: Gather race ID, count of participants, participant club IDs, and their times
    -- sorted by club ID to ensure consistent ordering for comparison.
    SELECT
        r.id AS race_id,
        r.same_as_id AS same_as_id,
        COUNT(p.id) AS num_participants,
        ARRAY_AGG(p.club_id ORDER BY p.club_id) AS participant_club_ids,
        ARRAY_AGG(extract(EPOCH FROM p.laps[array_length(p.laps, 1)]) ORDER BY p.club_id) AS participant_times
    FROM race r JOIN participant p ON r.id = p.race_id
    GROUP BY r.id
),
matching_races AS (
     -- Step 2: Find matching races by comparing participant and time arrays
     -- We compare races to find those with the same number of participants, same participant club IDs,
     -- and identical finish times. Races with the same set of participants and times are considered "matching."
    SELECT
        r1.race_id AS original_race_id,
        r2.race_id AS matching_race_id
    FROM race_data r1 JOIN race_data r2
            ON r1.num_participants = r2.num_participants  -- Ensure the races have the same number of participants
                AND r1.participant_club_ids = r2.participant_club_ids  -- Ensure the races have the same participant club IDs
                AND r1.participant_times = r2.participant_times  -- Ensure the participants have the same times
                AND r1.race_id != r2.race_id  -- Exclude the current race itself from the matching process
                AND (r2.same_as_id IS NULL OR r1.race_id != r2.same_as_id)  -- Exclude the races that are marked as the same
)
-- Step 3: Select races and any matching race IDs
SELECT
    COALESCE(ARRAY_AGG(r2.id), '{}') AS matching_race_ids,
    r1.*
FROM race r1
         LEFT JOIN matching_races mr ON r1.id = mr.original_race_id
         LEFT JOIN race r2 ON mr.matching_race_id = r2.id
WHERE r2.id IS NOT NULL  -- Filter out cases where there are no matches
GROUP BY r1.id;

------------------------------------------------------------------------------------------------------------------------
-- SPEEDS QUERY
------------------------------------------------------------------------------------------------------------------------
SELECT extract(YEAR from date)::INTEGER AS year,
       CAST((p.distance / (extract(EPOCH FROM p.laps[cardinality(p.laps)]))) * 3.6 AS DOUBLE PRECISION) AS speed
FROM participant p JOIN race r ON p.race_id = r.id
WHERE p.laps <> '{}'
  AND NOT r.cancelled
  AND NOT exists(SELECT * FROM penalty WHERE participant_id = p.id AND disqualification)
--   AND (p.gender = 'MALE' AND r.gender = 'MALE')
--   AND (p.category = 'ABSOLUT' AND r.category = 'ABSOLUT')
  AND (p.club_names = '{}' OR NOT EXISTS(SELECT 1 FROM unnest(p.club_names) AS club_name WHERE club_name LIKE '% B'))
  AND r.league_id = 11
  AND (extract(EPOCH FROM p.laps[cardinality(p.laps)])) > 0
  AND extract(YEAR FROM r.date) = 2023
ORDER BY speed DESC, extract(YEAR from date);
