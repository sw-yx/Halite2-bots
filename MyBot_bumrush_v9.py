# add bum rush of just 1 ship
# attacking docked enemy ships when planets are full


import hlt
import logging
from collections import OrderedDict

game = hlt.Game("swyx bumrush v9")
logging.info("Starting my Settler bot!")
turn = 0

def distToEnemies(enemyships, team_ships):
    enemydistances = map(
        lambda x: x.calculate_distance_between(team_ships[0]),
        enemyships
    )
    return min(enemydistances)

def goto(a, b, game_map, command_queue):
    if isinstance(a, hlt.entity.Ship) and isinstance(b, hlt.entity.Planet) and a.can_dock(b):
        command_queue.append(a.dock(b))
    else:
        navigate_command = a.navigate(
            a.closest_point_to(b),
            game_map,
            angular_step=5,
            max_corrections=18,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=False)

        if navigate_command:
            # logging.info("attacking: " + str(ship.id) + " attacking " + str(target_ship.id))
            command_queue.append(navigate_command)
    

while True:
    turn = turn + 1
    game_map = game.update_map()
    command_queue = []
    planned_planets = []
    me = game_map.get_me()
    team_ships = me.all_ships()
    allplayers = game_map.all_players()
    enemyships = [x.all_ships() for x in allplayers if x != me][0]
    health_myships = sum(map(lambda x: x.health, team_ships))
    health_enemyships = sum(map(lambda x: x.health, enemyships))
    battlemode = len(team_ships) > 10 and health_enemyships + 255 * 5 < health_myships # if we have more ships, just attack
    undockcounter = 0
    
    ### special bum rush code
    # if (turn > 40 and battlemode) or len(allplayers) == 2 and turn < 20 and distToEnemies(enemyships, team_ships) < 50:
    if len(allplayers) == 2 and turn < 100 and distToEnemies(enemyships, team_ships) < 50:
        logging.info("bumrushing!!!!")
        for idx, ship in enumerate(team_ships):
            # if ship.docking_status == ship.DockingStatus.DOCKED:
            #     if battlemode and undockcounter < 4:
            #         logging.info("battlemode!!!!")
            #         undockcounter = undockcounter + 1
            #         command_queue.append(ship.undock()) # flight of the valkryies plays
            #     continue
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(
                sorted(entities_by_distance.items(), key=lambda t: t[0]))
            # closest viable planets
            # closest viable planets
            closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
                entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
            closest_my_planets_with_spots = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
                entities_by_distance[distance][0], hlt.entity.Planet) and
                entities_by_distance[distance][0].owner == me and
                not entities_by_distance[distance][0].is_full()
            ]
            closest_viable_planets = closest_empty_planets + closest_my_planets_with_spots
            closest_viable_planets = sorted(closest_viable_planets, key=lambda k: ship.calculate_distance_between(k)) 
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if 
                isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and 
                entities_by_distance[distance][0] not in team_ships]
            closest_docked_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if 
                isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and 
                entities_by_distance[distance][0] not in team_ships and
                entities_by_distance[distance][0].docking_status != ship.DockingStatus.UNDOCKED]
            target_ship = closest_docked_enemy_ships[0] if len(closest_docked_enemy_ships) > 0 else closest_enemy_ships[0]
            # target_ship = enemyships[idx % len(enemyships)]
            if len(closest_viable_planets) > 0 and (idx == 0 or idx == 1):
                goto(ship, closest_viable_planets[0], game_map, command_queue) ## colonize
            else:
                goto(ship, target_ship, game_map, command_queue) ## attack
            # logging.info("attacking: " + str(ship.id) + " attacking " + str(target_ship.id))
    else:
    ### no bum rush
        for idx, ship in enumerate(team_ships):
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                continue

            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(
                sorted(entities_by_distance.items(), key=lambda t: t[0]))
            # closest viable planets
            closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
                entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
            closest_my_planets_with_spots = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
                entities_by_distance[distance][0], hlt.entity.Planet) and
                entities_by_distance[distance][0].owner == me and
                not entities_by_distance[distance][0].is_full()
            ]
            closest_viable_planets = closest_empty_planets + closest_my_planets_with_spots
            closest_viable_planets = sorted(closest_viable_planets, key=lambda k: ship.calculate_distance_between(k)) 
            # closets ships
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if 
                isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and 
                entities_by_distance[distance][0] not in team_ships]
            closest_docked_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if 
                isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and 
                entities_by_distance[distance][0] not in team_ships and
                entities_by_distance[distance][0].docking_status != ship.DockingStatus.UNDOCKED]
            # If there are any empty planets, let's try to mine!
            if len(closest_viable_planets) > 0:
                target_planet = closest_viable_planets[0]
                if ship.can_dock(target_planet):
                    command_queue.append(ship.dock(target_planet))
                else:
                    if turn < 30 and target_planet in planned_planets:
                        # might as well attack
                        target_ship = closest_docked_enemy_ships[0] if len(closest_docked_enemy_ships) > 0 else closest_enemy_ships[0]
                        goto(ship, target_ship, game_map, command_queue) ## attack
                    else:
                        goto(ship, target_planet, game_map, command_queue) ## go to planet
                        planned_planets.append(target_planet)

            # FIND SHIP TO ATTACK!
            elif len(closest_enemy_ships) > 0:
                # target_ship = closest_docked_enemy_ships[0 if idx % 10 == 0 else -1] ## 10% chance of attacking furthest?
                target_ship = closest_docked_enemy_ships[0] if len(closest_docked_enemy_ships) > 0 else closest_enemy_ships[0] ## 10% chance of attacking furthest?
                goto(ship, target_ship, game_map, command_queue) ## attack

    game.send_command_queue(command_queue)
    # TURN END
# GAME END