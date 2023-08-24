package models

type Trophy struct {
	ID      int64  `json:"id"`
	Name    string `json:"name"`
	Edition *int   `json:"edition,omitempty"`
}
