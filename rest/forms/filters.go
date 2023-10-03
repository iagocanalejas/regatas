package forms

type RaceFilters struct {
	Keywords     string
	Year         int64
	League       int64
	Trophy       int64
	Flag         int64
	TrophyOrFlag []int64
	Participant  int64
	Page         int64
	Limit        int64
}
