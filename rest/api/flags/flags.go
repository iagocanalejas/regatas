package flags

import (
	"log"
	"net/http"

	"r4l/rest/db"

	sq "github.com/Masterminds/squirrel"
	"github.com/gin-gonic/gin"
)

func getFlags(ctx *gin.Context) {
	query, args, err := sq.
		Select("id, name").
		From("flag f").
		PlaceholderFormat(sq.Dollar).
		ToSql()
	if err != nil {
		log.Print(query)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
	}

	var flags []Flag
	err = db.GetDB().Select(&flags, query, args...)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, flags)
}

func AddFlagRoutes(router *gin.Engine) *gin.Engine {
	router.GET("/api/flags", getFlags)
	return router
}
