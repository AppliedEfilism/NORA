# agent.py
import random
import config
from src.timer import timeit

active_status = [ "intact", "TVHR" ]

class Cat:
    def __init__(self,sex,age,unit=0):

        self.age = age
        self.is_alive = True 
        self.sex = sex 
        self.unit = unit

        #...繁殖ステータス
        self.status = "intact" 
        self.is_active = False 
        self.is_pregnant = False
        self.is_pseudo_pregnant = False
        self.is_nursing  = False
        self.gives_birth = False
        self.cop_count = 0
        self.gestation_timer = 0
        self.nursing_timer = 0 
        self.estrus_timer = 0
        self.interestrus_timer = 0

        if self.sex=="female":
    
            self.dominance = 0

            r = random.random()
            self.mature_age = random.randint( config.MATURE_MIN_F, config.MATURE_MAX_F )

        elif self.sex=="male":

            self.mature_age = random.randint( config.MATURE_MIN_M, config.MATURE_MAX_M )
            self.dominance = self.calc_dominance()

        else:

            print( f" # Error: invalid sex is detected ({self.sex}) )" )

        self.update_maturity()

    #==============
    @timeit
    def calc_dominance(self):
    #==============

        if self.age> 319:
            dominance = min( 1.0, ( self.age - 319 ) / 761 ) # 最大でも1.0
        else:
            dominance = 0.0

        return dominance

    #==============
    @timeit   
    def update_age(self,N_tot,N_neut):
    #==============

        if not self.is_alive:
            return

        p_0 = config.P_0
        K   = config.KCAP

        if self.age_category in [ "kitten", "young_juvenile" ] and config.METHOD=="TNR":

            p_K = self.prob_survival()
            fct_TNR = config.TNR_EFFECT * N_neut / N_tot 
            if fct_TNR <= 1:
                P_EFF = p_0 - ( p_0 - p_K ) * N_tot * ( 1 - fct_TNR ) / K
            else:
                P_EFF = p_0

        else:

            p_K = self.prob_survival()
            P_EFF = p_0 - ( p_0 - p_K ) * ( N_tot / K )**config.KEXP

        if random.random() > P_EFF:

            self.is_alive = False
            return

        self.age += 1

        self.update_maturity()    

        return

    #==============
    @timeit
    def advance_counters(self,is_breeding_season):
    #==============

        if self.sex == "female":

            if is_breeding_season:

                if not self.is_pregnant and not self.is_pseudo_pregnant and not self.is_nursing:
                  
                    if self.interestrus_timer > 0:
                    
                        self.interestrus_timer -= 1

                        if self.interestrus_timer == 0:
                            self.estrus_timer = config.ESTRUS_DURATION 
                            #self.erestrus_timer = random.randint(5, 8)

                    elif self.estrus_timer > 0:

                        self.estrus_timer -= 1
                    
                        if self.estrus_timer == 0:
                            self.interestrus_timer = config.INTERESTRUS_DURATION 

                    elif self.interestrus_timer==0 and self.estrus_timer==0:

                        self.estrus_timer = config.ESTRUS_DURATION                      

            #...Anestrus period
            else:
                self.estrus_timer = 0
                self.interestrus_timer = 0
                self.cop_count = 0

            if self.gestation_timer > 0:

                self.gestation_timer -= 1

                if self.gestation_timer == 0:

                    if self.is_pregnant:
                        self.gives_birth = True
                        self.is_pregnant = False

                    if self.is_pseudo_pregnant:
                        self.is_pseudo_pregnant = False

            if self.is_nursing:

                self.nursing_timer -= 1

                if self.nursing_timer == 0:

                    self.is_nursing = False

            self.update_activity()

        #...male
        elif self.sex == "male":

            self.dominance = self.calc_dominance()
            self.update_activity()

        else:

            print( f" # Error: invalid sex is detected ({self.sex}) )" )

        return

    #==============
    @timeit
    def prob_survival(self):
    #==============

        p_sv   = config.P_0
        p_baby = config.P_BABY
        p_male = config.P_MALE
        p_female = config.P_FEMALE
        p_TNR    = config.P_TNR

        # Kitten / Juv
        if self.age_category == "kitten" or self.age_category == "young_juvenile":
            p_sv = p_baby

        elif self.age_category == "older_juvenile":
            if self.sex == "female":
                if self.status == "TNR":
                    p_sv = p_TNR
                else:
                    p_sv = p_female

            elif self.sex == "male":
            
                if self.status == "intact":
                    p_sv =  p_male
                elif self.status == "TNR": # Castrated
                    p_sv =  0.999051
                elif self.status == "TVHR": # Vasectomized
                    p_sv =  p_male 

        elif self.age_category == "adult":

            if self.sex == "female":
                if self.status == "TNR": # Spayed
                    p_sv = p_TNR 
                else:
                    p_sv = p_female

            elif self.sex == "male": # Male

                if self.status == "intact":
                   p_sv =  p_male
                elif self.status == "TNR": # Castrated
                   p_sv =  p_TNR
                elif self.status == "TVHR": # Vasectomized
                   p_sv =  p_male

        else:

            print( f" # Error: invalid age category is detected ({self.age_category}) )" )

        return p_sv

    #==============
    @timeit
    def reproduce(self,N_tot):
    #==============

        if self.gives_birth:
    
            newborns = []

            r = random.random() 

            litter_size = 3 if r <= 0.4 else 4
            
            for _ in range(litter_size):
                sex = random.choice(["male", "female"])

                unit = self.unit if sex == "female" else 0 
                newborns.append(Cat(sex, 0, unit=unit))
            
            self.gives_birth = False 
            self.is_nursing = True
            self.nursing_timer = config.WEANING_AGE

            return newborns

        return []

    #==============
    @timeit
    def update_maturity(self):
    #==============

        if self.age >= self.mature_age:

            self.age_category = "adult"
            self.update_activity()

        elif self.age >= config.AGE_OLD_JUV:

            self.age_category = "older_juvenile"

        elif self.age >= config.AGE_YOUNG_JUV:

            self.age_category = "young_juvenile"

        elif self.age >= 0:

            self.age_category = "kitten"

        else:

            print( f" # Error: invalid age is detected ({self.age}) )" )

    #==============
    @timeit
    def update_activity(self):
    #==============

        if self.age_category == "adult" and self.status in active_status:

           if self.sex == "male":

               self.is_active = True

           elif self.estrus_timer > 0 and not self.is_pregnant and not self.is_pseudo_pregnant and not self.is_nursing:

               self.is_active = True

           else:

               self.is_active = False            

        else:

            self.is_active = False

        return 



