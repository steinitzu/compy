import os

import cocos
from cocos.collision_model import CollisionManagerGrid

import pyglet

from component import *
from entity import Entity
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
            24, 24)

        self.platforms = self.build_platforms()
        self.player = self.build_player()

        self.systems_manager = SystemsManager()
        self.systems_manager.add_entities(*self.platforms)
        self.systems_manager.add_entities(self.player)
        self.player.rect.x = 200
        self.player.rect.y = 500

        self.add(self.player, z=2)

        for p in self.platforms:
            self.add(p, z=1)

        self.schedule(self.update)

    def build_platforms(self):
        platforms = []
        xpos = 0
        for i in range(self.width/256):
            img = 'greyplatform256x24.png'
            display = Display({'default': img})
            collisions = Collisions(self.collidables)
            e = Entity(img, width_multi=1, height_multi=1)
            e.add_components(display, collisions)
            platforms.append(e)
            e.rect.left = xpos
            e.rect.bottom = 300
            xpos += e.rect.width

        img = 'greyplatform256x24.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        e = Entity(img, width_multi=1, height_multi=1)
        e.add_components(display, collisions)
        platforms.append(e)
        e.rect.left = 0
        e.rect.bottom = 340

        img = 'greyplatform256x24.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        e = Entity(img, width_multi=1, height_multi=1)
        e.add_components(display, collisions)
        platforms.append(e)
        e.rect.right = self.width
        e.rect.bottom = 340

        img = 'greyplatform256x24.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        collisions.solid_edges = ['top']
        e = Entity(img, width_multi=1, height_multi=1)
        e.add_components(display, collisions)
        platforms.append(e)
        e.rect.right = 400
        e.rect.bottom = 550

        return platforms

    def build_player(self):
        rightimg = 'ballman72x72.png'
        leftimg = 'ballman72x72left.png'
        display = Display({'default': rightimg,
                           'right': rightimg,
                           'leftl': leftimg})
        # Always add controller before movement
        # Or won't be able to jump
        keyboard = KeyboardController()
        movement = PlayerMovement()
        collisions = Collisions(self.collidables)
        health = Health()
        gravity = Gravity()

        e = Entity(rightimg, width_multi=0.8, height_multi=0.8)
        e.add_components(display,
                         keyboard,
                         collisions,
                         movement,
                         health,
                         gravity)
        return e

    def update(self, dt):
        # TODO: Update systems and components here
        self.systems_manager.update(dt)
        cols = self.collidables.known_objs()
        self.collidables.clear()
        for c in cols:
            self.collidables.add(c)

cocos.director.director.init(width=1920, height=1080,
                             caption='Compy',
                             autoscale=True, resizable=True,
                             fullscreen=False)
cocos.director.director.show_FPS = True

scene = cocos.scene.Scene(Level0())
cocos.director.director.run(scene)
