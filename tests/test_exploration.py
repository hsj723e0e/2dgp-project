import random
import unittest

from exploration import Asteroid, Bomb, Expedition, OreDrop, PLANETS, ROCK_AREA, SURFACE_ROOM
from game_state import GameState
from player import Player


class ExplorationTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now, starter_equipment=True, rng=random.Random(71))
        self.expedition = Expedition(self.state)
        self.player = Player()
        for item in self.state.inventory_items():
            self.assertTrue(self.expedition.choose_gear(item))

    def land(self, index=2):
        self.expedition.destination = PLANETS[index]
        self.assertTrue(self.expedition.launch()[0])
        self.now += PLANETS[index].flight_seconds
        self.expedition.update_flight()
        self.assertTrue(self.expedition.leave_ship(self.player)[0])

    def test_exact_resource_tables(self):
        self.assertEqual([planet.resources for planet in PLANETS], [
            ('mat_01','mat_03'), ('mat_01','mat_03'), ('mat_03',), ('mat_01','mat_03'),
            ('mat_02','mat_01'), ('mat_02','mat_01'), ('item_chip','mat_02'),
            ('item_chip','mat_02'), ('item_core',)])

    def test_launch_requires_three_real_selected_items(self):
        self.expedition.loadout.clear()
        self.assertFalse(self.expedition.launch()[0])
        for item in self.state.inventory_items():
            self.expedition.choose_gear(item)
        unit = self.state.available_units('eq_drill_01')[0]
        self.state.store_equipment(unit.equipment, unit.identifier)
        self.assertFalse(self.expedition.launch()[0])
        self.state.withdraw_equipment(unit.equipment, unit.identifier)
        self.assertTrue(self.expedition.launch()[0])

    def test_travel_has_delay_cannot_exit_early_and_arrives_once(self):
        self.assertTrue(self.expedition.launch()[0])
        self.assertFalse(self.expedition.leave_ship(self.player)[0])
        self.assertFalse(self.expedition.launch()[0])
        self.now = 2.9
        self.expedition.update_flight()
        self.assertIsNone(self.expedition.planet)
        self.now = 3
        self.expedition.update_flight()
        self.assertEqual(self.expedition.planet.name, '지구')
        self.assertIn('도착', self.expedition.notice)
        self.assertTrue(self.expedition.leave_ship(self.player)[0])
        self.assertFalse(self.expedition.leave_ship(self.player)[0])

    def test_flight_keeps_original_destination(self):
        self.expedition.launch()
        self.expedition.destination = PLANETS[-1]
        self.now = 3
        self.expedition.update_flight()
        self.assertEqual(self.expedition.planet, PLANETS[2])

    def test_each_planet_has_only_its_resources_and_walkable_landing(self):
        for index, planet in enumerate(PLANETS):
            self.land(index)
            self.assertEqual({node.resource for node in self.expedition.rocks}, set(planet.resources))
            self.assertTrue(self.player.can_stand(self.player.x,self.player.y,SURFACE_ROOM,self.expedition.obstacles))
            self.assertTrue(self.expedition.return_to_ship(self.player))

    def test_receiving_resources_validates_kind_amount_and_capacity(self):
        for image,quantity in [('bad',1),('mat_01',0),('mat_01',True),('mat_01',1.5)]:
            self.assertFalse(self.state.receive_resource(image,quantity))
        self.assertTrue(self.state.receive_resource('mat_01',5))
        self.assertEqual(self.state.materials['mat_01'],5)

    def fixed_rock(self, health=100, resource='mat_03'):
        self.player.x, self.player.y = 500, 300
        self.expedition.rocks.clear()
        self.expedition.bombs.clear()
        self.expedition.bomb_spawn_at = 1000
        rock = Asteroid(620,330,0,0,30,health,health,resource)
        self.expedition.rocks.append(rock)
        return rock

    def test_drill_aim_hits_only_front_target_in_reach(self):
        self.land()
        rock=self.fixed_rock()
        self.assertIs(self.expedition.target_at(self.player,(1000,330)),rock)
        self.assertIsNone(self.expedition.target_at(self.player,(0,330)))
        self.assertIsNone(self.expedition.target_at(self.player,(500,650)))
        rock.x=800
        self.assertIsNone(self.expedition.target_at(self.player,(1000,330)))

    def test_holding_drill_reduces_health_and_release_stops_damage(self):
        self.land()
        rock=self.fixed_rock()
        self.expedition.update_surface(self.player,0.5,mining=True,aim=(1000,330))
        self.assertAlmostEqual(rock.health,83)
        self.assertEqual(self.state.materials['mat_03'],0)
        health=rock.health
        self.expedition.update_surface(self.player,0.2,mining=False)
        self.assertEqual(rock.health,health)

    def test_destroyed_rock_drops_ore_and_nearby_player_collects_once(self):
        self.land()
        rock=self.fixed_rock(health=5)
        self.expedition.update_surface(self.player,0.2,mining=True,aim=(1000,330))
        self.assertNotIn(rock,self.expedition.rocks)
        self.assertEqual(self.expedition.destroyed_rocks,1)
        self.assertEqual(self.state.materials['mat_03'],0)
        self.assertEqual(sum(drop.quantity for drop in self.expedition.drops),3)
        self.player.x=580
        self.expedition.update_surface(self.player,0.4)
        self.assertEqual(self.state.materials['mat_03'],3)
        self.assertEqual(self.expedition.earned['mat_03'],3)
        self.expedition.update_surface(self.player,0.2)
        self.assertEqual(self.state.materials['mat_03'],3)

    def test_destroying_same_rock_twice_cannot_duplicate_drops(self):
        self.land()
        rock=self.fixed_rock()
        self.expedition.destroy_rock(rock)
        self.expedition.destroy_rock(rock)
        self.assertEqual(self.expedition.destroyed_rocks,1)
        self.assertEqual(sum(drop.quantity for drop in self.expedition.drops),3)

    def test_ore_stays_available_when_bag_full_and_collects_after_space_frees(self):
        self.land()
        self.fixed_rock()
        self.state.add_equipment('eq_drill_01',6)
        drop=OreDrop(500,322,'mat_03',4)
        self.expedition.drops=[drop]
        self.expedition.update_surface(self.player,0.05)
        self.assertIn(drop,self.expedition.drops)
        self.assertEqual(self.state.materials['mat_03'],0)
        unit=self.state.available_units('eq_drill_01')[0]
        self.state.store_equipment(unit.equipment,unit.identifier)
        self.expedition.update_surface(self.player,0.05)
        self.assertNotIn(drop,self.expedition.drops)
        self.assertEqual(self.state.materials['mat_03'],4)

    def test_full_bag_accepts_existing_stack_and_chip_core_drops(self):
        self.land()
        self.fixed_rock()
        self.state.materials['mat_03']=10
        self.state.add_equipment('eq_drill_01',5)
        self.expedition.drops=[OreDrop(500,322,'mat_03',3)]
        self.expedition.update_surface(self.player,0.05)
        self.assertEqual(self.state.materials['mat_03'],13)
        self.assertEqual(self.state.inventory_used,9)
        for image in ('item_chip','item_core'):
            state=GameState(clock=lambda:0)
            expedition=Expedition(state)
            expedition.drops=[OreDrop(500,322,image,2)]
            expedition.collect_drops(self.player,0.05)
            self.assertEqual(state.rewards[image],2)

    def test_successful_return_keeps_collected_resources(self):
        self.land()
        self.expedition.drops=[OreDrop(285,342,'mat_03',4)]
        self.expedition.update_surface(self.player,0.05)
        self.assertTrue(self.expedition.return_to_ship(self.player))
        self.assertEqual(self.state.materials['mat_03'],4)
        self.assertFalse(self.expedition.return_to_ship(self.player,rescued=True))
        self.assertEqual(self.state.materials['mat_03'],4)

    def test_rescue_removes_only_current_sortie_collected_loot(self):
        self.state.materials['mat_03']=10
        self.land()
        self.expedition.drops=[OreDrop(285,342,'mat_03',3)]
        self.expedition.update_surface(self.player,0.05)
        self.assertEqual(self.state.materials['mat_03'],13)
        self.expedition.health=0
        self.expedition.update_surface(self.player,0.025)
        self.assertFalse(self.expedition.outside)
        self.assertEqual(self.state.materials['mat_03'],10)
        self.assertEqual(sum(self.state.equipment.values()),3)

    def test_rocks_move_rotate_and_bounce_at_boundary(self):
        self.land()
        rock=self.fixed_rock()
        rock.x=ROCK_AREA.right-rock.radius-1
        rock.vx=100
        rock.spin=0.5
        self.expedition.update_surface(self.player,0.05)
        self.assertLess(rock.vx,0)
        self.assertLessEqual(rock.x,ROCK_AREA.right-rock.radius)
        self.assertGreater(rock.angle,0)

    def test_collision_damage_has_recovery_interval(self):
        self.land()
        rock=self.fixed_rock()
        rock.x,rock.y=500,330
        self.expedition.update_surface(self.player,0.025)
        health=self.expedition.health
        self.assertEqual(health,90)
        self.expedition.update_surface(self.player,0.2)
        self.assertEqual(self.expedition.health,health)

    def test_bomb_touch_explodes_once_and_grants_no_resources(self):
        self.land()
        self.fixed_rock()
        bomb=Bomb(500,330,0,0)
        self.expedition.bombs=[bomb]
        self.expedition.update_surface(self.player,0.025)
        self.assertFalse(bomb.active)
        self.assertEqual(self.expedition.health,55)
        self.assertEqual(self.expedition.destroyed_rocks,0)
        self.assertFalse(self.expedition.drops)
        self.expedition.explode_bomb(bomb,self.player)
        self.assertEqual(self.expedition.health,55)

    def test_drill_can_trigger_bomb_in_front_of_rock(self):
        self.land()
        rock=self.fixed_rock()
        bomb=Bomb(580,330,0,0)
        self.expedition.bombs=[bomb]
        self.expedition.update_surface(self.player,0.025,mining=True,aim=(1000,330))
        self.assertFalse(bomb.active)
        self.assertLess(self.expedition.health,100)
        self.assertEqual(rock.health,100)

    def test_bomb_explosion_outside_radius_does_not_hurt_player(self):
        self.land()
        bomb=Bomb(1000,550,0,0)
        self.expedition.explode_bomb(bomb,self.player)
        self.assertEqual(self.expedition.health,100)

    def test_better_drill_and_individual_enhancement_raise_damage(self):
        self.land()
        basic=self.expedition.drill_damage
        self.expedition.return_to_ship(self.player)
        unit=self.state.available_units('eq_drill_01')[0]
        unit.level=5
        self.expedition.leave_ship(self.player)
        self.assertGreater(self.expedition.drill_damage,basic)
        self.expedition.return_to_ship(self.player)
        self.state.add_equipment('eq_drill_advanced',1)
        item=next(item for item in self.state.inventory_items() if item.image=='eq_drill_advanced')
        self.expedition.choose_gear(item)
        self.expedition.leave_ship(self.player)
        self.assertGreater(self.expedition.drill_damage,basic*2)

    def test_better_suit_reduces_collision_and_bomb_damage(self):
        self.land()
        self.expedition.hurt(40)
        basic_damage=100-self.expedition.health
        self.expedition.return_to_ship(self.player)
        self.state.add_equipment('eq_suit_advanced',1)
        item=next(item for item in self.state.inventory_items() if item.image=='eq_suit_advanced')
        self.expedition.choose_gear(item)
        self.expedition.leave_ship(self.player)
        self.expedition.hurt(40)
        self.assertLess(100-self.expedition.health,basic_damage)

    def test_better_oxygen_tank_extends_time_outside_ship(self):
        self.land()
        capacity=self.expedition.max_oxygen
        self.expedition.return_to_ship(self.player)
        self.state.add_equipment('eq_oxygen_advanced',1)
        item=next(item for item in self.state.inventory_items() if item.image=='eq_oxygen_advanced')
        self.expedition.choose_gear(item)
        self.expedition.leave_ship(self.player)
        self.assertGreater(self.expedition.max_oxygen,capacity)
        self.expedition.update_surface(self.player,10)
        self.assertGreater(self.expedition.oxygen,capacity)

    def test_personal_equipment_is_available_for_each_slot(self):
        self.land()
        self.expedition.return_to_ship(self.player)
        for image in self.state.personal_equipment:
            self.state.personal_equipment[image]=5
        for item in self.state.inventory_items():
            if item.image.endswith('_03'):
                self.expedition.choose_gear(item)
        self.assertTrue(self.expedition.leave_ship(self.player)[0])
        self.assertGreater(self.expedition.drill_power,3)
        self.assertLess(self.expedition.armor,0.6)
        self.assertGreater(self.expedition.max_oxygen,200)

    def test_oxygen_depletion_can_force_rescue(self):
        self.land()
        self.expedition.oxygen=0
        self.expedition.health=5
        self.expedition.update_surface(self.player,1)
        self.assertFalse(self.expedition.outside)

    def test_session_end_blocks_damage_loot_and_flight(self):
        self.land()
        self.now=1200
        oxygen=self.expedition.oxygen
        self.expedition.update_surface(self.player,10,mining=True,aim=(1000,330))
        self.assertEqual(self.expedition.oxygen,oxygen)
        self.assertFalse(self.state.receive_resource('mat_01',1))
        self.assertFalse(self.expedition.launch()[0])

    def test_each_sortie_refills_health_and_resets_drops(self):
        self.land()
        self.expedition.health=30
        self.expedition.drops=[OreDrop(800,400,'mat_03',3)]
        self.expedition.return_to_ship(self.player)
        self.expedition.leave_ship(self.player)
        self.assertEqual(self.expedition.health,100)
        self.assertEqual(self.expedition.oxygen,self.expedition.max_oxygen)
        self.assertFalse(self.expedition.drops)
