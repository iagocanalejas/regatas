package api

import (
	"log"

	"r4l/rest/db"
	"r4l/rest/models"

	sq "github.com/Masterminds/squirrel"
)

func GetParticipantsByRaceId(raceId string) ([]models.Participant, error) {
	query, args, err := sq.
		Select("p.id", "p.gender", "p.category", "p.distance", "p.laps", "p.lane", "p.series",
			"p.club_id as club_id", "e.name as club_name", "p.club_name as club_raw_name",
			"((SELECT count(*) FROM penalty pe WHERE pe.participant_id = p.id AND disqualification) > 0) as disqualified").
		From("participant p").
		LeftJoin("entity e ON p.club_id = e.id").
		Where(sq.Eq{"p.race_id": raceId}).
		OrderBy("p.laps[ARRAY_UPPER(p.laps, 1)] ASC").
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query, args)
		return nil, err
	}

	var flatParticipants []db.Participant
	err = db.GetDB().Select(&flatParticipants, query, args...)
	if err != nil {
		return nil, err
	}

	participantIds := make([]int64, len(flatParticipants))
	participants := make([]models.Participant, len(flatParticipants))
	for idx, participant := range flatParticipants {
		participantIds[idx] = participant.ID
		participants[idx] = *new(models.Participant).FromDatabase(participant)
	}

	penalties, err := GetPenaltiesByParticipantIds(participantIds)
	if err != nil {
		return nil, err
	}

	for idx, participant := range participants {
		var filtered []models.Penalty
		for _, penalty := range penalties {
			if penalty.ParticipantId == participant.ID {
				filtered = append(filtered, penalty)
			}
		}

		if len(filtered) > 0 {
			participant.Penalties = &filtered
			participants[idx] = participant
		}
	}

	return participants, nil
}
