import random
import os

import cocos
#from cocos.collision_model import CollisionManagerGrid, CollisionManagerBruteForce
from cocos import layer

import pyglet

from component import *
from entity import Entity
import entity
from system import SystemsManager, PathSystem
from collisions import CollisionManager
#from control import KeyboardController

pyglet.resource.path = [os.path.join(os.path.realpath(''), 'resources')]
pyglet.resource.reindex()


class Level0(cocos.layer.Layer):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.is_event_handler = True
        self.width = 2560
        self.height = 2048
        self.collidables = CollisionManager()
        #CollisionManagerGrid(
            # 0, self.width, 0, self.height,
            # int(256*1.25), int(256*1.25))

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
        # Temporary
        self.systems_manager.pathfinding = PathSystem(
            self.systems_manager)
        self.systems_manager.pathfinding.generate_graph()
        self.systems_manager.pathfinding.draw_graph()
        self.schedule(self.update)

        self.is_event_handler = True

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
            p = entity.StaticPlatform(position=(xpos, ypos))
            if i % 2 == 0:
                p.component(Collisions).solid_edges = ('top',)
            platforms.append(p)
            ypos += 200

        # xpos, ypos = 400, 300
        # platforms.append(
        #     entity.StaticPlatform(position=(xpos, ypos)))

        elevator = entity.Elevator(
            position=(520, 300),
            move_by=(0, 500),
            duration=4,
            attached_switch=True,
            team='humans',
            continuous=True)
        platforms.append(elevator.platform)
        platforms.append(elevator.switch)

        elevator = entity.Elevator(
            position=(800, 300),
            move_by=(300, 0),
            duration=4,
            attached_switch=True,
            team='humans')
        platforms.append(elevator.platform)
        platforms.append(elevator.switch)

        elevator = entity.Elevator(
            position=(1100, 300),
            move_by=(300, 500),
            duration=4,
            attached_switch=True,
            team='humans')
        platforms.append(elevator.platform)
        platforms.append(elevator.switch)

        return platforms

    def build_enemies(self):
        e = entity.AIPlayer('cpu')
        e.component(Spatial).center = 600, 500
        return [e]

    def on_pop(self, *args, **kwargs):
        print 'shit fuck'

    def update(self, dt):
        self.systems_manager.update(dt)
        sp = self.player.component(Spatial)
        self.scroll_man.set_focus(sp.x, sp.y)


class Sena(cocos.scene.Scene):
    def on_exit(self, *args, **kwargs):
        super(Sena, self).on_exit()
        l = self.children[0][1]
        s = l.player.component(Spatial)
        h = s.history
        for line in h:
            print line
        c = l.player.component(Collisions)
        print c.cshape.rx, c.cshape.ry
        print s.width, s.height
        log.info('\n'.join(
            str(n) for n in l.systems_manager.pathfinding.nodes.items()))



cocos.director.director.init(width=1920, height=1080,
                             caption='Compy',
                             autoscale=True, resizable=True,
                             fullscreen=False)
cocos.director.director.show_FPS = True

scene = Sena(Level0())
cocos.director.director.run(scene)
