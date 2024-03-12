import random

def roll_dice():
    return random.randint(1, 6)

def main():
    # Displays game rules
    print("Welcome to the Dice Game!",
          "Rules:",
          "\tYou choose the number of rounds against the computer.",
          "\tYou and the computer will each roll a dice.",
          "\tThe one with the higher number wins a point for the round.",
          "\tIf there is a tie, the player with the highest roll total wins.",
          "\tMatching rolls results in no points being rewarded.\n\n", sep='\n')

    while True:
        # Asks for desired number of rounds
        round_total = 0
        while round_total < 5:
            try:
                round_total = int(input("Enter the number of rounds you would like to play (at least 5): "))
            except ValueError: #Ensures that an error is not returned when an integer is not inputted
                print("Please enter an integer greater than 5.")

        round_current = 1
        user_rolls = [] # History of user rolls
        comp_rolls = [] # History of computer rolls
        user_wins = [] # History of user round results (i.e. wins, losses, ties)
        print('', str(round_total) + " Rounds! Let's Go!", "Game Start!", sep='\n')
        
        while round_current <= round_total: # Repeat until out of rounds
            print("Round", round_current, '\n')
            input("Press Enter to roll the die...") # Waits on user begin round
            
            user_roll = roll_dice() # Generates number for user
            comp_roll = roll_dice() # Generates number for computer
            user_rolls.append( user_roll ) # Adds dice roll to user history
            comp_rolls.append( comp_roll ) # Adds dice roll to computer history

            print("You rolled:", user_roll)
            print("Computer rolled:", comp_roll)

            if user_roll > comp_roll: # If user wins
                user_wins.append("Win") # Add win to round result history
                print("Congratulations! You won this round!")
            elif user_roll < comp_roll: # If computer wins
                user_wins.append("Lose") # Add loss to round result history
                print("Darn! You lost. Better luck next round!")
            else: # If tie
                user_wins.append("Tie") # Add tie to round result history
                print("It's a tie!")
            print()
            
            if round_current == round_total:
                # After final round, determines who won
                # The number of wins trumps the total roll number
                print("Game Over!", '', "Calculating Results...", sep='\n')
                
                wins = user_wins.count("Win")
                losses = user_wins.count("Lose")
                ties = round_total - wins - losses
                user_sum = sum(user_rolls)
                comp_sum = sum(comp_rolls)

                print("Wins:", wins, "Losses:", losses, "Ties:", ties)
                if wins == losses:
                    # If number of user wins equals number of computer wins,
                    #   display total roll information before moving to tie-breaker
                    print("Woah! It was a tie!", "Calculating sum of rolls...", sep='\n\n')
                    print("Your total rolls: " + str(sum(user_rolls)), "Computer total rolls: " + str(sum(comp_rolls)), sep='\t')

                # Displays game result
                if wins > losses or (wins == losses and user_sum > comp_sum): # If the USER has more wins or has a higher roll total in the tie-breaker
                    print("Congratulations! You won the game!")
                elif wins < losses or (wins == losses and user_sum < comp_sum): # If the COMPUTER has more wins or has a higher roll total in the tie-breaker
                    print("Darn! You lost. Better luck next time!")
                elif wins == losses and user_sum == comp_sum: # If the user and computer could not break the tie
                    print("Woah! It was an absolute tie!")
                    
                # Displays the game stastics
                print("\nDisplaying Statistics...")
                print("Round\t", "Your Rolls", "Comp Rolls","Round Results", sep='\t')
                
                for i in range(round_total):
                    print(i+1, '', user_rolls[i], '', comp_rolls[i], '', user_wins[i], sep='\t')

            round_current += 1
        
        # Asks if the player would like to continue
        play_again = input("\nDo you want to play again? (y/n): ").lower()
        print()
        if play_again != "y":
            print("Thanks for playing!")
            break

if __name__ == "__main__":
    main()
