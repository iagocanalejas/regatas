package api

import (
	"log"
	"net/http"

	"r4l/rest/db"
	"r4l/rest/models"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func GetLeagues(ctx *gin.Context) {
	query, _, err := sq.
		Select("id, name, gender, symbol").
		From("league").
		Where(sq.NotEq{"parent_id": nil}).
		ToSql()
	if err != nil {
		log.Print(query)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	var leagues []models.League
	err = db.GetDB().Select(&leagues, query)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, leagues)
}
