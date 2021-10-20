import threading
from pathlib import Path
import redis


class IllegalActionForRobot(Exception):
    """Exception raised when an action cannot be executed by the selected type of robot"""
    pass


class AbstractSICConnector(object):

    def __init__(self, server_ip, robot):
        if not robot == 'nao' and not robot == 'pepper':
            raise ValueError('Robot can only have the value of "nao" or "pepper"')
        else:
            self.robot = robot

        self.__topics = ['events_robot', 'detected_person', 'recognised_face', 'audio_language', 'audio_intent',
                         'audio_newfile', 'text_speech', 'picture_newfile', 'detected_emotion']

        self.__redis = redis.Redis(host=server_ip, ssl=True, ssl_ca_certs='cert.pem')
        self.__pubsub = self.__redis.pubsub(ignore_subscribe_messages=True)
        self.__pubsub.subscribe(**dict.fromkeys(self.__topics, self.__listen))
        self.__pubsub_thread = self.__pubsub.run_in_thread(sleep_time=0.001)

        self.__running_thread = threading.Thread(target=self.__run)
        self.__stop_event = threading.Event()

        self.__running = False

    ###########################
    # Event handlers          #
    ###########################

    def on_robot_event(self, event):
        """Triggered upon an event from the robot. This can be either an event related to some action called here,
        i.e. one of: GestureStarted, GestureDone, PlayAudioStarted, PlayAudioDone, TextStarted, TextDone,
        EyeColourStarted, EyeColourDone, SetIdle, SetNonIdle, WakeUpDone, RestDone, BreathingEnabled, BreathingDisabled
         or LanguageChanged;
        or an event related to one of the robot's touch sensors, i.e. one of:
        RightBumperPressed, RightBumperReleased, LeftBumperPressed, LeftBumperReleased, BackBumperPressed,
        BackBumperReleased, FrontTactilTouched, FrontTactilReleased, MiddleTactilTouched, MiddleTactilReleased,
        RearTactilTouched, RearTactilReleased, HandRightBackTouched, HandRightBackReleased, HandRightLeftTouched,
        HandRightLeftReleased, HandRightRightTouched, HandRightRightReleased, HandLeftBackTouched, HandLeftBackReleased,
        HandLeftLeftTouched, HandLeftLeftReleased, HandLeftRightTouched, or HandLeftRightReleased
        See: http://doc.aldebaran.com/2-8/family/nao_technical/contact-sensors_naov6.html"""
        pass

    def on_person_detected(self):
        """Triggered when some person was detected in front of the robot (after a startWatching action was called).
        Only sent when the people detection service is running. Will be sent as long as a person is detected."""
        pass

    def on_face_recognized(self, identifier):
        """Triggered when a specific face was detected in front of the robot (after a startWatching action was called).
        Only sent when the face recognition service is running. Will be sent as long as the face is recognised.
        The identifiers of recognised faces are stored in a file, and will thus persist over a restart of the agent."""
        pass

    def on_audio_language(self, language_key):
        """Triggered whenever a language change was requested (for example by the user).
        Given is the full language key (e.g. nl-NL or en-US)."""
        pass

    def on_audio_intent(self, *args, intent_name):
        """Triggered whenever an intent was detected (by Dialogflow) on a user's speech.
        Given is the name of intent and a list of optional parameters (following from the dialogflow spec).
        See https://cloud.google.com/dialogflow/docs/intents-loaded_actions-parameters.
        These be sent as soon as an intent is recognised, which is always after some start_listening action,
        but might come in some time after the final stop_listening action (if there was some intent detected at least).
        Intents will keep being recognised until stop_listening is called."""
        pass

    def on_new_audio_file(self, audio_file):
        """Triggered whenever a new recording has been stored to an audio (WAV) file. See set_record_audio.
        Given is the name to the recorded file (which is in the folder required by the play_audio function).
        All audio received between the last start_listening and stop_listening calls is recorded."""
        pass

    def on_speech_text(self, text):
        """Triggered whenever text has been recognized (by Dialogflow) from a user's speech.
        Given is the recognized text(string). Also sent if no intent was recognised from the text."""
        pass

    def on_new_picture_file(self, picture_file):
        """Triggered whenever a new picture has been stored to an image (JPG) file. See take_picture.
        Given is the path to the taken picture."""
        pass

    def on_emotion_detected(self, emotion):
        """Triggered whenever an emotion has been detected by the emotion detection service (when running)."""
        pass

    ###########################
    # Dialogflow Actions      #
    ###########################

    def set_dialogflow_key(self, key_file: str):
        """Required for setting up Dialogflow: the path to the (JSON) keyfile."""
        contents = Path(key_file).read_text()
        self.__send('dialogflow_key', contents)

    def set_dialogflow_agent(self, agent_name:str):
        """Required for setting up Dialogflow: the name of the agent to use (i.e. the project id)."""
        self.__send('dialogflow_agent', agent_name)

    def set_audio_context(self, context: str):
        """Indicate the Dialogflow context to use for the next speech-to-text (or to intent)."""
        self.__send('audio_context', context)

    def set_audio_hints(self, *args):
        """Pass hints to Dialogflow about the words that it should recognize especially."""
        self.__send('audio_hints', '|'.join(args))

    def start_listening(self):
        """Tell the robot (and Dialogflow) to start listening to audio (and potentially recording it).
        Intents will be continuously recognised. At some point stop_listening needs to be called!"""
        self.__send('action_audio', 'start listening')

    def stop_listening(self):
        """Tell the robot (and Dialogflow) to stop listening to audio.
        Note that a potentially recognized intent might come in up to a second after this call."""
        self.__send('action_audio', 'stop listening')

    ###########################
    # Robot Actions           #
    ###########################

    def set_language(self, language_key: str):
        """Required for setting up Dialogflow (and the robot itself): the full key of the language to use
        (e.g. nl-NL or en-US). A LanguageChanged event will be sent when the change has propagated."""
        self.__send('audio_language', language_key)

    def set_record_audio(self, should_record: bool):
        """Indicate if audio should be recorded (see onNewAudioFile)."""
        self.__send('dialogflow_record', '1' if should_record else '0')

    def set_idle(self):
        """Put the robot into 'idle mode': always looking straight ahead.
        A SetIdle event will be sent when the robot has transitioned into the idle mode."""
        if not self.robot == 'pepper':
            raise IllegalActionForRobot()
        self.__send('action_idle', 'true')

    def set_non_idle(self):
        """Put the robot back into its default 'autonomous mode' (looking towards sounds).
        A SetNonIdle event will be sent when the robot has transitioned out of the idle mode."""
        if not self.robot == 'pepper':
            raise IllegalActionForRobot()
        self.__send('action_idle', 'false')

    def start_looking(self):
        """Tell the robot (and any recognition module) to start the camera feed).
        At some point stop_looking needs to be called!"""
        self.__send('action_video', 'start watching')

    def stop_looking(self):
        """Tell the robot (and Dialogflow) to stop listening to audio.
        Note that a potentially recognized intent might come in a bit later than this call."""
        self.__send('action_video', 'stop watching')

    def say(self, text: str):
        """A string that the robot should say (in the currently selected language!).
        A TextStarted event will be sent when the speaking starts and a TextDone event after it is finished."""
        self.__send('action_say', text)

    def say_animated(self, text: str):
        """A string that the robot should say (in the currently selected language!) in an animated fashion.
        This means that the robot will automatically try to add (small) animations to the text.
        Moreover, in this function, special tags are supported, see:
        http://doc.aldebaran.com/2-8/naoqi/audio/altexttospeech-tuto.html#using-tags-for-voice-tuning
        A TextStarted event will be sent when the speaking starts and a TextDone event after it is finished."""
        self.__send('action_say_animated', text)

    def do_gesture(self, gesture: str):
        """Make the robot perform the given gesture. The list of available gestures is available on:
        http://doc.aldebaran.com/2-8/naoqi/motion/alanimationplayer-advanced.html
        You can also install custom animations with Choregraphe.
        A GestureStarted event will be sent when the gesture starts and a GestureDone event when it is finished."""
        self.__send('action_gesture', gesture)

    def play_audio(self, audio_file: str):
        """Plays the audio file (in the webserver's html/audio directory) on the robot's speakers.
        A PlayAudioStarted event will be sent when the audio starts and a PlayAudioDone event after it is finished.
        Any previously playing audio will be cancelled first;
        calling play_audio with an empty string thus has the effect of cancelling any previously playing audio."""
        self.__send('action_play_audio', audio_file)

    def set_eye_color(self, color: str):
        """Sets the robot's eye LEDs to one of the following colours:
        white, red, green, blue, yellow, magenta, cyan, greenyellow or rainbow.
        An EyeColourStarted event will be sent when the change starts and a EyeColourDone event after it is done."""
        self.__send('action_eyecolour', color)

    def take_picture(self):
        """Instructs the robot to take a picture. See the onNewPictureFile function."""
        self.__send('action_take_picture', '')

    def turn_left(self):
        """Instructs the Pepper robot to make a left-hand turn."""
        if not self.robot == 'pepper':
            raise IllegalActionForRobot()
        self.__send('action_turn', 'left')

    def turn_right(self):
        """Instructs the Pepper robot to make a right-hand turn."""
        if not self.robot == 'pepper':
            raise IllegalActionForRobot()
        self.__send('action_turn', 'right')

    def wake_up(self):
        """Instructs the Nao robot to execute the default wake_up behavior.
        See: http://doc.aldebaran.com/2-8/naoqi/motion/control-stiffness-api.html?highlight=wakeup#ALMotionProxy::wakeUp"""
        if not self.robot == 'nao':
            raise IllegalActionForRobot()
        self.__send('action_wakeup', '')

    def rest(self):
        """Instructs the Nao robot to execute the default wake_up behavior.
        See: http://doc.aldebaran.com/2-8/naoqi/motion/control-stiffness-api.html?highlight=wakeup#ALMotionProxy::rest"""
        if not self.robot == 'nao':
            raise IllegalActionForRobot()
        self.__send('action_rest', '')

    def set_breathing(self, enable: bool):
        """
        Enable / disable default breathing animation of whole body.
        See: http://doc.aldebaran.com/2-8/naoqi/motion/idle-api.html?highlight=breathing#ALMotionProxy::setBreathEnabled__ssCR.bCR
        """
        if not self.robot == 'nao':
            raise IllegalActionForRobot()
        self.__send('action_set_breathing', 'Body;' + '1' if enable else '0')

    ###########################
    # Management              #
    ###########################

    def start(self):
        """Start the application"""
        self.__running = True
        self.__running_thread.start()

    def stop(self):
        """Stop listening to incoming events (which is done in a thread) so the Python application can close."""
        if self.__running:
            self.__running = False
            self.__stop_event.set()
            print('Trying to exit gracefully...')
            try:
                self.__running_thread.join()
                self.__pubsub_thread.stop()
                self.__redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + str(err))

    def __run(self):
        while self.__running:
            self.__stop_event.wait()

    def __listen(self, message):
        channel = message['channel'].decode()
        data = message['data'].decode()
        if channel == self.__topics[0]:
            self.on_robot_event(event=data)
        elif channel == self.__topics[1]:
            self.on_person_detected()
        elif channel == self.__topics[2]:
            self.on_face_recognized(identifier=data)
        elif channel == self.__topics[3]:
            self.on_audio_language(language_key=data)
        elif channel == self.__topics[4]:
            data = data.split('|')
            self.on_audio_intent(intent_name=data[0], *data[1:])
        elif channel == self.__topics[5]:
            self.on_new_audio_file(audio_file=data)
        elif channel == self.__topics[6]:
            self.on_speech_text(text=data)
        elif channel == self.__topics[7]:
            self.on_new_picture_file(picture_file=data)

    def __send(self, channel, data):
        self.__redis.publish(channel, data)

