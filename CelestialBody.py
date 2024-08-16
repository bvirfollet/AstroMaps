import gzip
from os.path import exists

from skyfield import almanac
from skyfield.api import load, Topos, Star, N, S, E, W, load, wgs84
from skyfield.data import mpc
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from skyfield.almanac import find_discrete, risings_and_settings
from skyfield.framelib import ecliptic_frame
import datetime
import pytz
import argparse
import json
import requests

from abc import ABC, abstractmethod
from memory_profiler import profile
from skyfield.units import Angle

planet_barycenters = {
        'sun': 10, 'mercury': 1, 'venus': 2, 'earth': 399, 'moon': 301, 'mars': 4,
        'jupiter': 5, 'saturn': 6, 'uranus': 7, 'neptune': 8, 'pluto': 9
    }
ts = load.timescale(builtin=True)

_loaded = False
_planets = None
_minor_planets = None


def planets():
    return _planets


def minor_planets():
    return _minor_planets


def load_database(load_minor_planet):
    # Load the ephemeris file once as a global variable
    global _loaded
    global _planets
    global _minor_planets
    if not _loaded:
        _planets = load('de422.bsp')
        if load_minor_planet and exists('MPCORB.DAT'):
            with load.open('MPCORB.DAT') as f:
                _minor_planets = mpc.load_mpcorb_dataframe(f)
                bad_orbits = _minor_planets.semimajor_axis_au.isnull()
                _minor_planets = _minor_planets[~bad_orbits]
                _minor_planets = _minor_planets.set_index('designation', drop=False)
                print(_minor_planets.shape[0], 'minor _planets _loaded')
        _loaded = True


class CelestialBody(ABC):
    @abstractmethod
    def observe(self, at):
        pass

    @abstractmethod
    def calculate_position(self, observer, t):
        pass


class Body(CelestialBody):
    def __init__(self, planet_name, barycenter_id, db):
        self.name = planet_name
        self.barycenter_id = barycenter_id
        if db is planets():
            self._body = db[self.barycenter_id]
        else:
            self.name = self.name.split()[-1]
            orbit = minor_planets().loc[planet_name]
            self._body = planets()['sun'] + mpc.mpcorb_orbit(orbit, ts, GM_SUN)

    def __call__(self):
        return self._body
    def observerAt(self, geopos):
        return (self._body + geopos)

    def observe(self, at):
        return self._body.at(at)

    def calculate_position(self, observer, t):
        position = observer.at(t).observe(self._body).apparent()
        lat, lon, distance = position.frame_latlon(ecliptic_frame)
        #altitude, azimut, distance = position.altaz()
        return {
            'latitude': lat,
            'longitude': lon,
            'distance': distance
        }


class Ascendant(CelestialBody):
    def observe(self, at):
        return self._body.at(at)

    def __init__(self):
        self.name = "Asc"
        self.barycenter_id = 399  # earth géo
        self._body = planets()[self.barycenter_id]

    def calculate_position(self, observer, t):
        position = observer.at(t).observe(self._body)
        lat, lon, distance = position.frame_latlon(ecliptic_frame)
        res = lon.degrees - 90
        if res < 0:
            res = res + 360
        return {
            'latitude': lat,
            'longitude': Angle(degrees=res),
            'distance': distance
        }
