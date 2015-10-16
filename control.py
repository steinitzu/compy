from pyglet.window import key as keycode

from component import *


class Controller(object):
    def __init__(self, entity):
        self.entity = entity


class KeyBoardController(Controller):
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
        self.pressed.add(key)
        self.modifiers = modifiers

    def on_key_release(self, key, modifiers):
        try:
            self.keys_pressed.remove(key)
        except KeyError:
            pass
        self.modifiers = modifiers

    def do_movement(self, entity, pressed):
        m = p.components[Movement]
        if self.map['left'].intersection(pressed):
            m.walk(-1)
        elif self.map['right'].intersection(pressed):
            m.walk(1)
        if self.map['jump'].intersection(pressed):
            m.jump()
        else:
            m.end_jump()

    def update(self):
        p = self.entity
        pressed = self.pressed
        try:
            # Will error if no movement component
            self.do_movement(p, pressed)
        except:
            pass
