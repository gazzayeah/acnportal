from unittest import TestCase
from unittest.mock import Mock, create_autospec

import pandas as pd
import numpy as np
import os

from acnportal.acnsim import Simulator
from acnportal.acnsim.network import ChargingNetwork
from acnportal.acnsim import acndata_events
from acnportal.acnsim import sites
from acnportal.algorithms import BaseAlgorithm
from acnportal.acnsim.events import EventQueue, Event
from datetime import datetime
from acnportal.acnsim.models import EVSE

import json
import pytz
from copy import deepcopy

class TestSimulator(TestCase):
    def setUp(self):
        start = Mock(datetime)
        network = ChargingNetwork()
        evse1 = EVSE('PS-001', max_rate=32)
        network.register_evse(evse1, 240, 0)
        evse2 = EVSE('PS-002', max_rate=32)
        network.register_evse(evse2, 240, 0)
        evse3 = EVSE('PS-003', max_rate=32)
        network.register_evse(evse3, 240, 0)
        scheduler = create_autospec(BaseAlgorithm)
        events = EventQueue(events=[Event(1), Event(2)])
        self.simulator = Simulator(network, scheduler, events, start)

    def test_correct_on_init_pilot_signals(self):
        np.testing.assert_allclose(self.simulator.pilot_signals,
            np.zeros((len(self.simulator.network.station_ids), self.simulator.event_queue.get_last_timestamp() + 1)))

    def test_correct_on_init_charging_rates(self):
        np.testing.assert_allclose(self.simulator.charging_rates,
            np.zeros((len(self.simulator.network.station_ids), self.simulator.event_queue.get_last_timestamp() + 1)))

    def test_update_schedules_not_in_network(self):
        new_schedule = {'PS-001' : [24, 16], 'PS-004' : [16, 24]}
        with self.assertRaises(KeyError):
            self.simulator._update_schedules(new_schedule)

    def test_update_schedules_valid_schedule(self):
        new_schedule = {'PS-001' : [24, 16], 'PS-002' : [16, 24]}
        self.simulator._update_schedules(new_schedule)
        np.testing.assert_allclose(self.simulator.pilot_signals[:, :2], np.array([[24, 16], [16, 24], [0, 0]]))

    def test_index_of_evse_error(self):
        with self.assertRaises(KeyError):
            _ = self.simulator.index_of_evse('PS-004')

    def test_index_of_evse(self):
        idx = self.simulator.index_of_evse('PS-002')
        self.assertEqual(idx, 1)