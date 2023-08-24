package models

type Entity struct {
	ID      int64   `json:"id"`
	Name    string  `json:"name"`
	RawName *string `json:"raw_name"`
}
