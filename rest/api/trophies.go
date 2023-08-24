package api

import (
	"log"
	"net/http"

	"r4l/rest/db"
	"r4l/rest/models"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func GetTrohies(ctx *gin.Context) {
	query, args, err := sq.
		Select("id, name").
		From("trophy t").
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	var trophies []models.Trophy
	err = db.GetDB().Select(&trophies, query, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, trophies)
}
