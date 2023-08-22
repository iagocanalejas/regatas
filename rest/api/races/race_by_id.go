package races

import (
	"log"
	"net/http"

	"r4l/rest/api/participants"
	"r4l/rest/db"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func GetRaceById(ctx *gin.Context) {
	raceId := ctx.Param("raceId")

	query, args, err := sq.
		Select("r.id", "r.date", "r.day", "r.sponsor", "r.type", "r.modality", "r.laps", "r.lanes", "r.cancelled", "r.town",
			"t.id as trophy_id", "t.name as trophy_name", "r.trophy_edition",
			"f.id as flag_id", "f.name as flag_name", "r.flag_edition",
			"l.id as league_id", "l.name as league_name", "l.gender as league_gender", "l.symbol as league_symbol",
			"(SELECT ARRAY_AGG(DISTINCT(gender)) FROM participant WHERE race_id = r.id) as genders",
			"(SELECT MAX(series) FROM participant WHERE race_id = r.id) as series").
		From("race r").
		LeftJoin("trophy t ON r.trophy_id = t.id").
		LeftJoin("flag f ON r.flag_id = f.id").
		LeftJoin("league l ON r.league_id = l.id").
		Where(sq.Eq{"r.id": raceId}).
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query, args)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var flatRace db.Race
	err = db.GetDB().Get(&flatRace, query, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	participants, err := participants.GetParticipantsByRaceId(raceId)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	race := *NewRace(flatRace)
	race.Participants = participants

	ctx.JSON(http.StatusOK, race)
}
