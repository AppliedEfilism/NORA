# main.py  
import numpy as np
import matplotlib.pyplot as plt
import config
from src.timer import print_time_stats
from src.model import Colony
import os

ver = "1.0"

def main():

    print( f" *** Simulation started *** "  )

    N_mean = []
    nrun = config.NRUN
    nstep = config.NSTEP

    project_dir = config.DIR_OUT
    os.makedirs( project_dir, exist_ok=True)
    fout_master_log = open( f"{project_dir}/out_master_log.txt", "w")

    P_cap = 1 - ( 1 - config.P_CAPTURE ) ** ( config.TRAP_DAYS *  config.TRAP_EPISODES )
    print( f"Annual capture probability: {P_cap:.3f}" )

    # log
    print( f"=== Code info ===\n"
           f"  Code Name     : NORA\n"
           f"  Version       : {ver}\n"
           f"  Copyright     : (c) 2026 Applied Efilism Society\n\n"
           f"=== Basic parameters ===\n"
           f"Annual capture probability: {P_cap:.3f}\n", 
           file=fout_master_log)

    for method in config.METHOD:

        print( f"\n # === Simulation with neutering method {method} started === "  )

        out_dir = f"{config.DIR_OUT}/{method}"

        os.makedirs(out_dir, exist_ok=True)

        #...open log file
        fout_log = open( f"{out_dir}/out_log.txt", "w")

        all_histories = []

        for irun in range( nrun ):

            cat_colony = Colony(config.N0)

            for step in range( 1, nstep+1 ):

                cat_colony.advance(step,method)

            if config.OUTPUT_DIAG:
                filename = os.path.join( out_dir, f"{config.FDATA}_{irun}.csv")
                cat_colony.collector.export_csv( irun, fout_log, filename )
        
            all_histories.append( cat_colony.N_history )

            print( f" # run {irun+1} is completed " )

        N_mean.append( np.mean(all_histories, axis=0) )

    if config.SHOW_PLOT:

        print( " # Plotting the result... " )

        color_list = ["k","b","r","grey"]       
        linestyles = ["-","--","-.",":"]
        Nmax = np.max( np.array(N_mean) )

        for i, method in enumerate(config.METHOD):
            plt.plot(N_mean[i], label=f"{method}", 
                    color=color_list[i],
                    ls = linestyles[i] )

        plt.title( f"Annual capture probability: {P_cap:.3f}" )
        plt.xlabel("Time (day)")
        plt.ylabel("Population")
        plt.xlim(0,nstep)
        plt.ylim(0,1.2*Nmax)
        plt.grid(True, alpha=0.5)
        plt.legend()
        plt.show()

    print_time_stats( fout_master_log )
    print( f" # *** Simulation completed *** "  )

if __name__ == "__main__":
    main()
    
