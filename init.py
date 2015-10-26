import os

import cocos
from cocos.collision_model import CollisionManagerGrid, CollisionManagerBruteForce
from cocos import layer

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

        self.player.rect.y = 500
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
        e.rect.left = 400
        e.rect.bottom = 700

        # Collidable
        img = 'greyplatform256x24.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        e = Entity(img, width_multi=1, height_multi=1)
        e.add_components(display, collisions)
        platforms.append(e)
        e.rect.left = 800
        e.rect.bottom = 340

        # Moving platform
        img = 'greyplatform256x24.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        #collisions.solid_edges = ['top']
        collisions.no_handlers = True
        movement = Movement()
        automove = ElevatorController(movement)
        automove.move_by = 300, 200
        automove.duration = 4
        e = Entity(img, width_multi=1, height_multi=1)
        e.add_components(display, collisions, automove, movement)
        e.rect.left = 400
        e.rect.bottom = 324
        platforms.append(e)


        img = 'switch32x32.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        collisions.solid_edges = []
        collisions.no_handlers = True
        usable = Usable(automove)
        team = Team('humans')
        switch = Entity(img)
        switch.add_components(display,
                              collisions,
                              usable,
                              team)
        switch.rect.x, switch.rect.bottom = (400, 380)
        switch.bound_to = e
        platforms.append(switch)


        # Moving platform2
        img = 'greyplatform256x24.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        #collisions.solid_edges = ['top']
        collisions.no_handlers = True
        movement = Movement()
        automove = ElevatorController(movement)
        automove.move_by = 300, 0
        automove.duration = 1
        e = Entity(img, width_multi=1, height_multi=1)
        e.add_components(display, collisions, automove, movement)
        e.rect.left = 800
        e.rect.bottom = 440
        platforms.append(e)


        img = 'switch32x32.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        collisions.solid_edges = []
        collisions.no_handlers = True
        usable = Usable(automove)
        team = Team('humans')
        switch = Entity(img)
        switch.add_components(display,
                              collisions,
                              usable,
                              team)
        switch.rect.x, switch.rect.bottom = (800, 480)
        switch.bound_to = e
        platforms.append(switch)


        # Moving platform3
        img = 'greyplatform256x24.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        #collisions.solid_edges = ['top']
        collisions.no_handlers = True
        movement = Movement()
        automove = ElevatorController(movement)
        automove.move_by = 0, 500
        automove.continuous = True
        automove.duration = 2
        e = Entity(img, width_multi=1, height_multi=1)
        e.add_components(display, collisions, automove, movement)
        e.rect.left = 1200
        e.rect.top = 360
        platforms.append(e)


        img = 'switch32x32.png'
        display = Display({'default': img})
        collisions = Collisions(self.collidables)
        collisions.solid_edges = []
        collisions.no_handlers = True
        usable = Usable(automove)
        team = Team('humans')
        switch = Entity(img)
        switch.add_components(display,
                              collisions,
                              usable,
                              team)
        switch.rect.x, switch.rect.bottom = (1200, 400)
        switch.bound_to = e
        platforms.append(switch)

        return platforms

    def build_player(self):
        rightimg = 'ballman72x72.png'
        leftimg = 'ballman72x72left.png'
        display = Display({'default': rightimg,
                           'right': rightimg,
                           'left': leftimg})
        # Always add controller before movement
        # Or won't be able to jump
        keyboard = KeyboardController()
        movement = PlayerMovement()
        collisions = Collisions(self.collidables)
        collisions.solid_edges = []
        health = Health()
        gravity = Gravity()
        team = Team('humans')
        inventory = Inventory()
        use = Use()
        fighting = Fighting()

        e = Entity(rightimg, width_multi=0.8, height_multi=0.8)
        e.add_components(display,
                         keyboard,
                         collisions,
                         movement,
                         health,
                         gravity,
                         team,
                         use,
                         inventory,
                         fighting)
        inventory.add(Pistol())
        inventory.equip(0)
        return e

    def build_enemies(self):
        collisions = Collisions(self.collidables)
        collisions.solid_edges = []
        health = Health()
        team = Team('cpu')

        img = {'left': 'evilballman72x72left.png',
               'right': 'evilballman72x72.png',
               'default': 'evilballman72x72.png'}
        display = Display(img)
        entity = Entity(img['default'], width_multi=0.8, height_multi=0.8)
        entity.add_components(collisions, health, display, team)
        entity.rect.x = 600
        entity.rect.y = 400
        return [entity]

    def update(self, dt):
        # TODO: Update systems and components here
        # dt = 1.0/340
        self.systems_manager.update(dt)
        # cols = self.collidables.known_objs()
        # self.collidables.clear()
        # for c in cols:
        #     self.collidables.add(c)
        self.scroll_man.set_focus(self.player.x, self.player.y)


cocos.director.director.init(width=1920, height=1080,
                             caption='Compy',
                             autoscale=True, resizable=True,
                             fullscreen=False)
cocos.director.director.show_FPS = True

scene = cocos.scene.Scene(Level0())
cocos.director.director.run(scene)
