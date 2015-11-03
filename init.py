import random
import os

import cocos
from cocos.collision_model import CollisionManagerGrid, CollisionManagerBruteForce
from cocos import layer

import pyglet

from component import *
from entity import Entity
import entity
from system import SystemsManager
#from control import KeyboardController

pyglet.resource.path = [os.path.join(os.path.realpath(''), 'resources')]
pyglet.resource.reindex()


class Level0(cocos.layer.Layer):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.is_event_handler = True
        self.width = 2560
        self.height = 2048
        self.collidables = CollisionManagerGrid(
            0, self.width, 0, self.height,
            256, 256)

        self.scroller = layer.scrolling.ScrollableLayer()
        self.scroller.px_width, self.scroller.px_height = (
             self.width, self.height)
        self.scroll_man = layer.scrolling.ScrollingManager()
        self.scroll_man.add(self.scroller)
        self.add(self.scroll_man)

        self.systems_manager = SystemsManager(self.collidables, self.scroller)

        self.platforms = self.build_platforms()
        self.player = self.build_player()
        self.enemies = self.build_enemies()

        self.systems_manager.add_entities(*self.platforms)
        self.systems_manager.add_entities(self.player)
        self.systems_manager.add_entities(*self.enemies)

        self.schedule(self.update)

    def build_player(self):
        e = entity.HumanPlayer('humans')
        e.component(Spatial).center = (500,500)
        e.component(Inventory).add(Pistol())
        e.component(Inventory).equip(0)
        return e

    def build_platforms(self):
        platforms = []
        xpos = 0
        for i in range(self.width/256):
            platforms.append(
                entity.StaticPlatform(position=(xpos, 250)))
            xpos += 256

        ypos = 200
        for i in range(10):
            xpos = random.randrange(100, 1024)
            platforms.append(
                entity.StaticPlatform(position=(xpos, ypos)))
            ypos += 200

        elevator = entity.Elevator(
            position=(500, 350),
            move_by=(0, 500),
            duration=4,
            attached_switch=True,
            team='humans')
        platforms.append(elevator.platform)
        platforms.append(elevator.switch)

        return platforms

    def build_enemies(self):
        return []

    def update(self, dt):
        # TODO: Update systems and components here
        # dt = 1.0/340
        self.systems_manager.update(dt)
        # cols = self.collidables.known_objs()
        # self.collidables.clear()
        # for c in cols:
        #     self.collidables.add(c)
        sp = self.player.component(Spatial)
        self.scroll_man.set_focus(sp.x, sp.y)


cocos.director.director.init(width=1920, height=1080,
                             caption='Compy',
                             autoscale=True, resizable=True,
                             fullscreen=False)
cocos.director.director.show_FPS = True

scene = cocos.scene.Scene(Level0())
cocos.director.director.run(scene)
