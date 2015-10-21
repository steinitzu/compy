import logging

from cocos.director import director
from cocos.euclid import Point2

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


class AutoMoveController(Component):
    """
    Depends on a movement component.
    """
    def __init__(self):
        super(AutoMoveController, self).__init__()

        # x, y points to move by
        self.move_by = (0, 0)
        # Duration in seconds
        self.duration = 10
        self.target = (0, 0)
        self._elapsed = 0
        # When finished, will run in reverse on next start
        self.reversable = True

    def start(self):
        movement = self.entity.component(Movement)
        self._elapsed = 0
        px, py = self.entity.rect.x, self.entity.rect.y
        dx, dy = self.move_by
        self.target = (px+dx, py+dy)
        vx = dx/self.duration
        vy = dy/self.duration
        movement.velocity = [vx, vy]

    def stop(self):
        self.entity.component(Movement).velocity = [0, 0]
        self.reverse()

    def state(self):
        # State is either on or off, true/false, 1/0
        m = self.entity.component(Movement)
        return m.velocity[0] or m.velocity[1]

    def reverse(self):
        if self.reversable:
            self.move_by = -self.move_by[0], -self.move_by[1]

    def update(self, dt):
        if self.state():
            self._elapsed += dt
            if  self._elapsed >= self.duration:
                self.stop()


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
            'use': {keycode.E},
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

    def do_use(self, entity, pressed):
        u = entity.component(Use)
        if self.map['use'].intersection(pressed):
            u.use()
            for k in self.map['use']:
                pressed.discard(k)

    def update(self, dt):
        p = self.entity
        pressed = self.pressed
        # Will error if no movement component
        self.do_movement(p, pressed)
        self.do_use(p, pressed)


class Usable(Component):
    """
    Makes an entity usable, generally by player pressing
    the 'use' button while touching. (e.g. a switch)
    It controls a second component referenced by 'controls_component' attribute.
    That component should have a 'start' attribute.
    The entity should generally have a Collision component.
    If entity has a Team component, only entities of same team can use it.
    """
    def __init__(self, controlled_component):
        super(Usable, self).__init__()
        self.controlled_component = controlled_component
        self.state = 0

    def can_use(self, used_by):
        can_use = False
        if Team in self.entity.components:
            if self.entity.component(Team) == used_by.component(Team):
                can_use = True
        else:
            can_use = True
        return can_use

    def use(self, used_by):
        if self.can_use(used_by):
            if self.controlled_component.state():
                self.controlled_component.stop()
            else:
                self.controlled_component.start()


class Use(Component):
    """
    Allows entity to use Usable components.
    Must have Collisions component.
    """
    def __init__(self):
        super(Use, self).__init__()

    def use(self):
        for entity in self.entity.component(Collisions).get_colliding():
            try:
                entity.component(Usable).use(self.entity)
            except KeyError:
                pass


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
    def __init__(self):
        super(self.__class__, self).__init__()


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

    def __str__(self):
        return 'Acceleration: {}\nVelocity: {}'.format(
            self.acceleration, self.velocity)


class PlayerMovement(Movement):
    """
    Movement for players, jump, walk and such functions.
    """
    def __init__(self):
        super(PlayerMovement, self).__init__()
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


class Pickupable(Component):
    def __init__(self, name=''):
        super(Pickupable, self).__init__(self)
        self.name = name

    def pick_up(self, picked_up_by):
        i = picked_up_by.component(Inventory)
        i.add(self)


class Inventory(Component):
    def __init__(self):
        super(Inventory, self).__init__(self)
        self.items = []

    def add(self, pickup):
        self.items.append(pickup)


class Collisions(Component):
    def __init__(self, collidables):
        super(self.__class__, self).__init__()
        # collidables should be a CollisionManager instance
        # Parent entity is added to collision manager when
        # this component is added to entity
        self.collidables = collidables
        self.solid_edges = ['left', 'right', 'top', 'bottom']
        self.disabled = 0
        self.no_handlers = False

    def get_colliding(self):
        if not self.disabled:
            return self.collidables.objs_colliding(self.entity)

    def collides_with(self, other):
        # Check one collision component against this one
        return self.collidables.they_collide(
            self.entity, other.entity)

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
