import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

eps = 1e-16
INIT_TRAP = 2001

# Directories and filenames
dir_proj = f"./sample"
fout   = f"{dir_proj}/fig_NORA_comp.pdf" 
output = PdfPages( fout )
out_log = f"{dir_proj}/out_comp.txt" 

# Options
rasterized = True
Cost_neut_m = 15000
Cost_neut_f = 30000

METHOD_CONFIG = {
    "NONE": {"color": "k",    "ls": "-",  "label": "No action"},
    "TNR":  {"color": "b",    "ls": "--", "label": "TNR"},
    "TVHR": {"color": "r",    "ls": "-.", "label": "TVHR"},
    "LC":   {"color": "grey", "ls": ":",  "label": "LC"}
}

#...all possible options
ALL_METHODS = ["NONE", "TNR", "TVHR", "LC"]

#...
METHODS    = [ ]

N_tot  = []
N_male = []
N_neut_m = []
N_mating = []
N_nontreat_m = []
N_birth = []
N_death = []
N_prev_death = []
N_early_death = []
N_early_survived = []

for method in ALL_METHODS:

    out_dir  = f"{dir_proj}/{method}"
    filename = f"out_results_*.csv"

    print( f" reading data from {out_dir}" )

    csv_files = glob.glob( os.path.join( out_dir, filename ) )
    if not csv_files:
        print(f" The files '{filename}' are not found in {out_dir} ")
        continue

    METHODS.append(method)

    df_list = [ pd.read_csv(f) for f in csv_files ]
    df_concat = pd.concat(df_list)
    df_mean = df_concat.groupby("day").mean().reset_index()
    df_std  = df_concat.groupby("day").std().reset_index()

    # Load data
    time = df_mean["day"]
    total_time = time.max() - time.min()

    #...Population composition
    N_tot.append( df_mean["N_tot"] )
    N_male.append( df_mean["N_male"] )
    N_mating.append( df_mean["daily_mating"] )
    N_birth.append( df_mean["daily_births"] )
    N_death.append( df_mean["daily_deaths"] )
    N_prev_death.append( df_mean["daily_preventable_death"] )
    N_early_survived.append( df_mean["daily_early_survived"] )
    N_early_death.append( df_mean["daily_early_death"] )
   
    if method=="TNR":
        w = np.array(df_mean["N_male"]) - np.array(df_mean["N_treated_male"])
    else:
        w = np.array(df_mean["N_male"])
    N_nontreat_m.append(w)

# Set range
time_range = [time.min(), time.max()]

# Process data
Marking = np.nansum( np.array(N_nontreat_m)[:,INIT_TRAP:], axis=1 )
Noise   = np.nansum( np.array(N_mating)[:,INIT_TRAP:], axis=1 )
Marking = Marking / Marking[0] 
Noise   = Noise / Noise[0] 

cat_days = np.nansum( np.array( N_tot )[:,INIT_TRAP:], axis=1 )
Total_early_survived = np.nansum( np.array( N_early_survived )[:,INIT_TRAP:], axis=1 )
Total_early_death = np.nansum( np.array( N_early_death )[:,INIT_TRAP:], axis=1 )
early_survival_rate = Total_early_survived / ( Total_early_survived + Total_early_death )
Total_prev_death = np.nansum( np.array( N_prev_death )[:,INIT_TRAP:] , axis=1 )
Total_adult_LC   = Total_prev_death - Total_early_death

Total_births = np.nansum( np.array( N_birth )[:,INIT_TRAP:], axis=1 )
Total_deaths = np.nansum( np.array( N_death )[:,INIT_TRAP:], axis=1 )

#===========
# Output text data
#===========
print( f" writing summary text {out_log}" )

with open(out_log, mode="w") as f:
    f.write("=== Comparison between different intervention methods ===\n\n")
    
    header = f"{'Value':<30} | " + " | ".join([f"{method:<15}" for method in METHODS])
    f.write(header + "\n")
    f.write("-" * len(header) + "\n") 
    
    # function to dynamically create data rows
    def write_row(label, data_array, fmt=".2f", is_int=False):

        row_contents = []
        for val in data_array:
            if is_int:
                # insert comma
                row_contents.append(f"{int(val):<15,}")
            else:
                # float data
                row_contents.append(f"{val:<15{fmt}}")
                
        row_str = f"{label:<30} | " + " | ".join(row_contents)
        f.write(row_str + "\n")
    
    write_row("Cat-days", cat_days, fmt=".2f", is_int=False)
    write_row("Total early survived", Total_early_survived, is_int=True)
    write_row("Total early death", Total_early_death, is_int=True)
    write_row("180-day survival rate", early_survival_rate, is_int=False)
    write_row("Total preventable death", Total_prev_death, is_int=True)
    write_row("Total adult LC", Total_adult_LC, is_int=True)
    write_row("Total births", Total_births, is_int=True)
    write_row("Total deaths", Total_deaths, is_int=True)
    write_row("Marking (Normalized)", Marking, fmt=".4f", is_int=False)
    write_row("Noise (Normalized)", Noise, fmt=".4f", is_int=False)

# Visualization options
ALPHA_FILL = 0.2 
LW_MEAN = 2.0 

def lower_bound(mean_s, std_s):
    return np.maximum(0, mean_s - std_s)
def upper_bound(mean_s, std_s):
    return mean_s + std_s

current_colors = [METHOD_CONFIG[m]["color"] for m in METHODS]

#=============
# Total population
#=============
plt.figure(figsize=(8, 5))
plt.title("History of total population",fontsize=12)
Nmax = np.max( N_tot )
for i, method in enumerate(METHODS):

    cfg = METHOD_CONFIG[method]

    plt.plot(time, N_tot[i], 
            color=cfg["color"], ls=cfg["ls"], lw=3, 
            label=f"{cfg['label']} (Cat-days: {int(cat_days[i]):,})", rasterized=rasterized)
plt.xlabel("Time (day)",fontsize=12)
plt.ylabel("Population",fontsize=12)
plt.ylim(0, 1.2*Nmax )
plt.xlim(time_range)
plt.legend(fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
output.savefig()
plt.close()

#=============
# Birth and death
#=============
fig, axes = plt.subplots( 1, 2, figsize=(8, 5) )

axes[0].bar( METHODS, Total_early_survived, color="tab:blue", label="180-day survived" )
axes[0].bar( METHODS, Total_early_death, color="tab:red", label="Deaths under 180 days", bottom=Total_early_survived )
axes[0].legend()
axes[0].set_xticks(range(len(METHODS)))
axes[0].set_xticklabels([METHOD_CONFIG[m]["label"] for m in METHODS])
axes[0].set_ylim( 0, 1.2 * np.max( Total_prev_death ) )
axes[0].set_title("Cumulative number of kittens")

axes[1].bar( METHODS, Total_early_death, color="tab:blue", label="Kittens and juveniles" )
axes[1].bar( METHODS, Total_adult_LC, color="tab:red", label="Adults", bottom=Total_early_death )
axes[1].legend()
axes[1].set_xticks(range(len(METHODS)))
axes[1].set_xticklabels([METHOD_CONFIG[m]["label"] for m in METHODS])
axes[1].set_ylim( 0, 1.2 * np.max( Total_prev_death ) )
axes[1].set_title("Preventable deaths")


plt.tight_layout()
output.savefig()
plt.close()

#...
fig, axes = plt.subplots( 1, 2, figsize=(8, 5) )

axes[0].bar( METHODS, Total_births, color=current_colors )
axes[0].set_title("Total births")
axes[0].set_xticks(range(len(METHODS)))
axes[0].set_xticklabels([METHOD_CONFIG[m]["label"] for m in METHODS])

axes[1].bar( METHODS, Total_deaths, color=current_colors )
axes[1].set_title("Total deaths")
axes[1].set_xticks(range(len(METHODS)))
axes[1].set_xticklabels([METHOD_CONFIG[m]["label"] for m in METHODS])

plt.tight_layout()
output.savefig()
plt.close()

#=============
# Nuisance 
#=============
fig, axes = plt.subplots( 1, 2, figsize=(8, 5) )

axes[0].bar( METHODS, Marking, color=current_colors )
axes[0].set_title("Marking")
axes[0].set_ylabel("Nuisance measure (normalized)")
axes[0].set_xticks(range(len(METHODS)))
axes[0].set_xticklabels([METHOD_CONFIG[m]["label"] for m in METHODS])

axes[1].bar( METHODS, Noise, color=current_colors )
axes[1].set_title("Noise")
axes[1].set_ylabel("Nuisance measure (normalized)")
axes[1].set_xticks(range(len(METHODS)))
axes[1].set_xticklabels([METHOD_CONFIG[m]["label"] for m in METHODS])

plt.tight_layout()
output.savefig()
plt.close()

output.close()

print( f" Plotting figures '{fout}' completed " )
