#!/usr/bin/env python3
"""Арифметическая проверка текстовой спецификации транспортного интерфейса."""
from math import pi, tan, radians, log, cos

# Canonical station values
R = 5000.0
r0 = 150.0
omega = 0.0443
angle = radians(10.0)

# Interface dimensions
opening = 30.0
clear_bore = 8.0
bore_wall = 0.40
bore_od = clear_bore + 2 * bore_wall
lane_pitch = 12.0
shaft_envelope = 30.0
cabin_od = 7.0
cabin_len = 16.0
empty_mass = 5_000.0
full_mass = 15_000.0
people_per_cabin = 100
cycle_s = 17.8 * 60

# Two 8 m channels with 12 m center distance
channel_pack = lane_pitch + bore_od
assert channel_pack < shaft_envelope, (channel_pack, shaft_envelope)
assert cabin_od + 2 * 0.5 <= clear_bore

# Two independent shafts/corridors, each with 2 directions and 2 cabin pairs.
capacity_per_corridor = 2 * people_per_cabin / (17.8 / 60.0)
capacity_per_cylinder = 2 * capacity_per_corridor
capacity_one_corridor_out = capacity_per_corridor / 2

# Spiral section. For phi = tan(theta) ln(R/r), ds = sec(theta) dr.
spiral_length = (R - r0) / cos(angle)
spiral_time = (1.0 / (omega * tan(angle) / 2.0)) * (1.0 / cos(angle)) * log(R / r0)
axial_section = 2506.0
route_length = axial_section + spiral_length

# Bearing annulus and average axial pressure.
bearing_diameter = 400.0
bearing_width = 3.0
bearing_area = pi * bearing_diameter * bearing_width
axial_load = 1.0e10
avg_pressure = axial_load / bearing_area / 1.0e6

# Work of transport from the document's 24.52 kJ/kg basis.
work_per_kg = 24_520.0
empty_kwh = work_per_kg * empty_mass / 3.6e6
full_kwh = work_per_kg * full_mass / 3.6e6

assert abs(spiral_length - 4923.0) < 5.0, spiral_length
assert abs(route_length - 7429.0) < 5.0, route_length
assert 14.0 * 60 < spiral_time < 16.0 * 60, spiral_time
assert 2.6 < avg_pressure < 2.7, avg_pressure
assert abs(empty_kwh - 34.06) < 0.2, empty_kwh
assert abs(full_kwh - 102.17) < 0.5, full_kwh
assert abs(capacity_per_corridor - 674.1573) < 1.0
assert abs(capacity_per_cylinder - 1348.3146) < 2.0

print("PASS")
print(f"channel pack: {channel_pack:.2f} m < shaft opening {shaft_envelope:.2f} m")
print(f"spiral length: {spiral_length:.1f} m; total route: {route_length:.1f} m")
print(f"spiral travel time: {spiral_time/60:.2f} min")
print(f"bearing mean pressure: {avg_pressure:.3f} MPa")
print(f"capacity: {capacity_per_corridor:.1f} person/h per corridor; {capacity_per_cylinder:.1f} per cylinder")
print(f"descent work: {empty_kwh:.2f} kWh empty; {full_kwh:.2f} kWh full")
