package db

import (
	"fmt"
	"log"
	"os"

	"github.com/jmoiron/sqlx"
	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
)

var (
	db *sqlx.DB
)

func init() {
	connStr := getConnectionString()

	// Open a connection to the database
	conn, err := sqlx.Connect("postgres", connStr)
	if err != nil {
		log.Fatal(fmt.Errorf("error connecting to the database: %w", err))
	}

	// Test the connection
	err = conn.Ping()
	if err != nil {
		log.Fatal(fmt.Errorf("error pinging the database: %w", err))
	}

	db = conn
}

func getConnectionString() string {
	// Load environment variables from .env file
	err := godotenv.Load("../.env")
	if err != nil {
		log.Fatal(fmt.Errorf("error loading .env file: %w", err))
	}

	// Get PostgreSQL connection details from environment variables
	host := os.Getenv("DATABASE_HOST")
	port := "5432"
	user := os.Getenv("DATABASE_USERNAME")
	password := os.Getenv("DATABASE_PASSWORD")
	dbname := os.Getenv("DATABASE_NAME")

	// Construct PostgreSQL connection string
	return fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=require", host, port, user, password, dbname)
}

func GetDB() *sqlx.DB {
	return db
}
