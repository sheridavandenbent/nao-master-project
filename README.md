# robot_math_tutor
This code is based on the Social Interaction Cloud (SIC, https://socialrobotics.atlassian.net/wiki/spaces/CBSR/overview?homepageId=229432).

## code_lesson.py
Code_lesson.py is the basis of the code, and is the code that has to run for the robot to work. At the end of the code, the IP address, name of the robot, file with key from Dialogflow and the name of the agent should be filled in. 
The code generates a logfile while it runs.
To run the code, the function run should be called.

The function answer_structure contains the main 

Listen_for_step is called when the student needs to give an step. It waits until one of the feet of the robot are pressed, after which it will listen for an answer for 3 seconds. If the robot does not hear a number, it will ask the student to press the feet again. 
Listen_for_answer is called when the student needs to give an answer. It waits until one of the feet of the robot are pressed, after which it will listen for an answer for 3 seconds. If the robot does not hear a number, it will ask the student to press the feet again. 

If a student gives an incorrect answer for the first time, choice_after_incorrect_answer will be called. Here the student can choose whether they want to try the sum again, or if they want an explanation from the robot. The robot waits until either the head or feet are pressed. 

Play_introduction plays the introcution of the session. The robot gives an introduction and asks the student to press the head when they are ready to start. 

Play_conclusion starts after the student has practised exercises for 20 minutes. The robot gives a short conclusion. 

On_intent_number checks if a number is heard when the robot listens for a step or answer. If this is not the case, the robot will ask the student to repeat their answer.

On_intent_name checks if a name is heard when the robot listens for one in the introduction of the session. 

## code_exercise.py 
Code_exercise contains generate_exercise, which contains the code in which a random exercise is generated. It is called in code_lesson.py. 
The function acceptable_step is called in code_lesson, to check if the step that a student gave is correct for the current sum.
The funciton take_step is called in code_lesson, and it gives information about the current numbers of the sum. 
Acceptable_answer is called in code_lesson, and it contains code that decides if a given answer by a student is acceptable or not. 

## explain_exercise.py
Code_exercise contains the code that is used when the robot needs to explain the exercise to the student. It is called in code_lesson.py. 

## randomized_responses.py
Randomized_responses is called in code_lesson.py. It contains sentences that are used when a student finished a sum correctly or incorrectly, and sentences to indicate that they are moving to the next sum.
# nao-master-project
