import logging

from cocos.director import director

from pyglet.window import key as keycode
from pyglet.window.key import KeyStateHandler

import config

log = logging.getLogger('compy')


class Component(object):

    def __init__(self):
        self.entity = None
        # Added with this classname
        self.add_as = self.__class__

    def on_add(self):
        """
        Called when component is added to entity.
        """
        pass

    def update(self, dt):
        # Called each frame
        pass


class EventComponent(Component):
    """
    A component that receives pyglet events.
    """
    def __init__(self):
        super(EventComponent, self).__init__()

    def on_add(self):
        director.window.push_handlers(self)


class Controller(EventComponent):
    def __init__(self):
        super(Controller, self).__init__()


class KeyboardController(Controller):
    def __init__(self):
        super(KeyboardController, self).__init__()
        self.pressed = set()
        self.modifiers = None

        self.map = {
            'left': {keycode.LEFT},
            'right': {keycode.RIGHT},
            'jump': {keycode.SPACE},
            'down': {keycode.DOWN},
            'up': {keycode.UP},
            }

    def on_key_press(self, key, modifiers):
        self.pressed.add(key)
        self.modifiers = modifiers

    def on_key_release(self, key, modifiers):
        try:
            self.pressed.remove(key)
        except:
            pass
        self.modifiers = modifiers

    def do_movement(self, entity, pressed):
        m = entity.components[Movement]
        if self.map['left'].intersection(pressed):
            m.walk(-1)
        elif self.map['right'].intersection(pressed):
            m.walk(1)
        else:
            m.end_walk()
        if self.map['jump'].intersection(pressed):
            m.jump()
        else:
            m.end_jump()

    def update(self, dt):
        p = self.entity
        pressed = self.pressed
        # Will error if no movement component
        self.do_movement(p, pressed)


class PathNodes(Component):
    """
    When added to a walkable surface, adds pathnodes to it.
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.nodes = []

    def generate_nodes(self):
        entity = self.entity
        if (Collisions not in entity.components
            or 'top' not in entity.component(Collisions).solid_edges):
            self.nodes = []
            return
        nodes = []
        width = entity.rect.width
        xpos = entity.rect.left
        for i in range(width/config.NODE_SPACING):
            nodes.append([xpos, self.rect.top])
            xpos += config.NODE_SPACING
        self.nodes = nodes

    def on_add(self):
        self.generate_nodes()

    def update(self, dt):
        rect = self.entity.rect
        if rect.y != rect.old.y or rect.x != rect.old.x:
            self.generate_nodes()


class PathFinding(Component):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.goal = None
        self.current_destination = None
        self.path = []


class Display(Component):
    def __init__(self, images):
        """
        images should be a dict of pyglet images, or paths.
        {name: Image}
        """
        super(self.__class__, self).__init__()
        self.images = images

    def set_image(self, name):
        self.entity.image = self.images[name]


class Health(Component):
    def __init__(self):
        super(Health, self).__init__()
        self.amount = 100

    def is_dead(self):
        return self.amount <= 0

    def take_damage(self, damage):
        self.amount -= damage


class Team(Component):
    def __init__(self, name):
        super(self.__class__, self).__init__()
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name


class Hurt(Component):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.damage = damage


class Weapon(Component):
    # When a player changes weapons, just swap out his Weapon component
    # Keep a second list of components not equipped
    def __init__(self):
        super(self.__class__, self).__init__()

    def get_components(self):
        """
        Return a list of components
        which will be used to create an attack entity.
        Override this method in subclass.
        """
        team = self.entity.components.get(Team, None)
        teamname = team.name if team else ''
        return [Team(teamname)]


class Fist(Weapon):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.add_as = Weapon
        self.damage = damage

    def get_components(self):
        base = super(self.__class__, self).get_components()

        return [Hurt(self.damage),
                Push(),
                Collisions()] + base


class Pistol(Weapon):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.add_as = Weapon
        self.damage = damage
        # When a bullet goes off screen, delete it

    def get_components(self):
        # Get the components for a bullet
        base = super(self.__class__, self).__init__()
        return [Hurt(self.damage),
                Collisions(),
                Movement()] + base


class Push(Component):
    """
    This component, coupled with a push component
    will push any entity it comes into contact with.
    """
    def __init__(self, strength=1):
        super(self.__class__, self).__init__()
        self.strength = strength


class Movement(Component):
    """
    Basic movement component.
    """
    def __init__(self):
        super(Movement, self).__init__()
        self.acceleration = [0, 0]
        self.velocity = [0, 0]

    def update(self, dt):
        self.velocity[0] += self.acceleration[0]*dt
        self.velocity[1] += self.acceleration[1]*dt


class PlayerMovement(Movement):
    """
    Movement for players, jump, walk and such functions.
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.add_as = Movement
        self.walk_acceleration = 8*config.METER
        self.max_walk_speed = 4*config.METER
        self.jump_acceleration = 40*config.METER
        self.max_jump_speed = 5.5*config.METER
        self.is_jumping = False
        self.direction = 1

    def walk(self, accel_mod):
        accel = accel_mod*self.walk_acceleration
        self.direction = accel_mod
        if accel_mod * self.velocity[0] < 0:
            # Changing direction, add some extra acceleration
            accel += accel_mod*self.walk_acceleration
        elif abs(self.velocity[0]) >= self.max_walk_speed:
            accel = 0
        self.acceleration[0] = accel

    def end_walk(self):
        if self.velocity[0] * self.direction < 0:
            # Stop immediately when player starts
            # moving in opposite direction
            self.velocity[0] = 0
            self.acceleration[0] = 0
        elif abs(self.velocity[0]) > 0:
            self.acceleration[0] = -self.direction*self.walk_acceleration

    def jump(self):
        if not self.is_jumping and self.velocity[1] == 0:
            self.is_jumping = True
            self.acceleration[1] = self.jump_acceleration

    def end_jump(self):
        if self.is_jumping:
            self.is_jumping = False
            self.acceleration[1] = 0

    def update(self, dt):
        # Update velocity using acceleration, call each frame
        if self.velocity[1] >= self.max_jump_speed:
            log.info('at max jump speed')
            # To prevent jumping to infinite heights
            self.acceleration[1] = 0
            self.velocity[1] = self.max_jump_speed

        super(self.__class__, self).update(dt)


class Collisions(Component):
    def __init__(self, collidables):
        super(self.__class__, self).__init__()
        # collidables should be a CollisionManager instance
        # Parent entity is added to collision manager when
        # this component is added to entity
        self.collidables = collidables
        self.solid_edges = ['left', 'right', 'top', 'bottom']
        self.disabled = 0

    def get_colliding(self):
        if not self.disabled:
            return self.collidables.objs_colliding(self.entity)

    def on_add(self):
        self.collidables.add(self.entity)

    def disable(self, frames=1):
        # Disable collision checking for x frames
        self.disabled = frames

    def update(self, dt):
        if self.disabled:
            self.disabled -= 1


class Gravity(Component):
    """
    Add this to Entity to make it fall by config.GRAVITY every second.
    Must have a Movement component as well.
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.amount = config.GRAVITY*0.5

    def update(self, dt):
        # Gravity amount updated every frame gravity*time
        self.amount = config.GRAVITY*dt
