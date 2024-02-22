import numpy as np
import argparse
import random
import copy

class ArgumentParser(argparse.ArgumentParser):

    def __init__(this, *args, **kwargs):
        super(ArgumentParser, this).__init__(*args, **kwargs)
        this.error_message = ''

    def error(this, message):
        this.error_message = message
        raise ValueError(message)
    
    def print_help(this):
        super(ArgumentParser, this).print_help()


class TicTacToeGame():
    def __init__(this):
        this.game_state = np.array([['','',''],['','',''],['','','']])
        this.number_of_moves_made = 0
        this.size = 3
        this.slots_with_draws = 0
        this.bot_player = True
        this.bot_optimized = True
        this.next_symbol = "x"
        this.bound_users = []
        this.user_bound = False

    def create_copy(this):
        copy_game = TicTacToeGame()
        copy_game.game_state = copy.deepcopy(this.game_state)
        copy_game.number_of_moves_made = this.number_of_moves_made
        copy_game.size = this.size
        copy_game.slots_with_draws = this.slots_with_draws
        copy_game.bot_player = this.bot_player
        copy_game.bot_optimized = this.bot_optimized
        copy_game.next_symbol = this.next_symbol
        copy_game.bound_users = copy.deepcopy(this.bound_users)
        copy_game.user_bound = this.user_bound
        return copy_game

    def place_at_location(this, location, symbol):
        if not (symbol=="x" or symbol=="o"):
            raise ValueError("Not a valid symbol, must be either 'x' or 'o'")
        # assumes usable location and valid symbol
        if not this.game_state[location[0]][location[1]]:
            this.game_state[location[0]][location[1]] = symbol
            return this.game_state
        else:
            raise ValueError("Location already occupied")
            return None
        
    def check_for_termination(this, location, symbol):
        """" Checks where the most recent move leads to a termination of the game. 
        Returns -1 if it doesn't terminate, 0 if it leads to a draw, 1 if it leads to a win"""
        row = location[0]
        column = location[1]
        this.number_of_moves_made += 1


        # check row
        is_draw = False
        is_new_draw = True
        n_symbol = 0
        for i,v in enumerate(this.game_state[row]):
            if v==symbol:
                n_symbol+=1
            if v != '' and v != symbol:
                is_draw = True
            elif v != '' and i != column:
                    is_new_draw = False

            if n_symbol == this.size:
                return 1

        if is_draw and is_new_draw:
            this.slots_with_draws +=1
        if this.slots_with_draws == this.size*2+2:
            return 0
        
        is_draw = False
        is_new_draw = True
        n_symbol = 0
        # check column
        for i,v in enumerate(this.game_state[:, column]):
            if v==symbol:
                n_symbol+=1
            if v != '' and v != symbol:
                is_draw = True
            elif v != '' and i != row:
                    is_new_draw = False

            if n_symbol == this.size:
                return 1
                
        if is_draw and is_new_draw:
            this.slots_with_draws +=1
        if this.slots_with_draws == this.size*2+2:
            return 0
        
        is_draw = False
        is_new_draw = True
        n_symbol = 0
        
        # check diagonals
        if row == column:
            for i,v in enumerate(this.game_state[np.arange(this.size), np.arange(this.size)]):
                if v==symbol:
                    n_symbol+=1
                if v != '' and v != symbol:
                    is_draw = True
                elif v != '' and i != row:
                        is_new_draw = False

                if n_symbol == this.size:
                    return 1

        if is_draw and is_new_draw:
            this.slots_with_draws +=1
        if this.slots_with_draws == this.size*2+2:
            return 0
        
        is_draw = False
        is_new_draw = True
        n_symbol = 0
        if row+column == this.size-1:
            for i,v in enumerate(this.game_state[np.arange(this.size), np.arange(this.size)[::-1]]):
                if v==symbol:
                    n_symbol+=1
                if v != '' and v != symbol:
                    is_draw = True
                elif v != '' and i != row:
                        is_new_draw = False

                if n_symbol == this.size:
                    return 1

        if is_draw and is_new_draw:
            this.slots_with_draws +=1
        if this.slots_with_draws == this.size*this.size+2:
            return 0

        if this.number_of_moves_made == this.size*this.size:
            return 0
                      
        return -1

    def get_printed_game_state(this):
        game_string = ""
        for i,row in  enumerate(this.game_state):
            if i != 0:
                game_string += "———｜———｜———\n"
            for j,value in enumerate(row):
                if j != 0:
                    game_string += "｜"

                game_string += " "
                if value=="x":
                    game_string += "ｘ" 
                elif value=="o":
                    game_string += "ｏ" 
                elif not value:
                    game_string += " "
                game_string += " "
            game_string += "\n"

        return game_string
   
    def print_help(this):
        return("""This is the help for the Tic-tac-toe chat bot. Use /ttt at the beginning of your message to use this bot. To make a play simply use "/ttt" followed by the coordinates where you want to place the next symbol. For example: /ttt 1 2\n
                \n
                Available commands:\n
                \t --help Print this help text. \n
                \t new_game -n Start a new game, abandoning the old one. \n
                \t\t -p Number of non-bot players, can be 1 or 2. \n
                \t\t -b Bot option, describing the difficulty level, use either "e" for easy or "h" for hard. \n
                \t\t -u Flag to make the game user-bound, so that only messages from the starting user(s) advance the game. \n""")

    def reset_game(this):
        this.game_state = np.array([['','',''],['','',''],['','','']])
        this.number_of_moves_made = 0
        this.size = 3
        this.slots_with_draws = 0
        this.bot_player = True
        this.bot_optimized = True
        this.next_symbol = "x"
        this.bound_users = []
        this.user_bound = False

    def minimax(this, move, depth, current_player, maximizing_player):
            # perform current move and check whether this is a terminal state, if so, return the value of the state

            t = this.create_copy()
            game_state_copy = t.place_at_location(move, current_player)
            value = t.check_for_termination(move, current_player)
            t.next_symbol = "x" if t.next_symbol=="o" else "o"

            if value > 0:
                return 10-depth if current_player==maximizing_player else -20+depth
            if value == 0:
                return 0-depth

            else:
                # otherwise, continue playing
                # get possible moves
                possible_moves = np.argwhere(game_state_copy=='')
                
                if t.next_symbol == maximizing_player:
                    best_value = -np.inf
                    for move in possible_moves:
                        state_value = t.minimax(move, depth+1, t.next_symbol, maximizing_player)
                        best_value = max(best_value, state_value)
                    return best_value
                else:
                    best_value = np.inf
                    for move in possible_moves:
                        state_value = t.minimax(move, depth+1, t.next_symbol, maximizing_player)
                        best_value = min(best_value, state_value)
                    return best_value
          

    def get_best_next_move(this, game_state, symbol):
        # get possible moves
        possible_moves = np.argwhere(game_state=='')
        
        best_move = None
        best_value = -np.inf
        for move in possible_moves:
            state_value = this.minimax(move, 0, symbol, symbol)
            best_value = max(best_value, state_value)
            if best_value == state_value:
                best_move = move
        return best_move
     
      
    def parse_message(this, message, user):
        parser = ArgumentParser(description='Tic-tac-toe chat bot.')
        parser.add_argument('c1', type=int)
        parser.add_argument('c2', type=int)
        parser.add_argument('-n', '--new_game', action='store_true', help='Start a new game, abandoning the old one.')
        parser.add_argument('-p', type=int, choices=[1, 2], help='Number of non-bot players, can be 1 or 2.')
        parser.add_argument('-b', type=str, choices=["e", "h"], help='Bot option, describing the difficulty level, use either "e" for easy or "h" for hard.')
        parser.add_argument('-u', action='store_true', help='Flag to make the game user-bound, so that only messages from the starting user(s) advance the game.')

        args = parser.parse_args(message.split())

        if args.new_game:
            this.reset_game()
            if args.p:
                if args.p == 2:
                    this.bot_player = False
                elif args.p == 1:
                    this.bot_player = True

            if args.b:
                if args.b == "e":
                    this.bot_optimized = False
                elif args.p == "h":
                    this.bot_optimized = True
            if args.u:
                this.user_bound = True
            else: 
                this.user_bound = False


        if this.user_bound:
            if this.bot_player and len(this.bound_users) < 1 or not this.bot_player and len(this.bound_users) <2:
                #add user to bound users
                this.bound_users.append(user)

            elif user not in this.bound_users:
                return "This game is user-bound and you are not a player in this game. Players associated with this game are " + str(this.bound_users)
            else:
                if not this.bot_player and ((user == this.bound_users[0] and this.next_symbol!="x") or (user == this.bound_users[1] and this.next_symbol!="o")) and not this.bound_users[0]==this.bound_users[1]:
                    return "This game is user bound and you are a player but it is not your turn. Wait until {} has made their move".format(this.bound_users[1] if user==this.bound_users[0] else this.bound_users[0])


        # make a move
        this.place_at_location((args.c1, args.c2), this.next_symbol)
        v = this.check_for_termination((args.c1, args.c2), this.next_symbol)
        
        m = ""
        if v == 0:
            m = "Draw"
        elif v == 1:
            m = this.next_symbol + " wins"

        this.next_symbol = "x" if this.next_symbol=="o" else "o"
        if v < 0:

            if this.bot_player:
                if this.bot_optimized:
                    move = this.get_best_next_move(this.game_state, this.next_symbol)
                    this.place_at_location(move, this.next_symbol)
                    v = this.check_for_termination(move, this.next_symbol)
                    if v == 0:
                        m = "Draw"
                    elif v == 1:
                        m = this.next_symbol + " wins"
                    this.next_symbol = "x" if this.next_symbol=="o" else "o"
                else:
                    possible_moves = np.argwhere(this.game_state=='')
                    move =  random.choice(possible_moves)
                    this.place_at_location(move, this.next_symbol)
                    v = this.check_for_termination(move, this.next_symbol)
                    if v == 0:
                        m = "Draw"
                    elif v == 1:
                        m = this.next_symbol + " wins"
                    this.next_symbol = "x" if this.next_symbol=="o" else "o"
        

        return this.get_printed_game_state() + "\n" +m
        
