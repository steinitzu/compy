import logging
from collections import OrderedDict

from component import *
from entity import Entity

log = logging.getLogger('compy')


class System(object):
    def __init__(self, manager):
        self.manager = manager
    def update(self, dt):
        pass


class MovementSystem(System):
    def __init__(self, entity, manager):
        super(MovementSystem, self).__init__(manager)
        self.entity = entity

        self.movement = None
        self.collisions = None
        self.gravity = None
        components = self.entity.components
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
            self.collision_system = self.manager.get_system(
                self.entity, CollisionSystem)
            self.collision_system.is_child = True
            #self.collision_system = CollisionSystem(self.collisions, manager)

    def _move_horizontal(self, entity, movement, dt):
        vx = movement.velocity[0]
        entity.component(Spatial).x += vx * dt
        if self.collisions:
            self.collision_system.handle_collisions(axis='x')

    def _move_vertical(self, entity, movement, dt):
        try:
            movement.velocity[1] -= self.gravity.amount
        except:
            pass
        vy = movement.velocity[1]
        entity.component(Spatial).y += vy * dt
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
    def __init__(self, collision_component, manager):
        super(CollisionSystem, self).__init__(manager)
        self.manager.collidables.add(collision_component)
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
        # Set of usable Components
        # Will contain any Usable components colliding with entity
        # if entity has a Use component
        self.usable = set()

    def handle_collisions(self, axis='x'):
        """
        Check and handle all collisions.
        """
        if not self.handlers:
            # No collision handlers, move along
            return
        cobs = self.manager.collidables.known_objs()
        self.manager.collidables.clear()
        for c in cobs:
            self.manager.collidables.add(c)
        self.usable.clear()
        for ob in self.manager.collidables.objs_colliding(self.component):
            if Use in self.entity.components:
                # Update the set of usables in range of entity
                try:
                    usable = ob.entity.component(Usable)
                    self.usable.add(usable)
                except KeyError:
                    pass
            self.handle_collision(ob, axis=axis)

    def handle_collision(self, colliding_object, axis='x'):
        for h in self.handlers:
            h(self.entity, colliding_object, axis=axis)

    def correct_position(self, entity, colliding_object, axis='x'):
        #solid_edges = colliding_object.component(Collisions).solid_edges
        solid_edges = colliding_object.solid_edges
        movement = entity.component(Movement)
        entity_spatial = entity.component(Spatial)
        cob = colliding_object

        goingleft = entity_spatial.x < entity_spatial.old.x
        goingright = entity_spatial.x > entity_spatial.old.x
        goingup = entity_spatial.y > entity_spatial.old.y
        goingdown = entity_spatial.y < entity_spatial.old.y
        notmoving = (not goingleft and not goingright
                     and not goingup and not goingdown)

        cob_spatial = cob.entity.component(Spatial)

        cobgoingleft = cob_spatial.x < cob_spatial.old.x
        cobgoingright = cob_spatial.x > cob_spatial.old.x
        cobgoingup = cob_spatial.y > cob_spatial.old.y
        cobgoingdown = cob_spatial.y < cob_spatial.old.y
        cobnotmoving = (not cobgoingleft and not cobgoingright
                     and not cobgoingup and not cobgoingdown)
        cobmovingx = cobgoingleft or cobgoingright
        cobmovingy = cobgoingup or cobgoingdown

        # TODO: handle this shit later

        def stop_movement(m, i):
            m.velocity[i] = 0
            m.acceleration[i] = 0

        if axis == 'x':
            if goingright:
                if 'left' not in solid_edges:
                    return
                if cobmovingx:
                    return
                if cobgoingup:
                    if entity_spatial.bottom >= cob_spatial.old.top:
                        # Otherwise player will fall be warped off
                        # fast moving elevators
                        return
                entity_spatial.right = cob_spatial.left
                stop_movement(movement, 0)
            elif goingleft:
                if 'right' not in solid_edges:
                    return
                if cobmovingx:
                    return
                if cobgoingup:
                    if entity_spatial.bottom >= cob_spatial.old.top:
                        # Otherwise player will fall be warped off
                        # fast moving elevators
                        return
                entity_spatial.left = cob_spatial.right
                stop_movement(movement, 0)
            elif cobgoingleft:
                if 'left' not in solid_edges:
                    return
                stop_movement(movement, 0)
            elif cobgoingright:
                if 'right' not in solid_edges:
                    return
                stop_movement(movement, 0)
        elif axis == 'y':
            if goingup:
                if 'bottom' not in solid_edges:
                    return
                if entity_spatial.old.top > cob_spatial.bottom:
                    return
                entity_spatial.top = cob_spatial.bottom
                stop_movement(movement, 1)
            elif goingdown:
                if 'top' not in solid_edges:
                    return
                if entity_spatial.old.bottom < cob_spatial.top:
                    if (entity_spatial.old.bottom >= cob_spatial.old.top
                        and cobmovingy):
                        pass
                    else:
                        return
                # This makes it so that entity
                # doesn't slide off moving platforms
                dx = cob_spatial.x - cob_spatial.old.x
                entity_spatial.left += dx
                entity_spatial.bottom = cob_spatial.top
                stop_movement(movement, 1)
            elif cobgoingdown:
                if 'bottom' not in solid_edges:
                    return
                entity_spatial.top = cob_spatial.bottom
                stop_movement(movement, 1)
            elif cobgoingup:
                if 'top' not in solid_edges:
                    return
                entity_spatial.bottom = cob_spatial.top
                stop_movement(movement, 1)

    def deal_damage(self, entity, colliding_object, axis=None):
        """
        This handler deals damage to colliding object.
        This is for entities with a Hurt component (e.g. a bullet)
        """
        base_damage = entity.components[Hurt].damage
        try:
            if (entity.component(Team) != colliding_object.component(Team)
                or config.TEAMKILL):
                colliding_object.component(Health).take_damage(base_damage)
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


class AttackSystem(System):
    def __init__(self, entity, collidables, manager):
        super(AttackSystem, self).__init__(manager)
        # Weapon entity
        self.entity = entity
        self.collidables = collidables

    def attack(self, weapon):
        attack_entity = Entity('ballman72x72.png')
        entity = attack_entity
        if Team in self.entity.components:
            attack_entity.add_components(
                Team(self.entity.component(Team).name))
        for c_class, kwargs in weapon.components.items():
            if c_class == Collisions:
                col = c_class(self.collidables, **kwargs)
                col.solid_edges = ()
                entity.add_components(col)
            else:
                entity.add_components(c_class(**kwargs))
        entity.rect.x, entity.rect.y = self.entity.rect.x, self.entity.rect.y
        self.manager.add_entities(entity)
        weapon.fire(entity)

    def update(self, dt):
        weapon = self.entity.component(Inventory).equipped
        if not isinstance(weapon, Weapon):
            return
        if weapon and weapon.attacking:
            self.attack(weapon)


class UseSystem(System):
    def __init__(self, entity, manager):
        super(UseSystem, self).__init__(manager)
        self.entity = entity

    def do_use(self):
        cs = self.manager.get_system(self.entity, CollisionSystem)
        for u in cs.usable:
            u.use(self.entity)

    def update(self, dt):
        if self.entity.component(Use).is_using:
            self.do_use()


class SystemsManager(object):
    """
    One per level/scene.
    """
    def __init__(self, collidables, layer):
        # Entity: [systems]
        self.systems = OrderedDict()
        self.collidables = collidables
        self.layer = layer
        self.to_remove = set()

    def get_system(self, entity, system_type):
        for s in self.systems[entity]:
            if isinstance(s, system_type):
                return s
        # No system of type, raise exception
        raise Exception('{} has no system of type {}'.format(
            entity, system_type))


    def add_entities(self, *entities):
        """
        Add entity to systems manager and
        create systems for it.
        """
        for entity in entities:
            self.systems[entity] = []
            systems = self.systems[entity]
            if Collisions in entity.components:
                c = CollisionSystem(entity.component(Collisions), self)
                systems.append(c)
            if Movement in entity.components:
                m = MovementSystem(entity, self)
                systems.append(m)
            if Fighting in entity.components:
                a = AttackSystem(entity, self.collidables, self)
                systems.append(a)
            if Use in entity.components:
                systems.append(UseSystem(entity, self))
            if Display in entity.components:
                self.layer.add(entity.component(Display).sprite,
                               z=entity.component(Display).z)
            entity.systems_manager = self

    def remove(self, entity):
        """
        Schedules an entity to be removed
        from the system on next update cycle.
        """
        self.to_remove.add(entity)

    def update(self, dt):
        # Update all components and systems
        for entity in self.systems.keys():
            for component in entity.components.values():
                component.update(dt)
            for system in self.systems[entity]:
                system.update(dt)
        while self.to_remove:
            torm = self.to_remove.pop()
            del self.systems[torm]
            super(Entity, torm).kill()
