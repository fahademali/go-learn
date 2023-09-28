package main

import (
	"fmt"
)

func main() {
	// TODO: convert it into Struct of Arrays
	beverages := [5]string{"Kashmiri Chai", "Latte", "Cappuccino", "Cardimom Tea", "Lemon Water"}
	prices := map[string]uint{
		"Kashmiri Chai": 54,
		"Cardimom Tea":  99,
		"Lemon Water":   22,
		"Cappuccino":    12,
		"Latte":         32,
	}
	quantities := map[string]uint{
		"Kashmiri Chai": 10,
		"Cardimom Tea":  5,
		"Lemon Water":   2,
		"Cappuccino":    1,
		"Latte":         0,
	}
	validOptions := map[int8]bool{
		0: true,
		1: true,
		2: true,
		3: true,
		4: true,
	}

	var userChoice int8
	var totalBill uint = 0

	fmt.Println("Welcome Sir What would you like to have")

	for index, beverage := range beverages {
		fmt.Printf("%v- %v\n", index, beverage)
	}

	for {
		var userChosenDrink string

		fmt.Println("Select Bevergae by typing the prefix number of the drink.")
		fmt.Scan(&userChoice)

		userChosenDrink = beverages[userChoice]

		if _, isValid := validOptions[userChoice]; !isValid {
			fmt.Println("Select between the range 0-4")
			continue
		}
		if quantities[userChosenDrink] == 0 {
			fmt.Printf("The Cartage for %v is empty, fill it or check back later.\n", userChosenDrink)
			continue
		}
		if _, exists := prices[userChosenDrink]; !exists {
			fmt.Println("There is no such beverage in the stock")
			continue
		}

		quantities[userChosenDrink] = quantities[userChosenDrink] - 1
		fmt.Printf("%v is in making...\n", userChosenDrink)
		totalBill = totalBill + prices[userChosenDrink]
		fmt.Printf("Total bill so far: %v", totalBill)

		fmt.Println()
		fmt.Println()
		fmt.Println()
	}

}
