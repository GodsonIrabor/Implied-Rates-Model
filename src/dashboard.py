"""
This file will serve as the Yield Curve Visualization component.
specificially this will be connected to the main execution file
features continuous tenor mapping for smooth spline visualizations.
"""

import matplotlib.pyplot as plt
import numpy as np

def generate_rv_dashboard(engine, fly_metrics: dict, t_short: float, t_intermediate: float, t_long: float) -> None:
    #Generates and displays the RV metrics plot
    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(15, 5.5))
    signals = engine.identifying_sector_value()

    #Plot 1: Showcases Smooth Implied Forward Yields vs Interpolated Par Yields
    ax1.plot(engine.maturities, engine.par_yields * 100, color='black', label="Interpolated Par Curve")
    ax1.plot(engine.maturities, engine.implied_forwards * 100, color='blue', linestyle='--', label="Implied Forward")

    #Using Distinct color coding to highlight Cheap/Expensive maturity sectors
    for i, maturity in enumerate(engine.maturities):
        if signals[i] == 'teal':
            ax1.scatter(maturity, engine.implied_forwards[i] * 100, color='teal', s=140, marker='^', zorder=3)
        elif signals[i] == 'crimson':
            ax1.scatter(maturity, engine.implied_forwards[i] * 100, color='crimson', s=140, marker='v', zorder=3)
        else:# Lower size for neutral points so execution signals pop visually
            ax1.scatter(maturity, engine.implied_forwards[i] * 100, color='grey', s=40, marker='o', zorder=3)
    
    ax1.set_title("Implied Forwards vs Par Yields Deviations", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Maturity Tenor (Years)")
    ax1.set_ylabel("Yield / Return Rate (%)")
    ax1.grid(True, linestyle=':', alpha=0.5)
    ax1.legend(frameon=True, facecolor='white', edgecolor='lightgrey')

    #Plot 2: Showcases Barbell vs Bullet Strategy Analysis
    legs = [f'{t_short}Y Barbell Leg', f'{t_intermediate}Y Bullet Node', f'{t_long}Y Barbell Leg']
    idx_s, idx_i, idx_l = fly_metrics["tenor_indices"]

    #Pulling the exact interpolated yields from the engine using dynamically resolved indices
    yields_rv = [engine.par_yields[idx_s] * 100, engine.par_yields[idx_i] * 100, engine.par_yields[idx_l] *100]
    
    ax2.bar(legs, yields_rv, color=['darkorange', 'teal', 'darkorange'], alpha=0.8, width=0.4, edgecolor='black')
    ax2.axhline(fly_metrics["barbell_yield"] * 100, color='crimson', linestyle='--', linewidth=1.5,
                label=f"Duration-Linked Barbell Yield ({fly_metrics['barbell_yield']*100:.2f}%)")
    
    ax2.set_title(f"Carry Premium (Bullet Advantage ={fly_metrics['carry_pickup_bps']:.1f} bps)",
                  fontsize=11, fontweight='bold')
    ax2.set_ylabel("Yield (%)")
    ax2.set_ylim(min(yields_rv) - 0.5, max(yields_rv) +0.5)
    ax2.grid(True, linestyle=':', alpha=0.5)
    ax2.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='lightgrey')

    plt.tight_layout()
    plt.show()
            
