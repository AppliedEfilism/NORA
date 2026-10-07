# intervention.py
import random
import config

#===========
def is_trapping_day(day,method):
#===========

    if not method in ["TNR", "TVHR", "LC"]:

        return False

    if day < config.INIT_TRAP:

        return False

    if config.TRAP_EPISODES <= 0 or config.TRAP_DAYS <= 0:

        return False

    block_size = 365 // config.TRAP_EPISODES
    
    day_of_year = ( (day-1) % 365 ) + 1
    
    day_in_block = ( day_of_year -1 ) % block_size
    
    if day_in_block < config.TRAP_DAYS:

        return True
    
    return False

#===========
def trapping(colony, day, method):
#===========

    colony.daily_capture_male = 0
    colony.daily_capture_female = 0

    if not is_trapping_day(day,method):
        return

    if method in ["TNR", "TVHR"]:
        target_cats = [ cat for cat in colony.cats if cat.is_alive and cat.age_category != "kitten" and cat.status=="intact" ]
    else:
        target_cats = [ cat for cat in colony.cats if cat.is_alive and cat.status=="intact" ]

    for cat in target_cats:
        if random.random() <= config.P_CAPTURE:

            #cat.status = method
            if cat.sex=="male":
                colony.daily_capture_male += 1
            else:
                colony.daily_capture_female += 1

            if method in ["TNR", "TVHR"]:
                           
                cat.status = method
                cat.update_activity()

            elif method == "LC":

                cat.status = method
                cat.is_alive = False


