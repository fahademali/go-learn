package main

import (
	"fmt"
)

var prices = map[string]uint{
	"Kashmiri Chai": 54,
	"Cardimom Tea":  99,
	"Lemon Water":   22,
	"Cappuccino":    12,
	"Latte":         32,
}
var quantities = map[string]uint{
	"Kashmiri Chai": 10,
	"Cardimom Tea":  5,
	"Lemon Water":   2,
	"Cappuccino":    1,
	"Latte":         0,
}
var validOptions = map[int8]bool{
	0: true,
	1: true,
	2: true,
	3: true,
	4: true,
}
var beverages = [5]string{"Kashmiri Chai", "Latte", "Cappuccino", "Cardimom Tea", "Lemon Water"}

func main() {
	// TODO: convert it into Struct of Arrays

	var userChoice int8
	var totalBill uint = 0

	fmt.Println("Welcome Sir What would you like to have")

	for index, beverage := range beverages {
		fmt.Printf("%v- %v\n", index, beverage)
	}

	for {
		var userChosenDrink string

		fmt.Println("Select Bevergae by typing the prefix number of the drink")
		fmt.Scan(&userChoice)

		isValid, message := validateInput(userChoice)

		if !isValid {
			fmt.Println(message)
			continue
		}

		userChosenDrink = beverages[userChoice]
		quantities[userChosenDrink] = quantities[userChosenDrink] - 1

		fmt.Printf("%v is in making...\n", userChosenDrink)

		totalBill = totalBill + prices[userChosenDrink]
		fmt.Printf("Total bill so far: $%v\n", totalBill)

		isCheckout := isCheckingOut()

		if isCheckout {
			totalBill = selectPaymentMethod(totalBill)
			fmt.Println("Thank you for using me")
			fmt.Printf("Total Bill after tax: $%v", totalBill)
			return
		}

		fmt.Println()
		fmt.Println()
		fmt.Println()
	}

}
