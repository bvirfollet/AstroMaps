from matplotlib import pyplot as plt
from skyfield import almanac
from skyfield.timelib import Timescale
from skyfield.api import load, Topos, Star, N, S, E, W, load, wgs84
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from skyfield.almanac import find_discrete, risings_and_settings
import datetime
import pytz
import json

from abc import ABC, abstractmethod
import json
from memory_profiler import profile

from CelestialBody import *


def linear(t, list_coords):
    pass


class PositionHistory():
    def __init__(self, body=None):
        '''
        Init method
        '''
        self.positions = {}
        self._interp = linear

    def __dict__(self):
        res = {}
        for key in self.positions.keys():
            res[key] = []
            for time, lon in self.positions[key].items():
                res[key].append((time.timestamp(), lon.degrees))
        return res

    def set_interp(self, interp):
        self._interp = interp

    def compute_position(self, t):
        return self._interp(t)

    def save(self, filename):
        # Write results to JSON file
        if filename:
            with open(filename, 'w') as f:
                json.dump(self.__dict__(), f, indent=4)

    def load(self, filename):
        pass

    def add_position(self, body, t, position):
        '''
        Add a position in the "known position"
        :param t:
        :param position:
        :return:
        '''
        if isinstance(body, str) and isinstance(t, datetime.datetime):
            if body not in self.positions.keys():
                self.positions[body] = {}
            self.positions[body][t] = position

    # Add methods for interpolation and other computations
    def plot(self, bodies):
        times = {
            'all': []
        }
        longitudes = {}

        for body in bodies:
            if body not in self.positions.keys():
                raise Exception("No records for body " + body)
            else:
                times[body] = []
                longitudes[body] = []

        for body in bodies:
            for time, position in self.positions[body].items():
                if time not in times['all']:
                    times['all'].append(time)
                if time not in times[body]:
                    times[body].append(time)

        for body in bodies:
            for time in times['all']:
                if time in times[body]:
                    longitudes[body].append(self.positions[body][time].degrees)
                else:
                    idx_low = None
                    idx_high = None
                    for idx, body_time in times[body]:
                        if body_time < time:
                            idx_low = idx

                    idx_high = idx_low + 1
                    longitudes[body].append((self.positions[body][idx_high] + self.positions[body][idx_low]) / 2)

        # Create the plot
        plt.figure(figsize=(10, 6))  # Adjust figure size as needed
        # Add horizontal grid lines for zodiac signs
        zodiac_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        for i in range(12):
            plt.axhline(y=i * 30, color='gray', linestyle='--', linewidth=0.5)  # Grid lines at 30-degree intervals
            plt.text(-0.05, i * 30 + 15, zodiac_signs[i], ha='right', va='center',
                     transform=plt.gca().get_yaxis_transform())  # Sign labels
        # Plot altitudes
        for body in bodies:
            plt.plot(list(map(lambda x: x.strftime("%d/%m/%Y %Hh%M"), times['all'])), longitudes[body], label=body, marker='o')
            plt.text(times['all'][-1].strftime("%d/%m/%Y %Hh%M"), longitudes[body][-1], body, va='center')

        plt.xlabel('times')
        #plt.ylabel('Longitude (degrees)')
        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
        #plt.grid(True)
        plt.show()
