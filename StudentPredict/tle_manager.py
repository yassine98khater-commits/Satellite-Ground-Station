# tle_manager.py
"""
Manages TLE (Two-Line Element) data downloads and parsing
"""

import requests
import os
from datetime import datetime
from config import TLE_SOURCES, DATA_FOLDER

class TLEManager:
    def __init__(self):
        self.tle_sources = TLE_SOURCES
        self.satellites = {}
        
        # Create data folder if it doesn't exist
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
    
    def download_tles(self, category='active'):
        """Download TLEs from CelesTrak"""
        print(f"Downloading {category} satellites...")
        
        try:
            url = self.tle_sources[category]
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Save to file
            filename = os.path.join(DATA_FOLDER, f'{category}.tle')
            with open(filename, 'w') as f:
                f.write(response.text)
            
            # Parse and store
            satellites = self.parse_tle(response.text)
            self.satellites[category] = satellites
            
            print(f"✓ Downloaded {len(satellites)} satellites")
            return satellites
            
        except Exception as e:
            print(f"✗ Error downloading TLEs: {e}")
            return []
    
    def parse_tle(self, tle_data):
        """Parse TLE data into list of satellites"""
        lines = tle_data.strip().split('\n')
        satellites = []
        
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                satellites.append({
                    'name': lines[i].strip(),
                    'line1': lines[i + 1].strip(),
                    'line2': lines[i + 2].strip()
                })
        
        return satellites
    
    def load_from_file(self, category):
        """Load TLEs from saved file"""
        filename = os.path.join(DATA_FOLDER, f'{category}.tle')
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                tle_data = f.read()
            return self.parse_tle(tle_data)
        else:
            return None
    
    def get_satellite_by_name(self, name, category='active'):
        """Get specific satellite TLE by name"""
        if category not in self.satellites:
            sats = self.load_from_file(category)
            if sats:
                self.satellites[category] = sats
        
        if category in self.satellites:
            for sat in self.satellites[category]:
                if name.upper() in sat['name'].upper():
                    return sat
        return None