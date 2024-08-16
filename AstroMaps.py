from skyfield import almanac
from skyfield.api import load, Topos, Star, N, S, E, W, load, wgs84
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from skyfield.almanac import find_discrete, risings_and_settings
import datetime
import pytz
import argparse
import json
import requests

from abc import ABC, abstractmethod
#from memory_profiler import profile

from CelestialBody import planets, minor_planets
from Paths import *

hour = 3600.0
day = 24* hour
month = 30.5 * day
year = 12 * month

def download_file(uri, filename):
    """
    Downloads a file from the specified URI and saves it with the given filename.

    Args:
        uri: The URI of the file to download.
        filename: The name to save the downloaded file as.
    """

    try:
        response = requests.get(uri, stream=True)  # Stream the download for large files
        response.raise_for_status()  # Raise an exception for bad status codes

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"File downloaded successfully as {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    return False


class AstroChart:
    def __dict__(self):
        return {
            'date': self.date_time,
            'location': self.location,
            'positions': self.compute_positions()
        }

    def __init__(self, date_time, latitude, longitude, use_minor_planets=False, elevation=0):
        self.use_minor_planets = use_minor_planets
        load_database(self.use_minor_planets)
        self.date_time = date_time
        self.location = Topos(latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation)
        self.geopos = wgs84.latlon(latitude * N, longitude * W)
        self._ts = load.timescale(builtin=True)
        self._t = self._ts.utc(self.date_time)
        self._celestial_bodies = {}
        self._init_bodies()
        self._observer = self.getBody('earth').observerAt(self.geopos) # self.getOrbit('earth') + self.geopos

    def _init_bodies(self):
        # Add planets
        for planet_name, barycenter_id in planet_barycenters.items():
            planet = Body(planet_name, barycenter_id, planets())
            self._celestial_bodies[planet_name] = planet

        if self.use_minor_planets:
            # Add minor planets
            for planet_name in minor_planets()['designation']:
                minor_planet = Body(planet_name, -1, minor_planets())
                self._celestial_bodies[planet_name.split()[-1]] = minor_planet

        # Add ascendant
        ascendant = Ascendant()
        self._celestial_bodies['Asc'] = ascendant

    def getBodyNames(self):
        return self._celestial_bodies.keys()

    def compute_positions(self):
        res = {}
        for body in self._celestial_bodies.keys():
            res[body] = self.compute_position(body)
        return res

    def getOrbit(self, bodyname):
        """
        Provide accessor to a celestial body or an interesting point
        :param bodyname:
        :return:
        """
        res = None
        if bodyname in self._celestial_bodies.keys():
            res = self._celestial_bodies[bodyname]()
        return res

    def getBody(self, bodyname):
        """
        Provide accessor to a celestial body or an interesting point
        :param bodyname:
        :return:
        """
        res = None
        if bodyname in self._celestial_bodies.keys():
            res = self._celestial_bodies[bodyname]
        return res

    def compute_position(self, body_name):
        body = self.getBody(body_name)
        return body.calculate_position(self._observer, self._t)


#@profile
def main():
    # Set default values
    default_location = Topos('48.8566 N', '2.3522 E')  # Paris coordinates
    default_time = datetime.datetime.now(pytz.utc)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Calculate celestial positions.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format", default=default_time.strftime('%Y-%m-%d'))
    parser.add_argument("--time", help="Time in UTC HH:MM:SS format", default=default_time.strftime('%H:%M:%S'))
    parser.add_argument("--dtime", help="difference of time from now (HH:MM:SS format)", default=0)
    parser.add_argument("--latitude", type=float, help="Latitude in degrees",
                        default=default_location.latitude.degrees)
    parser.add_argument("--longitude", type=float, help="Longitude in degrees",
                        default=default_location.longitude.degrees)
    parser.add_argument("--output", help="Output JSON file name", default="celestial_positions.json")
    parser.add_argument("--minor_planets", action='store_true',
                        help="Include minor planets in calculations")  # New argument
    parser.add_argument("--tracks", help="Include minor planets in calculations", default='all')  # New argument
    parser.add_argument("--sampling", help="Interval for history (in sec)", type=float, default=5*day)
    parser.add_argument("--span", help="Interval of time to monitor in history (in sec)", type=float, default=9*month)# New argument
    args = parser.parse_args()

    # Convert date and time strings to datetime object
    date_time = datetime.datetime.strptime(args.date + ' ' + args.time, '%Y-%m-%d %H:%M:%S')
    if args.dtime:
        dtime = datetime.datetime.strptime(args.date + ' ' + args.dtime, '%Y-%m-%d %H:%M:%S').timestamp()
        date_time = datetime.datetime.fromtimestamp(date_time.timestamp() + dtime)
    date_time = pytz.utc.localize(date_time)

    if args.minor_planets:
        if not exists('MPCORB.DAT.gz'):
            if not download_file('https://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT.gz', 'MPCORB.DAT.gz'):
                print("Error downloading MPC")
                exit(-1)

        if not exists('MPCORB.DAT'):
            with gzip.open('MPCORB.DAT.gz', 'rb') as f_in:
                with open('MPCORB.DAT', 'wb') as f_out:
                    for it in range(43):
                        f_in.readline()
                    for it in range(20):
                        f_out.write(f_in.readline())

    history = PositionHistory()
    body_names = None
    it = date_time.timestamp()
    while 1:
        it = it + args.sampling
        if it > date_time.timestamp() + args.span:
            break

        sample_time = datetime.datetime.fromtimestamp(it)
        sample_time = pytz.utc.localize(sample_time)
        sample_chart = AstroChart(sample_time, args.latitude, args.longitude)
        body_names = ['jupiter', 'saturn', 'neptune', 'mars', 'venus', 'mercury', 'sun']
        for body_name in body_names:
            body_pos = sample_chart.compute_position(body_name)
            history.add_position(body_name, sample_time, body_pos["longitude"])
    history.plot(body_names)
    history.save(args.output)

    # Calculate celestial positions (lazy loading)
    chart = AstroChart(date_time, args.latitude, args.longitude)
    positions = chart.compute_positions()

    signe = [ 'Bélier', 'Taureau', 'Gémeaux', 'Cancer', 'Lion',
              'Vierge', 'Balance', 'Scorpion', 'Sagitaire',
              'Capricorne', 'Verseau', 'Poisson' ]

    # Afficher les résultats
    for body_name, position in positions.items():
        idx = int(position['longitude'].degrees / 30)
        degre_signe = position['longitude'].degrees % 30
        print(f"{body_name}:")
        # print(f"  longitude: {position['longitude']}")
        print(f"  Signe: {signe[idx]}")
        print(f"  Degré: {degre_signe}")


if __name__ == "__main__":
    main()
