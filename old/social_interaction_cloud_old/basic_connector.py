import threading
import time
from queue import Queue
from social_interaction_cloud.abstract_connector import AbstractSICConnector


class BasicSICConnector(AbstractSICConnector):

    def __init__(self, server_ip, robot, dialogflow_key_file=None, dialogflow_agent_id=None):
        super(BasicSICConnector, self).__init__(server_ip=server_ip, robot=robot)

        if dialogflow_key_file and dialogflow_agent_id:
            self.set_dialogflow_key(dialogflow_key_file)
            self.set_dialogflow_agent(dialogflow_agent_id)

        self.__listeners = {}
        self.__conditions = []
        self.__vision_listeners = {}
        self.__touch_listeners = {}

    ###########################
    # Event handlers          #
    ###########################

    def on_robot_event(self, event):
        self.__notify_listeners(event)
        self.__notify_touch_listeners(event)

    def on_audio_language(self, language_key):
        self.__notify_listeners('onAudioLanguage', language_key)

    def on_audio_intent(self, *args, intent_name):
        self.__notify_listeners('onAudioIntent', intent_name, *args)

    def on_new_audio_file(self, audio_file):
        self.__notify_listeners('onNewAudioFile', audio_file)

    def on_speech_text(self, text):
        self.__notify_listeners('onSpeechText', text)

    def on_new_picture_file(self, picture_file):
        if not self.__vision_listeners:
            self.stop_looking()
        self.__notify_listeners('onNewPictureFile', picture_file)

    def on_person_detected(self):
        self.__notify_vision_listeners('onPersonDetected')

    def on_face_recognized(self, identifier):
        self.__notify_vision_listeners('onFaceRecognized', identifier)

    def on_emotion_detected(self, emotion):
        self.__notify_vision_listeners('onEmotionDetected', emotion)

    ###########################
    # Speech Recognition      #
    ###########################

    def speech_recognition(self, context, max_duration, callback=None):
        enhanced_callback, lock = self.__get_enhanced_callback(callback)
        self.__register_listener('onAudioIntent', enhanced_callback)
        threading.Thread(target=self.__recognizing, args=(context, lock, max_duration)).start()

    def record_audio(self, max_duration, callback=None):
        enhanced_callback, lock = self.__get_enhanced_callback(callback)
        self.__register_listener('onNewAudioFile', enhanced_callback)
        threading.Thread(target=self.__recording, args=(lock, max_duration)).start()

    def __recognizing(self, context, lock, max_duration):
        self.set_audio_context(context)
        self.start_listening()
        lock.wait(timeout=max_duration)
        self.stop_listening()
        if not lock.is_set():
            time.sleep(1)  # wait one more second after stopListening (if needed)

    def __recording(self, lock, max_duration):
        self.set_record_audio(True)
        self.start_listening()
        lock.wait(timeout=max_duration)
        self.stop_listening()
        self.set_record_audio(False)

    @staticmethod
    def __get_enhanced_callback(embedded_callback=None):
        lock = threading.Event()

        def callback(*args):
            if embedded_callback:
                embedded_callback(*args)
            lock.set()

        return callback, lock

    ###########################
    # Vision                  #
    ###########################

    def take_picture(self, callback=None):
        if not self.__vision_listeners:
            self.start_looking()
        self.__register_listener("onNewPictureFile", callback)
        super(BasicSICConnector, self).take_picture()

    def start_face_recognition(self, callback):
        self.__start_vision_recognition("onFaceRecognized", callback)

    def stop_face_recognition(self):
        self.__stop_vision_recognition("onFaceRecognized")

    def start_people_detection(self, callback):
        self.__start_vision_recognition("onPersonDetected", callback)

    def stop_people_detection(self):
        self.__stop_vision_recognition("onPersonDetected")

    def start_emotion_detection(self, callback):
        print("start emotion detection")
        self.__start_vision_recognition("onEmotionDetected", callback)

    def stop_emotion_detection(self):
        self.__stop_vision_recognition("onEmotionDetected")

    def __start_vision_recognition(self, event, callback):
        if not self.__vision_listeners:
            self.start_looking()
        self.__register_vision_listener(event, callback)

    def __stop_vision_recognition(self, event):
        self.__unregister_vision_listener(event)
        if not self.__vision_listeners:
            self.stop_looking()

    ###########################
    # Touch                   #
    ###########################

    def subscribe_touch_listener(self, touch_event, callback):
        self.__register_touch_listener(touch_event, callback)

    def unsubscribe_touch_listener(self, touch_event):
        self.__unregister_touch_listener(touch_event)

    ###########################
    # Robot actions           #
    ###########################

    def set_language(self, language_key: str, callback=None):
        if callback:
            self.__register_listener('LanguageChanged', callback)
        super(BasicSICConnector, self).set_language(language_key)

    def set_idle(self, callback=None):
        if callback:
            self.__register_listener("SetIdle", callback)
        super(BasicSICConnector, self).set_idle()

    def set_non_idle(self, callback=None):
        if callback:
            self.__register_listener("SetNonIdle", callback)
        super(BasicSICConnector, self).set_non_idle()

    def say(self, text: str, callback=None):
        if callback:
            self.__register_listener('TextDone', callback)
        super(BasicSICConnector, self).say(text)

    def say_animated(self, text: str, callback=None):
        if callback:
            self.__register_listener('TextDone', callback)
        super(BasicSICConnector, self).say_animated(text)

    def do_gesture(self, gesture: str, callback=None):
        if callback:
            self.__register_listener('GestureDone', callback)
        super(BasicSICConnector, self).do_gesture(gesture)

    def play_audio(self, audio_file: str, callback=None):
        if callback:
            self.__register_listener('PlayAudioDone', callback)
        super(BasicSICConnector, self).play_audio(audio_file)

    def set_eye_color(self, color: str, callback=None):
        if callback:
            self.__register_listener('EyeColourDone', callback)
        super(BasicSICConnector, self).set_eye_color(color)

    def turn_left(self, callback=None):
        if callback:
            self.__register_listener('TurnDone', callback)
        super(BasicSICConnector, self).turn_left()

    def turn_right(self, callback=None):
        if callback:
            self.__register_listener('TurnDone', callback)
        super(BasicSICConnector, self).turn_right()

    def wake_up(self, callback=None):
        if callback:
            self.__register_listener('WakeUpDone', callback)
        super(BasicSICConnector, self).wake_up()

    def rest(self, callback=None):
        if callback:
            self.__register_listener('RestDone', callback)
        super(BasicSICConnector, self).rest()

    def set_breathing(self, enable: bool, callback=None):
        if callback:
            if enable:
                self.__register_listener('BreathingEnabled', callback)
            else:
                self.__register_listener('BreathingDisabled', callback)
        super(BasicSICConnector, self).set_breathing(enable)

    ###########################
    # Listeners               #
    ###########################

    def subscribe_condition(self, condition: threading.Condition):
        self.__conditions.append(condition)

    def unsubscribe_condition(self, condition: threading.Condition):
        if condition in self.__conditions:
            self.__conditions.remove(condition)

    def __notify_conditions(self):
        for condition in self.__conditions:
            with condition:
                condition.notify()

    def __register_listener(self, event, callback):
        if event in self.__listeners:
            self.__listeners[event].put(callback)
        else:
            queue = Queue()
            queue.put(callback)
            self.__listeners[event] = queue

    def __register_vision_listener(self, event, callback):
        self.__vision_listeners[event] = callback

    def __unregister_vision_listener(self, event):
        del self.__vision_listeners[event]

    def __register_touch_listener(self, event, callback):
        self.__touch_listeners[event] = callback

    def __unregister_touch_listener(self, event):
        del self.__touch_listeners[event]

    def __notify_listeners(self, event, *args):
        # If there is a listener for the event
        if event in self.__listeners and not self.__listeners[event].empty():
            # only the the first one will be notified
            listener = self.__listeners[event].get()
            # notify the listener
            listener(*args)
            self.__notify_conditions()

    def __notify_vision_listeners(self, event, *args):
        if event in self.__vision_listeners:
            listener = self.__vision_listeners[event]
            listener(*args)
            self.__notify_conditions()

    def __notify_touch_listeners(self, event, *args):
        if event in self.__touch_listeners:
            listener = self.__touch_listeners[event]
            listener(*args)
            self.__notify_conditions()

    ###########################
    # Management              #
    ###########################

    def start(self):
        self.__clear_listeners()
        super(BasicSICConnector, self).start()

    def stop(self):
        self.__clear_listeners()
        super(BasicSICConnector, self).stop()

    def __clear_listeners(self):
        self.__listeners = {}
        self.__conditions = []
        self.__vision_listeners = {}
        self.__touch_listeners = {}
