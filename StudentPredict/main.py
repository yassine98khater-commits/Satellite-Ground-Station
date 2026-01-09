# main.py
"""
Satellite Tracker - Command Line Version
Run this first to test everything works!
"""

from tle_manager import TLEManager
from tracker import SatelliteTracker
from predictor import PassPredictor
from satellite_db import get_satellite_info
from datetime import datetime

def main():
    print("=" * 60)
    print("🛰️  SATELLITE TRACKER")
    print("=" * 60)
    
    # Step 1: Download TLEs
    print("\n1. Downloading satellite data...")
    tle_mgr = TLEManager()
    
    # Download different categories
    stations = tle_mgr.download_tles('stations')
    weather = tle_mgr.download_tles('weather')
    amateur = tle_mgr.download_tles('amateur')
    
    # Step 2: Initialize tracker
    print("\n2. Initializing tracker...")
    tracker = SatelliteTracker()
    
    # Add ISS
    iss_tle = tle_mgr.get_satellite_by_name('ISS', 'stations')
    if iss_tle:
        tracker.add_satellite(iss_tle['name'], iss_tle['line1'], iss_tle['line2'])
        print(f"✓ Added: {iss_tle['name']}")
    
    # Add NOAA satellites
    for noaa_name in ['NOAA 15', 'NOAA 18', 'NOAA 19']:
        sat = tle_mgr.get_satellite_by_name(noaa_name, 'weather')
        if sat:
            tracker.add_satellite(sat['name'], sat['line1'], sat['line2'])
            print(f"✓ Added: {sat['name']}")
    
    # Step 3: Get current positions
    print("\n3. Current satellite positions:")
    print("-" * 60)
    for sat_name in tracker.satellites.keys():
        pos = tracker.get_position(sat_name)
        if pos:
            print(f"\n{sat_name}:")
            print(f"   Latitude:  {pos['latitude']:.2f}°")
            print(f"   Longitude: {pos['longitude']:.2f}°")
            print(f"   Altitude:  {pos['altitude_km']:.1f} km")
            print(f"   Azimuth:   {pos['azimuth']:.1f}°")
            print(f"   Elevation: {pos['elevation']:.1f}°")
            print(f"   Distance:  {pos['distance_km']:.1f} km")
            print(f"   Visible:   {'YES ✓' if pos['is_visible'] else 'NO ✗'}")
    
    # Step 4: Predict passes
    print("\n" + "=" * 60)
    print("4. PASS PREDICTIONS (Next 7 days)")
    print("=" * 60)
    
    predictor = PassPredictor(tracker)
    
    for sat_name in list(tracker.satellites.keys())[:2]:
        print(f"\n📡 {sat_name}")
        print("-" * 60)
        
        passes = predictor.find_passes(sat_name, duration_days=7)
        
        if passes:
            best_pass = predictor.get_best_pass(passes)
            print(f"Total passes: {len(passes)}")
            print(f"\n🌟 BEST PASS:")
            print(f"   Rise:  {best_pass['rise_time_str']}")
            print(f"   Max:   {best_pass['max_time_str']} (Elevation: {best_pass['max_elevation']:.1f}°)")
            print(f"   Set:   {best_pass['set_time_str']}")
            print(f"   Duration: {best_pass['duration_str']}")
            
            info = get_satellite_info(sat_name)
            if info.get('description'):
                print(f"\nℹ️  Info: {info['description']}")
        else:
            print("   No passes above 10° elevation in next 7 days")
    
    print("\n" + "=" * 60)
    print("✓ Tracker test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()




