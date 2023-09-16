package main

import (
	"fmt"

	"r4l/rest/server"
)

func main() {
	fmt.Printf("Project Version: %s\n", Version)
	server.Init()
}
