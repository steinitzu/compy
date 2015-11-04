import types
from collections import OrderedDict

from cocos.sprite import Sprite
from cocos.rect import Rect
from cocos import collision_model

from component import *


class Entity(object):
    def __init__(self, *components):
        self.components = OrderedDict()
        self.add_components(*components)

    def add_components(self, *components):
        for component in components:
            component.entity = self
            self.components[component.add_as] = component
            component.on_add()

    def component(self, klass):
        return self.components[klass]

    def remove_component(self, component):
        if isinstance(component, (type, types.ClassType)):
            self.components.pop(component)
        else:
            self.components.pop(component.__class__)

    def kill(self):
        self.systems_manager.remove(self)


# Convenience classes

class HumanPlayer(Entity):
    def __init__(self, team_name):
        rightimg = 'ballman72x72.png'
        leftimg = 'ballman72x72left.png'

        # Always add controller before movement
        # Or won't be able to jump

        display = Display({'default': rightimg,
                           'right': rightimg,
                           'left': leftimg})
        # TODO: Odd numbers for width and height
        # break collisions
        # cshape half_width needs to be a whole number
        spatial = Spatial(display.sprite,
                          width_multi=0.9,
                          height_multi=0.9)
        collisions = Collisions(solid_edges=[])
        keyboard = KeyboardController()
        movement = PlayerMovement()
        inventory = Inventory()
        use = Use()
        team = Team(team_name)
        gravity = Gravity()
        fighting = Fighting()
        super(HumanPlayer, self).__init__(
            display, spatial, collisions,
            keyboard, movement, inventory, use,
            team, gravity, fighting)


class StaticPlatform(Entity):
    def __init__(self, position=(0, 0)):
        display = Display({'default': 'greyplatform256x24.png'})
        spatial = Spatial(display.sprite)
        collisions = Collisions()
        walkable = Walkable()
        super(StaticPlatform, self).__init__(display,
                                             spatial,
                                             collisions,
                                             walkable)
        spatial.left, spatial.top = position


class Switch(Entity):
    def __init__(self, position=(0, 0), controls=None, team=''):
        display = Display({'default': 'switch32x32.png'})
        spatial = Spatial(display.sprite)
        collisions = Collisions(solid_edges=(), no_handlers=True)
        usable = Usable(controls)
        teamm = Team(team)
        super(Switch, self).__init__(display,
                                     spatial,
                                     collisions,
                                     usable,
                                     teamm)
        spatial.left, spatial.top = position


class Elevator(object):
    """
    An elevator is two entities, platform and switch
    """
    def __init__(self, position=(0, 0), move_by=(0, 0),
                 duration=5, attached_switch=True,
                 team=''):
        platform = StaticPlatform(position=position)
        movement = Movement()
        control = ElevatorController(move_by=move_by, duration=duration)
        platform.add_components(movement, control)
        platform.component(Collisions).no_handlers = True

        switch = Switch(position=(position[0], position[1]+64),
                        controls=control,
                        team=team)
        if attached_switch:
            switch.add_components(
                Attach(platform))
        self.platform = platform
        self.switch = switch


class PathNode(Entity):
    def __init__(self, position, attach_to=None):
        spatial = Spatial(width=1, height=1)
        collisions = Collisions(solid_edges=(), no_handlers=True)
        super(PathNode, self).__init__(spatial, collisions)
        spatial.center = position
        if attach_to:
            attach = Attach(attach_to)
            self.add_components(attach)
