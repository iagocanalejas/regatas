package leagues

import (
	"log"
	"net/http"

	"r4l/rest/db"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func getLeagues(ctx *gin.Context) {
	query, _, err := sq.
		Select("id, name, gender, symbol").
		From("league").
		Where(sq.NotEq{"parent_id": nil}).
		ToSql()
	if err != nil {
		log.Print(query)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	var leagues []League
	err = db.GetDB().Select(&leagues, query)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, leagues)
}

func AddLeagueRoutes(router *gin.Engine) *gin.Engine {
	router.GET("/api/leagues", getLeagues)
	return router
}
