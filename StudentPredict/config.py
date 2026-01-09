# config.py
"""
Configuration file - EDIT YOUR LOCATION HERE
"""

# YOUR OBSERVER LOCATION (Change these!)
OBSERVER_LAT = 48.11704  #  latitude
OBSERVER_LON = -1.64126  #  longitude  
OBSERVER_ELEVATION = 37  # meters above sea level

# TLE Sources
TLE_SOURCES = {
    'active': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',
    'amateur': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle',
    'cubesat': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=cubesat&FORMAT=tle',
    'weather': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
    'stations': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle'
}

# Prediction settings
MIN_ELEVATION = 10  # Minimum elevation for pass predictions (degrees)
PREDICTION_DAYS = 7  # How many days ahead to predict

# Data folder
DATA_FOLDER = 'data'