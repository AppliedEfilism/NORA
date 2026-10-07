import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

eps = 1e-16

#================
# Functions
#================
def mean_per_year( f, total_time, axis=0  ):

    f_mean = np.sum( f, axis=axis ) * 365 / total_time

    return f_mean

def lower_bound(mean_s, std_s):
    return np.maximum(0, mean_s - std_s)
def upper_bound(mean_s, std_s):
    return mean_s + std_s

#================
# Directory path
#================
#...method and data directory
method   = "NONE" 
dir_proj = f"./sample"
filename = f"out_results_*.csv"
out_dir  = f"{dir_proj}/{method}"

#================
# Output file 
#================
fout     = f"{dir_proj}/fig_NORA_diag_{method}.pdf"
output   = PdfPages( fout )

#...visualization options
rasterized = True
ALPHA_FILL = 0.2
LW_MEAN = 2.0 # 平均線の太さ

LABEL_MAP = {
    "NONE": "No action",
    "TNR": "TNR",
    "TVHR": "TVHR",
    "LC": "LC"
}

#================
# Cost (yen)
#================
unit_cost_m = 15000
unit_cost_f = 30000

#================
# Read data
#================
csv_files = glob.glob( os.path.join( out_dir, filename ) )
if not csv_files:
    print(f" The files '{filename}' are not found in {out_dir} ")
    exit()

df_list = [ pd.read_csv(f) for f in csv_files ]
df_concat = pd.concat(df_list)
df_mean = df_concat.groupby("day").mean().reset_index()
df_std  = df_concat.groupby("day").std().reset_index()

#...yearly data
df_mean['year'] = (df_mean['day'] // 365) + 1
df_yearly_days  = df_mean.groupby('year').size().reset_index(name='days_in_year')
df_yearly_sum   = df_mean.groupby('year').sum().reset_index()
df_yearly = pd.merge(df_yearly_sum, df_yearly_days, on='year')
df_yearly['scale_factor'] = 365.0 / df_yearly['days_in_year']

#================
# Process data
#================

#----------------
# Time parameters
#----------------
time = df_mean["day"]
total_time = time.max() - time.min()
time_range = [time.min(), time.max()]

#----------------
# Population composition
#----------------
N_tot  = df_mean["N_tot"]
std_N_tot  = df_std["N_tot"]
N_male = df_mean["N_male"]
N_feml = df_mean["N_female"]
N_adlt   = df_mean["N_adult"]
N_adlt_f = df_mean["N_adult_female"]
N_kttn   = df_mean["N_kitten"]
N_yngj   = df_mean["N_young_juv"]
N_oldj   = df_mean["N_older_juv"]
N_preg   = df_mean["N_pregnant"]
N_psdo   = df_mean["N_pseudo_pregnant"]
N_nurs   = df_mean["N_nursing"]

mean_adult_female = np.nanmean( N_adlt_f )

rate_male = N_male / N_tot
rate_mom  = ( N_preg + N_nurs ) / ( N_adlt_f + eps )
rate_baby = ( N_kttn + N_yngj ) / ( N_tot + eps )

mean_male_rate = np.nanmean(rate_male)
mean_mom_rate  = np.nanmean(rate_mom)
mean_baby_rate = np.nanmean(rate_baby)

#----------------
# Intervention and cost
#----------------
N_capt_m = df_mean["daily_capture_male"]
N_capt_f = df_mean["daily_capture_female"]
cost_m = unit_cost_m * N_capt_m
cost_f = unit_cost_f * N_capt_f
cost_m_tot = np.sum( cost_m )
cost_f_tot = np.sum( cost_f )

#----------------
# Mating and pregnancy
#----------------
daily_mating = df_mean["daily_mating"]
daily_pregnancy = df_mean["daily_pregnancy"]
daily_pseudo_pregnancy = df_mean["daily_pseudo_pregnancy"]
daily_litter = df_mean["daily_litter"]

#----------------
# Death and survival
#----------------
cumulative_early_survived = np.cumsum( np.array( df_mean["daily_early_survived"] ) )
cumulative_early_death    = np.cumsum( np.array( df_mean["daily_early_death"] ) )

early_survival_rate = cumulative_early_survived / ( cumulative_early_survived + cumulative_early_death + eps ) 
mean_early_survival = np.nanmean(early_survival_rate)

r_birth = df_mean["r_birth"]
r_death = df_mean["r_death"]
P_sv_baby         = df_mean["P_sv_baby"]
P_sv_adult_male   = df_mean["P_sv_adult_male"]
P_sv_adult_female = df_mean["P_sv_adult_female"]

#=============
# Total population
#=============
plt.figure(figsize=(8, 5))
plt.title("History of total population")
plt.plot(time, N_tot, color="tab:blue", lw=3, label="Average Total", rasterized=rasterized)
plt.fill_between(time, lower_bound(N_tot, std_N_tot), upper_bound(N_tot, std_N_tot), 
                 color="tab:blue", alpha=ALPHA_FILL, rasterized=rasterized)

plt.xlabel("Time (day)")
plt.ylabel("Population")
plt.ylim(0, 1.2*N_tot.max())
plt.xlim(time_range)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
output.savefig()
plt.close()

#=============
# Male and Female
#=============
plt.figure(figsize=(8, 5))
plt.title("Sex composition")
plt.plot(time, N_male, lw=LW_MEAN, label="Male",   color="b", ls="-",  rasterized=rasterized)
plt.plot(time, N_feml, lw=LW_MEAN, label="Female", color="r", ls="--", rasterized=rasterized)
plt.xlabel("Time (day)")
plt.ylabel("Population")
plt.xlim(time_range)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
output.savefig()
plt.close()

#=============
# Age Categories
#=============
plt.figure(figsize=(8, 5))
plt.title("Age composition")
plt.stackplot(time, 
              df_mean["N_kitten"], df_mean["N_young_juv"], df_mean["N_older_juv"], df_mean["N_adult"],
              labels=["Kitten", "Young Juv", "Old Juv", "Adult"],
              colors=["tab:cyan", "tab:blue", "tab:orange", "tab:red"],
              alpha=0.8)

plt.xlabel("Time (day)")
plt.ylabel("Population")
plt.xlim(time_range)
plt.legend(loc="upper left")
plt.grid(True, alpha=0.3)
plt.tight_layout()
output.savefig()
plt.close()

#=============
# Female states
#=============
plt.figure(figsize=(8, 5))
plt.title(f"Number of pregnant and nursing females ({LABEL_MAP.get(method, method)})")
plt.plot(time, N_adlt_f, ls="-", color="k", lw=2,
        label=f"Total adult female (mean={np.mean(N_adlt_f):.2f})", rasterized=rasterized)
plt.plot(time, N_preg,   ls="--", color="tab:orange",
        label=f"Pregnant female (mean={np.mean(N_preg):.2f})", rasterized=rasterized)
plt.plot(time, N_psdo,   ls="-.", color="tab:purple",
        label=f"Pseudo pregnant female (mean={np.mean(N_psdo):.2f})", rasterized=rasterized)
plt.plot(time, N_nurs,   ls=":",  color="tab:green",
        label=f"Nursing female (mean={np.mean(N_nurs):.2f})", rasterized=rasterized)
plt.xlabel("Time (day)")
plt.ylabel("Population")
plt.xlim(time_range)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
output.savefig()
plt.close()

#=============
# Pregnancy events
#=============
plt.figure(figsize=(8, 5))
plt.title(f"Annual reproductive events ({LABEL_MAP.get(method, method)})")

years = df_yearly['year']
width = 0.25

# 年間換算した合計値
y_preg = df_yearly['daily_pregnancy'] * df_yearly['scale_factor']
y_pseudo = df_yearly['daily_pseudo_pregnancy'] * df_yearly['scale_factor']
y_litter = df_yearly['daily_litter'] * df_yearly['scale_factor']

plt.bar(years - width, y_preg, width=width, color="tab:orange", label=f"Pregnancy")
plt.bar(years, y_pseudo, width=width, color="tab:purple", label=f"Pseudo pregnancy")
plt.bar(years + width, y_litter, width=width, color="tab:green", label=f"Litter")

plt.xlabel("Year")
plt.ylabel("Annual Total Count")
plt.xticks(years)
plt.legend()
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
output.savefig()
plt.close()

#=============
# Population composition
#=============
plt.figure(figsize=(8, 5))
plt.title("Population composition")
plt.plot(time, rate_mom,  label=f"Rate of pregnant/nursing adult females (mean={mean_mom_rate:.2f})", ls="-", lw=LW_MEAN, rasterized=rasterized)
plt.plot(time, rate_baby, label=f"Rate of kitten/young juveniles (mean={mean_baby_rate:.2f})", ls="--", lw=LW_MEAN, rasterized=rasterized)
plt.plot(time, rate_male, label=f"Rate of males (mean={mean_male_rate:.2f})", ls="-.", lw=LW_MEAN, rasterized=rasterized)
plt.xlabel("Time (day)")
plt.ylabel("Rate")
plt.xlim(time_range)
plt.ylim(0, 1.0)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
output.savefig()
plt.close()

#=============
# Event statistics
#=============
plt.figure(figsize=(8, 5))
plt.plot(time, early_survival_rate, label=f"Rate of survival during the first 180 days", ls="-", rasterized=rasterized)
plt.xlabel("Time (day)")
plt.ylabel("Rate (accumulated value)")
plt.xlim(time_range)
plt.ylim(0, 1.0)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
output.savefig()
plt.close()

if not method=="NONE":
#=============
# Neutering cost
#=============
    plt.figure(figsize=(8, 5))
    plt.title(f"Annual intervention cost ({LABEL_MAP.get(method, method)})")
    
    y_cost_m = df_yearly['daily_capture_male'] * unit_cost_m * df_yearly['scale_factor']
    y_cost_f = df_yearly['daily_capture_female'] * unit_cost_f * df_yearly['scale_factor']
    
    plt.bar(years - 0.2, y_cost_m, width=0.4, color="b", alpha=0.7, label=f"Males (Total cost=¥{cost_m_tot:,.0f})")
    plt.bar(years + 0.2, y_cost_f, width=0.4, color="r", alpha=0.7, label=f"Females (Total cost=¥{cost_f_tot:,.0f})")
    
    plt.xlabel("Year")
    plt.ylabel("Annual cost (¥)")
    plt.xticks(years)
    # Y軸の数値を通常の整数表記にする
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    output.savefig()
    plt.close()

output.close()

print( f" Plotting figure '{fout}' completed " )
