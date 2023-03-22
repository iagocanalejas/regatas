package trophies

import (
	"log"
	"net/http"

	"r4l/rest/api"
	"r4l/rest/db"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func getTrohies(ctx *gin.Context) {
	query, args, err := sq.
		Select("id, name").
		From("trophy t").
		Where(sq.Gt{"(SELECT COUNT(*) FROM race r WHERE r.trophy_id = t.id)": 0}).
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
        log.Print(query)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	var trophies []api.Trophy
	err = db.GetDB().Select(&trophies, query, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, trophies)
}

func AddTrophyRoutes(router *gin.Engine) *gin.Engine {
	router.GET("/api/trophies", getTrohies)
	return router
}
