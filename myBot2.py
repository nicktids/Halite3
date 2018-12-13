
# Need to add this
# for y in range(game_map.height):
#     for x in range(game_map.width):
#         this_cell = game_map[hlt.Position(x, y)]



#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

# This library allows you to generate random numbers.
import random
import numpy as np
np.set_printoptions(threshold=np.nan)

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging
logging.basicConfig(filename='mybot2.log', filemode='w', level=logging.DEBUG)
""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
me = game.me
game_map = game.game_map

occ_arr = np.zeros((game_map.width,game_map.height))
hlt_amt = np.zeros((game_map.width,game_map.height))

def get_info(game_map, occ_arr, hlt_amt):
    for y in range(game_map.height):
         for x in range(game_map.width):
            this_cell = game_map[hlt.Position(x, y)]
            occ_arr[x,y] = this_cell.is_occupied
            hlt_amt[x,y] = this_cell.halite_amount
    return occ_arr, hlt_amt


direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
ship_max_hlt = constants.MAX_HALITE
max_turns = constants.MAX_TURNS
ship_cost = constants.SHIP_COST
yard = [me.shipyard.position.x,me.shipyard.position.y]

# logging.debug("yard: {}".format(yard))

def move_ship(ship,occ_arr,hlt_amt):
    ship_state = occ_arr[ship.position] 
    





game.ready("BBCMicroTurtle_v2")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.debug("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """
ship_states = {}
while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()

    # You extract player metadata and the updated map metadata here for convenience.

    occ_arr, hlt_amt = get_info(game_map, occ_arr, hlt_amt)
    logging.debug(me.halite_amount)

    # making my ships == 2 and competitior ships == 1 
    for ship in me.get_ships():
        occ_arr[ship.position.x,ship.position.y] = 2
        # logging.debug("shipposition: {}".format(ship.position))
    # logging.debug("occupied array {}".format(occ_arr))
    # logging.debug("halite ammount {}".format(hlt_amt))

    drops = me.get_dropoffs()
    yard = me.shipyard.position.x
    logging.debug("drop_off location {} and yard {}".format(drops,yard))
   
    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    position_choices = []
    
    if game.turn_number <= (constants.MAX_TURNS- 10):
        for ship in me.get_ships():
            if ship.id not in ship_states:
                ship_states[ship.id] =  "collecting"
    
            position_options = ship.position.get_surrounding_cardinals() + [ship.position]        
            logging.debug("This ship position: {}, and occ_array {}".format(ship.position, occ_arr[ship.position.x,ship.position.y]))
            # {(0,1):(19,38)}
            position_dict = {}

            # {(0,1): 500}
            halite_dict = {}
            
            for n, direction in enumerate(direction_order):
                logging.debug("n:{}, direction{}".format(n,direction))
                # logging.debug()
                position_dict[direction] = position_options[n]
    
            for direction in position_dict:
                position = position_dict[direction]
                logging.debug("direction: {} position: {}".format(direction,position))
                # logging.debug("checking Dictionary {}".format(occupied_map[position.x,position.y]))
                halite_amount = game_map[position].halite_amount

                if position_dict[direction] not in position_choices:
                    if direction == Direction.Still:
                        halite_dict[direction] = halite_amount*3
                    else:
                        halite_dict[direction] = halite_amount
                else:
                    logging.info("attempting to move to same spot\n")
    
            if ship_states[ship.id] == "depositing":
                move = game_map.naive_navigate(ship, me.shipyard.position)
                position_choices.append(position_dict[move]) 
                command_queue.append(ship.move(move))
                if move == Direction.Still:
                    ship_states[ship.id] = "collecting"
     
            elif ship_states[ship.id] == 'collecting':        
                directional_choice = max(halite_dict, key=halite_dict.get)
                position_choices.append(position_dict[directional_choice]) 
                command_queue.append(ship.move(directional_choice))
    
                if ship.halite_amount > constants.MAX_HALITE *.8:
                    ship_states[ship.id] = "depositing"
    
        # If the game is in the first 200 turns and you have enough halite, spawn a ship.
        # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
        if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())

    else:
         for ship in me.get_ships():
                move = game_map.naive_navigate(ship, me.shipyard.position)
                position_choices.append(position_dict[move]) 
                command_queue.append(ship.move(move))


         
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

