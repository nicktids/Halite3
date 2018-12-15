
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
# np.set_printoptions(threshold=np.nan)
import pandas as pd

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

direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
ship_max_hlt = constants.MAX_HALITE
max_turns = constants.MAX_TURNS
ship_cost = constants.SHIP_COST
yard = [me.shipyard.position.x,me.shipyard.position.y]
drops = me.get_dropoffs()
drops.append(yard)
logging.debug("drops {}".format(drops))

def get_info(game_map, occ_arr, hlt_amt,me):
    for y in range(game_map.height):
         for x in range(game_map.width):
            this_cell = game_map[hlt.Position(x, y)]
            occ_arr[x,y] = this_cell.is_occupied
            hlt_amt[x,y] = this_cell.halite_amount
    for ship in me.get_ships():
        occ_arr[ship.position.x,ship.position.y] = 2
    return occ_arr, hlt_amt


ship_states = {}

def create_ship_states(me,ship_states):
    '''
    Test the ship and decide collecting or depositing or something else in future
    '''
    for ship in me.get_ships():
        if ship not in ship_states:
            ship_states[ship.id] == "collecting"
        if ship.halite_amount >= constants.MAX_HALITE *.9:
            ship_states[ship.id] == "depositing"
    return ship_states

def f1(d1):  
     v=list(d1.values())
     k=list(d1.keys())
     return k[v.index(max(v))]

def movement(ship,ship_states,occ_arr,hlt_amt,drops,yard):
    if ship_states[ship.id] == "collecting":
        position_options = ship.position.get_surrounding_cardinals() + [ship.position]
        choice_dic = {}
        for pos in position_options:
            choice_dic[pos] = hlt_amt[pos.x,pos.y]
            directional_choice = f1(choice_dic)
    return (ship.move(directional_choice))   


   
game.ready("BBCMicroTurtle_v2")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.debug("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()

    # You extract player metadata and the updated map metadata here for convenience.
    command_queue = []
    occ_arr, hlt_amt = get_info(game_map, occ_arr, hlt_amt, me)
    logging.debug("I have this much halite: {}".format(me.halite_amount))


    ship_states = create_ship_states(me,ship_states)
    for ship in me.get_ships():
        command_queue.append(movement(ship,ship_states,occ_arr,hlt_amt,drops,yard))
   
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())
    # making my ships == 2 and competitior shnment, ending this turn.
    game.end_turn(command_queue)

