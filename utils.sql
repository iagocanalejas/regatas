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
  AND race_id NOT IN (SELECT id FROM race WHERE race.trophy_id IN (SELECT id FROM trophy WHERE name ilike '%PLAY%')) -- ignore play-offs
ORDER BY race_id;

-- RETRIEVE RACES WHERE THE NUMBER OF LANES IS DIFFERENT FROM THE EXPECTED NUMBER OF LANES (BASED ON THE NUMBER OF PARTICIPANTS)
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
       town,
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
       town,
       gender,
       metadata
FROM race r
WHERE not r.cancelled
  AND (SELECT count(*) FROM participant WHERE race_id = r.id)
          <> (SELECT max(cnt)
              FROM (SELECT COUNT(*) as cnt, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY COUNT(*) DESC) as seqnum
                    FROM participant p JOIN race r1 ON p.race_id = r1.id
                    WHERE r1.league_id = r.league_id
                      AND extract(YEAR FROM r1.date) = extract(YEAR FROM r.date)
                      AND r1.gender = r.gender
                      AND not r1.cancelled
                    GROUP BY race_id
                    ORDER BY cnt DESC) as cs
              WHERE seqnum = 1)
ORDER BY extract(YEAR FROM r.date), league_id, date;
