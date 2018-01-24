import hlt
import logging
from collections import OrderedDict
from functools import reduce
import math

game = hlt.Game("swyx planetrank v6")
logging.info("Starting my Settler bot!")
turn = 1
battlemode = False

# notes
# battlemode added
# planetrank formula + level 1 recursion
# early planet dispersal

def rankPlanet(planet, ship, allEnemies, allPlanets):
    # distanceToShip, enemyScore, availSpots
    distanceToShip = 1 * math.sqrt(ship.calculate_distance_between(planet))
    availSpots = 1 * (planet.num_docking_spots - len(planet.all_docked_ships()))
    enemyScore = 3 * sum(map(lambda x: 0 if x == planet else 1 / math.sqrt(planet.calculate_distance_between(x)), allEnemies))
    score = availSpots - distanceToShip - enemyScore
    if len(allPlanets) > 0:
        # recursive planet rank to account for clusters of unoccupied planets
        score = score + 0.5 * sum(map(lambda x: rankPlanet(x, planet, allEnemies, []) / math.sqrt(ship.calculate_distance_between(x)), [x for x in allPlanets if x != planet]))
    # logging.info("ship " + str(ship.id) + ", " + str(planet.id) + " planet score is " + str(score) + "| distanceToShip" + str(distanceToShip) + "| availSpots" + str(availSpots) + "| enemyScore " + str(enemyScore))
    return score

# # closest viable planets
#         closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
#             entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
#         closest_my_planets_with_spots = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
#             entities_by_distance[distance][0], hlt.entity.Planet) and
#             entities_by_distance[distance][0].owner == me and
#             not entities_by_distance[distance][0].is_full()
#         ]
#         closest_viable_planets = closest_empty_planets + closest_my_planets_with_spots
#         closest_viable_planets = sorted(closest_viable_planets, key=lambda k: ship.calculate_distance_between(k)) 
        

def find_target_planet(allPlanets, ship, allEnemies):
    closest_viable_planets = [planet for planet in allPlanets if planet.owner == me and not planet.is_full()]
    closest_viable_planets = closest_viable_planets + [planet for planet in allPlanets if not planet.is_owned()]
    if len(closest_viable_planets) > 0:
        closest_viable_planets = sorted(closest_viable_planets, key=lambda k: rankPlanet(k, ship, allEnemies, allPlanets)) 
        return closest_viable_planets[-1]
    else:
        return None

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
    game_map = game.update_map()
    allplanets = game_map.all_planets()
    command_queue = []
    planned_planets = []
    me = game_map.get_me()
    enemyships = [x.all_ships() for x in game_map.all_players() if x != me]
    num_enemyships = reduce(lambda x, y: len(y) + x, enemyships, 0)
    team_ships = me.all_ships()
    battlemode = len(team_ships) > 10 and num_enemyships < len(team_ships) # if we have more ships, just attack
    logging.info("**** BATTLE MODE ON *****")
    turn = turn + 1
    # give more chance to avoid initial collision
    if turn < 3: 
        team_ships = team_ships[:turn]
    # basic rambo strategy
    # if len(team_ships) > 4:
    #     rambo = team_ships[-1]
    #     if rambo.docking_status == rambo.DockingStatus.UNDOCKED:
    #         team_ships = team_ships[:-1]
    #         entities_by_distance = game_map.nearby_entities_by_distance(rambo)
    #         entities_by_distance = OrderedDict(
    #             sorted(entities_by_distance.items(), key=lambda t: t[0]))
    #         # closets ships that are not undocked
    #         closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
    #             entities_by_distance[distance][0], hlt.entity.Ship) and 
    #             entities_by_distance[distance][0] not in team_ships and 
    #             entities_by_distance[distance][0].docking_status != entities_by_distance[distance][0].DockingStatus.UNDOCKED
    #             ]
    #         # might as well attack
    #         target_ship = closest_enemy_ships[0]
    #         navigate_command = rambo.navigate(
    #             rambo.closest_point_to(target_ship),
    #             game_map,
    #             speed=int(hlt.constants.MAX_SPEED),
    #             ignore_ships=False)
    #         if navigate_command:
    #             command_queue.append(navigate_command)

    for ship in team_ships:
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue
        # https://pythonprogramming.net/custom-ai-halite-ii-artificial-intelligence-competition/?completed=/modify-starter-bot-halite-ii-artificial-intelligence-competition/
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        # closets ships
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(
            entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
        allEnemies = [entities_by_distance[distance][0] for distance in entities_by_distance if
            entities_by_distance[distance][0].owner != me and
            entities_by_distance[distance][0].owner != None
            ]
        #special case for battlemode
        if battlemode:
            attackClosestEnemy(closest_enemy_ships, ship, game_map, command_queue)
        else:
            # If there is a valid target planet, go to there
            target_planet = find_target_planet(allplanets, ship, allEnemies)
            # logging.info(str(ship.id) + " targets " + str(target_planet.id) + " on turn " + str(turn))
            if target_planet:
                if ship.can_dock(target_planet):
                    logging.info("docking: " + str(ship.id))
                    command_queue.append(ship.dock(target_planet))
                else:
                    if turn < 10 and target_planet in planned_planets: # early planet dispersal
                        attackClosestEnemy(closest_enemy_ships, ship, game_map, command_queue)
                    else:
                        navigate_command = ship.navigate(
                            ship.closest_point_to(target_planet),
                            game_map,
                            angular_step=5,
                            max_corrections=18,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                        if navigate_command:
                            logging.info("navigating: " + str(ship.id) + " goingto " + str(target_planet.id))
                            command_queue.append(navigate_command)
                            planned_planets.append(target_planet)

            # FIND SHIP TO ATTACK!
            elif len(closest_enemy_ships) > 0:
                attackClosestEnemy(closest_enemy_ships, ship, game_map, command_queue)

    game.send_command_queue(command_queue)
    # TURN END
# GAME END