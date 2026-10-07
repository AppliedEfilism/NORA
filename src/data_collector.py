# data_collector.py
import csv
import numpy as np
import config
from src.timer import timeit

eps = 1e-16

class DataCollector:
    def __init__(self):
        self.history = []
        self.annual_hist = []
        self.annual_adult_females = set()
        self.annual_total_pregnancy = 0
        self.annual_total_pseudo_pregnancy = 0
        self.annual_total_litter = 0
              
    #================
    @timeit
    def collect(self, model, method, day, prev_cats, new_cats, dead_cats):
    #================

        #------------
        # annual reproduction statistics
        #------------
        day_of_year = day_of_year = ( (day-1) % 365 ) + 1
        if config.BREEDING_SEASON_START <= day_of_year <= config.BREEDING_SEASON_END:        
            if day_of_year == config.BREEDING_SEASON_START:
                self.annual_adult_females.clear()
                self.annual_total_pregnancy = 0
                self.annual_total_pseudo_pregnancy = 0
                self.annual_total_litter = 0

            adult_females = [ c for c in model.cats if c.age_category=="adult" and c.sex=="female" ]
            self.annual_adult_females.update(adult_females)

            self.annual_total_pregnancy += model.daily_pregnancy
            self.annual_total_pseudo_pregnancy += model.daily_pseudo_pregnancy
            self.annual_total_litter += model.daily_litter

        if day_of_year == 365:

            Naaf = len( self.annual_adult_females ) + eps
            annual_mean_pregnancy = self.annual_total_pregnancy / Naaf
            annual_mean_pseudo_pregnancy = self.annual_total_pseudo_pregnancy / Naaf
            annual_mean_litter = self.annual_total_litter / Naaf

            annual_stats ={
                        "annual_mean_pregnancy": annual_mean_pregnancy,
                        "annual_mean_pseudo_pregnancy": annual_mean_pseudo_pregnancy,
                        "annual_mean_litter": annual_mean_litter
                        }
            self.annual_hist.append(annual_stats)

        #------------ 
        # birth and death statistics
        #------------
        daily_births = len( new_cats )
        daily_deaths = len( dead_cats )
        N_prev  = len( prev_cats )


        #...populations
        N_baby         = sum(1 for c in prev_cats if c.age_category == "kitten" or c.age_category == "young_juvenile")
        N_adult_male   = sum(1 for c in prev_cats if c.age_category == "adult" and c.sex == "male")
        N_adult_female = sum(1 for c in prev_cats if c.age_category == "adult" and c.sex == "female")

        #...deaths
        daily_dead_baby         = sum(1 for c in dead_cats if c.age_category == "kitten" or c.age_category == "young_juvenile")
        daily_dead_adult_male   = sum(1 for c in dead_cats if c.age_category == "adult" and c.sex == "male")
        daily_dead_adult_female = sum(1 for c in dead_cats if c.age_category == "adult" and c.sex == "female")        
   
        #...early survival judgement
        daily_early_death = sum(1 for c in dead_cats if c.age <= 180 ) 
        daily_early_survived = sum(1 for c in model.cats if c.age == 180 ) 
        daily_preventable_death = daily_early_death
        if method=="LC":
            daily_preventable_death += sum(1 for c in dead_cats if c.status == "LC" and c.age>180 )

        #...survival rate
        P_sv_baby         = 1 - daily_dead_baby / ( N_baby + eps )
        P_sv_adult_male   = 1 - daily_dead_adult_male / ( N_adult_male + eps ) 
        P_sv_adult_female = 1 - daily_dead_adult_female / ( N_adult_female + eps )

        #...death and birth rate
        r_birth = daily_births / ( N_prev + eps )
        r_death = daily_births / ( N_prev + eps )
        
        #...pregnancy rate
        rate_pregnancy = model.daily_pregnancy / ( model.daily_mating + eps )
          
        female_cats  = [ c for c in model.cats if c.sex=="female" ] 
        female_units = list(range(1, model.num_units + 1))
        for c in female_cats:
            if c.unit in female_units:
                female_units.remove(c.unit)

        nonempty_units = model.num_units - len( female_units )
        
        stats = {
            "day": day,
            "N_tot": len(model.cats),
            "N_male": sum(1 for c in model.cats if c.sex == "male"),
            "N_female": sum(1 for c in model.cats if c.sex == "female"),
            "N_kitten": sum(1 for c in model.cats if c.age_category == "kitten"),
            "N_young_juv": sum(1 for c in model.cats if c.age_category == "young_juvenile"),
            "N_older_juv": sum(1 for c in model.cats if c.age_category == "older_juvenile"),
            "N_adult": sum(1 for c in model.cats if c.age_category == "adult"),
            "N_adult_female": sum(1 for c in model.cats if c.sex == "female" and c.age_category == "adult"),
            "N_pregnant": sum(1 for c in model.cats if c.sex == "female" and c.is_pregnant),
            "N_pseudo_pregnant": sum(1 for c in model.cats if c.sex == "female" and c.is_pseudo_pregnant),
            "N_nursing": sum(1 for c in model.cats if c.sex == "female" and c.is_nursing),
            "N_treated_male": sum(1 for c in model.cats if c.sex == "male" and not c.status == "intact" ),
            "N_treated_female": sum(1 for c in model.cats if c.sex == "female" and not c.status == "intact" ),            
            "daily_capture_male": model.daily_capture_male,
            "daily_capture_female": model.daily_capture_female,
            "daily_active_units": model.daily_active_units,
            "daily_mating": model.daily_mating,
            "daily_pregnancy": model.daily_pregnancy,
            "daily_pseudo_pregnancy": model.daily_pseudo_pregnancy,
            "daily_litter": model.daily_litter,
            "daily_early_death": daily_early_death,
            "daily_early_survived": daily_early_survived,
            "daily_preventable_death": daily_preventable_death,
            "P_sv_baby": P_sv_baby,
            "P_sv_adult_male": P_sv_adult_male,
            "P_sv_adult_female": P_sv_adult_female,
            "r_birth": r_birth,
            "r_death": r_death,
            "rate_pregnancy": rate_pregnancy,
            "nonempty_units": nonempty_units,
            "daily_births": daily_births,
            "daily_deaths": daily_deaths
        }
        self.history.append(stats)
 
    #==============      
    @timeit
    def export_csv(self, irun, fout_log, filename="simulation_results.csv"):
    #==============

        def mean_per_year( f, axis=0  ):

            f_mean = np.sum( f, axis=axis ) * 365 / config.NSTEP

            return f_mean

        if config.OUTPUT_DIAG:

            breed_season_duration = config.BREEDING_SEASON_END - config.BREEDING_SEASON_START
            mothering_duration = config.PREGNANCY_DURATION + config.WEANING_AGE

            maxmum_annual_pregnancy = breed_season_duration / mothering_duration 

            #...load data
            N_tot = [ data["N_tot"] for data in self.history ]
            N_female = [ data["N_female"] for data in self.history ]
            P_sv_baby = [ data["P_sv_baby"] for data in self.history ]
            P_sv_adult_male = [ data["P_sv_adult_male"] for data in self.history ]
            P_sv_adult_female = [ data["P_sv_adult_female"] for data in self.history ]
            N_adult_female = [ data["N_adult_female"] for data in self.history ]
            nonempty_units = [ data["nonempty_units"] for data in self.history ]
            daily_early_survived = [ data["daily_early_survived"] for data in self.history ]
            daily_early_death    = [ data["daily_early_death"] for data in self.history ]
            daily_preventable_death = [ data["daily_preventable_death"] for data in self.history ]
            daily_births = [ data["daily_births"] for data in self.history ]
            daily_mating = [ data["daily_mating"] for data in self.history ]
            daily_pregnancy = [ data["daily_pregnancy"] for data in self.history ]


            annual_mean_pregnancy = [ data["annual_mean_pregnancy"] for data in self.annual_hist ]
            annual_mean_pseudo_pregnancy = [ data["annual_mean_pseudo_pregnancy"] for data in self.annual_hist ]
            annual_mean_litter = [ data["annual_mean_litter"] for data in self.annual_hist ]           

            total_preventable_death = np.sum( np.array( daily_preventable_death ) )

            #...pregnancy events
            annual_pregnancy = np.mean( np.array(annual_mean_pregnancy ) ) 
            annual_pseudo_pregnancy = np.mean( np.array( annual_mean_pseudo_pregnancy ) ) 
            annual_litter = np.mean( np.array( annual_mean_litter ) )
            pregnancy_per_mating = sum( daily_pregnancy )  / sum( daily_mating )

            #...early survival rate
            total_early_survived = np.sum( np.array(daily_early_survived) )
            total_early_death = np.sum( np.array(daily_early_death) )
            early_survival_rate = total_early_survived / ( total_early_survived + total_early_death + eps )
            
            #...mean values
            mean_N_tot = np.mean( N_tot )
            mean_P_sv_baby = np.mean( P_sv_baby )
            mean_P_sv_adult_male = np.mean( P_sv_adult_male )
            mean_P_sv_adult_female = np.mean( P_sv_adult_female )           

            print( f"\n*** Run {irun+1} ***", file=fout_log )
            print( "=== Summary of key metrics ===\n"
                   f"{'Metric':<35} | {'Simulation result':<25} | {'Expected w/o intervention':<25}",
                   file=fout_log)
            print( "-" * 90, file=fout_log )
            print( f"{'Mean total population':<35} | {mean_N_tot:<25.2f} | {config.KCAP:<25.2f}\n"
                   f"{'Litters/year/adult female':<35} | {annual_litter:<25.6f} | {'~1.5':<25}\n"
                   f"{'Pregnancy/year/adult female':<35} | {annual_pregnancy:<25.6f} | {f'<{maxmum_annual_pregnancy:.2f}':<25}\n"
                   f"{'Pseudo pregnancy/year/adult female':<35} | {annual_pseudo_pregnancy:<25.6f} | {'---':<25}\n"                
                   f"{'Pregnancy per mating':<35} | {pregnancy_per_mating:<25.6f} | {'---':<25}\n"
                   f"{'180-day survival probability':<35} | {early_survival_rate:<25.6f} | {'~0.1--0.25':<25}\n"
                   f"{'Preventable deaths':<35} | {total_preventable_death:<25} | {'---':<25}\n"
                   f"{'Daily P_sv (kitten and young juv.)':<35} | {mean_P_sv_baby:<25.6f} | {config.P_BABY:<25.6f}\n"
                   f"{'Daily P_sv (adult male)':<35} | {mean_P_sv_adult_male:<25.6f} | {config.P_MALE:<25.6f}\n"
                   f"{'Daily P_sv (adult female)':<35} | {mean_P_sv_adult_female:<25.6f} | {config.P_FEMALE:<25.6f}\n"
                   #f"{'Adult females in each unit':<35} | {np.mean(unit_size):<25.2f} | {'2--11 ?':<25}\n"
                   ,file=fout_log
                   )

        fieldnames = self.history[0].keys()
        with open(filename, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.history)

        return
