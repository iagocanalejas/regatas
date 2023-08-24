package server

func Init() {
	router := NewRouter()
	router.Run("localhost:8080")
}
