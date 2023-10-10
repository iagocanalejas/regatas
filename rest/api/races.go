package api

import (
	"fmt"
	"log"
	"math"
	"net/http"
	"strconv"
	"strings"

	"r4l/rest/db"
	"r4l/rest/forms"
	"r4l/rest/models"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func GetRaces(ctx *gin.Context) {
	filters := parseFilters(ctx)

	query, countQuery, args, err := filterQuery(filters)
	if err != nil {
		log.Print(query, args)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var flatRaces []db.Race
	err = db.GetDB().Select(&flatRaces, query, args...)
	if err != nil {
		log.Print(query, args)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var count int
	err = db.GetDB().Get(&count, countQuery, args...)
	if err != nil {
		log.Print(countQuery, args)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	races := make([]models.Race, len(flatRaces))
	for idx, race := range flatRaces {
		races[idx] = *new(models.Race).FromDatabase(race)
	}

	ctx.JSON(http.StatusOK, gin.H{
		"results": races,
		"pagination": gin.H{
			"current_page":  filters.Page,
			"page_size":     filters.Limit,
			"total_records": count,
			"total_pages":   math.Ceil(float64(count) / float64(filters.Limit)),
		},
	})
}

func GetRaceById(ctx *gin.Context) {
	raceId := ctx.Param("raceId")

	query, args, err := sq.
		Select("r.id", "r.date", "r.day", "r.sponsor", "r.type", "r.modality", "r.laps", "r.lanes", "r.cancelled", "r.town",
			"r.associated_id", "r.metadata",
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

	participants, err := GetParticipantsByRaceId(raceId)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	race := *new(models.Race).FromDatabase(flatRace)
	race.Participants = participants

	ctx.JSON(http.StatusOK, race)
}

func parseFilters(ctx *gin.Context) forms.RaceFilters {
	filters := forms.RaceFilters{
		Keywords: ctx.DefaultQuery("keywords", ""),
	}
	filters.Year, _ = strconv.ParseInt(ctx.DefaultQuery("year", ""), 10, 64)
	filters.Trophy, _ = strconv.ParseInt(ctx.DefaultQuery("trophy", ""), 10, 64)
	filters.Flag, _ = strconv.ParseInt(ctx.DefaultQuery("flag", ""), 10, 64)
	filters.League, _ = strconv.ParseInt(ctx.DefaultQuery("league", ""), 10, 64)
	filters.Participant, _ = strconv.ParseInt(ctx.DefaultQuery("participant", ""), 10, 64)
	filters.Page, _ = strconv.ParseInt(ctx.DefaultQuery("page", "0"), 10, 64)
	filters.Limit, _ = strconv.ParseInt(ctx.DefaultQuery("limit", "100"), 10, 64)

	maybeTrophyOrFlag := strings.Split(ctx.DefaultQuery("trophyOrFlag", ","), ",")
	if len(maybeTrophyOrFlag) == 2 {
		trophyOrFlag := make([]int64, 2)
		for idx, item := range maybeTrophyOrFlag {
			trophyOrFlag[idx], _ = strconv.ParseInt(item, 10, 64)
		}
		filters.TrophyOrFlag = trophyOrFlag
	}

	return filters
}

func filterQuery(filters forms.RaceFilters) (string, string, []interface{}, error) {
	baseSelect := sq.
		Select("r.id", "r.date", "r.day", "r.sponsor", "r.type", "r.modality", "r.laps", "r.lanes", "r.cancelled", "r.town",
			"t.id as trophy_id", "t.name as trophy_name", "r.trophy_edition",
			"f.id as flag_id", "f.name as flag_name", "r.flag_edition",
			"l.id as league_id", "l.name as league_name", "l.gender as league_gender", "l.symbol as league_symbol").
		From("race r").
		LeftJoin("trophy t ON r.trophy_id = t.id").
		LeftJoin("flag f ON r.flag_id = f.id").
		LeftJoin("league l ON r.league_id = l.id")

	if filters.Keywords != "" {
		baseSelect = baseSelect.Where(sq.Or{
			sq.ILike{"t.name": fmt.Sprint("%", filters.Keywords, "%")},
			sq.ILike{"f.name": fmt.Sprint("%", filters.Keywords, "%")},
			sq.ILike{"sponsor": fmt.Sprint("%", filters.Keywords, "%")},
		})
	}

	if filters.Year > 0 {
		baseSelect = baseSelect.Where(sq.Eq{"EXTRACT(YEAR FROM r.date)": filters.Year})
	}

	if filters.Trophy > 0 {
		baseSelect = baseSelect.Where(sq.And{
			sq.NotEq{"r.trophy_id": nil},
			sq.Eq{"r.trophy_id": filters.Trophy},
		})
	}

	if filters.Flag > 0 {
		baseSelect = baseSelect.Where(sq.And{
			sq.NotEq{"r.flag_id": nil},
			sq.Eq{"r.flag_id": filters.Flag},
		})
	}

	if filters.TrophyOrFlag[0] > 0 && filters.TrophyOrFlag[1] > 0 {
		baseSelect = baseSelect.Where(sq.Or{
			sq.And{
				sq.NotEq{"r.trophy_id": nil},
				sq.Eq{"r.trophy_id": filters.TrophyOrFlag[0]},
			},
			sq.And{
				sq.NotEq{"r.flag_id": nil},
				sq.Eq{"r.flag_id": filters.TrophyOrFlag[1]},
			},
		})
	}

	if filters.League > 0 {
		baseSelect = baseSelect.Where(sq.And{
			sq.NotEq{"r.league_id": nil},
			sq.Eq{"r.league_id": filters.League},
		})
	}

	if filters.Participant > 0 {
		subQ := fmt.Sprint("EXISTS(SELECT 1 FROM participant p WHERE p.race_id = r.id AND p.club_id = ", filters.Participant, ")")
		baseSelect = baseSelect.Where(subQ)
	}

	query, args, err := baseSelect.
		OrderBy("date DESC").
		Limit(uint64(filters.Limit)).Offset(uint64(filters.Page) * uint64(filters.Limit)).
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query, args)
		return "", "", nil, err
	}

	countQuery, _, err := sq.
		Select("COUNT(*)").
		FromSelect(baseSelect, "count").
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query, args)
		return "", "", nil, err
	}

	return query, countQuery, args, nil
}
