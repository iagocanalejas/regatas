package db

import "github.com/lib/pq"

type Race struct {
	ID int64 `db:"id"`

	TrophyId      *int64  `db:"trophy_id"`
	TrophyName    *string `db:"trophy_name"`
	TrophyEdition *int    `db:"trophy_edition"`

	FlagId      *int64  `db:"flag_id"`
	FlagName    *string `db:"flag_name"`
	FlagEdition *int    `db:"flag_edition"`

	LeagueId     *int64  `db:"league_id"`
	LeagueName   *string `db:"league_name"`
	LeagueGender *string `db:"league_gender"`
	LeagueSymbol *string `db:"league_symbol"`

	Day      int    `db:"day"`
	Date     string `db:"date"`
	Type     string `db:"type"`
	Modality string `db:"modality"`

	Laps        *int `db:"laps"`
	Lanes       *int `db:"lanes"`
	Series      *int `db:"series"`
	IsCancelled bool `db:"cancelled"`

	Genders pq.StringArray `db:"genders"`
	Sponsor *string        `db:"sponsor"`
	Town    *string        `db:"town"`
}

type Participant struct {
	ID int64 `db:"id"`

	Gender   string `db:"gender"`
	Category string `db:"category"`
	Distance int    `db:"distance"`

	ClubId      int64   `db:"club_id"`
	ClubName    string  `db:"club_name"`
	ClubRawName *string `db:"club_raw_name"`

	IsDisqualified bool `db:"disqualified"`

	Laps   pq.StringArray `db:"laps"`
	Lane   *int           `db:"lane"`
	Series *int           `db:"series"`
}

type Penalty struct {
	ParticipantId      int64   `db:"participant_id"`
	Penalty            int     `db:"penalty"`
	IsDisqualification bool    `db:"disqualification"`
	Reason             *string `db:"reason"`
}
