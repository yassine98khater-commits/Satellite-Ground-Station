# predictor.py
"""
Satellite pass prediction and signal analysis
"""

from skyfield.api import load
from datetime import datetime, timedelta
import numpy as np
from config import MIN_ELEVATION

class PassPredictor:
    def __init__(self, tracker):
        self.tracker = tracker
        self.ts = tracker.ts
    
    def find_passes(self, sat_name, duration_days=7, min_elevation=MIN_ELEVATION):
        """Find all passes of a satellite above minimum elevation"""
        
        if sat_name not in self.tracker.satellites:
            return []
        
        satellite = self.tracker.satellites[sat_name]
        observer = self.tracker.observer
        
        # Time range
        t0 = self.ts.now()
        t1 = self.ts.utc(t0.utc_datetime() + timedelta(days=duration_days))
        
        # Find events (rise, culminate, set)
        t, events = satellite.find_events(observer, t0, t1, altitude_degrees=min_elevation)
        
        passes = []
        current_pass = {}
        
        for ti, event in zip(t, events):
            if event == 0:  # Rise
                current_pass['rise_time'] = ti
                current_pass['rise_az'] = self._get_azimuth(satellite, observer, ti)
                
            elif event == 1:  # Culmination (maximum elevation)
                current_pass['max_time'] = ti
                pos = self.tracker.get_position(sat_name, ti)
                current_pass['max_elevation'] = pos['elevation']
                current_pass['max_azimuth'] = pos['azimuth']
                
            elif event == 2:  # Set
                current_pass['set_time'] = ti
                current_pass['set_az'] = self._get_azimuth(satellite, observer, ti)
                
                # Calculate duration
                if 'rise_time' in current_pass:
                    duration = (ti.utc_datetime() - current_pass['rise_time'].utc_datetime()).total_seconds()
                    current_pass['duration_seconds'] = duration
                    
                    # Format times
                    current_pass['rise_time_str'] = current_pass['rise_time'].utc_iso()
                    current_pass['max_time_str'] = current_pass['max_time'].utc_iso()
                    current_pass['set_time_str'] = ti.utc_iso()
                    
                    # Duration in readable format
                    hours = int(duration // 3600)
                    minutes = int((duration % 3600) // 60)
                    seconds = int(duration % 60)
                    current_pass['duration_str'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    passes.append(current_pass.copy())
                    current_pass = {}
        
        return passes
    
    def _get_azimuth(self, satellite, observer, time):
        """Get azimuth at specific time"""
        difference = satellite - observer
        topocentric = difference.at(time)
        alt, az, distance = topocentric.altaz()
        return az.degrees
    
    def get_best_pass(self, passes):
        """Get the pass with highest elevation"""
        if not passes:
            return None
        return max(passes, key=lambda p: p.get('max_elevation', 0))
    
    def predict_signal_quality(self, sat_name, frequency_mhz=145.800, antenna_gain_dbi=3):
        """Estimate if satellite signal is receivable"""
        
        position = self.tracker.get_position(sat_name)
        
        if not position or position['elevation'] < 0:
            return {
                'receivable': False,
                'reason': 'Below horizon',
                'elevation': position['elevation'] if position else 0
            }
        
        # Simple path loss calculation (Friis equation)
        distance_m = position['distance_km'] * 1000
        
        # Free space path loss (dB)
        fspl_db = 20 * np.log10(distance_m) + 20 * np.log10(frequency_mhz) + 32.45
        
        # Atmospheric attenuation (simplified)
        elevation = position['elevation']
        if elevation > 45:
            atm_loss = 0.5
        elif elevation > 10:
            atm_loss = 2.0
        else:
            atm_loss = 5.0
        
        total_loss = fspl_db + atm_loss - antenna_gain_dbi
        
        # Typical satellite transmitter power ~1W (30 dBm)
        # Typical receiver sensitivity ~ -120 dBm
        estimated_signal = 30 - total_loss
        
        return {
            'receivable': estimated_signal > -120 and elevation > MIN_ELEVATION,
            'elevation': elevation,
            'azimuth': position['azimuth'],
            'distance_km': position['distance_km'],
            'estimated_signal_dbm': estimated_signal,
            'signal_quality': 'Excellent' if estimated_signal > -90 else 
                            'Good' if estimated_signal > -100 else
                            'Fair' if estimated_signal > -110 else 'Poor'
        }