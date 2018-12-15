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

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging
logging.basicConfig(filename='mybot_v1.log', filemode='w', level=logging.DEBUG)
""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """
ship_states = {}
while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
    position_choices = []
    for ship in me.get_ships():
        if ship.id not in ship_states:
            ship_states[ship.id] =  "collecting"

        position_options = ship.position.get_surrounding_cardinals() + [ship.position]        
        logging.debug("position options {}".format(position_options))
        for pos in position_options:
            logging.debug("pos x:{} y:{}".format(pos.x,pos.y))
        # {(0,1):(19,38)}
        position_dict = {}

        # {(0,1): 500}
        halite_dict = {}
        
        for n, direction in enumerate(direction_order):
            # logging.info(n,direction)
            position_dict[direction] = position_options[n]

        for direction in position_dict:
            position = position_dict[direction]
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
            logging.debug("directional choice = {}".format(directional_choice))
            position_choices.append(position_dict[directional_choice]) 
            command_queue.append(ship.move(directional_choice))

            if ship.halite_amount > constants.MAX_HALITE *.8:
                ship_states[ship.id] = "depositing"

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

