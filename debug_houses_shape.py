
import swisseph as swe
import numpy as np
from datetime import datetime

t = datetime.now()
jd = swe.julday(t.year, t.month, t.day, t.hour + t.minute/60.0)
lat, lon = -34.6, -58.4

res = swe.houses(jd, lat, lon, b'P')
cusps = res[0]
ascmc = res[1]

print(f"JD: {jd}")
print(f"Cusps Raw Length: {len(cusps)}")
print(f"Cusps Raw: {cusps}")
print(f"AscMC Raw Length: {len(ascmc)}")
print(f"AscMC Raw: {ascmc}")

# Simulating VectorizedHouses logic
cusps_list = [cusps[1:]] 
print(f"Processed Cusps Length (slicing [1:]): {len(cusps_list[0])}")

# Check numpy array shape
arr = np.array(cusps_list)
print(f"Numpy Shape: {arr.shape}")
