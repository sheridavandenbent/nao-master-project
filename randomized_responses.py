import random
from social_interaction_cloud.action import ActionRunner


responses_correct_exercise = ['Goed zo! Dat antwoord klopt,',
                             'Heel goed! Dat is inderdaad het juiste antwoord.',
                             'Yes, dat klopt, je bent goed bezig.',
                             'Helemaal goed!',
                             'Inderdaad, dat antwoord klopt,']

responses_incorrect_answer = ['Ik denk dat je een fout hebt gemaakt. Kan gebeuren!',
                              'Jouw antwoord is helaas niet goed. Ik vond dit ook lastig!',
                              'Jouw antwoord klopt helaas niet helemaal.',
                              'Jammer, je antwoord is niet goed. Dat kan gebeuren!',
                              'Ik denk dat je antwoord niet klopt, maar van fouten kan je leren!']

lines_next_sum = ['Op naar de volgende som!',
                 'Laten we nog een som maken!',
                 'Laten we nog een som doen!']

def response_correct_exercise():
    return responses_correct_exercise[random.randint(0, 4)]

def response_incorrect_answer():
    return responses_incorrect_answer[random.randint(0, 4)]

def text_next_sum():
    return lines_next_sum[random.randint(0,2)]
