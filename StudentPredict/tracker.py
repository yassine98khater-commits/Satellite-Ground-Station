# tracker.py
"""
Core satellite tracking functionality using Skyfield
"""

from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timedelta
import numpy as np
from config import OBSERVER_LAT, OBSERVER_LON, OBSERVER_ELEVATION

class SatelliteTracker:
    def __init__(self):
        self.ts = load.timescale()
        self.observer = wgs84.latlon(OBSERVER_LAT, OBSERVER_LON, OBSERVER_ELEVATION)
        self.satellites = {}
        
        print(f"Observer location: {OBSERVER_LAT}°N, {OBSERVER_LON}°E")
    
    def add_satellite(self, name, line1, line2):
        """Add a satellite to track"""
        try:
            sat = EarthSatellite(line1, line2, name, self.ts)
            self.satellites[name] = sat
            return True
        except Exception as e:
            print(f"Error adding satellite {name}: {e}")
            return False
    
    def get_position(self, sat_name, time=None):
        """Get satellite position at a given time"""
        if sat_name not in self.satellites:
            return None
        
        if time is None:
            time = self.ts.now()
        
        satellite = self.satellites[sat_name]
        
        # Get geocentric position
        geocentric = satellite.at(time)
        subpoint = wgs84.subpoint(geocentric)
        
        # Get observer-relative position
        difference = satellite - self.observer
        topocentric = difference.at(time)
        alt, az, distance = topocentric.altaz()
        
        # Check if in sunlight
        sunlit = satellite.at(time).is_sunlit(load('de421.bsp'))
        
        return {
            'time': time.utc_iso(),
            'latitude': subpoint.latitude.degrees,
            'longitude': subpoint.longitude.degrees,
            'altitude_km': subpoint.elevation.km,
            'azimuth': az.degrees,
            'elevation': alt.degrees,
            'distance_km': distance.km,
            'is_visible': alt.degrees > 0,
            'sunlit': sunlit,
            'velocity_km_s': satellite.at(time).velocity.km_per_s
        }
    
    def get_all_positions(self, time=None):
        """Get positions of all tracked satellites"""
        positions = {}
        for sat_name in self.satellites.keys():
            positions[sat_name] = self.get_position(sat_name, time)
        return positions