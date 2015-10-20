import logging
from collections import OrderedDict

from component import *
from entity import Entity

log = logging.getLogger('compy')


class System(object):
    def update(self, dt):
        pass


class MovementSystem(System):
    def __init__(self, movement_component):
        self.movement = movement_component
        self.collisions = None
        self.gravity = None
        components = self.movement.entity.components
        for c in components.values(): # TODO: Fix later
            if isinstance(c, Movement):
                self.movement = c
            elif isinstance(c, Collisions):
                self.collisions = c
            elif isinstance(c, Gravity):
                self.gravity = c
        if not self.movement:
            raise Exception('MovementSystem must be initialized'
                            + ' with at least a'
                            + ' components.Movement component.')
        self.collision_system = None
        if self.collisions:
            self.collision_system = CollisionSystem(self.collisions)
            self.collision_system.is_child = True

    def _move_horizontal(self, entity, movement, dt):
        vx = movement.velocity[0]
        entity.rect.x += vx * dt
        if self.collisions:
            self.collision_system.handle_collisions(axis='x')

    def _move_vertical(self, entity, movement, dt):
        try:
            movement.velocity[1] -= self.gravity.amount
        except:
            pass
        vy = movement.velocity[1]
        entity.rect.y += vy * dt
        if self.collisions:
            self.collision_system.handle_collisions(axis='y')

    def move(self, dt):
        entity = self.movement.entity
        movement = self.movement
        self._move_horizontal(entity, movement, dt)
        self._move_vertical(entity, movement, dt)

    def update(self, dt):
        self.move(dt)


class CollisionSystem(System):
    def __init__(self, collision_component):
        super(self.__class__, self).__init__()
        self.entity = collision_component.entity
        entity = self.entity
        self.component = collision_component
        if self.component.no_handlers:
            self.handlers = []
        else:
            handlers = []
            if Hurt in entity.components:
                handlers.append(self.deal_damage)
            if Push in entity.components:
                handlers.append(self.push)
            if (Movement in entity.components
                and (Push not in entity.components
                     and Hurt not in entity.components)):
                handlers.append(self.correct_position)
            self.handlers = handlers
        # Is child and therefor controlled by external system
        self.is_child = False

    def handle_collisions(self, axis='x'):
        """
        Check and handle all collisions.
        """
        if not self.handlers:
            # No collision handlers, move along
            return
        for ob in self.component.get_colliding():
            self.handle_collision(ob, axis=axis)

    def handle_collision(self, colliding_object, axis='x'):
        for h in self.handlers:
            h(self.entity, colliding_object, axis=axis)

    def correct_position(self, entity, colliding_object, axis='x'):
        """
        This handler is for moving entities.
        When entity collides with object, it's position will be corrected
        so that it is no longer colliding.
        """
        solid_edges = colliding_object.component(Collisions).solid_edges
        movement = entity.component(Movement)
        rect = entity.rect
        # Axis can be X or Y

        if axis == 'x':
            if rect.x > rect.old.x:
                # moving right
                if 'left' not in solid_edges:
                    return
                log.info('Rect.x: %s, old.x: %s, right: %s, oldright: %s',
                         rect.x, rect.old.x, rect.right, rect.old.right)
                log.info('rect width: %s, old width: %s', rect.width, rect.old.width)
                if entity.rect.old.right > colliding_object.rect.left+5:
                    return
                try:
                    # To detect moving platforms going up
                    if colliding_object.component(Movement).velocity[1] > 0:
                        return
                except KeyError:
                    pass
                entity.rect.right = colliding_object.rect.left
                movement.velocity[0] = 0
                movement.acceleration[0] = 0
            elif rect.x < rect.old.x:
                # moving left
                if 'right' not in solid_edges:
                    return
                if entity.rect.old.left < colliding_object.rect.right:
                    return
                try:
                    if colliding_object.component(Movement).velocity[1] > 0:
                        return
                except KeyError:
                    pass
                entity.rect.left = colliding_object.rect.right
                movement.velocity[0] = 0
                movement.acceleration[0] = 0
        elif axis == 'y':
            if rect.y > rect.old.y:
                # Moving up
                if 'bottom' not in solid_edges:
                    return
                if entity.rect.old.top > colliding_object.rect.bottom:
                      return
                entity.rect.top = colliding_object.rect.bottom
                movement.velocity[1] = 0
                movement.acceleration[1] = 0
            elif rect.y < rect.old.y:
                if 'top' not in solid_edges:
                    return
                if entity.rect.old.bottom < colliding_object.rect.top:
                    return
                if (Movement in colliding_object.components
                    and colliding_object.rect.x != colliding_object.rect.old.x):
                    # FUUUUUUUUUUUUUUUUUU
                    dx = colliding_object.rect.x - colliding_object.rect.old.x
                    entity.rect.x += dx
                # if (entity.rect.old.bottom < colliding_object.rect.top
                #     and (colliding_object.rect.old.top
                #          >= colliding_object.rect.top)):
                    # Seconds contition is for moving platforms
                    # going up (elevators)
                    #return
                entity.rect.bottom = colliding_object.rect.top
                movement.velocity[1] = 0
                movement.acceleration[1] = 0


    def deal_damage(self, entity, colliding_object, axis=None):
        """
        This handler deals damage to colliding object.
        This is for entities with a Hurt component (e.g. a bullet)
        """
        base_damage = entity.components[Attack].damage
        try:
            if (entity.component(Team) != colliding_object.component(Team)
                or config.TEAMKILL):
                colliding_object.health.take_damage(base_damage)
        except KeyError:
            return

    def push(self, entity, colliding_object, axis=None):
        """
        This handler pushes colliding objects.
        A moving platform for instance, will move any players
        it collides with accordingly.
        """
        # Axis doesn't matter here
        if not Movement in colliding_object.components:
            return
        dx = entity.rect.x - entity.rect.old.x
        dy = entity.rect.y - entity.rect.old.y
        m = colliding_object.component(Movement)
        colliding_object.rect.x += dx
        colliding_object.rect.y += dy

    def update(self, dt):
        if not self.is_child:
            self.handle_collisions()


class SystemsManager(object):
    """
    One per level/scene.
    """
    def __init__(self):
        # Entity: [systems]
        self.systems = OrderedDict()

    def add_entities(self, *entities):
        """
        Add entity to systems manager and
        create systems for it.
        """
        for entity in entities:
            systems = []
            if Movement in entity.components:
                m = MovementSystem(entity.component(Movement))
                systems.append(m)
            elif Collisions in entity.components:
                # Not moving, so we add collision system
                # seperately
                c = CollisionSystem(entity.component(Collisions))
                systems.append(c)
            self.systems[entity] = systems

    def update(self, dt):
        # Update all components and systems
        for entity in self.systems.keys():
            for component in entity.components.values():
                component.update(dt)
            for system in self.systems[entity]:
                system.update(dt)


class AttackSystem(System):
    # Nah...

    def __init__(self, fast=None, strong=None, ranged=None):
        self.fast = fast
        self.strong = strong
        self.ranged = ranged

    def build_ranged_attack(self):
        if not self.ranged:
            return
        p = self.ranged.entity
        e = Entity()
        e.add_component(self.ranged)
        e.add_component(Movement())
        if self.ranged.push:
            e.add_component(Push(strength=self.ranged.push))
        try:
            e.add_component(p.components[Team])
        except KeyError:
            pass
        # TODO: calculate velocity based on angle
        e.components[Movement].velocity = [self.ranged.travel_velocity, 0]
        # Attach a movement system and add to world in caller
        return e
