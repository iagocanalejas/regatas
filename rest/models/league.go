package models

type League struct {
	ID     int64   `json:"id"`
	Name   string  `json:"name"`
	Gender *string `json:"gender"`
	Symbol string  `json:"symbol"`
}