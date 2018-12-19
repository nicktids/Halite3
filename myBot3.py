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
logging.basicConfig(filename='mybot3.log', filemode='w', level=logging.DEBUG)
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
ship_max_hlt = constants.MAX_HALITE *.8
max_turns = constants.MAX_TURNS
ship_cost = constants.SHIP_COST
yard = [me.shipyard.position.x,me.shipyard.position.y]
drops = me.get_dropoffs()
drops.append(yard)
logging.debug("drops {}".format(drops))

ship_states = {}

def get_info(game_map, occ_arr, hlt_amt,me):
    for y in range(game_map.height):
         for x in range(game_map.width):
            this_cell = game_map[hlt.Position(x, y)]
            occ_arr[x,y] = this_cell.is_occupied
            hlt_amt[x,y] = this_cell.halite_amount
    for ship in me.get_ships():
        occ_arr[ship.position.x,ship.position.y] = 2
    occ_arr[yard[0],yard[1]] =0
    return occ_arr, hlt_amt


def create_ship_states(me,ship_states,yard):
    '''
    Test the ship and decide collecting or depositing or something else in future
    '''
    logging.info("ship_states before {}".format(ship_states))
    for ship in me.get_ships():
        if ship not in ship_states:
            ship_states[ship.id] = "collecting"

    for ship in me.get_ships():
        if ship.halite_amount >= ship_max_hlt:
            logging.debug("ship.id: {}, ship hlt: {}".format(ship.id,ship.halite_amount))
            ship_states[ship.id] = "depositing"
    logging.info("ship_states{}".format(ship_states))
    return ship_states

def sort_dic(x):  
    return sorted(x.items(),reverse=True, key=lambda kv: kv[1])

def sort_dic_depo(x):  
    return sorted(x.items(), key=lambda kv: kv[1])

def space_free(ship,choice_dic,occ_arr,ship_states):
    '''
    Returns where to go and 
    '''
    logging.debug("ship position: {},halite at ship {}, \n {}".format(ship.position,ship.halite_amount,occ_arr))
    
    new_occ ={}
    for key,v in choice_dic.items():
    
        # logging.debug("key: {}".format(key))
        # logging.debug("normalised key: {}".format(game_map.normalize(Position(key))))
       
        if occ_arr[key[0],key[1]] == 0 and key != (ship.position.x,ship.position.y):
            new_occ[key] = v
            # logging.debug("new_occ: {}".format(new_occ))
        if ship_states[ship.id] == "collecting":
            new_occ[(ship.position.x,ship.position.y)] = choice_dic[(ship.position.x,ship.position.y)] *3
        elif new_occ =={}:
            new_occ[(ship.position.x,ship.position.y)] = 1000
    logging.debug("Choice_dice nowwww: {}".format(new_occ))
    return new_occ




def movement(ship,ship_states,occ_arr,hlt_amt,drops,yard):
    choice_dic = {}
    choice_new ={}
    logging.debug('start movement ship.id: {}, ship_state {}'.format(ship.id,ship_states[ship.id]))
        
    if ship_states[ship.id] == "collecting":
        position_opts = ship.position.get_surrounding_cardinals() + [ship.position]
        position_options =[]
        for pos in position_opts:
            position_options.append(game_map.normalize(pos))
        
        logging.debug('position_options {}'.format(position_options))
        

        for pos in position_options:
            choice_dic[(pos.x,pos.y)] = hlt_amt[pos.x,pos.y]
        logging.debug("Choice dic before removing occupied{}".format(choice_dic))
        choice_new = space_free(ship,choice_dic,occ_arr,ship_states)
        
        logging.debug("Choice dic before sort{}".format(choice_new))
        sorted_dic={}
        sorted_dic = sort_dic(choice_new)
        if len(sorted_dic) >=2 and sorted_dic[0][1] <=10:
            directional_choice =sorted_dic[1][0]
        else:
            directional_choice =sorted_dic[0][0]
        # directional_choice = sort_dic(choice_new)[0][0]
        logging.debug("Choice dic after sort{}".format(directional_choice))

        direction_x = np.sign(directional_choice[0] - ship.position.x)
        direction_y = np.sign(directional_choice[1] - ship.position.y)
        #direction choice is the position in the space not vs the original position
    elif ship_states[ship.id]  == "depositing":
        logging.info("Going back to base")
        logging.info("yard position {}, ship: {}".format(yard, ship.position))
        to_yard = [yard[0]- ship.position.x  ,yard[1] - ship.position.y]
        to_yard = (np.sign(to_yard[0]),np.sign(to_yard[1]))
        logging.info("to yard {}".format(to_yard))


        if [ship.position.x,ship.position.y] != yard:
            # Add a loop to create a dic of choices and pass in to the space free
            # x = np.random.choice(2)
            choice_dic[ship.position.x + to_yard[0],ship.position.y] = hlt_amt[ship.position.x + to_yard[0],ship.position.y]
            choice_dic[ship.position.x ,ship.position.y + to_yard[1]] = hlt_amt[ship.position.x ,ship.position.y+ to_yard[1]]
            logging.debug("depo choice dic: {}".format(choice_dic))

            choice_new = space_free(ship,choice_dic,occ_arr,ship_states)
            logging.debug("depo choice new: {}".format(choice_new))
            directional_choice = sort_dic_depo(choice_new)[0][0]
            logging.debug("depo direction: {}, current pos: {}, yard: {}".format(directional_choice, ship.position, yard))
            direction_x = np.sign(directional_choice[0] - ship.position.x)
            direction_y = np.sign(directional_choice[1] - ship.position.y)

            # if choice_new == ():
            #     direction_x = 0
            #     direction_x = 0
            # else:
            #     direction_x = np.sign(choice_new[0] - ship.position.x)
            #     direction_y = np.sign(choice_new[1] - ship.position.y)
        #     for x in [0,1]
        #     if x == 0:
        #         direction_x = to_yard[0]
        #         direction_y = 0
        #     else:
        #         direction_x = 0
        #         direction_y = to_yard[1]
        else:
            ship_states[ship.id] ="collecting"
            logging.info("Ship at yard so making collect")
            return movement(ship,ship_states,occ_arr,hlt_amt,drops,yard)
        # else:
        #     direction_x = to_yard[0]
        #     direction_y = to_yard[1]           


        directional_choice = (direction_x + ship.position.x ,direction_y +ship.position.y)

    logging.debug("ship state {}, directional Choice x:{} y:{}".format(ship_states[ship.id],(direction_x),(direction_y)))

    occ_arr[ship.position.x,ship.position.y] = 0
    occ_arr[directional_choice[0],directional_choice[1]] = 2

    return ship.move((direction_x,direction_y)), occ_arr

   
game.ready("BBCMicroTurtle_v3")

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

    
    ship_states = create_ship_states(me,ship_states,yard)

    for ship in me.get_ships():
        move_this, occ_arr = movement(ship,ship_states,occ_arr,hlt_amt,drops,yard)
        command_queue.append(move_this)
   
    logging.debug("command_queue: {}".format(command_queue))

    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        logging.info("generate ship")
        command_queue.append(me.shipyard.spawn())
    # making my ships == 2 and competitior shnment, ending this turn.
    game.end_turn(command_queue)

