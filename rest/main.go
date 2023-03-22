package main

import (
	"net/http"

	"r4l/rest/api/flags"
	"r4l/rest/api/leagues"
	"r4l/rest/api/races"
	"r4l/rest/api/trophies"

	"github.com/gin-gonic/gin"
)

func CORSMiddleware() gin.HandlerFunc {
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

func main() {
	router := gin.Default()
	router.Use(CORSMiddleware())

	trophies.AddTrophyRoutes(router)
	flags.AddFlagRoutes(router)
	races.AddRaceRoutes(router)
	leagues.AddLeagueRoutes(router)

	router.Run("localhost:8080")
}
