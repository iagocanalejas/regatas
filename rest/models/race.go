package models

import (
	"fmt"
	"strings"
	"time"

	"r4l/rest/db"
	"r4l/rest/utils"
)

type Race struct {
	ID   int64  `json:"id"`
	Name string `json:"name"`

	Trophy *Trophy `json:"trophy"`
	Flag   *Flag   `json:"flag"`
	League *League `json:"league"`

	Day      int    `json:"day"`
	Date     string `json:"date"`
	Type     string `json:"type"`
	Modality string `json:"modality"`

	Laps        *int `json:"laps"`
	Lanes       *int `json:"lanes"`
	Series      *int `json:"series"`
	IsCancelled bool `json:"cancelled"`

	Sponsor *string  `json:"sponsor"`
	Town    *string  `json:"town"`
	Genders []string `json:"genders"`

	Participants []Participant `json:"participants,omitempty"`
}

func (r Race) FromDatabase(race db.Race) *Race {
	var trophy *Trophy
	if race.TrophyId != nil {
		trophy = &Trophy{ID: *race.TrophyId, Name: *race.TrophyName, Edition: race.TrophyEdition}
	}

	var flag *Flag
	if race.FlagId != nil {
		flag = &Flag{ID: *race.FlagId, Name: *race.FlagName, Edition: race.FlagEdition}
	}

	var league *League
	if race.LeagueId != nil {
		league = &League{ID: *race.LeagueId, Name: *race.LeagueName, Gender: race.LeagueGender, Symbol: *race.LeagueSymbol}
	}

	date, _ := time.Parse(time.RFC3339, race.Date)
	return &Race{
		ID:   race.ID,
		Name: buildRaceName(race),

		Trophy: trophy,
		Flag:   flag,
		League: league,

		Day:      race.Day,
		Date:     date.Format("02-01-2006"),
		Type:     race.Type,
		Modality: race.Modality,

		Laps:        race.Laps,
		Lanes:       race.Lanes,
		Series:      race.Series,
		IsCancelled: race.IsCancelled,

		Sponsor: race.Sponsor,
		Town:    race.Town,
		Genders: race.Genders,
	}
}

func buildRaceName(race db.Race) string {
	day := ""
	if race.Day > 1 {
		day = fmt.Sprintf("XORNADA %d", race.Day)
	}

	gender := ""
	if utils.ContainsString(race.Genders, "FEMALE") || (race.LeagueGender != nil && *race.LeagueGender == "FEMALE") {
		gender = "(FEMENINA)"
	}

	trophy := ""
	if race.TrophyId != nil && *race.TrophyEdition > 0 {
		trophy = fmt.Sprintf("%s - %s", utils.Int2Roman(*race.TrophyEdition), *race.TrophyName)
		trophy = strings.Replace(trophy, "(CLASIFICATORIA)", "", -1)
	}

	flag := ""
	if race.FlagId != nil && *race.FlagEdition > 0 {
		flag = fmt.Sprintf("%s - %s", utils.Int2Roman(*race.FlagEdition), *race.FlagName)
	}

	sponsor := ""
	if race.Sponsor != nil {
		sponsor = *race.Sponsor
	}

	nameParts := []string{trophy, flag, sponsor}
	var filteredParts []string
	for _, part := range nameParts {
		if part != "" {
			filteredParts = append(filteredParts, part)
		}
	}
	name := strings.Join(filteredParts, " - ")

	return strings.TrimSpace(fmt.Sprintf("%s %s %s", name, day, gender))
}