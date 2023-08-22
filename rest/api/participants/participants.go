package participants

import (
	"log"

	"r4l/rest/db"

	sq "github.com/Masterminds/squirrel"
)

func GetParticipantsByRaceId(raceId string) ([]Participant, error) {
	query, args, err := sq.
		Select("p.id", "p.gender", "p.category", "p.distance", "p.laps", "p.lane", "p.series",
			"p.club_id as club_id", "e.name as club_name", "p.club_name as club_raw_name",
			"((SELECT count(*) FROM penalty pe WHERE pe.participant_id = p.id AND disqualification) > 0) as disqualified").
		From("participant p").
		LeftJoin("entity e ON p.club_id = e.id").
		Where(sq.Eq{"p.race_id": raceId}).
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
	participants := make([]Participant, len(flatParticipants))
	for idx, participant := range flatParticipants {
		participantIds[idx] = participant.ID
		participants[idx] = *NewParticipant(participant)
	}

	penalties, err := getPenaltiesByParticipantIds(participantIds)
	if err != nil {
		return nil, err
	}

	for idx, participant := range participants {
		var filtered []Penalty
		for _, penalty := range penalties {
			if penalty.ParticipantId == participant.ID {
				filtered = append(filtered, *NewPenalty(penalty))
			}
		}

		if len(filtered) > 0 {
			participant.Penalties = &filtered
			participants[idx] = participant
		}
	}

	return participants, nil
}

func getPenaltiesByParticipantIds(participantIds []int64) ([]db.Penalty, error) {
	query, args, err := sq.
		Select("p.participant_id", "p.reason", "p.penalty", "p.disqualification").
		From("penalty p").
		Where(sq.Eq{"p.participant_id": participantIds}).
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query, args)
		return nil, err
	}

	var penalties []db.Penalty
	err = db.GetDB().Select(&penalties, query, args...)
	if err != nil {
		return nil, err
	}

	return penalties, nil
}
