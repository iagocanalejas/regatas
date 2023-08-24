package models

import "r4l/rest/db"

type Penalty struct {
	ParticipantId      int64   `json:"-"`
	Penalty            int     `json:"penalty"`
	IsDisqualification bool    `json:"disqualification"`
	Reason             *string `json:"reason"`
}

func (p Penalty) FromFatabase(penalty db.Penalty) *Penalty {
	return &Penalty{
		ParticipantId:      penalty.ParticipantId,
		Penalty:            penalty.Penalty,
		IsDisqualification: penalty.IsDisqualification,
		Reason:             penalty.Reason,
	}
}
