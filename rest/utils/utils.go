package utils

func ContainsString(slice []string, target string) bool {
	for _, s := range slice {
		if s == target {
			return true
		}
	}
	return false
}

func Int2roman(original int) string {
	if original < 1 || original > 3999 {
		return ""
	}

	numerals := [][]string{
		{"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"}, // 1-9
		{"X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"}, // 10-90
		{"C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"}, // 100-900
		{"M", "MM", "MMM"}, // 1000-3000
	}

	digits := []int{}
	n := original
	for n > 0 {
		digits = append(digits, n%10)
		n /= 10
	}

	position := len(digits) - 1
	roman := ""

	for _, digit := range digits {
		if digit != 0 {
			roman += numerals[position][digit-1]
		}
		position--
	}

	return roman
}
