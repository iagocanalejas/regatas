package server

import (
	"net/http"

	"r4l/rest/api"

	"github.com/gin-gonic/gin"
)

func cors() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}

func NewRouter() *gin.Engine {
	router := gin.Default()
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	router.Use(cors())

	router.GET("/api/trophies", api.GetTrohies)
	router.GET("/api/flags", api.GetFlags)
	router.GET("/api/leagues", api.GetLeagues)
	router.GET("/api/clubs", api.GetClubs)
	router.GET("/api/races", api.GetRaces)
	router.GET("/api/races/:raceId", api.GetRaceById)

	return router
}
