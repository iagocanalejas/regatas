package api

import (
	"log"
	"net/http"

	"r4l/rest/db"
	"r4l/rest/models"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func GetClubs(ctx *gin.Context) {
	query, args, err := sq.
		Select("id, name").
		From("entity e").
		Where(sq.And{
			sq.Eq{"e.type": "CLUB"},
			sq.Gt{"(SELECT COUNT(*) FROM participant p WHERE p.club_id = e.id)": 0},
		}).
		OrderBy("normalized_name").
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	var flags []models.Entity
	err = db.GetDB().Select(&flags, query, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, flags)
}
