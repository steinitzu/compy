from pyglet.window import key as keycode

from component import *


class Controller(object):
    def __init__(self, entity):
        self.entity = entity


class KeyboardController(Controller):
    def __init__(self, entity):
        super(self.__class__, self).__init__(entity)
        self.pressed = set([])
        self.modifiers = None

        self.map = {
            'left': {keycode.LEFT},
            'right': {keycode.RIGHT},
            'jump': {keycode.SPACE},
            'down': {keycode.DOWN},
            'up': {keycode.UP},
            }

    def on_key_press(self, key, modifiers):
        print 'key presssed'
        self.pressed.add(key)
        self.modifiers = modifiers

    def on_key_release(self, key, modifiers):
        try:
            self.pressed.remove(key)
        except KeyError:
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

    def update(self):
        p = self.entity
        pressed = self.pressed
        # Will error if no movement component
        self.do_movement(p, pressed)
