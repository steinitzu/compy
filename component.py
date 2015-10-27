import logging
import math

from cocos.director import director
from cocos.euclid import Point2
from cocos.sprite import Sprite

from pyglet.window import key as keycode
from pyglet.window.key import KeyStateHandler
import pyglet

import config
from util import distance

log = logging.getLogger('compy')


class Component(object):

    def __init__(self):
        """
        Called when component is initalized.
        Entity is not known here, so do not try to reference it
        in subclasses.
        Override |on_add| function to handle entity specific code.
        """
        self.entity = None
        # Added with this classname
        self.add_as = self.__class__

    def on_add(self):
        """
        Called when component is added to entity.
        """
        pass

    def update(self, dt):
        """
        Update method will be called each frame
        by SystemsManager.
        dt is the amount of time, in seconds, since last frame.
        """
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


class ElevatorController(Component):
    """
    Controls a Movement component.
    """
    def __init__(self, move_by=(0, 0), duration=5,
                 reversable=True, stoppable=True, continuous=False):
        super(ElevatorController, self).__init__()
        self.move_by = move_by
        self.duration = 5
        self._elapsed = 0

        # Can be stopped before duration has passed
        self.stoppable = stoppable
        self.reversable = reversable
        # Keeps running until explicitly stopped
        # Implies reversable
        self.continuous = continuous

    def start(self):
        if self._elapsed >= self.duration:
            self._elapsed = 0
        dx, dy = self.move_by
        vx = dx/self.duration
        vy = dy/self.duration
        self.entity.component(Movement).velocity = [vx, vy]

    def stop(self):
        m = self.entity.component(Movement)
        if self._elapsed >= self.duration:
            if self.reversable:
                self.reverse()
            m.velocity = [0, 0]
        elif self.stoppable:
            m.velocity = [0, 0]

    def reverse(self):
        self.move_by = -self.move_by[0], -self.move_by[1]

    def is_running(self):
        v = self.entity.component(Movement).velocity
        return v[0] or v[1]

    def update(self, dt):
        if self.is_running():
            self._elapsed += dt
            if self._elapsed >= self.duration:
                if self.continuous:
                    self.reverse()
                    self.start()
                else:
                    self.stop()


class BulletController(ElevatorController):
    """
    Controller that moves entity to a point at a given velocity.
    """
    def __init__(self, target_point=(0, 0), velocity=1000):
        super(BulletController, self).__init__()
        self.reversable = False
        self.continuous = False
        self._velocity = velocity
        self._target_point = target_point

    def set_velocity(self, value):
        spatial = self.entity.component(Spatial)
        pos = spatial.x, spatial.y
        d = distance(self.target_point, pos)
        self.duration = d/value
        self._velocity = value

    velocity = property(lambda self: self._velocity, set_velocity)

    def set_target_point(self, value):
        dx = value[0] - self.entity.component(Spatial).x
        dy = value[1] - self.entity.component(Spatial).y
        self.move_by = (dx, dy)
        self._target_point = value
        # Causes duration to update with new distance
        self.velocity = self._velocity

    target_point = property(lambda self:
                            self._target_point, set_target_point)

    def on_add(self):
        self.target_point = self._target_point

    # start method is same elevator_controller

    def stop(self):
        self.entity.component(Movement).velocity = [0, 0]
        self.entity.kill()

    # Update method is same as elevatorcontroller


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
            'attack': {keycode.A},
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
        d = entity.components[Display]
        weapon = entity.component(Inventory).equipped
        up = self.map['up'].intersection(pressed)
        down = self.map['down'].intersection(pressed)
        waxis = [0, 0]
        if self.map['left'].intersection(pressed):
            m.walk(-1)
            d.set_image('left')
            if weapon:
                waxis[0] = -1
        elif self.map['right'].intersection(pressed):
            m.walk(1)
            d.set_image('right')
            if weapon:
                waxis[0] = 1
        else:
            m.end_walk()
            if weapon:
                if up or down:
                    waxis[0] = 0
                else:
                    waxis[0] = m.direction
        if self.map['up'].intersection(pressed):
            if weapon:
                waxis[1] = 1
        elif self.map['down'].intersection(pressed):
            if weapon:
                waxis[1] = -1
        else:
            waxis[1] = 0

        if weapon:
            weapon.facing = waxis
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
        else:
            u.end_use()

    def do_attack(self, entity, pressed):
        weapon = entity.component(Inventory).equipped
        if not weapon:
            return
        if self.map['attack'].intersection(pressed):
            log.info('Attacking')
            entity.component(Movement).end_walk()
            weapon.perform_attack()
            for k in self.map['attack']:
                pressed.discard(k)
        else:
            weapon.end_attack()

    def update(self, dt):
        p = self.entity
        pressed = self.pressed
        # Will error if no movement component
        self.do_movement(p, pressed)
        self.do_use(p, pressed)
        self.do_attack(p, pressed)


class Fighting(Component):
    """
    A flag for systems manager, tells it to attach AttackSystem.
    """
    def __init__(self):
        super(Fighting, self).__init__()


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
            if self.controlled_component.is_running():
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
        self.is_using = False

    def use(self):
        self.is_using = True
        return
        for entity in self.entity.component(Collisions).get_colliding():
            try:
                entity.component(Usable).use(self.entity)
            except KeyError:
                pass

    def end_use(self):
        self.is_using = False


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
    def __init__(self, images={}, z=1):
        """
        images should be a dict of pyglet images, or paths.
        {name: Image}
        """
        super(self.__class__, self).__init__()
        self.images = images
        for k, v in self.images.items():
            self.add_image(k, v)
        self.z = z
        self.sprite = Sprite(self.images['default'])

    def set_image(self, name):
        self.sprite.image = self.images[name]

    def old_set_image(self, name):
        self.entity.image = self.images[name]

    def add_image(self, key, value):
        if isinstance(value, basestring):
            value = pyglet.resource.image(value)
        self.images[key] = value


from cocos.rect import Rect
class Spatial(Component):
    """
    Gives entity a rectangular area on screen.
    Can either pass a Sprite object, in which case, the rectangle created
    will use the width, height and position of the sprite.
    If no sprite is passed, will use width and height keyword arguments.
    width/height_multi arguments are multiplied by passed width and height
    (e.g. if you want the occupied rectangle to be smaller or larger than
    the actual sprite).

    Position can be updated using any 'rect' supported properties.
    If Entity has a Display component as well, its position is updated
    accordingly any time Spatial position is changed.
    Same applies to Collision components, cshape position will be updated
    to reflect spatial changes.
    """
    def __init__(self, sprite=None, width=1, height=1,
                 width_multi=1.0, height_multi=1.0):
        super(Spatial, self).__init__()
        self.width_multi, self.height_multi = width_multi, height_multi
        self.rect = self.get_rect(sprite=sprite, width=width, height=height)
        self.old = self.get_rect(sprite=sprite, width=width, height=height)

    def get_rect(self, sprite=None, width=1, height=1):
        if sprite:
            x, y = sprite.position
            x -= sprite.image_anchor_x
            y -= sprite.image_anchor_x
            bw, bh = sprite.width, sprite.height
        else:
            x = y = 0
            bw, bh = width, height
        return Rect(x, y,
                    int(bw*self.width_multi),
                    int(bh*self.height_multi))

    def _set_property(self, name, value):
        if not self.entity or Movement not in self.entity.components:
            old_val = value
        else:
            old_val = getattr(self.rect, name)
        setattr(self.old, name, old_val)
        setattr(self.rect, name, value)
        try:
            s = self.entity.component(Display).sprite
            s.position = self.rect.center
        except:
            # NO Display component, carry on
            pass
        try:
            # Adjust collision shape accordingly
            self.entity.component(Collisions).cshape.center = self.rect.center
        except:
            # No collisions
            pass

    def __setattr__(self, name, value):
        posattrs = ('bottom', 'top', 'left', 'right',
                    'center', 'midtop', 'midbottom',
                    'midleft', 'midright', 'topleft', 'topright',
                    'bottomleft', 'bottomright',
                    'x', 'y')
        if name in posattrs:
            self._set_property(name, value)
        elif name in ('width', 'height'):
            setattr(self.old, name, value)
            setattr(self.rect, name, value)
        else:
            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        posattrs = ('bottom', 'top', 'left', 'right',
                    'center', 'midtop', 'midbottom',
                    'midleft', 'midright', 'topleft', 'topright',
                    'bottomleft', 'bottomright',
                    'x', 'y', 'position')
        sattrs = ('width', 'height')
        if name in posattrs + sattrs:
            return getattr(self.rect, name)
        return object.__getattr__(self, name)


from cocos.collision_model import AARectShape
class Collisions(Component):
    def __init__(self, solid_edges=('left', 'right', 'top', 'bottom'),
                 no_handlers=False):
        super(Collisions, self).__init__()
        self.solid_edges = solid_edges
        self.no_handlers = no_handlers
        self.cshape = None

    def get_cshape(self):
        # Depends on a Spatial component
        sp = self.entity.component(Spatial)
        cshape = AARectShape(sp.center, sp.width/2, sp.height/2)
        return cshape

    def on_add(self):
        self.cshape = self.get_cshape()


class Attached(Component):
    """
    Entity with this component is attached to a
    given Spatial component.
    That means, whenever the attached component moves,
    this entity moves.
    Requires Spatial
    """
    def __init__(self, to=None):
        super(Attached, self).__init__()
        # Should be a Spatial component
        self.attached_to = to

    def update(self, dt):
        target = self.attached_to
        spatial = self.entity.component(Spatial)
        delta_pos = (target.x - target.old.x,
                     target.y - target.old.y)
        spatial.x += delta_pos[0]
        spatial.y += delta_pos[1]


class old_Collisions(Component):
    def __init__(self, collidables,
                 solid_edges=('left', 'right', 'top', 'bottom'),
                 no_handlers=False):
        super(self.__class__, self).__init__()
        # collidables should be a CollisionManager instance
        # Parent entity is added to collision manager when
        # this component is added to entity
        self.collidables = collidables
        self.solid_edges = solid_edges
        # Can be collided with but handles none of its own collisions
        self.no_handlers = no_handlers
        self.disabled = 0


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




class Health(Component):
    def __init__(self):
        super(Health, self).__init__()
        self.amount = 100

    def is_dead(self):
        return self.amount <= 0

    def take_damage(self, damage):
        log.info('giving damage: %s', damage)
        self.amount -= damage
        log.info('health after damage: %s', self.amount)


    def update(self, dt):
        if self.is_dead():
            self.entity.kill()


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
        super(Weapon, self).__init__()
        # X, Y axis where weapon is being aimed
        self.facing = [0, 0]
        self.components = {}
        self.attacking = True

    def perform_attack(self):
        log.info('Perform attack called')
        self.attacking = True

    def end_attack(self):
        self.attacking = False


class Fist(Weapon):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.add_as = Weapon
        self.damage = damage


class Pistol(Weapon):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.add_as = Weapon
        self.damage = damage
        self.range = 1000
        self.velocity = 3000

        # Components for bullet and kwarg dict
        self.components = (
            (Display, {'images': {'default': 'ballman72x72.png'},
                       'z': 4}),
            (Spatial, {}),
            (Hurt, {'damage': self.damage}),
            (Collisions, {'solid_edges': ()}),
            (Movement, {}),
            (BulletController, {'velocity': self.velocity}),
            (Gravity, {}),
        )

    def fire(self, bullet):
        bc = bullet.component(BulletController)
        bc.movement = bullet.component(Movement)
        arange = self.range
        degrees = math.atan2(self.facing[1], self.facing[0])*180/math.pi
        rads = degrees * (math.pi/180)
        spatial = self.entity.component(Spatial)
        endpoint = (spatial.x+math.cos(rads)*arange,
                    spatial.y+math.sin(rads)*arange)
        bc.target_point = endpoint
        bc.start()


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


class Pickupable(Component):
    def __init__(self, name=''):
        super(Pickupable, self).__init__(self)
        self.name = name

    def pick_up(self, picked_up_by):
        i = picked_up_by.component(Inventory)
        i.add(self)


class Inventory(Component):
    def __init__(self):
        super(Inventory, self).__init__()
        self.items = []
        self.equipped = None

    def add(self, pickup):
        self.items.append(pickup)
        pickup.entity = self.entity

    def equip(self, index):
        self.equipped = self.items[index]
