# satellite_db.py
"""
Database of satellite information with flexible name matching
"""

SATELLITE_DATABASE = {
    # Space Stations
    'ISS (ZARYA)': {
        'norad_id': 25544,
        'origin': 'International (USA, Russia, ESA, Japan, Canada)',
        'purpose': 'Space Station - Scientific Research',
        'deployment': '1998-11-20',
        'frequencies_mhz': [145.800, 437.800],
        'type': 'Crewed Space Station',
        'mass_kg': 419725,
        'description': 'The International Space Station is a modular space station in low Earth orbit. It serves as a microgravity and space environment research laboratory.',
        'website': 'https://www.nasa.gov/mission_pages/station/main/index.html'
    },
    
    'TIANGONG': {
        'norad_id': 48274,
        'origin': 'China',
        'purpose': 'Space Station - Scientific Research',
        'deployment': '2021-04-29',
        'frequencies_mhz': [437.200],
        'type': 'Crewed Space Station',
        'description': 'Chinese space station in low Earth orbit.',
        'active': True
    },
    
    # Weather Satellites
    'NOAA 15': {
        'norad_id': 25338,
        'origin': 'USA (NOAA)',
        'purpose': 'Weather Satellite - APT Imagery',
        'deployment': '1998-05-13',
        'frequencies_mhz': [137.620],
        'type': 'Polar Orbiting Weather Satellite',
        'description': 'NOAA-15 provides weather imagery via APT (Automatic Picture Transmission) on 137.620 MHz.',
        'active': True
    },
    
    'NOAA 18': {
        'norad_id': 28654,
        'origin': 'USA (NOAA)',
        'purpose': 'Weather Satellite - APT Imagery',
        'deployment': '2005-05-20',
        'frequencies_mhz': [137.9125],
        'type': 'Polar Orbiting Weather Satellite',
        'description': 'NOAA-18 transmits APT weather images on 137.9125 MHz. Great for receiving weather satellite images.',
        'active': True
    },
    
    'NOAA 19': {
        'norad_id': 33591,
        'origin': 'USA (NOAA)',
        'purpose': 'Weather Satellite - APT Imagery',
        'deployment': '2009-02-06',
        'frequencies_mhz': [137.100],
        'type': 'Polar Orbiting Weather Satellite',
        'description': 'NOAA-19 provides global weather data and APT imagery on 137.100 MHz.',
        'active': True
    },
    
    'METEOR-M2': {
        'norad_id': 40069,
        'origin': 'Russia',
        'purpose': 'Weather Satellite - LRPT Imagery',
        'deployment': '2014-07-08',
        'frequencies_mhz': [137.100],
        'type': 'Polar Orbiting Weather Satellite',
        'description': 'Russian weather satellite with LRPT digital transmission.',
        'active': True
    },
    
    'METEOR-M2 2': {
        'norad_id': 44387,
        'origin': 'Russia',
        'purpose': 'Weather Satellite - LRPT Imagery',
        'deployment': '2019-07-05',
        'frequencies_mhz': [137.900],
        'type': 'Polar Orbiting Weather Satellite',
        'description': 'Second generation Russian weather satellite.',
        'active': True
    },
    
    # Amateur Radio Satellites
    'SO-50': {
        'norad_id': 27607,
        'origin': 'USA (AMSAT)',
        'purpose': 'Amateur Radio Communications',
        'deployment': '2002-12-10',
        'frequencies_mhz': [145.850, 436.795],
        'type': 'Amateur Radio Satellite (CubeSat)',
        'description': 'Popular amateur radio FM repeater satellite.',
        'active': True
    },
    
    'AO-91': {
        'norad_id': 43017,
        'origin': 'USA (AMSAT)',
        'purpose': 'Amateur Radio Communications',
        'deployment': '2017-11-18',
        'frequencies_mhz': [145.960, 435.250],
        'type': 'Amateur Radio Satellite (CubeSat)',
        'description': 'FM voice repeater for amateur radio operators.',
        'active': True
    },
    
    'AO-92': {
        'norad_id': 43137,
        'origin': 'USA (AMSAT)',
        'purpose': 'Amateur Radio Communications',
        'deployment': '2018-01-12',
        'frequencies_mhz': [145.880, 435.350],
        'type': 'Amateur Radio Satellite (CubeSat)',
        'description': 'FM repeater satellite for ham radio.',
        'active': True
    },
    
    # CubeSats
    'DUCHIFAT-1': {
        'norad_id': 40021,
        'origin': 'Israel',
        'purpose': 'Educational CubeSat',
        'deployment': '2014-06-19',
        'frequencies_mhz': [145.825],
        'type': 'CubeSat (1U)',
        'mass_kg': 1,
        'description': 'Israeli educational CubeSat for testing space-based communication systems.',
        'active': True
    },
    
    'BEESAT-4': {
        'norad_id': 40074,
        'origin': 'Germany (TU Berlin)',
        'purpose': 'Technology Demonstration',
        'deployment': '2013-04-19',
        'frequencies_mhz': [435.950],
        'type': 'CubeSat (1U)',
        'description': 'Berlin Experimental and Educational Satellite for technology testing.',
        'active': True
    },
    
    'FUNCUBE-1': {
        'norad_id': 39444,
        'origin': 'UK/Netherlands (AMSAT)',
        'purpose': 'Educational / Amateur Radio',
        'deployment': '2013-11-21',
        'frequencies_mhz': [145.935],
        'type': 'CubeSat (1U)',
        'description': 'Educational satellite with telemetry beacon.',
        'active': True
    }
}


def get_satellite_info(sat_name):
    """Get detailed information about a satellite with flexible name matching"""
    
    # First try exact match
    if sat_name in SATELLITE_DATABASE:
        return SATELLITE_DATABASE[sat_name]
    
    # Try partial matching (case insensitive)
    sat_name_upper = sat_name.upper()
    
    for db_name, info in SATELLITE_DATABASE.items():
        db_name_upper = db_name.upper()
        
        # Check if satellite name contains database key or vice versa
        if db_name_upper in sat_name_upper or sat_name_upper in db_name_upper:
            return info
        
        # Check NORAD ID if it's in the name
        if str(info.get('norad_id', '')) in sat_name:
            return info
    
    # No match found
    return {
        'description': f'No detailed information available for {sat_name}',
        'purpose': 'Unknown',
        'origin': 'Unknown',
        'type': 'Satellite',
        'deployment': 'Unknown'
    }


def list_cubesats():
    """List all CubeSats in database"""
    return [name for name, info in SATELLITE_DATABASE.items() 
            if 'CubeSat' in info.get('type', '')]


def search_satellite(query):
    """Search for satellites by name or keyword"""
    query_upper = query.upper()
    results = []
    
    for name, info in SATELLITE_DATABASE.items():
        if (query_upper in name.upper() or 
            query_upper in info.get('purpose', '').upper() or
            query_upper in info.get('origin', '').upper()):
            results.append((name, info))
    
    return results