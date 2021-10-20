import functools
import threading
from social_interaction_cloud.basic_connector import BasicSICConnector


class Action:

    def __init__(self, action, *args, callback=None, lock: threading.Event() = None):
        self.action = action
        self.callback = callback
        self.lock = lock
        self.args = args

    def perform(self) -> threading.Event():
        self.action(*self.args, self.callback)
        return self.lock


class ActionFactory:

    def __init__(self, sic: BasicSICConnector):
        self.sic = sic

    def build_action(self, action_name: str, *args, callback=None, lock: threading.Event() = None):
        action = getattr(self.sic, action_name)
        return Action(action, *args, callback=callback, lock=lock)

    def build_waiting_action(self, action_name: str, *args, additional_callback=None):
        callback, lock = self.build_waiting_callback(additional_callback)
        return self.build_action(action_name, *args, callback=callback, lock=lock)

    def build_vision_listener(self, vision_type: str, callback=None, continuous=False):
        lock = None
        if not continuous:
            callback, lock = self.build_vision_stopping_callback(vision_type.lower(), callback)
        else:
            if not callback:
                raise ValueError("To build a continuous listener, you need to supply a callback function.")

        if vision_type.lower() == 'face':
            return self.build_action('start_face_recognition', callback=callback, lock=lock)
        elif vision_type.lower() == 'people':
            return self.build_action('start_people_detection', callback=callback, lock=lock)
        elif vision_type.lower() == 'emotion':
            return self.build_action('start_emotion_detection', callback=callback, lock=lock)
        else:
            raise ValueError('vision_type only supports a value of "face", "people", or "emotion"')

    def build_touch_listener(self, touch_event, callback=None, continuous=False):
        lock = None
        if not continuous:
            callback, lock = self.build_touch_stopping_callback(touch_event, callback)

        return self.build_action('subscribe_touch_listener', touch_event, callback=callback, lock=lock)

    @staticmethod
    def build_waiting_callback(additional_callback=None):
        lock = threading.Event()

        def callback(*args):
            if additional_callback:
                additional_callback(*args)
            lock.set()

        return callback, lock

    def build_vision_stopping_callback(self, vision_type, original_callback=None):
        if vision_type == 'face':
            stop_vision = self.sic.stop_face_recognition
        elif vision_type == 'people':
            stop_vision = self.sic.stop_people_detection
        elif vision_type == 'emotion':
            stop_vision = self.sic.stop_emotion_detection
        else:
            raise ValueError('vision_type only supports a value of "face", "people", or "emotion"')

        def callback(*args):
            if original_callback:
                original_callback(*args)
            stop_vision()

        return self.build_waiting_callback(callback)

    def build_touch_stopping_callback(self, touch_event, original_callback=None):
        stop_listening = functools.partial(self.sic.unsubscribe_touch_listener, touch_event)

        def callback(*args):
            if original_callback:
                original_callback(*args)
            stop_listening()

        return self.build_waiting_callback(callback)


class ActionRunner:

    def __init__(self, cbsr: BasicSICConnector):
        self.cbsr = cbsr
        self.action_factory = ActionFactory(cbsr)
        self.loaded_actions = []

    def load_action(self, action_name: str, *args, callback=None):
        self.loaded_actions.append(self.action_factory.build_action(action_name, *args, callback=callback))

    def load_waiting_action(self, action_name: str, *args, additional_callback=None):
        self.loaded_actions.append(self.action_factory.build_waiting_action(action_name, *args,
                                                                            additional_callback=additional_callback))

    def load_vision_listener(self, vision_type: str, callback, continuous=False):
        self.loaded_actions.append(self.action_factory.build_vision_listener(vision_type, callback, continuous))

    def load_touch_listener(self, touch_even: str, callback=None, continuous=False):
        self.loaded_actions.append(self.action_factory.build_touch_listener(touch_even, callback, continuous))

    def clear(self):
        self.loaded_actions = []

    def run_loaded_actions(self, clear: bool = True):
        locks = []
        for action in self.loaded_actions:
            lock = action.perform()
            if lock:
                locks.append(lock)

        if locks:
            condition = threading.Condition()
            self.cbsr.subscribe_condition(condition)
            with condition:
                condition.wait_for(lambda: all([_lock.is_set() for _lock in locks]))
            self.cbsr.unsubscribe_condition(condition)

        if clear:
            self.clear()
        else:
            for lock in locks:
                lock.clear()

    def run_action(self, action_name: str, *args, callback=None):
        action = self.action_factory.build_action(action_name, *args, callback=callback)
        action.perform()

    def run_waiting_action(self, action_name: str, *args, additional_callback=None):
        action = self.action_factory.build_waiting_action(action_name, *args, additional_callback=additional_callback)
        lock = action.perform()
        lock.wait()

    def run_vision_listener(self, vision_type: str, callback, continuous=False):
        action = self.action_factory.build_vision_listener(vision_type, callback, continuous)
        lock = action.perform()
        if lock:
            lock.wait()

    def run_touch_listener(self, touch_event: str, callback=None, continuous=False):
        action = self.action_factory.build_touch_listener(touch_event, callback, continuous)
        lock = action.perform()
        if lock:
            lock.wait()
