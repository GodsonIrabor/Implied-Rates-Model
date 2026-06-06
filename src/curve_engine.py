""" The purpose of this script is to implement Antti Ilmanen's forward rate framework for identifying structual mispricing within maturity sectors and calculating directional yield cushions/breakeven
With the ultimate goal of comparing duration-neutral bullet vs barbell portfolios """

import numpy as np
class YieldCurveEngine:
    def __init__(self, maturities: np.ndarray, par_yields: np.ndarray, implied_forwards: np.ndarray):
        """Ensures the engine comes with clean numpy data arrays.
        Additionally the arrays must be equal length and sorted by maturity in ascending order."""
        if not (len(maturities) == len(par_yields) ==len(implied_forwards)):
            raise ValueError("Data Array must possess identical structural dimensions")
        #this will raise an error if arrays are not in this format
        self.maturities = np.array(maturities, dtype=float)
        self.par_yields=np.array(par_yields, dtype=float)
        self.implied_forwards =np.array(implied_forwards, dtype=float)

    def calculate_yield_cushions(self)-> np.ndarray:
        
        """
        Calculating break-even yield cushions, this is a core point of Ilmanen's work which highlights the useful of forward rate analysis
        """
        return (self.implied_forwards -self.par_yields) * 10000
    
    def identifying_sector_value(self, threshold_bps: float =20.0) -> list[str]:
    
        """
        Evaluates whether a maturity sector is expensive or cheap based on the yield cushion within 
        the maturity range. String color tags are used to identify potential execution alerts.
        """
        cushions = self.calculate_yield_cushions()
        signals = []
        for cushion in cushions:
            if cushion > threshold_bps: # This signal indicates that the maturity sector is structually cheap
                signals.append('teal')
            elif cushion < -threshold_bps: # This indicates the opposites, the maturity sector is structually rich/expensive
                signals.append('crimson')
            else:
                signals.append('grey') # This would indicate flat/neutral
        return signals
    
    def construct_immunized_fly(self, t_short: float, t_intermediate: float, t_long: float) -> dict:
        """
        Develops  a duration-linked Bullet vs Barbell Portfolio 
        which is immune against parallel yield curve shifts
        Formula: w: weight, w_short + w_long = 1
        w_short * t_short + w_long * t_long = t_intermediate
        """
        for t in [t_short, t_intermediate, t_long]:
            if t not in self.maturities:
                raise KeyError(f"Target Tenor {t}Y missing from data array profile.") # a check  to ensure that the desired maturity is in the array
        #Using dynamic index lookups to match maturities with tenors
        idx_s =np.where(self.maturities ==t_short)[0][0]
        idx_i = np.where(self.maturities ==t_intermediate)[0][0]
        idx_l =np.where(self.maturities ==t_long)[0][0]
        
        #Calculating the risk-neutral duration weight.
        w_long = (t_intermediate - t_short) / (t_long - t_short)
        w_short = 1.0 - w_long
        #Pulling underyling yields for portfolio construction
        y_short = self.par_yields[idx_s]
        y_bullet = self.par_yields[idx_i]
        y_long = self.par_yields[idx_l]

        #Relevant calculations to identify barbell yield vs bullet and carry pickup
        barbell_yield = (w_short * y_short) + (w_long * y_long)
        carry_pickup_bps = (y_bullet - barbell_yield) * 10000

        return {
            "weights": (w_short, w_long),
            "tenor_indices": (idx_s, idx_i, idx_l),
            "bullet_yield": y_bullet,
            "barbell_yield": barbell_yield,
            "carry_pickup_bps":carry_pickup_bps,
            "forward_hurdle": self.implied_forwards[idx_i]

        }         
        
