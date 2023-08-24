package models

import (
	"r4l/rest/db"
)

type Participant struct {
	ID int64 `json:"id"`

	Gender   string `json:"gender"`
	Category string `json:"category"`
	Distance int    `json:"distance"`

	Club *Entity `json:"club"`

	IsDisqualified bool `json:"disqualified"`

	Laps   []string `json:"laps"`
	Lane   *int     `json:"lane"`
	Series *int     `json:"series"`

	Penalties *[]Penalty `json:"penalties"`
}

func (p Participant) FromDatabase(participant db.Participant) *Participant {
	club := &Entity{
		ID:      participant.ClubId,
		Name:    participant.ClubName,
		RawName: participant.ClubRawName,
	}

	return &Participant{
		ID: participant.ID,

		Gender:   participant.Gender,
		Category: participant.Category,
		Distance: participant.Distance,

		Club: club,

		IsDisqualified: false,

		Laps:   participant.Laps,
		Lane:   participant.Lane,
		Series: participant.Series,

		Penalties: &[]Penalty{},
	}
}
