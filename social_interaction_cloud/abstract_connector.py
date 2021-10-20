from enum import Enum
from io import open
from itertools import chain, product
from pathlib import Path
from threading import Event, Thread
from time import strftime, time
from tkinter import Tk, Checkbutton, Label, Entry, IntVar, StringVar, Button, E, W

from redis import Redis
from simplejson import dumps

from .detection_result_pb2 import DetectionResult


class AbstractSICConnector(object):
    """
    Abstract class that can be used as a template for a connector to connect with the Social Interaction Cloud.
    """

    def __init__(self, server_ip: str):
        """
        :param server_ip:
        """
        topics = ['events', 'detected_person', 'recognised_face', 'audio_language', 'audio_intent',
                  'audio_newfile', 'picture_newfile', 'detected_emotion',  # robot_audio_loaded?
                  'robot_posture_changed', 'robot_stiffness_changed', 'robot_battery_charge_changed',
                  'robot_charging_changed', 'robot_hot_device_detected', 'robot_motion_recording',
                  'tablet_connection', 'tablet_answer']
        device_types = {
            1: ['cam', 'Camera'],
            2: ['mic', 'Microphone'],
            3: ['robot', 'Robot'],
            4: ['speaker', 'Speaker'],
            5: ['tablet', 'Tablet']
        }
        self.device_types = Enum(
            value='DeviceType',
            names=chain.from_iterable(
                product(v, [k]) for k, v in device_types.items()
            )
        )
        topic_map = {
            self.device_types['cam']: ['action_video'],
            self.device_types['mic']: ['action_audio', 'dialogflow_language', 'dialogflow_context', 'dialogflow_key',
                                       'dialogflow_agent', 'dialogflow_record'],
            self.device_types['robot']: ['action_gesture', 'action_eyecolour', 'action_earcolour', 'action_headcolour',
                                         'action_idle', 'action_turn', 'action_turn_small', 'action_wakeup',
                                         'action_rest', 'action_set_breathing', 'action_posture', 'action_stiffness',
                                         'action_play_motion', 'action_record_motion'],
            self.device_types['speaker']: ['audio_language', 'action_say', 'action_say_animated', 'action_play_audio',
                                           'action_stop_talking', 'action_load_audio', 'action_clear_loaded_audio'],
            self.device_types['tablet']: ['tablet_control', 'tablet_audio', 'tablet_image', 'tablet_video',
                                          'tablet_web', 'render_html']
        }
        self.__topic_map = {}
        for k, v in topic_map.items():
            for x in v:
                self.__topic_map[x] = k
        self.devices = {}
        for device_type in self.device_types:
            self.devices[device_type] = []

        self.time_format = '%H-%M-%S'

        if server_ip.startswith('127.') or server_ip.startswith('192.') or server_ip == 'localhost':
            self.username = 'default'
            self.password = 'changemeplease'
            self.redis = Redis(host=server_ip, username=self.username, password=self.password, ssl=True,
                               ssl_ca_certs='cert.pem')
        else:
            self.__dialog1 = Tk()
            self.username = StringVar()
            self.password = StringVar()
            self.provide_user_information()
            self.redis = Redis(host=server_ip, username=self.username, password=self.password, ssl=True)
        self.__dialog2 = Tk()
        self.__checkboxes = {}
        self.select_devices()
        all_topics = []
        for device_list in self.devices.values():
            for device in device_list:
                for topic in topics:
                    all_topics.append(device + '_' + topic)
        self.__pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.__pubsub.subscribe(**dict.fromkeys(all_topics, self.__listen))
        self.__pubsub_thread = self.__pubsub.run_in_thread(sleep_time=0.001)

        self.__running_thread = Thread(target=self.__run)
        self.__stop_event = Event()

        self.__running = False

    def provide_user_information(self) -> None:
        Label(self.__dialog1, text='Username:').grid(row=1, column=1, sticky=E)
        Entry(self.__dialog1, width=15, textvariable=self.username).grid(row=1, column=2, sticky=W)
        Label(self.__dialog1, text='Password:').grid(row=2, column=1, sticky=E)
        Entry(self.__dialog1, width=15, show='*', textvariable=self.password).grid(row=2, column=2, sticky=W)
        Button(self.__dialog1, text='OK', command=self.__provide_user_information_done).grid(row=3, column=1,
                                                                                             columnspan=2)
        self.__dialog1.bind('<Return>', (lambda event: self.__provide_user_information_done()))
        self.__dialog1.mainloop()

    def __provide_user_information_done(self):
        self.__dialog1.destroy()
        self.username = self.username.get()
        self.password = self.password.get()

    def select_devices(self) -> None:
        devices = self.redis.zrevrangebyscore(name='user:' + self.username, min=(time() - 60), max='+inf')
        devices.sort()
        row = 1
        for device in devices:
            var = IntVar()
            self.__checkboxes[device] = var
            Checkbutton(self.__dialog2, text=device, variable=var).grid(row=row, column=1, sticky=W)
            Label(self.__dialog2, text='').grid(row=row, column=2, sticky=E)
            row += 1
        Button(self.__dialog2, text='(De)Select All', command=self.__select_devices_toggle).grid(row=row, column=1,
                                                                                                 sticky=W)
        Button(self.__dialog2, text='OK', command=self.__select_devices_done).grid(row=row, column=2, sticky=E)
        self.__dialog2.mainloop()

    def __select_devices_toggle(self):
        none_selected = True
        for var in self.__checkboxes.values():
            if var.get() == 1:
                none_selected = False
                break
        for var in self.__checkboxes.values():
            var.set(1 if none_selected else 0)

    def __select_devices_done(self):
        self.__dialog2.destroy()
        for name, var in self.__checkboxes.items():
            if var.get() == 1:
                split = name.decode('utf-8').split(':')
                device_type = self.device_types[split[1]]
                self.devices[device_type].append(self.username + '-' + split[0])

    ###########################
    # Event handlers          #
    ###########################

    def on_event(self, event: str) -> None:
        """Triggered upon any event This can be either an event related to some action called here,
        or an event related to one of the robot's touch sensors, i.e. one of:
        RightBumperPressed, RightBumperReleased, LeftBumperPressed, LeftBumperReleased, BackBumperPressed,
        BackBumperReleased, FrontTactilTouched, FrontTactilReleased, MiddleTactilTouched, MiddleTactilReleased,
        RearTactilTouched, RearTactilReleased, HandRightBackTouched, HandRightBackReleased, HandRightLeftTouched,
        HandRightLeftReleased, HandRightRightTouched, HandRightRightReleased, HandLeftBackTouched, HandLeftBackReleased,
        HandLeftLeftTouched, HandLeftLeftReleased, HandLeftRightTouched, or HandLeftRightReleased
        See: http://doc.aldebaran.com/2-8/family/nao_technical/contact-sensors_naov6.html"""
        pass

    def on_posture_changed(self, posture: str) -> None:
        """
        Trigger when the posture has changed.
        :param posture: new posture.
        :return:
        """
        pass

    def on_person_detected(self) -> None:
        """Triggered when some person was detected in front of the robot (after a startWatching action was called).
        Only sent when the people detection service is running. Will be sent as long as a person is detected."""
        pass

    def on_face_recognized(self, identifier: str) -> None:
        """Triggered when a specific face was detected in front of the robot (after a startWatching action was called).
        Only sent when the face recognition service is running. Will be sent as long as the face is recognised.
        The identifiers of recognised faces are stored in a file, and will thus persist over a restart of the agent."""
        pass

    def on_audio_language(self, language_key: str) -> None:
        """Triggered whenever a language change was requested (for example by the user).
        Given is the full language key (e.g. nl-NL or en-US)."""
        pass

    def on_audio_intent(self, detection_result: DetectionResult) -> None:
        """Triggered whenever an intent was detected (by Dialogflow) on a user's speech.
        Given is the name of the intent, a list of optional parameters (following from the dialogflow spec), and a confidence value.
        See https://cloud.google.com/dialogflow/docs/intents-loaded_actions-parameters.
        The recognized text itself is provided as well, even when no intent was actually matched (i.e. a failure).
        These are sent as soon as an intent is recognised, which is always after some start_listening action,
        but might come in some time after the final stop_listening action (if there was some intent detected at least).
        Intents will keep being recognised until stop_listening is called. In that case, this function can still be triggered,
        containing the recognized text but no intent (and a confidence value of 0)."""
        pass

    def on_new_audio_file(self, audio_file: str) -> None:
        """Triggered whenever a new recording has been stored to an audio (WAV) file. See set_record_audio.
        Given is the name to the recorded file (which is in the folder required by the play_audio function).
        All audio received between the last start_listening and stop_listening calls is recorded."""
        pass

    def on_new_picture_file(self, picture_file: str) -> None:
        """Triggered whenever a new picture has been stored to an image (JPG) file. See take_picture.
        Given is the path to the taken picture."""
        pass

    def on_emotion_detected(self, emotion: str) -> None:
        """Triggered whenever an emotion has been detected by the emotion detection service (when running)."""
        pass

    def on_is_awake(self, is_awake: bool) -> None:
        """
        Triggered when the robot transfers from an awake state to a sleep state or vice verse
        :param is_awake: True if awake or false when is asleep
        :return:
        """
        pass

    def on_stiffness_changed(self, stiffness: int) -> None:
        """
        Triggered when the average stiffness of the robot changes. See:
        http://doc.aldebaran.com/2-8/naoqi/sensors/alsensors-api.html#BodyStiffnessChanged
        :param stiffness:   0 means that average of stiffness is less than 0.05
                        1 means that average of stiffness is betwwen 0.05 and 0.95
                        2 means that average of stiffness is greater 0.95
        :return:
        """
        pass

    def on_battery_charge_changed(self, percentage: int) -> None:
        """
        Triggered when the battery level changes.
        :param percentage: battery level (0-100)
        :return:
        """
        pass

    def on_charging_changed(self, is_charging: bool) -> None:
        """
        Triggered when the robot is connected (True) or disconnected (False) from a power source.
        Warning: is not always accurate, see:
        http://doc.aldebaran.com/2-8/naoqi/sensors/albattery-api.html#BatteryPowerPluggedChanged
        :param is_charging:
        :return:
        """
        pass

    def on_hot_device_detected(self, hot_devices: list) -> None:
        """
        Triggered when one or more body parts of the robot become too hot.
        :param hot_devices: list of body parts that are too hot.
        :return:
        """
        pass

    def on_robot_motion_recording(self, motion: bytes) -> None:
        """
        Triggered when a motion recording becomes available.

        :param motion:
        :return:
        """
        pass

    def on_tablet_connection(self) -> None:
        """
        Triggered when the connection with a tablet display has been established.
        :return:
        """
        pass

    def on_tablet_answer(self, answer: str) -> None:
        """
        Triggered when a button has been pressed on the tablet display.

        :param answer:
        :return:
        """
        pass

    ###########################
    # Dialogflow Actions      #
    ###########################

    def set_dialogflow_key(self, key_file: str) -> None:
        """Required for setting up Dialogflow: the path to the (JSON) keyfile."""
        contents = Path(key_file).read_text()
        self.__send('dialogflow_key', contents)

    def set_dialogflow_agent(self, agent_name: str) -> None:
        """Required for setting up Dialogflow: the name of the agent to use (i.e. the project id)."""
        self.__send('dialogflow_agent', agent_name)

    def set_dialogflow_language(self, language_key: str) -> None:
        """Required for setting up Dialogflow: the full key of the language to use (e.g. nl-NL or en-US)."""
        self.__send('dialogflow_language', language_key)

    def set_dialogflow_context(self, context: str) -> None:
        """Indicate the Dialogflow context to use for the next speech-to-text (or to intent)."""
        self.__send('dialogflow_context', context)

    def start_listening(self, seconds: int) -> None:
        """Tell the robot (and Dialogflow) to start listening to audio (and potentially recording it).
        Intents will be continuously recognised. If seconds>0, it will automatically stop listening."""
        self.__send('action_audio', str(seconds))

    def stop_listening(self) -> None:
        """Tell the robot (and Dialogflow) to stop listening to audio.
        Note that a potentially recognized intent might come in up to a second after this call."""
        self.__send('action_audio', '-1')

    ###########################
    # Robot Actions           #
    ###########################

    def set_language(self, language_key: str) -> None:
        """For changing the robot's speaking language: the full key of the language to use
        (e.g. nl-NL or en-US). A LanguageChanged event will be sent when the change has propagated."""
        self.__send('audio_language', language_key)

    def set_record_audio(self, should_record: bool) -> None:
        """Indicate if audio should be recorded (see onNewAudioFile)."""
        self.__send('dialogflow_record', '1' if should_record else '0')

    def set_idle(self) -> None:
        """Put the robot into 'idle mode': always looking straight ahead.
        A SetIdle event will be sent when the robot has transitioned into the idle mode."""
        self.__send('action_idle', 'true')

    def set_non_idle(self) -> None:
        """Put the robot back into its default 'autonomous mode' (looking towards sounds).
        A SetNonIdle event will be sent when the robot has transitioned out of the idle mode."""
        self.__send('action_idle', 'false')

    def start_looking(self, seconds: int) -> None:
        """Tell the robot (and any recognition module) to start the camera feed.
        If seconds>0, it will automatically stop looking."""
        self.__send('action_video', str(seconds))

    def stop_looking(self) -> None:
        """Tell the robot (and any recognition module) to stop looking."""
        self.__send('action_video', '-1')

    def say(self, text: str) -> None:
        """A string that the robot should say (in the currently selected language!).
        A TextStarted event will be sent when the speaking starts and a TextDone event after it is finished."""
        self.__send('action_say', text)

    def say_animated(self, text: str) -> None:
        """A string that the robot should say (in the currently selected language!) in an animated fashion.
        This means that the robot will automatically try to add (small) animations to the text.
        Moreover, in this function, special tags are supported, see:
        http://doc.aldebaran.com/2-8/naoqi/audio/altexttospeech-tuto.html#using-tags-for-voice-tuning
        A TextStarted event will be sent when the speaking starts and a TextDone event after it is finished."""
        self.__send('action_say_animated', text)

    def do_gesture(self, gesture: str) -> None:
        """Make the robot perform the given gesture. The list of available gestures (not tags!) is available on:
        http://doc.aldebaran.com/2-8/naoqi/motion/alanimationplayer-advanced.html (Nao)
        http://doc.aldebaran.com/2-5/naoqi/motion/alanimationplayer-advanced.html (Pepper)
        You can also install custom animations with Choregraphe.
        A GestureStarted event will be sent when the gesture starts and a GestureDone event when it is finished."""
        self.__send('action_gesture', gesture)

    def play_audio(self, audio_file: str) -> None:
        """Plays the given audio file on the robot's speakers.
        A PlayAudioStarted event will be sent when the audio starts and a PlayAudioDone event after it is finished.
        Any previously playing audio will be cancelled first."""
        with open(audio_file, 'rb') as file:
            self.__send('action_play_audio', file.read())

    def set_eye_color(self, color: str) -> None:
        """Sets the robot's eye LEDs to one of the following colours:
        white, red, green, blue, yellow, magenta, cyan, greenyellow or rainbow.
        An EyeColourStarted event will be sent when the change starts and a EyeColourDone event after it is done."""
        self.__send('action_eyecolour', color)

    def set_ear_color(self, color: str) -> None:
        """Sets the robot's ear LEDs to one of the following colours:
        white, red, green, blue, yellow, magenta, cyan, greenyellow or rainbow.
        An EarColourStarted event will be sent when the change starts and a EarColourDone event after it is done."""
        self.__send('action_earcolour', color)

    def set_head_color(self, color: str) -> None:
        """Sets the robot's head LEDs to one of the following colours:
        white, red, green, blue, yellow, magenta, cyan, greenyellow or rainbow.
        A HeadColourStarted event will be sent when the change starts and a HeadColourDone event after it is done."""
        self.__send('action_headcolour', color)

    def take_picture(self) -> None:
        """Instructs the robot to take a picture. See the onNewPictureFile function."""
        self.__send('action_take_picture', '')

    def turn_left(self, small: bool = False) -> None:
        """Instructs the Pepper robot to make a (small) left-hand turn."""
        self.__send('action_turn' + ('_small' if small else ''), 'left')

    def turn_right(self, small: bool = False) -> None:
        """Instructs the Pepper robot to make a (small) right-hand turn."""
        self.__send('action_turn' + ('_small' if small else ''), 'right')

    def wake_up(self) -> None:
        """Instructs the robot to execute the default wake_up behavior.
        See: http://doc.aldebaran.com/2-8/naoqi/motion/control-stiffness-api.html?highlight=wakeup#ALMotionProxy::wakeUp"""
        self.__send('action_wakeup', '')

    def rest(self) -> None:
        """Instructs the robot to execute the default wake_up behavior.
        See: http://doc.aldebaran.com/2-8/naoqi/motion/control-stiffness-api.html?highlight=wakeup#ALMotionProxy::rest"""
        self.__send('action_rest', '')

    def set_breathing(self, enable: bool) -> None:
        """
        Enable/disable the default breathing animation of the robot.
        See: http://doc.aldebaran.com/2-8/naoqi/motion/idle-api.html?highlight=breathing#ALMotionProxy::setBreathEnabled__ssCR.bCR
        """
        self.__send('action_set_breathing', 'Body;' + '1' if enable else '0')

    def go_to_posture(self, posture: str, speed: int = 100) -> None:
        """
        Let the robot go to a predefined posture.

        Predefined postures for Pepper are: Stand or StandInit, StandZero, and Crouch.
        See: http://doc.aldebaran.com/2-5/family/pepper_technical/postures_pep.html#pepper-postures

        Predefined postures for Nao are: Stand, StandInit, StandZero, Crouch, Sit, SitRelax, LyingBelly, and LyingBack.
        See: http://doc.aldebaran.com/2-8/family/nao_technical/postures_naov6.html#naov6-postures

        :param posture: target posture
        :param speed: optional speed parameter to set the speed of the posture change. Default is 1.0 (100% speed).
        :return:
        """
        self.__send('action_posture', posture + ';' + str(speed) if 1 <= speed <= 100 else posture + ';100')

    def set_stiffness(self, chains: list, stiffness: int, duration: int = 1000) -> None:
        """
        Set the stiffness for one or more joint chains.
        Suitable joint chains for Nao are: Head, RArm, LArm, RLeg, LLeg
        Suitable joint chains for Pepper are: Head, RArm, LArm, Leg, Wheels

        :param chains: list of joints.
        :param stiffness: stiffness value between 0 and 100.
        :param duration: stiffness transition time in milliseconds.
        :return:
        """
        self.__send('action_stiffness', dumps(chains) + ';' + str(stiffness) + ';' + str(duration))

    def play_motion(self, motion: bytes) -> None:
        """
        Play a motion.
        Suitable joints and angles for Nao:
        https://developer.softbankrobotics.com/nao6/nao-documentation/nao-developer-guide/kinematics-data/joints
        Suitable joints and angles for Pepper:
        https://developer.softbankrobotics.com/pepper-naoqi-25/pepper-documentation/pepper-developer-guide/kinematics-data/joints

        :param motion: zlib compressed json with the following format
        {'robot': 'nao/pepper', 'compress_factor_angles': int,
        'compress_factor_times: int 'motion': {'joint1': { 'angles': [...], 'times': [...]}, 'joint2': {...}}}
        :return:
        """
        self.__send('action_play_motion', motion)

    def start_record_motion(self, joint_chains: list, framerate: int = 5) -> None:
        """
        Start recording of the angles over time of a given list of joints and or joint chains with an optional framerate.

        Suitable joints and joint chains for nao:
        http://doc.aldebaran.com/2-8/family/nao_technical/bodyparts_naov6.html#nao-chains

        Suitable joints and joint chains for pepper:
        http://doc.aldebaran.com/2-8/family/pepper_technical/bodyparts_pep.html

        :param joint_chains: a list with one or more joints or joint chains
        :param framerate: optional number of recordings per second. Default is 5.0 fps.
        :return:
        """
        self.__send('action_record_motion', 'start;' + dumps(joint_chains) + ';' + str(framerate))

    def stop_record_motion(self) -> None:
        """
        Stop recording of an active motion recording (started by start_record_motion())

        :return:
        """
        self.__send('action_record_motion', 'stop')

    ###########################
    # Tablet Actions          #
    ###########################

    def tablet_open(self) -> None:
        """
        Establish a connection with a tablet display (see on_tablet_connection).

        :return:
        """
        self.__send('tablet_control', 'show')

    def tablet_close(self) -> None:
        """
        Disconnect from the currently connected tablet display.

        :return:
        """
        self.__send('tablet_control', 'hide')

    def tablet_show(self, html: str) -> None:
        """
        Show the given HTML body on the currently connected tablet display.
        :param html: the HTML contents (put inside a <body>).
        By default, the Bootstrap rendering library is loaded: https://getbootstrap.com/docs/4.4/
        Moreover, various classes can be used (on e.g. divs) to automatically create dynamic elements:
        - listening_icon: shows a microphone that is enabled or disabled when the robot is listening or not.
        - speech_text: shows a live-stream of the currently recognized text (by e.g. dialogflow).
        - vu_logo: renders a VU logo.
        - english_flag: renders a English flag (changes the audio language when tapped on).
        - chatbox: allows text input (to e.g. dialogflow).
        Finally, each button element will automatically trigger an event when clicked (see on_tablet_answer).
        :return:
        """
        self.__send('render_html', html)

    def tablet_show_image(self, url: str) -> None:
        """
        Show the image at the given URL on the currently connected tablet display.
        :param url: the image link
        :return:
        """
        self.__send('tablet_image', url)

    def tablet_show_video(self, url: str) -> None:
        """
        Show the video at the given URL on the currently connected tablet display.
        :param url: the video link
        :return:
        """
        self.__send('tablet_video', url)

    def tablet_show_webpage(self, url: str) -> None:
        """
        Show the page at the given URL on the currently connected tablet display.
        :param url: the webpage link
        :return:
        """
        self.__send('tablet_web', url)

    ###########################
    # Management              #
    ###########################

    def enable_service(self, name: str) -> None:
        """
        Enable the given service (for the previously selected devices)
        :param name: people_detection, face_recognition, emotion_detection or intent_detection
        :return:
        """
        pipe = self.redis.pipeline()
        if name == 'people_detection' or name == 'face_recognition' or name == 'emotion_detection':
            for cam in self.devices[self.device_types['cam']]:
                pipe.publish(name, cam)
        elif name == 'intent_detection':
            for mic in self.devices[self.device_types['mic']]:
                pipe.publish(name, mic)
        else:
            print('Unknown service: ' + name)
        pipe.execute()

    def start(self) -> None:
        """Start the application"""
        self.__running = True
        self.__running_thread.start()

    def stop(self) -> None:
        """Stop listening to incoming events (which is done in a thread) so the Python application can close."""
        self.__running = False
        self.__stop_event.set()
        print('Trying to exit gracefully...')
        try:
            self.__pubsub_thread.stop()
            self.redis.close()
            print('Graceful exit was successful.')
        except Exception as err:
            print('Graceful exit has failed: ' + err.message)

    def __run(self) -> None:
        while self.__running:
            self.__stop_event.wait()

    def __listen(self, message) -> None:
        raw_channel = message['channel'].decode('utf-8')
        split = raw_channel.index('_') + 1
        channel = raw_channel[split:]
        data = message['data']

        if channel == 'events':
            self.on_event(event=data.decode('utf-8'))
        elif channel == 'detected_person':
            self.on_person_detected()
        elif channel == 'recognised_face':
            self.on_face_recognized(identifier=data.decode('utf-8'))
        elif channel == 'audio_language':
            self.on_audio_language(language_key=data.decode('utf-8'))
        elif channel == 'audio_intent':
            detection_result = DetectionResult()
            detection_result.ParseFromString(data)
            self.on_audio_intent(detection_result=detection_result)
        elif channel == 'audio_newfile':
            audio_file = strftime(self.time_format) + '.wav'
            with open(audio_file, 'wb') as wav:
                wav.write(data)
            self.on_new_audio_file(audio_file=audio_file)
        elif channel == 'picture_newfile':
            picture_file = strftime(self.time_format) + '.jpg'
            with open(picture_file, 'wb') as jpg:
                jpg.write(data)
            self.on_new_picture_file(picture_file=picture_file)
        elif channel == 'detected_emotion':
            self.on_emotion_detected(emotion=data.decode('utf-8'))
        elif channel == 'robot_posture_changed':
            self.on_posture_changed(posture=data.decode('utf-8'))
        elif channel == 'robot_stiffness_changed':
            self.on_stiffness_changed(stiffness=int(data.decode('utf-8')))
        elif channel == 'robot_battery_charge_changed':
            self.on_battery_charge_changed(percentage=int(data.decode('utf-8')))
        elif channel == 'robot_charging_changed':
            self.on_charging_changed(is_charging=bool(int(data.decode('utf-8'))))
        elif channel == 'robot_hot_device_detected':
            self.on_hot_device_detected(data.decode('utf-8').split(';'))
        elif channel == 'robot_motion_recording':
            self.on_robot_motion_recording(data)
        elif channel == 'tablet_connection':
            self.on_tablet_connection()
        elif channel == 'tablet_answer':
            self.on_tablet_answer(data.decode('utf-8'))
        else:
            print('Unknown channel: ' + channel)

    def __send(self, channel: str, data) -> None:
        pipe = self.redis.pipeline()
        target_type = self.__topic_map[channel]
        for device in self.devices[target_type]:
            pipe.publish(device + '_' + channel, data)
        pipe.execute()
