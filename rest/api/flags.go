package api

import (
	"log"
	"net/http"

	"r4l/rest/db"
	"r4l/rest/models"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func GetFlags(ctx *gin.Context) {
	query, args, err := sq.
		Select("id, name").
		From("flag f").
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	var flags []models.Flag
	err = db.GetDB().Select(&flags, query, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, flags)
}
