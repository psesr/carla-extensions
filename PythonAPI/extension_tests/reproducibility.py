import argparse
import pickle

import carla
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import random
import tqdm
from typing import List

from common import convert_location, convert_locations, deep_map, get_timestamp_formatted, \
    reset_all_traffic_light_groups


def spawn_others(
        carla_client: carla.Client,
        carla_world: carla.World,
        n_veh: int = 10,
        global_distance_to_leading_vehicle: float = 5.0,  # [m] between center to center of the vehicles objects
        global_percentage_speed_difference: float = 30.0,  # # `-20` means drive at 120% its current speed limit
        disable_unsafe_vehicles: bool = True,
        p_others_ignore_traffic_lights: float = 0.0
) -> List[carla.Actor]:
    vehicles_list = []

    traffic_manager = carla_client.get_trafficmanager(port=8000)
    traffic_manager.set_global_distance_to_leading_vehicle(global_distance_to_leading_vehicle)
    traffic_manager.global_percentage_speed_difference(global_percentage_speed_difference)
    traffic_manager.set_hybrid_physics_mode(True)  # reduces veh. dynamics computation: far away veh are just teleported
    # traffic_manager.set_synchronous_mode(True)

    blueprints = carla_world.get_blueprint_library().filter("vehicle.*")

    if disable_unsafe_vehicles:
        blueprints = [x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4]
        blueprints = [x for x in blueprints if not x.id.endswith('isetta')]
        blueprints = [x for x in blueprints if not x.id.endswith('carlacola')]
        blueprints = [x for x in blueprints if not x.id.endswith('cybertruck')]
        blueprints = [x for x in blueprints if not x.id.endswith('t2')]

    spawn_points = carla_world.get_map().get_spawn_points()
    number_of_spawn_points = len(spawn_points)

    if n_veh < number_of_spawn_points:
        random.shuffle(spawn_points)
    elif n_veh > number_of_spawn_points:
        logging.warning("requested {} veh, but could only find {} spawn points".format(n_veh, number_of_spawn_points))
        n_veh = number_of_spawn_points

    batch = []
    for n, transform in enumerate(spawn_points):
        if n >= n_veh:
            break
        blueprint = random.choice(blueprints)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)
        blueprint.set_attribute('role_name', 'autopilot')
        batch.append(carla.command.SpawnActor(blueprint, transform).then(
            carla.command.SetAutopilot(carla.command.FutureActor, True, traffic_manager.get_port())))

    for response in carla_client.apply_batch_sync(batch, True):
        if response.error:
            logging.error(response.error)
        else:
            vehicles_list.append(response.actor_id)

    actor_list = []
    for actor_id in vehicles_list:
        a = carla_world.get_actor(actor_id=actor_id)
        actor_list.append(a)
        assert a.id == actor_id
        traffic_manager.ignore_lights_percentage(a, p_others_ignore_traffic_lights)

    logging.info('{} vehicles were spawned'.format(len(vehicles_list)))

    return actor_list


def waypoint_stop_map_to_lists(wpm):
    """
    @param wpm: dict (actor_id -> waypoint stops), where waypoints stops is a list of waypoints lists
    """
    wpl = [wpm[actor_id] for actor_id in sorted(wpm.keys())]  # list of list of list of waypoints
    return deep_map(convert_locations, wpl, depth=1)


def run(ticks: int, num_vehicles: int):
    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(10.0)
    # synchronous_master = False
    world = client.get_world()
    tm = client.get_trafficmanager(port=8000)
    fps = 30

    settings_org = world.get_settings()

    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.no_rendering_mode = True
    settings.fixed_delta_seconds = 1 / fps
    tm.set_synchronous_mode(True)
    world.apply_settings(settings)

    tmp_dir = Path('tmp')
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # timestamp = get_timestamp_formatted()
    location_map = dict()

    try:
        random.seed(1234)

        # tm.initialize_random_states(1234)
        # reset_all_traffic_light_groups(world)

        vehicles = spawn_others(client, world, n_veh=num_vehicles)
        tm.reset_traffic_lights()

        # tm.initialize_random_states(1234)
        # reset_all_traffic_light_groups(world)

        # it takes some ticks until the traffic manager returns some meaningful results.
        # tick = 0
        # while len(tm.get_waypoint_buffer_map()) == 0:
        #     world.tick()
        #     tick += 1
        # print(f'Waited {tick} ticks for traffic manager initialization.')

        # tick = 0
        # waypoint_map = tm.get_waypoint_buffer_map()
        # for actor_id, waypoint_list in waypoint_map.items():
        #     waypoint_stop_map.setdefault(actor_id, []).append(waypoint_list)

        pbar = tqdm.tqdm(desc='run simulation', total=ticks)

        for tick in range(ticks):
            for vehicle in vehicles:
                location_map.setdefault(vehicle.id, []).append(convert_location(vehicle.get_location()))

            world.tick()
            pbar.update()

        pbar.close()

        # path = tmp_dir / f'wp_{timestamp}.p'
        # with path.open('wb') as file:
        #     waypoint_stop_lists = waypoint_stop_map_to_lists(waypoint_stop_map)
        #     pickle.dump(waypoint_stop_lists, file)

    finally:
        for vehicle in vehicles:
            vehicle.destroy()
        world.apply_settings(settings_org)

    locations = np.array([location_map[actor_id] for actor_id in sorted(location_map.keys())], np.float32)
    return locations


def evaluate(data: List[np.ndarray], plot: bool):
    if len(data) > 1:
        for veh_index in range(len(data[0])):
            diffs = list()
            for run_index in range(1, len(data)):
                diff = np.array(data[0][veh_index]) - np.array(data[run_index][veh_index])
                diffs.append(diff)
            print(f'vehicle {veh_index} mean diff: {np.mean(diffs):.4f}')
    else:
        logging.info('Cannot compute differences for only one iteration.')

    if plot:
        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_subplot(1, 1, 1)
        plt.axis('equal')

        colors = ['blue', 'green', 'red', 'orange']

        def plot_trajectory(traj, alpha=0.3, color='black'):
            ax.plot(traj[:, 0], traj[:, 1], lw=2, alpha=alpha, color=color)
            ax.scatter([traj[0, 0]], [traj[0, 1]], s=30, color=color, alpha=alpha)

        for run_index in range(len(data)):
            for veh_index in range(len(data[run_index])):
                plot_trajectory(data[run_index][veh_index], color=colors[run_index])

        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--iterations', type=int, default=3)
    parser.add_argument('--ticks', type=int, default=2000)
    parser.add_argument('--vehicles', type=int, default=15)
    parser.add_argument('--plot', action='store_true')
    parser.add_argument('--dst', help='optional directory where vehicle positions are saved to')
    args = parser.parse_args()

    dst = None
    if args.dst is not None:
        dst = Path(args.dst)
        dst.mkdir(parents=True, exist_ok=True)

    data = list()
    for iteration in range(args.iterations):
        positions = run(args.ticks, args.vehicles)
        data.append(positions)
        if dst is not None:
            timestamp = get_timestamp_formatted()
            path = dst / f'pos_{timestamp}.p'
            with path.open('wb') as file:
                pickle.dump(positions, file)

    evaluate(data=data, plot=args.plot)







