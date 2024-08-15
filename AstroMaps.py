from skyfield import almanac
from skyfield.api import load, Topos, Star, N, S, E, W, load, wgs84
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from skyfield.almanac import find_discrete, risings_and_settings
import datetime
import pytz
import argparse
import json

from abc import ABC, abstractmethod
import argparse
import json
from memory_profiler import profile

from CelestialBody import *

def linear(t, list_coords):
    pass

class PositionHistory(ABC):
    def __init__:
        self._interp = linear
    def set_interp(self, interp):
        self._interp = interp

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def load(self):
        pass

class LinInterp_PositionHistory:
    def __init__(self):
        self.positions = []

    def add_position(self, t, position):
        self.positions.append((t, position))

    # Add methods for interpolation and other computations

class AstroChart:
    def __init__(self, date_time, latitude, longitude, elevation=0):
        self.date_time = date_time
        self.location = Topos(latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation)
        self.celestial_bodies = {}
        self.positions_calculated = False

    def calculate_positions(self):
        if not self.positions_calculated:
            ts = load.timescale(builtin=True)
            t = ts.utc(self.date_time)
            observer = self.location.at(t)

            # Add planets
            planet_barycenters = {
                'sun': 10, 'mercury': 1, 'venus': 2, 'earth': 3, 'mars': 4,
                'jupiter': 5, 'saturn': 6, 'uranus': 7, 'neptune': 8, 'pluto': 9
            }
            for planet_name, barycenter_id in planet_barycenters.items():
                planet = Planet(planet_name, barycenter_id)
                self.celestial_bodies[planet_name] = planet

            # Add ascendant
            ascendant = Ascendant()
            self.celestial_bodies['ascendant'] = ascendant

            self.positions_calculated = True

    def get_position(self, body_name):
        self.calculate_positions()  # Ensure positions are calculated
        body = self.celestial_bodies[body_name]
        t = ts.utc(self.date_time)
        observer = self.location.at(t)
        position = body.calculate_position(t, observer)
        if body_name == 'ascendant':
            return position
        else:
            alt, az, distance = observer.observe(position).apparent().altaz()
            return {
                'altitude': alt.degrees,
                'azimuth': az.degrees,
                'distance': distance.au
            }

    # Add methods for generating chart representations

@profile
def main():
    # Set default values
    default_location = Topos('48.8566 N', '2.3522 E')  # Paris coordinates
    default_time = datetime.datetime.now(pytz.utc)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Calculate celestial positions.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format", default=default_time.strftime('%Y-%m-%d'))
    parser.add_argument("--time", help="Time in UTC HH:MM:SS format", default=default_time.strftime('%H:%M:%S'))
    parser.add_argument("--latitude", type=float, help="Latitude in degrees",
                        default=default_location.latitude.degrees)
    parser.add_argument("--longitude", type=float, help="Longitude in degrees",
                        default=default_location.longitude.degrees)
    parser.add_argument("--output", help="Output JSON file name", default="celestial_positions.json")
    args = parser.parse_args()

    # Convert date and time strings to datetime object
    date_time = datetime.datetime.strptime(args.date + ' ' + args.time, '%Y-%m-%d %H:%M:%S')
    date_time = pytz.utc.localize(date_time)

    # Calculate celestial positions (lazy loading)
    chart = AstroChart(date_time, args.latitude, args.longitude)



    # Access positions (triggers calculation if not already done)
    if chart.positions_calculated:
        # Write results to JSON file
        with open(args.output, 'w') as f:
            json.dump(chart.positions_calculated, f, indent=4)

        # Afficher les résultats
        for body_name, position in chart.positions_calculated.items():
            alt, az, distance = position.apparent().altaz()
            print(f"{body_name}:")
            print(f"  Alt: {alt}")
            print(f"  Azimut: {az}")
            print(f"  Distance: {distance}")


if __name__ == "__main__":
    main()
