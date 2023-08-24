package api

import (
	"log"
	"r4l/rest/db"
	"r4l/rest/models"

	sq "github.com/Masterminds/squirrel"
)

func GetPenaltiesByParticipantIds(participantIds []int64) ([]models.Penalty, error) {
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

	var flatPenalties []db.Penalty
	err = db.GetDB().Select(&flatPenalties, query, args...)
	if err != nil {
		return nil, err
	}

	penalties := make([]models.Penalty, len(flatPenalties))
	for idx, penalty := range flatPenalties {
		penalties[idx] = *new(models.Penalty).FromFatabase(penalty)
	}

	return penalties, nil
}
