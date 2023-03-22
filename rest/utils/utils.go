package utils

func ContainsString(slice []string, target string) bool {
	for _, s := range slice {
		if s == target {
			return true
		}
	}
	return false
}

var romanSymbols = []struct {
	Value  int
	Symbol string
}{
	{1000, "M"},
	{900, "CM"},
	{500, "D"},
	{400, "CD"},
	{100, "C"},
	{90, "XC"},
	{50, "L"},
	{40, "XL"},
	{10, "X"},
	{9, "IX"},
	{5, "V"},
	{4, "IV"},
	{1, "I"},
}

func Int2Roman(num int) string {
	roman := ""
	for _, symbol := range romanSymbols {
		for num >= symbol.Value {
			roman += symbol.Symbol
			num -= symbol.Value
		}
	}
	return roman
}
