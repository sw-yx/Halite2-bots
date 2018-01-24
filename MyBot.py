# adding one persistent rambo


import hlt
import logging
from collections import OrderedDict

game = hlt.Game("swyx rambo v10")
logging.info("Starting my Settler bot!")
turn = 0
rambo = -1
ramboTarget = -1

def getEnemyDetails(game_map, team_ships, ship):
    entities_by_distance = game_map.nearby_entities_by_distance(ship)
    entities_by_distance = OrderedDict(
        sorted(entities_by_distance.items(), key=lambda t: t[0]))
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
    return (closest_viable_planets, closest_enemy_ships, closest_docked_enemy_ships, entities_by_distance)

def distToEnemies(enemyships, team_ships):
    enemydistances = map(
        lambda x: x.calculate_distance_between(team_ships[0]),
        enemyships
    )
    return min(enemydistances)

def goto(a, b, game_map, command_queue, log):
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
            if isinstance(b, hlt.entity.Planet):
                logging.info(log + " | ship: " + str(a.id) + " going to Planet " + str(b.id))
            else:
                logging.info(log + " | ship: " + str(a.id) + " going to Ship " + str(b.id))
            command_queue.append(navigate_command)
    

while True:
    turn = turn + 1
    game_map = game.update_map()
    command_queue = []
    planned_planets = []
    me = game_map.get_me()
    team_ships = me.all_ships()
    if rambo < 0: ## no rambo assigned
        avail_ships = [x for x in team_ships if x.docking_status != x.DockingStatus.UNDOCKED]
        if len(avail_ships) > 1:
            rambo = avail_ships[0].id # new rambo!
    if rambo >= 0: ## if there is a rambo
        ramboShip = me.get_ship(rambo)
        if ramboShip == None:
            rambo = -1
        else:
            team_ships = [x for x in team_ships if x.id != ramboShip.id]
            (closest_viable_planets, closest_enemy_ships, closest_docked_enemy_ships, entities_by_distance) = getEnemyDetails(game_map, team_ships, ramboShip)
            if ramboTarget >= 0: ## there is a target
                ramboTargetShip = [x for x in closest_enemy_ships if x.id == ramboTarget]
                ramboTargetShip = ramboTargetShip[0] if len(ramboTargetShip) > 0 else closest_enemy_ships[-1]
                ramboTarget = ramboTargetShip.id
            else: ## there is no target, set the target
                ramboTargetShip = closest_docked_enemy_ships[-1] if len(closest_docked_enemy_ships) > 0 else closest_enemy_ships[-1]
                ramboTarget = ramboTargetShip.id
            goto(ramboShip, ramboTargetShip, game_map, command_queue, 'rambo attack')
            logging.info("rambo: id " + str(ramboShip.id) + " health: " + str(ramboShip.health) + str(ramboShip))
            logging.info("ramboTarget: id " + str(ramboTargetShip.id) + " health: " + str(ramboTargetShip.health))
            logging.info(str(command_queue))
    allplayers = game_map.all_players()
    enemyships = [x.all_ships() for x in allplayers if x != me][0]
    health_myships = sum(map(lambda x: x.health, team_ships))
    health_enemyships = sum(map(lambda x: x.health, enemyships))
    battlemode = len(team_ships) > 10 and health_enemyships + 255 * 5 < health_myships # if we have more ships, just attack
    undockcounter = 0
    
    ### special bum rush code
    # if (turn > 40 and battlemode) or len(allplayers) == 2 and turn < 20 and distToEnemies(enemyships, team_ships) < 50:
    dist = distToEnemies(enemyships, team_ships)
    logging.info('distance: ' + str(dist) + ' turn ' + str(turn))
    if len(allplayers) == 2 and turn < 50 and dist < 30:
        for idx, ship in enumerate(team_ships):
            # if ship.docking_status == ship.DockingStatus.DOCKED:
            #     if battlemode and undockcounter < 4:
            #         logging.info("battlemode!!!!")
            #         undockcounter = undockcounter + 1
            #         command_queue.append(ship.undock()) # flight of the valkryies plays
            #     continue
            if ship.docking_status == ship.DockingStatus.DOCKED:
                continue
            else:
                (closest_viable_planets, closest_enemy_ships, closest_docked_enemy_ships, entities_by_distance) = getEnemyDetails(game_map, team_ships, ship)
                # target_ship = enemyships[idx % len(enemyships)]
                if len(closest_docked_enemy_ships) > 0: # and (idx == 0 or idx == 3):
                    target_ship = closest_docked_enemy_ships[0] if len(closest_docked_enemy_ships) > 0 else closest_enemy_ships[0]
                    goto(ship, target_ship, game_map, command_queue, 'bumrush attack-closest') ## attack
                else:
                    goto(ship, closest_viable_planets[0], game_map, command_queue, 'bumrush colonize') ## colonize
    else:
    ### no bum rush
        for idx, ship in enumerate(team_ships):
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                continue

            (closest_viable_planets, closest_enemy_ships, closest_docked_enemy_ships, entities_by_distance) = getEnemyDetails(game_map, team_ships, ship)
            # If there are any empty planets, let's try to mine!
            if len(closest_viable_planets) > 0:
                target_planet = closest_viable_planets[0]
                if ship.can_dock(target_planet):
                    command_queue.append(ship.dock(target_planet))
                else:
                    # if turn < 30 and target_planet in planned_planets:
                    if target_planet in planned_planets:
                        # might as well attack
                        target_ship = closest_docked_enemy_ships[0] if len(closest_docked_enemy_ships) > 0 else closest_enemy_ships[0]
                        goto(ship, target_ship, game_map, command_queue, 'attack') ## attack
                    else:
                        goto(ship, target_planet, game_map, command_queue, 'go to planet') ## go to planet
                        planned_planets.append(target_planet)

            # FIND SHIP TO ATTACK!
            elif len(closest_enemy_ships) > 0:
                # target_ship = closest_docked_enemy_ships[0 if idx % 10 == 0 else -1] ## 10% chance of attacking furthest?
                target_ship = closest_docked_enemy_ships[0] if len(closest_docked_enemy_ships) > 0 else closest_enemy_ships[0] ## 10% chance of attacking furthest?
                goto(ship, target_ship, game_map, command_queue, 'planetsarefull, attack') ## attack

    game.send_command_queue(command_queue)
    # TURN END
# GAME END