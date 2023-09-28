package main

import (
	"fmt"
)

func validateInput(userChoice int8) (bool, string) {
	isValid := false
	message := "Every thing is good"

	if _, isRightOption := validOptions[userChoice]; !isRightOption {
		message = "Select between the range 0-4"
	} else if quantities[beverages[userChoice]] == 0 {
		message = fmt.Sprintf("The Cartage for %v is empty, fill it or check back later.\n", beverages[userChoice])
	} else if _, exists := prices[beverages[userChoice]]; !exists {
		message = "There is no such beverage in the stock"
	} else {
		isValid = true
	}

	return isValid, message
}

func isCheckingOut() bool {
	var userInput string
	fmt.Println("Would you like to checkout?(y/n)")
	fmt.Scan(&userInput)

	if userInput == "y" {
		return true
	} else if userInput == "n" {
		return false
	} else {
		fmt.Println("Invalid choice. Please enter 'y' or 'n'.")
		return isCheckingOut()
	}
}

func selectPaymentMethod(totalBill uint) uint {
	var userInput string
	fmt.Println("Cash(5% Tax) or Digital Payment(18% Tax) ? (c/d)")
	fmt.Scan(&userInput)
	if userInput == "c" {
		return totalBill + uint(float64(totalBill)*0.18)
	} else if userInput == "d" {
		return totalBill + uint(float64(totalBill)*0.05)
	} else {
		fmt.Println("Invalid choice. Please enter 'c' or 'd'.")
		return selectPaymentMethod(totalBill)
	}

}
