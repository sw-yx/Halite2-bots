import hlt
import logging
from collections import OrderedDict

game = hlt.Game("swyx battlemode v6")
logging.info("Starting my Settler bot!")
turn = 1
battlemode = False

#notes
# simple rambo
# battlemode
# turn spreading

def navigateTo(ship, target_planet, command_queue, planned_planets):
    navigate_command = ship.navigate(
        ship.closest_point_to(target_planet),
        game_map,
        angular_step=5,
        max_corrections=18,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False)

    if navigate_command:
        command_queue.append(navigate_command)
        planned_planets.append(target_planet)

def attackClosestEnemy(closest_enemy_ships, ship, game_map, command_queue):
    target_ship = closest_enemy_ships[0]
    navigate_command = ship.navigate(
        ship.closest_point_to(target_ship),
        game_map,
        angular_step=5,
        max_corrections=18,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False)

    if navigate_command:
        logging.info("attacking: " + str(ship.id) + " attacking " + str(target_ship.id))
        command_queue.append(navigate_command)

while True:
    turn = turn + 1
    game_map = game.update_map()
    command_queue = []
    planned_planets = []
    me = game_map.get_me()
    team_ships = me.all_ships()
    # give more chance to avoid initial collision
    if turn < 3: 
        team_ships = team_ships[:turn]
    enemyships = [x.all_ships() for x in game_map.all_players() if x != me][0]
    health_myships = sum(map(lambda x: x.health, team_ships))
    logging.info("enemyships" + str(enemyships))
    health_enemyships = sum(map(lambda x: x.health, enemyships))
    battlemode = len(team_ships) > 10 and health_enemyships + 255 * 5 < health_myships # if we have more ships, just attack
    for ship in team_ships:
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        # https://pythonprogramming.net/custom-ai-halite-ii-artificial-intelligence-competition/?completed=/modify-starter-bot-halite-ii-artificial-intelligence-competition/
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
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
            entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]

        #special case for battlemode
        if battlemode:
            attackClosestEnemy(closest_enemy_ships, ship, game_map, command_queue)
        else:
            # If there are any empty planets, let's try to mine!
            if len(closest_viable_planets) > 0:
                target_planet = closest_viable_planets[0]
                if ship.can_dock(target_planet):
                    command_queue.append(ship.dock(target_planet))
                else:
                    if target_planet in planned_planets:
                        if turn < 10:
                            target_planet = closest_viable_planets[1]
                            navigateTo(ship, target_planet, command_queue, planned_planets)
                        else:
                            attackClosestEnemy(closest_enemy_ships, ship, game_map, command_queue)
                    else:
                        navigateTo(ship, target_planet, command_queue, planned_planets)

            # FIND SHIP TO ATTACK!
            elif len(closest_enemy_ships) > 0:
                attackClosestEnemy(closest_enemy_ships, ship, game_map, command_queue)

    game.send_command_queue(command_queue)
    # TURN END
# GAME END