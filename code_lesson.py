from social_interaction_cloud.action import ActionRunner, Action, ActionFactory
from social_interaction_cloud.basic_connector import BasicSICConnector
from social_interaction_cloud.detection_result_pb2 import DetectionResult
from code_exercise import Exercise
import time
from time import sleep
import logging
import randomized_responses
from explain_exercise import explain_exercise

#Classes used for touch listeners:
class Feet_Chosen:
    def __call__(self):
        print('Feet touched')
        lesson.feet_pressed = True

class Tactil_Chosen:
    def __call__(self):
        print('Tactil touched')
        lesson.head_pressed = True

class Feet_For_Step:
    def __call__(self):
        print('Feet pressed to give step')
        lesson.ready_for_step = True

class Feet_For_Answer:
    def __call__(self):
        print('Feet pressed to give answer')
        lesson.ready_for_answer = True

class Head_For_Start_Lesson:
    def __call__(self):
        print('Head pressed to start the lesson')
        lesson.waiting_for_start_lesson = False


class Lesson:

    def __init__(self, server_ip, robot, dialogflow_key_file, dialogflow_agent_id):
        self.sic = BasicSICConnector(server_ip, robot, dialogflow_key_file, dialogflow_agent_id)

        self.user_model = {}
        self.recognition_manager = {'attempt_success': False, 'attempt_number': 0}

    def run(self):
        #  self.sic.start()
        self.action_runner = ActionRunner(self.sic)
        print("doing stuff")

        self.action_runner.run_waiting_action('set_language', 'nl-NL')
        self.action_runner.run_waiting_action('wake_up')
        self.sic.do_gesture('sitting_down/behavior_1') # Todo: fix that the robot's sitting down

        self.exercise = Exercise()


### ### Change before each session: ### ###

        #change level of the student:
        self.level = 1
        #change filename:
        logging.basicConfig(filename='student_x.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

### ### End change before each session  ### ###

        duration_lesson = int(20) # 20 minutes, time in seconds

        logging.info('------------------------------ BEGIN OF SESSION ------------------------------')

        logging.info('- Level = %s' % (self.level))

        self.waiting_for_start_lesson = True
        self.previous_exercise_correct = True

        #variables needed for logging:
            #basic statistics
        self.number_of_exercises_done = 0
        self.times_finished_sum_correct = 0
        self.times_finished_sum_incorrect = 0
            #at making the first mistake in an exercise, the student gets the choice to either hear the explanation, or to try the sum again
        self.times_asked_for_explanation = 0
        self.times_tried_sum_again = 0
            #mistakes can be made when subtracting tens, or when subtracting units
        self.mistake_in_tens = 0
        self.end_in_tens = 0
        self.mistake_in_units = 0
        self.end_in_units = 0
            #mistakes can be made when doing the steps (in level 2, 3, 4), or when giving the (intermediate) answers
        self.mistake_in_step = 0
        self.end_in_step = 0
        self.mistake_in_answer = 0
        self.end_in_answer = 0
            #when the student presses the feet to give an answer, but the student either says nothing, or the robot does not recognize a number
        self.robot_did_not_hear_number = 0
            #students get a level assigned, and they can either answer on that level, under, or above the level
        self.bigger_steps_than_level_tens = 0
        self.bigger_steps_than_level_units = 0
        self.steps_on_level_tens = 0
        self.steps_on_level_units = 0
        self.smaller_steps_than_level_tens = 0
        self.smaller_steps_than_level_units = 0


        logging.info('- Play introduction')
        self.play_introduction(self.level)
        logging.info('- Done with introduction')
        
        start_time = time.time()

        while (time.time() - start_time) < duration_lesson:

            #if the previous exercise was solved by the student, they will do a more difficult exercise (over), than when the previous exercise was explained by the robot
            if self.previous_exercise_correct:
                self.over = True
            else:
                self.over = False

            logging.info('')
            logging.info('========= New exercise =========')

            #generating a new exercise
            self.exercise.generate_exercise(over=self.over)

            #variables that need to be reset before every new exercise
            self.wrong_responses = 0
            self.feet_pressed = False
            self.head_pressed = False
            self.ready_for_answer = False
            self.ready_for_step = False
            self.asked_for_help = False

            logging.info('--------- Sum: %s - %s ---------' % (self.exercise.first_number, self.exercise.second_number))
            print('De som is: ', self.exercise.first_number, 'min', self.exercise.second_number)
            self.action_runner.run_waiting_action('say', 'De som die we nu gaan doen is' + str(self.exercise.first_number) + 'min' + str(self.exercise.second_number))

            self.answer_structure(self.level)

            self.number_of_exercises_done += 1
            logging.info('- number_of_exercises_done += 1')

            if (time.time() - start_time) < (duration_lesson - 4):
                self.action_runner.run_waiting_action('say', randomized_responses.text_next_sum())

            sleep(2)

        logging.info('')

        logging.info('- Play conclusion')
        self.play_conclusion()
        logging.info('- Done with conclusion')

        logging.info('')
        logging.info('')

        #logging at the end of the session:
        logging.info('- Number of exercises done: %s' % (self.number_of_exercises_done))
        logging.info('- Times finished sum correctly: %s' % (self.times_finished_sum_correct))
        logging.info('- Times student did not finish the sum: %s' % (self.times_finished_sum_incorrect))

        logging.info('- Times asked for explanation: %s' % (self.times_asked_for_explanation))
        logging.info('- Times tried sum again: %s' % (self.times_tried_sum_again))

        logging.info('- Times student made mistake in tens: %s' % (self.mistake_in_tens))
        logging.info('- Times student stranded while doing the tens: %s' % (self.end_in_tens))
        logging.info('- Times student made mistake in units: %s' % (self.mistake_in_units))
        logging.info('- Times student stranded while doing the units: %s' % (self.end_in_units))

        logging.info('- Times student made mistake in step: %s' % (self.mistake_in_step))
        logging.info('- Times student stranded while giving a steps: %s' % (self.end_in_step))
        logging.info('- Times student made mistake in answer: %s' % (self.mistake_in_answer))
        logging.info('- Times student stranded while giving an answer: %s' % (self.end_in_answer))

        logging.info('- Times the robot did not hear the student: %s' % (self.robot_did_not_hear_number))

        logging.info('- Exercises where student took bigger steps in tens than level: %s' % (self.bigger_steps_than_level_tens))
        logging.info('- Exercises where student took bigger steps in units than level: %s' % (self.bigger_steps_than_level_units))
        logging.info('- Exercises where student took steps on level in tens: %s' % (self.steps_on_level_tens))
        logging.info('- Exercises where student took steps on level in units: %s' % (self.steps_on_level_units))
        logging.info('- Exercises where student took smaller steps in tens than level: %s' % (self.smaller_steps_than_level_tens))
        logging.info('- Exercises where student took smaller steps in units than level: %s' % (self.smaller_steps_than_level_units))

        logging.info('------------------------------ END OF SESSION ------------------------------')


        self.action_runner.run_waiting_action('rest')
        self.sic.stop()



    def answer_structure(self, level=None):

        if level == 1:
            first_step = True
            last_step = False

            self.action_runner.run_waiting_action('say', 'Als we ' + str(self.exercise.first_number) + ' min ' + str(self.exercise.second_number) + ' moeten doen, gaan we eerst de tientallen eraf halen. Dit kunnen we best in sprongen van 10 tegelijk doen!')

            while self.exercise.current_second != 0:

                previous_first = self.exercise.current_first
                previous_second = self.exercise.current_second

                tens = int(self.exercise.current_second/10)
                last_tens_step = tens == 1
                doing_tens = tens > 0

                if doing_tens:
                    self.exercise.take_step(int(10))
                    if first_step == True:
                        while not self.recognition_manager['attempt_success']:
                            self.action_runner.run_waiting_action('say', 'Wat is ' + str(self.exercise.first_number) + ' min 10?')
                            self.listen_for_answer()
                        self.reset_recognition_management()
                        first_step = False
                    else:
                        while not self.recognition_manager['attempt_success']:
                            self.listen_for_answer()
                        self.reset_recognition_management()

                elif not self.over or last_step:
                    while not self.recognition_manager['attempt_success']:
                        self.action_runner.run_waiting_action('say', ' Wat is ' + str(self.exercise.current_first) + ' min ' + str(self.exercise.current_second) + ".")
                        self.listen_for_answer()
                    self.reset_recognition_management()
                    self.exercise.take_step(self.exercise.current_second)

                else:
                    while not self.recognition_manager['attempt_success']:
                        self.action_runner.run_waiting_action('say', ' Wat is ' + str(self.exercise.current_first) + ' min ' + str(self.exercise.current_first % 10) + ".")
                        self.listen_for_answer()
                    self.reset_recognition_management()
                    self.exercise.take_step(self.exercise.current_first % 10)

                if doing_tens:

                    if self.answer != self.exercise.current_first:
                        logging.info('- wrong answer given: %s' % (self.answer))
                        self.wrong_responses += 1
                        logging.info('- wrong_responses += 1')
                        self.mistake_in_tens += 1
                        logging.info('- mistake_in_tens += 1')
                        self.mistake_in_answer += 1
                        logging.info('- mistake_in_answer += 1')

                        self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                        self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                        if self.wrong_responses != 2:
                            self.choice_after_incorrect_answer()

                            if self.asked_for_help:
                                self.end_in_tens += 1
                                logging.info('- end_in_tens += 1')
                                self.end_in_answer += 1
                                logging.info('- end_in_answer += 1')
                                self.times_finished_sum_incorrect += 1
                                logging.info('- times_finished_sum_incorrect += 1')
                                self.previous_exercise_correct = False
                                break

                            else:
                                self.action_runner.run_waiting_action('say', 'De som was ' + str(self.exercise.first_number) + ' min ' + str(self.exercise.second_number) + '. Er moet nog ' + str(previous_second) + ' af. We zijn gebleven bij ' + str(previous_first) + '.')

                                while not self.recognition_manager['attempt_success']:
                                    self.action_runner.run_waiting_action('say', ' Wat is ' + str(previous_first) + ' min 10?')
                                    self.listen_for_answer()
                                self.reset_recognition_management()

                                if self.answer != self.exercise.current_first:
                                    logging.info('- wrong answer given: %s' % (self.answer))
                                    self.wrong_responses += 1
                                    logging.info('- wrong_responses += 1')
                                    self.mistake_in_tens += 1
                                    logging.info('- mistake_in_tens += 1')
                                    self.mistake_in_answer += 1
                                    logging.info('- mistake_in_answer += 1')
                                    self.end_in_tens += 1
                                    logging.info('- end_in_tens += 1')
                                    self.end_in_answer += 1
                                    logging.info('- end_in_answer += 1')
                                    self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                                    self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                                else:
                                    self.exercise.step_accepted = False
                                    if not last_tens_step:
                                        self.action_runner.run_waiting_action('say', ' Wat is ' + str(self.exercise.current_first) + ' min 10?')

                        else:
                            self.end_in_tens += 1
                            logging.info('- end_in_tens += 1')
                            self.end_in_answer += 1
                            logging.info('- end_in_answer += 1')

                    else:
                        self.exercise.step_accepted = False
                        if not last_tens_step:
                            self.action_runner.run_waiting_action('say', ' Wat is ' + str(self.exercise.current_first) + ' min 10?')

                elif (not self.over) or last_step:

                    if self.answer != self.exercise.current_first:
                        logging.info('- wrong answer given: %s' % (self.answer))
                        self.wrong_responses += 1
                        logging.info('- wrong_responses += 1')
                        self.mistake_in_units += 1
                        logging.info('- mistake_in_units += 1')
                        self.mistake_in_answer += 1
                        logging.info('- mistake_in_answer += 1')
                        self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                        self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                        if self.wrong_responses != 2:

                            self.choice_after_incorrect_answer()

                            if self.asked_for_help:
                                print('The student has asked for help, so the exercise ends.')
                                self.end_in_units += 1
                                logging.info('- end_in_units += 1')
                                self.end_in_answer += 1
                                logging.info('- end_in_answer += 1')
                                self.times_finished_sum_incorrect += 1
                                logging.info('- times_finished_sum_incorrect += 1')
                                self.previous_exercise_correct = False

                                break

                            else:
                                self.action_runner.run_waiting_action('say', 'De som was ' + str(self.exercise.first_number) + ' min ' + str(self.exercise.second_number) + '. Er moet nog ' + str(previous_second) + ' af. We zijn gebleven bij ' + str(previous_first) + '.')

                                while not self.recognition_manager['attempt_success']:
                                    self.action_runner.run_waiting_action('say', ' Wat is ' + str(previous_first) + ' min ' + str(previous_second) + ".")
                                    self.listen_for_answer()
                                self.reset_recognition_management()

                                if self.answer != self.exercise.current_first:
                                    logging.info('- wrong answer given: %s' % (self.answer))
                                    self.wrong_responses += 1
                                    logging.info('- wrong_responses += 1')
                                    self.mistake_in_units += 1
                                    logging.info('- mistake_in_units += 1')
                                    self.end_in_units += 1
                                    logging.info('- end_in_units += 1')
                                    self.mistake_in_answer += 1
                                    logging.info('- mistake_in_answer += 1')
                                    self.end_in_answer += 1
                                    logging.info('- end_in_answer += 1')
                                    self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                                    self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                                else:
                                    self.action_runner.run_waiting_action('say', randomized_responses.response_correct_exercise())
                                    print('End of the exercise, none left to subtract, 1 mistake was made')
                                    self.times_finished_sum_correct += 1
                                    logging.info('- times_finished_sum_correct += 1')
                                    logging.info('- one mistake was made')
                                    self.previous_exercise_correct = True
                        else:
                            self.end_in_units += 1
                            logging.info('- end_in_units += 1')
                            self.end_in_answer += 1
                            logging.info('- end_in_answer += 1')


                    else:
                        self.action_runner.run_waiting_action('say', randomized_responses.response_correct_exercise())
                        print('End of the exercise, none left to subtract, no mistake was made')
                        self.times_finished_sum_correct += 1
                        logging.info('- times_finished_sum_correct += 1')
                        logging.info('- no mistake was made')
                        self.previous_exercise_correct = True

                else:
                    last_step = True

                    if self.answer != self.exercise.current_first:
                        logging.info('- wrong answer given: %s' % (self.answer))
                        self.wrong_responses += 1
                        logging.info('- wrong_responses += 1')
                        self.mistake_in_units += 1
                        logging.info('- mistake_in_units += 1')
                        self.mistake_in_answer += 1
                        logging.info('- mistake_in_answer += 1')
                        self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                        self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                        if self.wrong_responses != 2:

                            self.choice_after_incorrect_answer()

                            if self.asked_for_help:
                                print('The student has asked for help, so the exercise ends.')
                                self.end_in_units += 1
                                logging.info('- end_in_units += 1')
                                self.end_in_answer += 1
                                logging.info('- end_in_answer += 1')
                                self.times_finished_sum_incorrect += 1
                                logging.info('- times_finished_sum_incorrect += 1')
                                self.previous_exercise_correct = False
                                break

                            else:
                                self.action_runner.run_waiting_action('say', 'De som was ' + str(self.exercise.first_number) + ' min ' + str(self.exercise.second_number) + '. Er moet nog ' + str(previous_second) + ' af. We zijn gebleven bij ' + str(previous_first) + '.')

                                while not self.recognition_manager['attempt_success']:
                                    self.action_runner.run_waiting_action('say', ' Wat is ' + str(previous_first) + ' min ' + str(previous_first % 10) + ".")
                                    self.listen_for_answer()
                                self.reset_recognition_management()

                                if self.answer != self.exercise.current_first:
                                    logging.info('- wrong answer given: %s' % (self.answer))
                                    self.wrong_responses += 1
                                    logging.info('- wrong_responses += 1')
                                    self.mistake_in_units += 1
                                    logging.info('- mistake_in_units += 1')
                                    self.end_in_units += 1
                                    logging.info('- end_in_units += 1')
                                    self.mistake_in_answer += 1
                                    logging.info('- mistake_in_answer += 1')
                                    self.end_in_answer += 1
                                    logging.info('- end_in_answer += 1')
                                    self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                                    self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                                else:
                                    self.exercise.step_accepted = False

                        else:
                            self.end_in_units += 1
                            logging.info('- end_in_units += 1')
                            self.end_in_answer += 1
                            logging.info('- end_in_answer += 1')

                    else:
                        self.exercise.step_accepted = False


                if self.wrong_responses == 2:
                    self.action_runner.run_waiting_action('say', explain_exercise(self.level, first_number=self.exercise.first_number, second_number=self.exercise.second_number))
                    self.times_finished_sum_incorrect += 1
                    logging.info('- times_finshed_sum_incorrect += 1')
                    self.previous_exercise_correct = False
                    break

            logging.info('- End of the exercise, left to subtract: %s' % (self.exercise.current_second))


        if level == 2 or level == 3 or level == 4:
            bigger_steps_than_level_tens_occured = False
            steps_on_level_tens_occured = False
            smaller_steps_than_level_tens_occured = False
            bigger_steps_than_level_units_occured = False
            steps_on_level_units_occured = False
            smaller_steps_than_level_units_occured = False

            while self.exercise.current_second != 0:

                previous_first = self.exercise.current_first
                previous_second = self.exercise.current_second

                while not self.recognition_manager['attempt_success']:
                    self.action_runner.run_waiting_action('say', 'Welk getal haal je er af?')
                    self.listen_for_step()
                self.reset_recognition_management()

                step_accepted, action_level = self.exercise.take_step(self.step, level)

                if action_level == 'above tens':
                    bigger_steps_than_level_tens_occured = True
                elif action_level == 'on level tens':
                    steps_on_level_tens_occured = True
                elif action_level == 'below tens':
                    smaller_steps_than_level_tens_occured = True
                elif action_level == 'above units':
                    bigger_steps_than_level_units_occured = True
                elif action_level == 'on level units':
                    steps_on_level_units_occured = True
                elif action_level == 'below units':
                    smaller_steps_than_level_units_occured = True
                elif action_level == 'incorrect tens':
                    self.mistake_in_tens += 1
                    logging.info('- mistake_in_tens += 1')
                    if self.wrong_responses == 1:
                        self.end_in_tens += 1
                        logging.info('- end_in_tens += 1')
                elif action_level == 'incorrect units':
                    self.mistake_in_units += 1
                    logging.info('- mistake_in_units += 1')
                    if self.wrong_responses == 1:
                        self.end_in_units += 1
                        logging.info('- end_in_units += 1')

                if not step_accepted:
                    logging.info('- wrong step given: %s' % (self.step))
                    self.wrong_responses += 1
                    logging.info('- wrong_responses += 1')
                    self.mistake_in_step += 1
                    logging.info('- mistake_in_step += 1')
                    self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.step) + '.')
                    self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                    if self.wrong_responses != 2:

                        self.choice_after_incorrect_answer()

                        if self.asked_for_help:
                            print('The student has asked for help, so the exercise ends.')
                            self.end_in_step += 1
                            logging.info('- end_in_step += 1')

                            if action_level == 'incorrect tens':
                                self.end_in_tens += 1
                                logging.info('- end_in_tens += 1')
                                print('END incorrect tens')
                            elif action_level == 'incorrect units':
                                self.end_in_units += 1
                                logging.info('- end_in_units += 1')
                                print('END incorrect units')

                            self.times_finished_sum_incorrect += 1
                            logging.info('- times_finished_sum_incorrect += 1')
                            self.previous_exercise_correct = False
                            break

                        else:
                            self.action_runner.run_waiting_action('say', 'De som was ' + str(self.exercise.first_number) + ' min ' + str(self.exercise.second_number) + '. Er moet nog ' + str(self.exercise.current_second) + ' af. We zijn gebleven bij ' + str(self.exercise.current_first) + '.')

                            while not self.recognition_manager['attempt_success']: #and self.recognition_manager['attempt_number'] < 2:
                                self.action_runner.run_waiting_action('say', 'Welk getal haal je er af?')
                                self.listen_for_step()
                            self.reset_recognition_management()

                            step_accepted, action_level = self.exercise.take_step(self.step, level)

                            if action_level == 'above tens':
                                bigger_steps_than_level_tens_occured = True
                            elif action_level == 'on level tens':
                                steps_on_level_tens_occured = True
                            elif action_level == 'below tens':
                                smaller_steps_than_level_tens_occured = True
                            elif action_level == 'above units':
                                bigger_steps_than_level_units_occured = True
                            elif action_level == 'on level units':
                                steps_on_level_units_occured = True
                            elif action_level == 'below units':
                                smaller_steps_than_level_units_occured = True
                            elif action_level == 'incorrect tens':
                                self.mistake_in_tens += 1
                                logging.info('- mistake_in_tens += 1')
                                if self.wrong_responses == 1:
                                    self.end_in_tens += 1
                                    logging.info('- end_in_tens += 1')
                            elif action_level == 'incorrect units':
                                self.mistake_in_units += 1
                                logging.info('- mistake_in_units += 1')
                                if self.wrong_responses == 1:
                                    self.end_in_units += 1
                                    logging.info('- end_in_units += 1')

                            if not step_accepted:
                                logging.info('- wrong step given: %s' % (self.step))
                                self.wrong_responses += 1
                                logging.info('- wrong_responses += 1')
                                self.mistake_in_step += 1
                                logging.info('- mistake_in_step += 1')
                                self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.step) + '.')
                                self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                if self.wrong_responses == 2:
                    self.action_runner.run_waiting_action('say', explain_exercise(self.level, first_number=self.exercise.first_number, second_number=self.exercise.second_number))
                    self.end_in_step += 1
                    logging.info('- end_in_step += 1')
                    self.times_finished_sum_incorrect += 1
                    logging.info('- times_finished_sum_incorrect += 1')
                    self.previous_exercise_correct = False

                    break

                while not self.recognition_manager['attempt_success']:
                    self.action_runner.run_waiting_action('say', 'Op welk getal kom je uit?')
                    self.listen_for_answer()
                self.reset_recognition_management()

                answer_accepted, answer_type = self.exercise.acceptable_answer(self.answer)

                if answer_type == 'incorrect tens':
                    self.mistake_in_tens += 1
                    logging.info('- mistake_in_tens += 1')
                    if self.wrong_responses == 1:
                        self.end_in_tens += 1
                        logging.info('- end_in_tens += 1')
                elif answer_type == 'incorrect units':
                    self.mistake_in_units += 1
                    logging.info('- mistake_in_units += 1')
                    if self.wrong_responses == 1:
                        self.end_in_units += 1
                        logging.info('- end_in_units += 1')

                if not answer_accepted:
                    logging.info('- wrong answer given: %s' % (self.answer))
                    self.wrong_responses += 1
                    logging.info('- wrong_responses += 1')
                    self.mistake_in_answer += 1
                    logging.info('- mistake_in_answer += 1')
                    self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                    self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                    if self.wrong_responses != 2:

                        self.choice_after_incorrect_answer()

                        if self.asked_for_help:
                            print('The student has asked for help, so the exercise ends.')
                            self.end_in_answer += 1
                            logging.info('- end_in_answer += 1')

                            if answer_type == 'incorrect tens':
                                self.end_in_tens += 1
                                logging.info('- end_in_tens += 1')
                                print('END incorrect tens')
                            elif answer_type == 'incorrect units':
                                self.end_in_units += 1
                                logging.info('- end_in_units += 1')
                                print('END incorrect units')

                            self.times_finished_sum_incorrect += 1
                            logging.info('- times_finished_sum_incorrect += 1')

                            self.previous_exercise_correct = False
                            break

                        else:
                            self.action_runner.run_waiting_action('say', 'De som was ' + str(self.exercise.first_number) + ' min ' + str(self.exercise.second_number) + '. Er moet nog ' + str(previous_second) + ' af. We zijn gebleven bij ' + str(previous_first) + '.')

                            while not self.recognition_manager['attempt_success']: #and self.recognition_manager['attempt_number'] < 2:
                                self.action_runner.run_waiting_action('say', 'Op welk getal kom je uit?')
                                self.listen_for_answer()
                            self.reset_recognition_management()

                            answer_accepted, answer_type = self.exercise.acceptable_answer(self.answer)

                            if answer_type == 'incorrect tens':
                                self.mistake_in_tens += 1
                                logging.info('- mistake_in_tens += 1')
                                if self.wrong_responses == 1:
                                    self.end_in_tens += 1
                                    logging.info('- end_in_tens += 1')
                            elif answer_type == 'incorrect units':
                                self.mistake_in_units += 1
                                logging.info('- mistake_in_units += 1')
                                if self.wrong_responses == 1:
                                    self.end_in_units += 1
                                    logging.info('- end_in_units += 1')

                            if not answer_accepted:
                                logging.info('- wrong answer given: %s' % (self.answer))
                                self.wrong_responses += 1
                                logging.info('- wrong_responses += 1')
                                self.mistake_in_answer += 1
                                logging.info('- mistake_in_answer += 1')
                                self.action_runner.run_waiting_action('say', 'Volgens mij zei je ' + str(self.answer) + '.')
                                self.action_runner.run_waiting_action('say', randomized_responses.response_incorrect_answer())

                if self.wrong_responses == 2:
                    self.action_runner.run_waiting_action('say', explain_exercise(self.level, first_number=self.exercise.first_number, second_number=self.exercise.second_number))
                    self.end_in_answer += 1
                    logging.info('- end_in_answer += 1')
                    self.times_finished_sum_incorrect += 1
                    logging.info('- times_finished_sum_incorrect += 1')
                    self.previous_exercise_correct = False
                    break

            # Update logging parameters
            if bigger_steps_than_level_tens_occured:
                self.bigger_steps_than_level_tens += 1
                logging.info('- bigger_steps_than_level_tens += 1')
            if steps_on_level_tens_occured:
                self.steps_on_level_tens += 1
                logging.info('- steps_on_level_tens += 1')
            if smaller_steps_than_level_tens_occured:
                self.smaller_steps_than_level_tens += 1
                logging.info('- smaller_steps_than_level_tens += 1')
            if bigger_steps_than_level_units_occured:
                self.bigger_steps_than_level_units += 1
                logging.info('- bigger_steps_than_level_units += 1')
            if steps_on_level_units_occured:
                self.steps_on_level_units += 1
                logging.info('- steps_on_level_units += 1')
            if smaller_steps_than_level_units_occured:
                self.smaller_steps_than_level_units += 1
                logging.info('- smaller_steps_than_level_units += 1')

            if self.wrong_responses < 2 and not self.asked_for_help:
                self.action_runner.run_waiting_action('say', randomized_responses.response_correct_exercise())
                self.times_finished_sum_correct += 1
                logging.info('- times_finished_sum_correct += 1')
                self.previous_exercise_correct = True

            print('End of the exercise, left to subtract:', self.exercise.current_second)
            logging.info('- End of the exercise, left to subtract: %s' % (self.exercise.current_second))


    def listen_for_step(self):

        self.sic.subscribe_touch_listener('RightBumperPressed', Feet_For_Step())
        self.sic.subscribe_touch_listener('LeftBumperPressed', Feet_For_Step())
        self.sic.subscribe_touch_listener('BackBumperPressed', Feet_For_Step())
        self.ready_for_step = False

        while True:

            if self.ready_for_step:
                self.sic.unsubscribe_touch_listener('RightBumperPressed')
                self.sic.unsubscribe_touch_listener('LeftBumperPressed')
                self.sic.unsubscribe_touch_listener('BackBumperPressed')

                self.action_runner.run_action('set_eye_color', 'green')
                self.action_runner.run_waiting_action('speech_recognition', 'answer_sum', 3, additional_callback=self.on_intent_number)

                try:
                    self.step = int(self.user_model['number'])
                    self.action_runner.run_action('set_eye_color', 'white')

                    print(self.step)
                    logging.info('- step: %s' % (self.step))
                    return self.step

                except:
                    print('there is no number yet.')
                    sleep(1)
                    break


    def listen_for_answer(self):

        self.sic.subscribe_touch_listener('RightBumperPressed', Feet_For_Answer())
        self.sic.subscribe_touch_listener('LeftBumperPressed', Feet_For_Answer())
        self.sic.subscribe_touch_listener('BackBumperPressed', Feet_For_Answer())
        self.ready_for_answer = False

        while True:

            if self.ready_for_answer:
                self.sic.unsubscribe_touch_listener('RightBumperPressed')
                self.sic.unsubscribe_touch_listener('LeftBumperPressed')
                self.sic.unsubscribe_touch_listener('BackBumperPressed')

                self.action_runner.run_action('set_eye_color', 'green')
                self.action_runner.run_waiting_action('speech_recognition', 'answer_sum', 3, additional_callback=self.on_intent_number)

                try:
                    self.answer = int(self.user_model['number'])
                    self.action_runner.run_action('set_eye_color', 'white')

                    print(self.answer)
                    logging.info('- answer: %s' % (self.answer))
                    return self.answer

                except:
                    print('there is no number yet.')
                    sleep(1)
                    break


    def choice_after_incorrect_answer(self):
        self.action_runner.run_waiting_action('say', 'Wil je deze som nog een keer proberen, of zal ik uitleggen hoe ik hem heb opgelost? Als je het nog een keer wilt proberen mag je zachtjes op mijn hoofd drukken, en als je wilt dat ik de som voordoe kan je tegen mijn voet-en drukken.')

        self.sic.subscribe_touch_listener('RightBumperPressed', Feet_Chosen())
        self.sic.subscribe_touch_listener('LeftBumperPressed', Feet_Chosen())
        self.sic.subscribe_touch_listener('BackBumperPressed', Feet_Chosen())
        self.sic.subscribe_touch_listener('FrontTactilTouched', Tactil_Chosen())
        self.sic.subscribe_touch_listener('MiddleTactilTouched', Tactil_Chosen())
        self.sic.subscribe_touch_listener('RearTactilTouched', Tactil_Chosen())

        while True:

            if self.feet_pressed:

                self.sic.unsubscribe_touch_listener('RightBumperPressed')
                self.sic.unsubscribe_touch_listener('LeftBumperPressed')
                self.sic.unsubscribe_touch_listener('BackBumperPressed')
                self.sic.unsubscribe_touch_listener('FrontTactilTouched')
                self.sic.unsubscribe_touch_listener('MiddleTactilTouched')
                self.sic.unsubscribe_touch_listener('RearTactilTouched')

                self.times_asked_for_explanation += 1
                logging.info('- times_asked_for_explanation += 1')

                sleep(1)

                self.action_runner.run_waiting_action('say', explain_exercise(self.level, first_number=self.exercise.first_number, second_number=self.exercise.second_number))

                print('End of the exercise, the assignment was explained.')

                self.asked_for_help = True
                break


            elif self.head_pressed:
                self.sic.unsubscribe_touch_listener('RightBumperPressed')
                self.sic.unsubscribe_touch_listener('LeftBumperPressed')
                self.sic.unsubscribe_touch_listener('BackBumperPressed')
                self.sic.unsubscribe_touch_listener('FrontTactilTouched')
                self.sic.unsubscribe_touch_listener('MiddleTactilTouched')
                self.sic.unsubscribe_touch_listener('RearTactilTouched')

                sleep(1)

                self.times_tried_sum_again += 1
                logging.info('- times_tried_sum_again += 1')
                break


    def play_introduction(self, level=None):

#        while not self.recognition_manager['attempt_success'] and self.recognition_manager['attempt_number'] < 2:
        self.action_runner.run_waiting_action('say', 'Hoi, ik ben Nao. Hoe heet jij?')
        self.action_runner.run_waiting_action('speech_recognition', 'answer_name', 3, additional_callback=self.on_intent_name)
        sleep(1)
        print("naam printen") 
        print(self.user_model['name'])
        try:
            print(self.user_model['name'])
            logging.info('- name detected: %s' % (self.user_model['name']))
        except:
            print('No name recognized')
            logging.info('- no name detected')

        self.reset_recognition_management()

        

        self.action_runner.run_waiting_action('say', 'Leuk dat je er bent! Wij gaan vandaag sámen rekenen. We gaan minsommen oefenen. Ik ga je eerst kort uitleggen hoe we dit ook alweer doen. Daarna gaan we 20 minuten sommen maken. Als je een fout maakt is dat niet erg, dan proberen we het gewoon opnieuw. Of leg ik je uit hoe ik het zou doen. Volgens mij kan je dat!')

        sleep(1)

        self.action_runner.run_waiting_action('say', 'We gaan straks minsommen oefenen onder de honderd. We doen eerst de tientallen eraf, en dan de eenheden eraf.')

        if level == 1:
            self.action_runner.run_waiting_action('say', 'Zullen we samen de sommen maken? Dan zeg ik steeds welk getal we eraf halen, en dan mag jij zeggen op welk getal we uitkomen. ')

        elif level == 2:
            self.action_runner.run_waiting_action('say', 'Zullen we sprongen van 10 tegelijk nemen? Dan doen we daarna de eenheden.')

        elif level == 3:
            self.action_runner.run_waiting_action('say', 'Zullen we grote sprongen van alle tientallen tegelijk nemen, en daarna de eenheden eraf doen?')

        elif level == 4:
            self.action_runner.run_waiting_action('say', 'Zullen we grote sprongen van alle tientallen tegelijk nemen? Dan halen we daarna alle eenheden er in 1 keer af.')

        self.action_runner.run_waiting_action('say', 'Zorg ervoor dat je de som die ik zeg altijd meteen opschrijft. Als je het antwoord weet, kan je tegen een van mijn voeten drukken. Zodra mijn ogen groen zijn, kan jij je antwoord geven! Zorg ervoor dat je duidelijk en hardop je antwoord geeft. Zullen we dan nu beginnen met rekenen? Als je er klaar voor bent mag je zachtjes op mijn hoofd drukken!')

        while self.waiting_for_start_lesson:
            self.sic.subscribe_touch_listener('FrontTactilTouched', Head_For_Start_Lesson())
            self.sic.subscribe_touch_listener('MiddleTactilTouched', Head_For_Start_Lesson())
            self.sic.subscribe_touch_listener('RearTactilTouched', Head_For_Start_Lesson())

            if self.waiting_for_start_lesson is False:
                self.sic.unsubscribe_touch_listener('FrontTactilTouched')
                self.sic.unsubscribe_touch_listener('MiddleTactilTouched')
                self.sic.unsubscribe_touch_listener('RearTactilTouched')

                sleep(1)
                self.action_runner.run_waiting_action('say', 'Oke, dan ga ik nu de eerste oefening aan je vertellen, vergeet niet om de som op te schrijven!')

    def play_conclusion(self):
        self.action_runner.run_waiting_action('say', 'Onze rekenles zit erop! Ik vind dat je heel goed je best hebt gedaan. Ik denk dat jij nog veel beter gaat worden in rekenen, vooral blijven oefenen! Ik ga nu even pauzeren, misschien tot een andere keer!')



    def on_intent_number(self, detection_result: DetectionResult) -> None:
        if detection_result:
            try:
                print(detection_result.parameters['number'].number_value)
                self.user_model['number'] = detection_result.parameters['number'].number_value
                self.recognition_manager['attempt_success'] = True
      
            except:
                self.recognition_manager['attempt_number'] += 1
                self.action_runner.run_action('set_eye_color', 'white')
                print('no number recognized, else statement')
                self.robot_did_not_hear_number += 1
                logging.info('- robot_did_not_hear_number += 1')
                logging.info('- else')
                self.action_runner.run_action('say', 'Sorry, ik heb je niet goed verstaan. Wil je je antwoord opnieuw zeggen?')
                sleep(7)


    def on_intent_name(self, detection_result: DetectionResult) -> None:
        if detection_result:
            try:
                self.user_model['name'] = detection_result.parameters['name'].list_value.values[0].struct_value['name']
                self.recognition_manager['attempt_success'] = True
                print('Name recognized')
                print('Name is ', self.user_model['name'])
            except:
              print("Name could not be detected")
        else:
            print('No intent recognized')


    def reset_recognition_management(self) -> None:
        self.recognition_manager.update({'attempt_success': False, 'attempt_number': 0})


lesson = Lesson('127.0.0.1',
              'nl-NL',
              'math-tutor-n9yf-5f3ba0e72a70.json',
              'math-tutor-n9yf')
lesson.run()
