package races

import (
	"fmt"
	"log"
	"math"
	"net/http"
	"strconv"

	"r4l/rest/api"
	"r4l/rest/db"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

type RaceFilters struct {
	Keywords string
	Year     int64
	League   int64
	Trophy   int64
	Flag     int64
	Page     int64
	Limit    int64
}

func buildRacesQuery(ctx *gin.Context, filters RaceFilters) (string, string, []interface{}) {
	baseSelect := sq.
		Select("r.id", "r.date", "r.day", "r.sponsor", "r.type", "r.modality", "r.laps", "r.lanes", "r.cancelled",
			"t.id as trophy_id", "t.name as trophy_name", "r.trophy_edition",
			"f.id as flag_id", "f.name as flag_name", "r.flag_edition",
			"l.id as league_id", "l.name as league_name", "l.gender as league_gender", "l.symbol as league_symbol",
			"(SELECT ARRAY_AGG(DISTINCT(gender)) FROM participant WHERE race_id = r.id) as genders").
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

	if filters.League > 0 {
		baseSelect = baseSelect.Where(sq.And{
			sq.NotEq{"r.league_id": nil},
			sq.Eq{"r.league_id": filters.League},
		})
	}

	query, args, err := baseSelect.
		OrderBy("date DESC").
		Limit(uint64(filters.Limit)).Offset(uint64(filters.Page) * uint64(filters.Limit)).
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query, args)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	countQuery, _, err := sq.
		Select("COUNT(*)").
		FromSelect(baseSelect, "count").
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query, args)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	return query, countQuery, args
}

func getRaces(ctx *gin.Context) {
	filters := RaceFilters{}
	filters.Keywords = ctx.DefaultQuery("keywords", "")
	filters.Trophy, _ = strconv.ParseInt(ctx.DefaultQuery("trophy", ""), 10, 64)
	filters.Flag, _ = strconv.ParseInt(ctx.DefaultQuery("flag", ""), 10, 64)
	filters.League, _ = strconv.ParseInt(ctx.DefaultQuery("league", ""), 10, 64)
	filters.Page, _ = strconv.ParseInt(ctx.DefaultQuery("page", "0"), 10, 64)
	filters.Limit, _ = strconv.ParseInt(ctx.DefaultQuery("limit", "100"), 10, 64)

	query, countQuery, args := buildRacesQuery(ctx, filters)

	var flatRaces []db.Race
	err := db.GetDB().Select(&flatRaces, query, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var count int
	err = db.GetDB().Get(&count, countQuery, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	races := make([]api.Race, len(flatRaces))
	for idx, race := range flatRaces {
		races[idx] = *api.NewRace(race)
	}

	var next string
	if (filters.Page + 1) < int64(math.Ceil(float64(count)/float64(filters.Limit))) {
		next = fmt.Sprintf("/races?page=%d", filters.Page+1)
	}
	ctx.JSON(http.StatusOK, gin.H{
		"results": races,
		"pagination": gin.H{
			"current_page":  filters.Page,
			"next":          next,
			"page_size":     filters.Limit,
			"total_records": count,
			"total_pages":   math.Ceil(float64(count) / float64(filters.Limit)),
		},
	})
}

func AddRaceRoutes(router *gin.Engine) *gin.Engine {
	router.GET("/api/races", getRaces)
	return router
}
