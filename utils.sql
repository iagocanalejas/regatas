-- RETRIEVE TROPHIES/FLAGS WITH DIFFERENT LAPS/LANES/TOWNS/ORGANIZERS
SELECT id,
       date,
       type,
       race_name,
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
WHERE (SELECT count(DISTINCT laps) -- change here (laps | lanes | place_id | organizer_id)
       FROM race r2
       WHERE r.gender = r2.gender
         AND r.type = r2.type
         AND ((r.place_id IS NULL AND r2.place_id IS NULL) OR r.place_id = r2.place_id)  -- comment this to check
         AND ((r.league_id IS NULL AND r2.league_id IS NULL) OR r.league_id = r2.league_id)
         AND ((r.trophy_id IS NULL AND r2.trophy_id IS NULL) OR r.trophy_id = r2.trophy_id)
         AND ((r.flag_id IS NULL AND r2.flag_id IS NULL) OR r.flag_id = r2.flag_id)
         AND r2.type != 'TIME_TRIAL') > 1
        AND id NOT IN (SELECT id FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ilike '%PLAY%')) -- ignore play-offs
        AND type != 'TIME_TRIAL'
ORDER BY gender, trophy_id, trophy_edition, flag_id, flag_edition;

-- RETRIEVE PARTICIPANTS OF TIME TRIAL RACES WITH MORE THAN 1 LANE
SELECT *
FROM participant p1
WHERE (SELECT type FROM race WHERE race.id = p1.race_id) = 'TIME_TRIAL'
  AND (SELECT count(DISTINCT lane) FROM participant p2 WHERE p2.race_id = p1.race_id) > 1
  AND race_id NOT IN (SELECT id FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ilike '%PLAY%')) -- ignore play-offs
ORDER BY race_id;

-- RETRIEVE RACES WHERE THE NUMBER OF LANES IS DIFFERENT FROM THE EXPECTED NUMBER OF LANES (BASED ON THE NUMBER OF PARTICIPANTS)
SELECT id,
       date,
       type,
       cancelled,
       lanes,
       laps,
       race_name,
       trophy_id,
       trophy_edition,
       flag_id,
       flag_edition,
       league_id,
       place_id,
       gender,
       metadata
FROM race
WHERE (SELECT count(distinct lane) FROM participant WHERE race_id = race.id) <> lanes
  AND id NOT IN (SELECT id FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ilike '%PLAY%')) -- ignore play-offs
  AND (select count(p1.lane) FROM participant p1 WHERE race_id = race.id and lane is not null) > 1
ORDER BY date;

-- RETRIEVE RACES OF THE SAME LEAGUE/YEAR WITH DIFFERENT NUMBER OF PARTICIPANTS
SELECT id,
       date,
       type,
       lanes,
       laps,
       race_name,
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
    AND (SELECT count(*) FROM participant WHERE race_id = r.id and not guest)
        <> (SELECT max(cnt)
            FROM (SELECT COUNT(*) as cnt, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY COUNT(*) DESC) as seqnum
                FROM participant p JOIN race r1 ON p.race_id = r1.id
                WHERE not p.guest
                    AND r1.league_id = r.league_id
                    AND extract(YEAR FROM r1.date) = extract(YEAR FROM r.date)
                    AND r1.gender = r.gender
                    AND not r1.cancelled
                GROUP BY race_id
                ORDER BY cnt DESC) as cs
            WHERE seqnum = 1)
ORDER BY extract(YEAR FROM r.date) desc, league_id, date;

-- SPEEDS QUERY
SELECT r.date,
       r.metadata,
       p.club_name,
       p.laps,
       p.club_id,
       p.race_id,
       p.id,
       CAST((p.distance / (extract(EPOCH FROM p.laps[cardinality(p.laps)]))) * 3.6 AS DOUBLE PRECISION) as speed
--        extract(YEAR from date)::INTEGER as year,
--        array_agg(CAST((p.distance / (extract(EPOCH FROM p.laps[cardinality(p.laps)]))) * 3.6 AS DOUBLE PRECISION)) as speeds
FROM participant p
         JOIN race r ON p.race_id = r.id
WHERE p.laps <> '{}'
  AND not r.cancelled
  AND not exists(select * from penalty where participant_id = p.id and disqualification)
--   AND (p.gender = 'MALE' AND r.gender = 'MALE')
--   AND (p.category = 'ABSOLUT' AND r.category = 'ABSOLUT')
  AND (p.club_name IS NULL OR p.club_name <> '% B')
  AND r.league_id = 11
  AND (extract(EPOCH FROM p.laps[cardinality(p.laps)])) > 0
  AND extract(YEAR FROM r.date) = 2023
ORDER BY speed desc, extract(YEAR from date);
