from skyfield import almanac
from skyfield.api import load, Topos, Star, N, S, E, W, load, wgs84
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from skyfield.almanac import find_discrete, risings_and_settings
import datetime
import pytz
import argparse
import json

from abc import ABC, abstractmethod
import json
from memory_profiler import profile

# Load the ephemeris file once as a global variable
planets = load('de422.bsp')
ts = load.timescale(builtin=True)

class CelestialBody(ABC):
    @abstractmethod
    def calculate_position(self, t, observer):
        pass

class Planet(CelestialBody):
    def __init__(self, planet_name, barycenter_id):
        self.planet_name = planet_name
        self.barycenter_id = barycenter_id

    def calculate_position(self, t, observer):
        planet_barycenter = planets[self.barycenter_id]
        return planet_barycenter.at(t)

class Ascendant(CelestialBody):
    def __init__(self):
        self.earth = planets['earth']

    def calculate_position(self, t, observer):
        horizon = observer.at(t).observe(self.earth).apparent().horizon
        f = risings_and_settings(eph, Star(ra_hours=0, dec_degrees=0), horizon)
        times, ups = find_discrete(t - 12 * ts.hours, t + 12 * ts.hours, f)
        for ti, up in zip(times, ups):
            if up:
                ascendant_degree = horizon.from_altaz(
                    alt_degrees=0,
                    az_degrees=180 - horizon.at(ti).apparent().altaz()[1].degrees
                ).radec()[0].hours * 30
                ascendant_sign = int(ascendant_degree / 30) + 1
                return ascendant_sign