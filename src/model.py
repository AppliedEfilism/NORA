import random
import csv 
import config 
from src.intervention import trapping
from src.timer import timeit
from src.agent import Cat
from src.data_collector import DataCollector

eps = 1e-16

class Colony:
    def __init__(self,N0):

        self.cats = []
        self.N_history = []
        self.num_units = int( config.KCAP/10 )

        self.daily_mating = 0
        self.daily_pregnancy = 0
        self.daily_pseudo_pregnancy = 0
        self.daily_litter = 0
        self.daily_active_units = 0
        self.daily_capture_male = 0
        self.daily_capture_female = 0
              
        self.collector = DataCollector()

        female_units = list(range(1, self.num_units + 1))

        for i in range(N0):
            if i<N0//2:
                sex = "female"
                if female_units:
                    unit = female_units.pop()
                else:
                    unit = random.randint(1, self.num_units)
            else:
                sex = "male"
                unit = 0

            r1 = random.random()
            if r1 < 0.25:
                age = random.randint(0,config.AGE_YOUNG_JUV-1)
            elif r1 < 0.5:
                age = random.randint(config.AGE_YOUNG_JUV, config.AGE_OLD_JUV-1)
            elif r1 < 0.75:
                age = random.randint(config.AGE_OLD_JUV, 318)
            else:
                age = random.randint(319, config.AGE_MAX)

            cat = Cat(sex,age,unit=unit) 
            self.cats.append(cat) 

        if config.DEBUG:
            self.debug_properties()

    #==============
    @timeit
    def advance(self,day,method):
    #==============

        day_of_year = ( (day-1) % 365 ) + 1

        if config.BREEDING_SEASON_START <= day_of_year <= config.BREEDING_SEASON_END:
            is_breeding_season = True                      
        else:
            is_breeding_season = False

        #...save previous data        
        prev_cats = self.cats

        trapping(self, day, method)

        N_neut    = sum(1 for cat in self.cats if cat.status in ["TNR", "TVHR"] )
        N_current = sum(1 for cat in self.cats if cat.is_alive )

        for cat in self.cats:

            cat.update_age(N_current,N_neut)

            if not cat.is_alive:
                continue

            cat.advance_counters(is_breeding_season)

        dead_cats = [cat for cat in self.cats if not cat.is_alive]

        #...update living cat list
        self.cats = [cat for cat in self.cats if cat.is_alive]

        if is_breeding_season:
            self.process_mating()

        new_cats = []
        self.daily_litter = 0
        for cat in self.cats:
            if cat.gives_birth:
                newborns = cat.reproduce(N_current)
                if newborns is not None:
                    new_cats.extend(newborns)
                    self.daily_litter += 1
        self.cats.extend(new_cats)

        self.collector.collect(self, method, day, prev_cats, new_cats, dead_cats )

        self.N_history.append( len(self.cats) )
        
        if config.DEBUG:
            self.debug_properties()

    #==============
    @timeit
    def process_mating(self):
    #==============

        # list up active males
        active_males = []
        for cat in self.cats:
            if cat.sex == "male" and cat.is_active:
                active_males.append(cat)        
        if not active_males:
            return 

        # sort in order of dominance
        active_males.sort(key=lambda x: x.dominance, reverse=True)
    
        # dictionary of female unit
        female_units = {} 
        for i in range(1,self.num_units+1):
            female_units[i] = [] # prepare empty list

        active_females = []
        for cat in self.cats:
            if cat.sex == "female" and cat.is_active:
                female_units[cat.unit].append(cat)
                active_females.append(cat)
                cat.cop_count = 0
                cat.can_be_pregnant = False

        active_units = []
        for i in range(1, self.num_units + 1):
            if len(female_units[i]) > 0:
                active_units.append(i)       

        self.num_active_units = len( active_units )
        self.daily_mating = 0
        self.daily_pregnancy = 0
        self.daily_pseudo_pregnancy = 0
        while active_units and active_males:

            unit_id = random.choice(active_units)
            selected_unit = female_units[unit_id]

            male = active_males[0]
            cop_left = random.randint(1,config.COP_MAX)
            #cop_left = config.COP_MAX

            while cop_left > 0 and len(selected_unit) > 0:
                
                female = random.choice(selected_unit)
                cop_left -= 1
                female.cop_count += 1
                self.daily_mating  += 1

                if male.status == "intact" and female.status == "intact":
                    female.can_be_pregnant = True

            active_units.remove(unit_id)
            active_males.remove(male)

        for female in active_females:
            
            n = female.cop_count
            if n > 0:

                if n == 1:
                    P_ovu = 0.21
                elif n == 2:
                    P_ovu = 0.51
                else:
                    P_ovu = 0.81

                if random.random() <= P_ovu:

                    P_preg = 1.0 - (1.0 - config.P_PREGNANCY) ** n

                    if random.random() <= P_preg and female.can_be_pregnant:

                        female.is_pregnant = True
                        female.gestation_timer = config.PREGNANCY_DURATION       
                        female.is_active = False
                        female.estrus_timer = 0
                        self.daily_pregnancy += 1
               
                    else:

                        female.is_pseudo_pregnant = True
                        female.gestation_timer = config.PSEUDO_PREGNANCY_DURATION                
                        female.is_active = False
                        female.estrus_timer = 0
                        self.daily_pseudo_pregnancy += 1
                        
            female.cop_count = 0

        return
        
    #==============
    @timeit
    def debug_properties(self):
    #==============

       for cat in self.cats:

           if not cat.is_alive:

               print( " # Error: Dead cat is included in the list" )

           if cat.age_category == "kitten":

               if cat.is_active:
                   print( " # Error: sexually active kitten is found" )

               if cat.is_pregnant:
                   print( " # Error: pregnant kitten is found" )

           elif cat.age_category == "young_juvenile":

               if cat.is_active:
                   print( " # Error: sexually active young juvenile is found" )

               if cat.is_pregnant:
                   print( " # Error: pregnant young juvenile is found" )

           elif cat.age_category == "older_juvenile":

               if cat.is_active:
                   print( " # Error: sexually active older juvenile is found" )

               if cat.is_pregnant:
                   print( " # Error: pregnant older juvenile is found" )

           elif cat.age_category == "adult":

               if cat.sex == "male":
                   if cat.status =="intact" and not cat.is_active:
                       print( " # Error: sexually inactive intact adule male is found" )
                   if cat.is_pregnant:
                       print( " # Error: pregant male is found " )

               elif cat.sex == "female":

                   if cat.is_pregnant:

                       if cat.is_active:
                           print( " # Error: sexually active pregnant female is found" )

                       if cat.gestation_timer <=0:
                           print( f" # Error: wrong gestation timer value {cat.gestation_timer} for a pregnant cat" )

                       if cat.is_pseudo_pregnant:
                           print( f" # Error: pregnant and pseudo-pregnant simultaneously" )

                   if cat.is_pseudo_pregnant:

                       if cat.is_active:
                           print( " # Error: sexually active psudo-pregnant female is found" )

                       if cat.gestation_timer <=0:
                           print( f" # Error: wrong gestation timer value {cat.gestation_timer} for a pseudo-pregnant cat" )
                       if cat.is_pregnant:
                           print( f" # Error: pregnant and pseudo-pregnant simultaneously" )

                   if cat.is_nursing:

                       if cat.is_active:
                           print( " # Error: sexually active nursing female is found" )

                       if cat.nursing_timer <=0:
                           print( f" # Error: wrong nursing timer value {cat.nursing_timer} for a nursing cat" )                       
                       if cat.is_pregnant:
                           print( f" # Error: pregnant and nursing simultaneously" )

                   if cat.nursing_timer>0:

                       if not cat.is_nursing:
                           print( " # Error: nursing timer is not zero but the cat is not nursing" )

                       if cat.is_active:
                           print( " # Error: sexually active nursing female is found" )                        

               else:  

                   print( f" # Error: Unkown sex {cat.sex} is found" )
  
           else:

               print( f" # Error: Unkown age category {cat.age_category} is found" )

           return


