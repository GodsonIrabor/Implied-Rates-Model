"""
This script will load in live data and properly digest it. 
Additionally it will store local data into a CSV to prevent rate limiting
"""
import os
import time
import requests
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

class LiveCurveWithCache:
    """
    This requires an API key from FRED, once data is fetched live it will be sorted and stored 
    in a CSV file and then retrieved only when unable to fetch live data
    """
    def __init__(self, cache_filename: str="data/treasury_curve_cache.csv", cache_expiry_seconds: int=86400):
        self.cache_path= cache_filename
        self.cache_expiry = cache_expiry_seconds
        self.api_key = os.environ.get("FRED_API_KEY")# this line is what causes the search in the local enviroment for API key
    # Fred Constant Maturity Ticker Mapping
        self.series_mapping = {1: "DGS1", 2: "DGS2", 3:"DGS3", 5: "DGS5", 7: "DGS7", 10: "DGS10", 20: "DGS20", 30:"DGS30"
         }

    def _is_cache_valid(self) -> bool:  
      """
      Checks if their is a cached data file and checks if it is within the timelimit to refresh 
      the data
     """
      if not os.path.exists(self.cache_path):
         return False
      return (time.time() - os.path.getmtime(self.cache_path)) < self.cache_expiry
    
    def get_curve_data(self) -> tuple[np.ndarray, np.ndarray]:
       #Will typically use cached data first to minimize rate limiting
       if self._is_cache_valid():
          print(f"[Cache Hit] Loading curve configurations from {'self.cache_path'}")
          df_cached = pd.read_csv(self.cache_path)
          return df_cached["Maturity"].values, df_cached["Par_Yield"].values
       print("[Cache Miss] Retrieveing data from FRED API servers")
       return self._fetch_and_cache_live_data()
    
    def _fetch_and_cache_live_data(self) ->tuple[np.ndarray, np.ndarray]:
       #Fetches data from FRED API and commits to cache
       if not self.api_key:
          raise ValueError(
             "Error: 'FRED_API_KEY' environment variable not set. \n " 
             "Run: export FRED_API_KEY='your_key_here' in terminal before running the program"
          )
       maturities = []
       yields = []
       base_url = "https://api.stlouisfed.org/fred/series/observations"

       try:
            for tenor, series_id in self.series_mapping.items():
             
             
             params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 5
            }
             response=requests.get(base_url, params=params, timeout=10)
             response.raise_for_status()
             data = response.json()
             for observation in data.get("observations", []):
                 value_str = observation.get("value")
                 if value_str and value_str != ".":
                     maturities.append(tenor)
                     yields.append(float(value_str) / 100.0)
                     break
            
            
            
            maturities_arr = np.array(maturities, dtype=float)
            yields_arr = np.array(yields, dtype=float)

            sort_indices = np.argsort(maturities_arr)
            maturities_arr = maturities_arr[sort_indices]
            yields_arr = yields_arr[sort_indices]

            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            df_to_cache = pd.DataFrame({"Maturity": maturities_arr, "Par_Yield": yields_arr})
            df_to_cache.to_csv(self.cache_path, index=False)
            print(f"[Cache Saved] file stored at '{self.cache_path}'")

            return maturities_arr, yields_arr
       except Exception as e:
          if os.path.exists(self.cache_path):
             print(f"[Warning] Live API fetch failed ({e}). Using cached data at this point")
             df_cached = pd.read_csv(self.cache_path)
             return df_cached["Maturity"].values, df_cached["Par_Yield"].values
          raise ConnectionError(f"API request failed: {str(e)}")
       
    @staticmethod
    def fit_continuous_spline(raw_maturities: np.ndarray, raw_yields: np.ndarray) ->tuple[np.ndarray, np.ndarray, np.ndarray]:
               
               """
               We will use cubic spline interpolation to construct a continuous
               1Y-30YR curve and then calculate smooth implied forwards.
               """
               #Arranges a continuous grid from 1Y to 30Y
               continuous_maturities = np.arange(1, 31, dtype=float)
               #We now fit the cubic spline to raw par yields (match maturities and yields to interpolated yields and continuous maturities)
               spline_function = CubicSpline(raw_maturities, raw_yields, bc_type='natural')
               interpolated_par_yields = spline_function(continuous_maturities)

               #Calculating implied forward rates through continuous maturities
               #We use the  slope of the par yield to approximate how the forward rate will change
               par_slope = np.gradient(interpolated_par_yields) #NOTE: the use of np.gradient may contribute to localized distorations due to amplified twists
               implied_forwards = interpolated_par_yields + par_slope * continuous_maturities

               return continuous_maturities, interpolated_par_yields, implied_forwards


 
            
               
  

            
            
          


    
         
        
    

  