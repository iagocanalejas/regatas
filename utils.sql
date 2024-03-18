-- RETRIEVE TROPHIES/FLAGS WITH DIFFERENT LAPS
SELECT id, date, race_name, trophy_id, trophy_edition, flag_id, flag_edition, league_id, laps, lanes, town, type, gender
FROM race r
WHERE (
	SELECT count(distinct laps)
	FROM race r2
	WHERE r.gender = r2.gender AND (r.trophy_id = r2.trophy_id OR r.flag_id = r2.flag_id)
	) > 1
ORDER BY trophy_id, trophy_edition, flag_id, flag_edition;

-- RETRIEVE RACES FILTERING BY METADATA DATASOURCE
SELECT *
FROM race
WHERE extract(YEAR from date) = 2015
	and metadata->'datasource' @> '[{"datasource_name": "abe"}]';

-- TODO: command to find same trophy/flag races with different laps/lanes/towns
