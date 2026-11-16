import unittest

from exploration import Expedition, PLANETS, Alien, Deposit, GAS_POSITIONS, SURFACE_ROOM
from game_state import GameState
from player import Player


class ExplorationTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now, starter_equipment=True)
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
            self.assertEqual({node.resource for node in self.expedition.nodes}, set(planet.resources))
            self.assertTrue(self.player.can_stand(self.player.x,self.player.y,SURFACE_ROOM,self.expedition.obstacles))
            self.assertTrue(self.expedition.return_to_ship(self.player))

    def test_hold_mining_adds_resources_and_return_preserves_them(self):
        self.land()
        node = self.expedition.nodes[0]
        self.player.x, self.player.y = node.x, node.y-65
        self.expedition.update_surface(self.player, 1.7, mining=True)
        self.assertEqual(self.state.materials['mat_03'],1)
        self.assertEqual(node.remaining,7)
        self.assertFalse(self.expedition.return_to_ship(self.player))
        self.player.x,self.player.y=285,320
        self.assertTrue(self.expedition.return_to_ship(self.player))
        self.assertEqual(self.state.materials['mat_03'],1)

    def test_reward_resources_enter_same_bag_stacks(self):
        for index, image in ((6,'item_chip'),(8,'item_core')):
            self.land(index)
            node=self.expedition.nodes[0]
            self.player.x,self.player.y=node.x,node.y-65
            self.expedition.update_surface(self.player,1.7,mining=True)
            self.assertEqual(self.state.rewards[image],1)
            self.player.x,self.player.y=285,320
            self.expedition.return_to_ship(self.player)

    def test_full_bag_blocks_new_stack_without_depleting_node(self):
        self.land()
        self.state.add_equipment('eq_drill_01',6)
        node=self.expedition.nodes[0]
        self.player.x,self.player.y=node.x,node.y-65
        self.expedition.update_surface(self.player,2,mining=True)
        self.assertEqual(node.remaining,8)
        self.assertEqual(self.state.materials['mat_03'],0)

    def test_full_bag_allows_existing_resource_stack(self):
        self.land()
        self.state.materials['mat_03']=10
        self.state.add_equipment('eq_drill_01',5)
        node=self.expedition.nodes[0]
        self.player.x,self.player.y=node.x,node.y-65
        self.expedition.update_surface(self.player,1.7,mining=True)
        self.assertEqual(self.state.materials['mat_03'],11)
        self.assertEqual(self.state.inventory_used,9)

    def test_rescue_removes_only_current_sortie_loot(self):
        self.state.materials['mat_03']=10
        self.land()
        node=self.expedition.nodes[0]
        self.player.x,self.player.y=node.x,node.y-65
        self.expedition.update_surface(self.player,1.7,mining=True)
        self.assertEqual(self.state.materials['mat_03'],11)
        self.expedition.health=0
        self.expedition.update_surface(self.player,0.05)
        self.assertFalse(self.expedition.outside)
        self.assertEqual(self.state.materials['mat_03'],10)
        self.assertEqual(sum(self.state.equipment.values()),3)
        self.assertEqual(self.player.x,640)

    def test_oxygen_zero_deals_damage_and_can_force_rescue(self):
        self.land()
        self.expedition.oxygen=0
        self.expedition.health=5
        self.expedition.update_surface(self.player,1)
        self.assertFalse(self.expedition.outside)

    def test_gas_warns_before_damage_and_moving_away_is_safe(self):
        self.land()
        self.expedition.aliens=[]
        self.player.x,self.player.y=GAS_POSITIONS[0]
        self.expedition.surface_time=6.1
        self.expedition.update_surface(self.player,0.5)
        self.assertEqual(self.expedition.gas_phase(0),'warning')
        self.assertEqual(self.expedition.health,100)
        self.expedition.surface_time=8.1
        self.expedition.update_surface(self.player,0.5)
        self.assertLess(self.expedition.health,100)
        health=self.expedition.health
        self.player.x,self.player.y=285,320
        self.expedition.update_surface(self.player,0.2)
        self.assertEqual(self.expedition.health,health)

    def test_crystal_warns_then_explodes_once_after_retreat(self):
        self.land()
        node=self.expedition.nodes[1]
        self.expedition.aliens=[]
        self.player.x,self.player.y=node.x,node.y-65
        self.expedition.update_surface(self.player,2.1,mining=True)
        self.assertIsNotNone(node.explosion_at)
        self.player.x,self.player.y=285,320
        self.expedition.update_surface(self.player,1.6)
        self.assertEqual(node.remaining,0)
        self.assertEqual(self.expedition.health,100)
        self.assertIsNone(node.explosion_at)

    def test_crystal_explosion_hurts_if_player_stays(self):
        self.land()
        self.expedition.aliens=[]
        node=self.expedition.nodes[1]
        self.player.x,self.player.y=node.x,node.y-65
        self.expedition.update_surface(self.player,3.7,mining=True)
        self.assertLess(self.expedition.health,100)
        self.assertEqual(node.remaining,0)

    def test_aliens_hear_drilling_approach_and_can_be_fought(self):
        self.land()
        node=self.expedition.nodes[0]
        self.player.x,self.player.y=node.x,node.y-65
        alien=Alien(self.player.x+150,self.player.y)
        self.expedition.aliens=[alien]
        self.expedition.update_surface(self.player,0.5,mining=True)
        self.assertLess(alien.x,self.player.x+150)
        alien.x=self.player.x+35
        self.expedition.update_surface(self.player,0.1)
        self.assertLess(self.expedition.health,100)
        self.assertTrue(self.expedition.attack(self.player))
        self.assertFalse(self.expedition.attack(self.player))
        for _ in range(3):
            self.expedition.update_surface(self.player,0.5)
            self.expedition.attack(self.player)
        self.assertLessEqual(alien.health,0)

    def test_personal_equipment_and_enhancement_improve_stats(self):
        self.land()
        basic=(self.expedition.drill_power,self.expedition.armor,self.expedition.max_oxygen)
        self.expedition.return_to_ship(self.player)
        for image in self.state.personal_equipment:
            self.state.personal_equipment[image]=5
        for item in self.state.inventory_items():
            if item.image.endswith('_03'):
                self.expedition.choose_gear(item)
        self.assertTrue(self.expedition.leave_ship(self.player)[0])
        self.assertGreater(self.expedition.drill_power,basic[0])
        self.assertLess(self.expedition.armor,basic[1])
        self.assertGreater(self.expedition.max_oxygen,basic[2])

    def test_session_end_blocks_travel_mining_and_resource_receipt(self):
        self.land()
        self.now=1200
        oxygen=self.expedition.oxygen
        self.expedition.update_surface(self.player,10,mining=True)
        self.assertEqual(self.expedition.oxygen,oxygen)
        self.assertFalse(self.state.receive_resource('mat_01',1))
        self.assertFalse(self.expedition.launch()[0])

    def test_receiving_resources_validates_kind_amount_and_capacity(self):
        for image,quantity in [('bad',1),('mat_01',0),('mat_01',True),('mat_01',1.5)]:
            self.assertFalse(self.state.receive_resource(image,quantity))
        self.assertTrue(self.state.receive_resource('mat_01',5))
        self.assertEqual(self.state.materials['mat_01'],5)
