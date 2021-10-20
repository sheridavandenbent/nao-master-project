import random
import logging

class Exercise:

    def generate_exercise(self, over=False):

        # generating two random tens
        tens_a = random.randint(2, 9) * 10
        tens_b = random.randint(2, 9) * 10

        # exercises that go past the tens ("met overbrugging")
        if over:

            units_a = random.randint(1, 8)
            units_b = random.randint(1, 8)

            while units_a == units_b:
                units_b = random.randint(1, 8)

            while tens_a == tens_b:
                tens_b = random.randint(2, 9) * 10

            self.first_number = max(tens_a, tens_b) + min(units_a, units_b)
            self.current_first = self.first_number

            self.second_number = min(tens_a, tens_b) + max(units_a, units_b)
            self.current_second = self.second_number

        # exercises that do not go past the tens ("zonder overbrugging")
        else:
            units_a = random.randint(1, 9)
            units_b = random.randint(1, 9)

            if max(tens_a, tens_b) == 90:

                while max(units_a, units_b) == 9 or units_a == units_b:
                    units_a = random.randint(1, 9)
                    units_b = random.randint(1, 9)

            self.first_number = max(tens_a, tens_b) + max(units_a, units_b)
            self.current_first = self.first_number

            self.second_number = min(tens_a, tens_b) + min(units_a, units_b)
            self.current_second = self.second_number

        self.step_accepted = False


    def acceptable_step(self, step_taken, level=1):

        current_units = self.current_second % 10
        current_tens = int((self.current_second - current_units) / 10)

        #when second number is fully subtracted
        if self.current_second == 0:
            print('The exercise is already done.')
            return False, 'already done'

        if current_tens != 0:
            self.doing_units = False
            #all tens at once
            if self.current_second == self.second_number and step_taken == current_tens * 10:
                action_level = 'above tens' if level < 3 else 'on level tens'
                return True, action_level
            #steps of ten at a time
            elif step_taken == 10:
                action_level = 'below tens' if level > 2 else 'on level tens'
                return True, action_level
            #incorrect step tens
            else:
                return False, 'incorrect tens'

        #splitting the units, to get to a ten
        elif self.current_first % 10 != 0 and self.current_second > self.current_first % 10 and step_taken == self.current_first % 10:
            self.doing_units = True
            action_level = 'below units' if level == 4 else 'on level units'
            return True, action_level

        #all current units at once
        elif step_taken == self.current_second:
            if self.current_first % 10 == 0:
                self.doing_units = True
                action_level = 'on level units'
                return True, action_level
            else:
                self.doing_units = True
                action_level = 'on level units' if level == 4 else 'above units'
                return True, action_level

        #incorrect step units
        else:
            self.doing_units = True
            return False, 'incorrect units'


    def take_step(self, step_taken, level=1):
        acceptable, action_level = self.acceptable_step(step_taken, level)
        if acceptable and not self.step_accepted:
            self.step_accepted = True
            self.current_first -= step_taken
            self.current_second -= step_taken
            return True, action_level
        elif self.step_accepted:
            print('Step already taken! Please call \'acceptable_answer\' first. No numbers were updated.')
            return False, 'step already taken'
        else:
            print('Unacceptable step! No numbers were updated.')
            return False, action_level

    def acceptable_answer(self, answer_given):
        if answer_given == self.current_first and self.step_accepted:
            self.step_accepted = False
            return True, 'correct'
        else:
            print('Wrong answer. Try again!')
            if self.doing_units:
                return False, 'incorrect units'
            return False, 'incorrect tens'

