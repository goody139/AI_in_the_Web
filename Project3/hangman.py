import random 
from nltk.corpus import words

def choose_word():
    return random.choice(words.words())

class Hangman:
    def __init__(self):
        self.word = choose_word()
        self.attempts = 7
        self.guessed_letters = []
        self.masked_word = "".join("_ " if letter not in self.guessed_letters else letter for letter in self.word) 
        self.ingame = False
        self.finished = False

    def start(self): 
        self.ingame = True 

    def end(self): 
        self.ingame = False
        self.finished = True
    
    def update_values(self, guessed_letter, state):  
        if state == -1: 
            return -1
        if state == 1 and all(letter in guessed_letter for letter in self.word):
            self.guessed_letters += guessed_letter
            return 0
        elif state == 1 and not(guessed_letter == self.word) :
            self.guessed_letters.append(''.join(guessed_letter))
            self.attempts -= 1
            return 1 
        
        
            
        for g in guessed_letter: self.guessed_letters.append(g)
        self.masked_word = "".join("_ " if letter not in self.guessed_letters else letter for letter in self.word)        
        self.attempts -= sum(1 for g in guessed_letter if g not in self.word)
        return 0 


    def update_game_state(self, surrender):
        # was wenn andere reihenfolge?
        if all(letter in self.guessed_letters for letter in self.word):
            return True, "You won! The word was: " + self.word.upper()
        elif self.attempts <= 0:
            return True, "Game over! The word was: " + self.word.upper()
        elif self.attempts == 1: 
            return False, "Choose your next guess wisely! You have only {} attempt left.".format(self.attempts)
        elif self.attempts == 2: 
            return False, "Choose your next guesses wisely! You have only {} attempts left.".format(self .attempts)
        elif self.attempts < 4: 
            return False, random.choice([None, None, None, "Wanna surrender? Type in @surrender.", "You think u have a chance? You can also stop here in writing @surrender."])
        elif surrender == True: 
            return True, None
        else:
            return False, None