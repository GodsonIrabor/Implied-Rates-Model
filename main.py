"""
Execution file for both an nuanced view of the Forward Market compared to Par Yields 
and evaulating when to allocate towards a Barbell or Bullet strategy"""

from src.curve_engine import YieldCurveEngine
from src.dashboard import generate_rv_dashboard
from src.data_loader import LiveCurveWithCache

def main():
    print("==========")
    print("Live market data ingestion initializing")

    try:
        #Initalizing data retrieval framework
        loader = LiveCurveWithCache()
        raw_maturities, raw_yields = loader.get_curve_data()
        
        #Running Cubic Spline Transformation to generate a smooth, continuous tenor curve
        print("Fitting Cublic spline to uneven maturity tenors")
        maturities, par_yields, implied_forwards = LiveCurveWithCache.fit_continuous_spline(raw_maturities, raw_yields)

        #Initalizing calculation engine
        engine = YieldCurveEngine(maturities, par_yields, implied_forwards)

        # Construct Barbell/Bullet strategy using smooth interpolated points
        t_short, t_intermediate, t_long = 5,12,25
        fly_metrics = engine.construct_immunized_fly(t_short,t_intermediate, t_long)

        #Output summary of execution metrics
        w_short, w_long = fly_metrics["weights"]
        print("\n>>> Strategy Execution Metrics:")
        print(f"Target Structure: {t_intermediate}Y Bullet vs Barbell ({t_short}Y / {t_long}Y split)")
        print(f"Calculated Weights: Short Leg ({t_short}Y ={w_short*100:.1f}% | Long Leg ({t_long}Y) ={w_long*100:.1f}%")
        print(f"  *Net Duration Footprint: Balanced perfectly at {t_intermediate}.0 Years.")
        print(f"Initial Yield Advantage (Bullet Carry): {fly_metrics['carry_pickup_bps']:.1f} bps")
        print(f"Market-Implied Forward Hurdle at {t_intermediate}Y: {fly_metrics['forward_hurdle']*100:.2f}%")

        generate_rv_dashboard(engine, fly_metrics, t_short, t_intermediate, t_long)
    except Exception as e:
        print(f"\n [Engine didn't work]: {str(e)}")

if __name__ =="__main__":
    main()