import time
from typing import Callable, Iterable, List, Type

import carla
import numpy as np


def get_timestamp_formatted():
    return time.strftime('%y%m%d_%H%M%S')


def get_traffic_lights(world: carla.World) -> carla.ActorList:
    return world.get_actors().filter('traffic.traffic_light*')


def get_vehicles(world: carla.World) -> carla.ActorList:
    return world.get_actors().filter('vehicle*')


def get_traffic_light_groups(world) -> List[List[carla.TrafficLight]]:
    """
    Get the traffic light groups. The implementation is a bit hacky, because the direct method is not
    directly available in the API.
    """
    traffic_light_map = {tl.id: tl for tl in get_traffic_lights(world)}

    # create a set of unique group ids
    unique_id_groups = set()
    for tl in traffic_light_map.values():
        group_ids = tuple(sorted(sibling.id for sibling in tl.get_group_traffic_lights()))
        unique_id_groups.add(group_ids)

    # sort by lowest group id
    unique_id_groups = sorted(unique_id_groups, key=lambda group: group[0])

    # replace ids with traffic light objects
    return [[traffic_light_map[tl_id] for tl_id in group] for group in unique_id_groups]


def reset_all_traffic_light_groups(world: carla.World):
    """
    Calls reset_group() on the traffic light with the lowest id in each group.
    """
    for group in get_traffic_light_groups(world):
        if len(group) > 0:
            group[0].reset_group()


def deep_map(fn: Callable, iter: Iterable, depth: int = 0, dtype: Type = list):
    if depth == 0:
        return dtype(map(fn, iter))
    return dtype([deep_map(fn, el, depth - 1, dtype=dtype) for el in iter])


def convert_location(location):
    return np.array([location.x, location.y, location.z], dtype=np.float32)


def convert_locations(locations):
    return np.array([convert_location(loc) for loc in locations], dtype=np.float32)