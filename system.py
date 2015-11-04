import logging
from collections import OrderedDict

from component import *
from entity import Entity, PathNode

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

        self._move_vertical(entity, movement, dt)
        self._move_horizontal(entity, movement, dt)

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
        for e in self.manager.systems:
            try:
                self.manager.collidables.add(
                    e.component(Collisions))
            except KeyError:
                pass
            #self.manager.collidables.add(c)
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
        # log.info('%s, %s',
        #          self.entity.component(Spatial).right,
        #          self.entity.component(Spatial).left)
        for h in self.handlers:
            h(self.entity, colliding_object, axis=axis)

    def correct_position(self, entity, colliding_object, axis='x'):
        if axis == 'x':
            self._correct_position_x(entity, colliding_object)
        elif axis == 'y':
            self._correct_position_y(entity, colliding_object)

    def _correct_position_x(self, entity, colliding_object):
        solid_edges = colliding_object.solid_edges
        movement = entity.component(Movement)
        cobrect = colliding_object.entity.component(Spatial)
        erect = entity.component(Spatial)

        goingleft = erect.x < erect.old.x
        goingright = erect.x > erect.old.x
        cobgoingleft = cobrect.x < cobrect.old.x
        cobgoingright = cobrect.x > cobrect.old.x

        if goingright or cobgoingleft:
            if 'left' in solid_edges:
                if erect.old.right <= cobrect.old.left:
                    erect.right = erect.old.right = cobrect.left
                    movement.stop('x')
        elif goingleft or cobgoingright:
            if 'right' in solid_edges:
                if erect.old.left >= cobrect.old.right:
                    erect.left = cobrect.right
                    movement.stop('x')

    def _correct_position_y(self, entity, colliding_object):
        solid_edges = colliding_object.solid_edges
        movement = entity.component(Movement)
        cobrect = colliding_object.entity.component(Spatial)
        erect = entity.component(Spatial)

        goingup = erect.y > erect.old.y
        goingdown = erect.y < erect.old.y

        cobgoingleft = cobrect.x < cobrect.old.x
        cobgoingright = cobrect.x > cobrect.old.x

        if goingup:
            if 'bottom' in solid_edges:
                if erect.old.top <= cobrect.old.bottom:
                    erect.top = cobrect.bottom
                    movement.stop('y')
        elif goingdown:
            if 'top' in solid_edges:
                if erect.old.bottom >= cobrect.old.top:
                    erect.bottom = cobrect.top
                    movement.stop('y')
                    if cobgoingleft or cobgoingright:
                        # so we don't slide off moving platforms
                        erect.x += cobrect.x - cobrect.old.x

    def deal_damage(self, entity, colliding_object, axis=None):
        """
        This handler deals damage to colliding object.
        This is for entities with a Hurt component (e.g. a bullet)
        """
        base_damage = entity.components[Hurt].damage
        try:
            coe = colliding_object.entity
            if (entity.component(Team) != coe.component(Team)
                or config.TEAMKILL):
                coe.component(Health).take_damage(base_damage)
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
        log.info('ATTACKING')
        components = []
        if Team in self.entity.components:
            components.append(Team(
                self.entity.component(Team).name))
        display = None
        for klass, kwargs in weapon.components:
            log.info(klass)
            log.info(kwargs)
            if klass == Display:
                c = klass(**kwargs)
                display = c
            elif klass == Spatial:
                c = klass(sprite=display.sprite, **kwargs)
            else:
                c = klass(**kwargs)
            components.append(c)
        e = Entity(*components)
        e.component(Spatial).center = self.entity.component(Spatial).center
        self.manager.add_entities(e)
        weapon.fire(e)

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


class PathSystem(System):
    """
    Generally use only one instance per level.
    Differs from other systems in a way that it
    manages multiple entities.

    Should be created after all entities have
    been added to the manager.
    """

    def __init__(self, manager):
        super(PathSystem, self).__init__(manager)
        self.collidables = manager.collidables
        """
        { node: {
            (player.max_jump_x, player.max_jump_y): set([edges])
            }
          }
        """
        self.nodes = {}
        self._reverse_edges = {}
        for entity in self.manager.systems:
            if Walkable not in entity.components:
                continue
            for node in self.create_nodes(entity):
                self.nodes[node] = {}
                self._reverse_edges[node] = set()
        for player in self.manager.systems:
            if PathFinding in entity.components:
                for node in self.nodes:
                    self._set_edges(
                        node,
                        player,
                        self.create_edges(node, player))

    def _edges(self, start, player):
        m = player.component(Movement)
        return self.nodes[start][(m.max_jump_x, m.max_jump_y)]

    def _set_edges(self, start, player, edges):
        player = self._player_stats(player)
        self.nodes[start][player] = edges
        for edge in edges:
            self._reverse_edges[edge].add(start)

    def _player_stats(self, player):
        """
        Turn player into max_jump_x, max_jump_y tuple.
        """
        if isinstance(player, tuple):
            return player
        else:
            m = player.component(Movement)
            return (m.max_jump_x, m.max_jump_y)

    def create_nodes(self, entity):
        """
        Create pathnodes on top of given entity.
        """
        spatial = entity.component(Spatial)
        if (Collisions not in entity.components
            or 'top' not in entity.component(Collisions).solid_edges):
            self.nodes = []
            return
        nodes = []
        width = spatial.width
        xpos = spatial.left
        for i in range(width/config.NODE_SPACING):
            node = PathNode((xpos, spatial.top), attach_to=entity)
            nodes.append(node)
            xpos += config.NODE_SPACING
        return nodes

    def get_edges(self, start, player, refresh=False):
        """
        Get edges for given start using given player's
        max jump attributes.

        Checks for collisions between the two nodes
        to make sure there's a clear path.
        Return a set() of path nodes.
        """
        all_nodes = self.nodes
        m = player.component(Movement)
        max_jump_x = m.max_jump_x
        max_jump_y = m.max_jump_y
        if (start in all_nodes
            and (max_jump_x, max_jump_y) in all_nodes[start]
            and not refresh):
            # Return the previously existing nodes
            return _edges(start, player)

        reachable = set()
        for n in all_nodes:
            if abs(n[0]-start[0]) > max_jump_x:
                continue
            if abs(n[1]-start[1]) > max_jump_y:
                continue
            reachable.add(n)

        edges = set()

        for r in reachable:
            testity = Entity(
                Spatial(width=abs(r[0]-start[0]), height=abs(r[1]-start[1])),
                Collisions(no_handlers=True))
            s = testity.component(Spatial)
            if r[0] > start[0]:
                # Edge is right of start
                s.right = start[0]
            elif r[0] < start[0]:
                # Edge is left of start
                s.left = start[0]
            else:
                # vertical line, what do?
                s.left = start[0]
            if r[1] > start[1]:
                # Edge is above start
                s.bottom = start[1]
            elif r[1] < start[1]:
                # Edge is below start
                s.bottom = r[1]
            else:
                # Edge is level with start
                s.bottom = start[1]
            blocked = False
            for cop in self.collidables.objs_colliding:
                if r[0] > start[0] and 'left' in cop.solid_edges:
                    blocked = True
                    break
                if r[0] < start[0] and 'right' in cop.solid_edges:
                    blocked = True
                    break
                if r[1] > start[1] and 'bottom' in cop.solid_edges:
                    blocked = True
                    break
                if r[1] < start[1] and 'top' in cop.solid_edges:
                    blocked = True
                    break
            if blocked:
                continue
            else:
                edges.add(r)

        return edges

    def get_path(self, goal):
        current_node = self.current_node
        if not current_node or not goal:
            return []
        elif current_node == goal:
            return [goal]
        if not self.last_target_node:
            self.last_target_node = goal
        if goal.unreachable:
            log.info('Goal unreachable: %s', goal)
            return [current_node]
        elif self.last_target_node == goal:
            if self.destination not in self.current_node.get_edges(self):
                pass
            else:
                log.info('Reusing last path: %s', self.path)
                return self.path
        else:
            self.last_target_node = goal

        start = current_node
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while not frontier.empty():
            current = frontier.get()
            if current is goal:
                break
            # Get current node edges
            for next in current.get_edges(self):
                new_cost = cost_so_far[current] + current.cost(next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self._heuristic(goal, next)
                    frontier.put(next, priority)
                    came_from[next] = current
        path = []
        path.append(goal)
        current = goal
        while True:
            try:
                current = came_from[current]
            except KeyError:
                log.warning('No available path to %s', current)
                current.unreachable = True
                break
            if not current:
                break
            path.append(current)
        # Pop current node from path
        path.pop()
        return path

    def reverse_edges(self, edge):
        """
        Get all nodes that given node is an edge of.
        """
        return self.reverse_edges[edge]

    def update(self, dt):
        for node in self.nodes:
            spatial = node.component(Spatial)
            # TODO: Use reverse edges to update the edges


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
            try:
                torm.component(Display).sprite.kill()
            except KeyError:
                # No display component, move along
                pass
