import sys
import csv
import random
import string
import argparse
from turtle import end_fill

######### parsing input #########
mode = ''
command_parser = argparse.ArgumentParser()
command_parser.add_argument('-t', '--type', choices=['project', 'lab'], required=True,
                            help='provide a valid solver type to generate test for: project or lab')

# only included optional project arguments, as the others will be assumed 'y'
if command_parser.parse_known_args()[0].type.lower().startswith('project'):
    project_parser = argparse.ArgumentParser()
    project_parser.add_argument('--past_partners', type=ascii, 
        help='fill with "y" or "n" if you want to generate constraints for past partners')
    project_parser.add_argument('--blocklist', type=ascii, 
        help='fill with "y" or "n" if you want to generate constraints for a blocklist')
    project_parser.add_argument('--ta_group', type=ascii, 
        help='fill with "y" or "n" if you want to generate constraints for ta groups')
    project_parser.parse_known_args()

    # parsing for optional flags
    if(project_parser.parse_known_args()[0].past_partners != None):
        past_partners = project_parser.parse_known_args()[0].past_partners
    else:
        past_partners = None
    
    if(project_parser.parse_known_args()[0].blocklist != None):
        blocklist = project_parser.parse_known_args()[0].blocklist
    else:
        blocklist = None
    
    if(project_parser.parse_known_args()[0].ta_group != None):
        ta_group = project_parser.parse_known_args()[0].ta_group
    else:
        ta_group = None

    mode = 'project'

# TODO after TP    
elif command_parser.parse_known_args()[0].type.lower().startswith('lab'):
    mode = 'lab'

# constants
NUM_STUDENTS = random.randint(30, 201)
NUM_TAS = int(NUM_STUDENTS/10)

# global variables
students = set()
tas = set()
lab_locations = set()
ta_group_times = []
test_number = random.randint(1000, 10000)

######### generating files #########

# wrapper function for all project test files
def generate_project_test():
    generate_student_roster()
    if ta_group != None:
        generate_ta_groups()
    generate_prefs()
    if past_partners != None:
        generate_past_partners()
    if blocklist != None:
        generate_blocklist()
    
# wrapper function for all lab test files
def generate_lab_tests():
    # TODO: uncomment after implementing lab features

    # generate_student_roster()
    # generate_prefs()
    # generate_location()
    # generate_ta_groups()
    pass

# generate student roster
# 
# example file content:
#   Student CS Logins
#   elau5
#   crusch
def generate_student_roster():
    with open(f"Student Roster Test {test_number}.csv", mode="w") as student_roster_csv:
        student_roster_writer = csv.writer(student_roster_csv)
        student_roster_writer.writerow(["Student CS Login"])
        for i in range(NUM_STUDENTS):
            random_student = generate_random_login()
            student_roster_writer.writerow([random_student])
            students.add(random_student)

# helper function to generate a cs logins between 3-8 characters
def generate_random_login() -> string:
    login = ''
    login = login.join(random.choice(string.ascii_lowercase) for x in range(random.randint(3, 9)))
    return login

# generates individual preferences
# 
# example file content:
#   Individual Preferences
#   "elau, ['tues 8 PM - 9 PM', 'mon 1 PM - 2 PM', 'sat 6 PM - 7 PM', 'thurs 7 PM - 8 PM', 'sun 8 PM - 9 PM', 'mon 1 PM - 2 PM']"
#   "crusch, ['mon 1 PM - 2 PM', 'sun 8 PM - 9 PM', 'mon 1 PM - 2 PM', 'sat 6 PM - 7 PM', 'fri 4 PM - 5 PM', 'fri 9 PM - 10 PM', 'thurs 7 PM - 8 PM', 'tues 8 PM - 9 PM', 'mon 2 PM - 3 PM', 'fri 3 PM - 4 PM']"
def generate_prefs():
    if mode == "project":
        grouped_students = generate_group_pref()
        with open(f"Individual Preferences Test {test_number}.csv", mode="w") as individual_pref_csv:
            individual_pref_writer = csv.writer(individual_pref_csv)
            individual_pref_writer.writerow(["Individual Preferences, Preferences"])
            for student in students:
                if student not in grouped_students:
                    preferences = random.sample(ta_group_times, random.randint(3,len(ta_group_times)))
                    individual_pref_writer.writerow([f"{student}, {preferences}"])
                
    elif mode == "lab":
        pass

# generates group preferences. called in generate_prefs before individual preferences are generated
#
# example file content:
#   Group Preferences
#   "['mdxlxeg', 'anwadj', 'zbygj', 'rvyx'], ['thurs 9 PM - 10 PM', 'thurs 5 PM - 6 PM', 'sun 7 PM - 8 PM', 'tues 2 PM - 3 PM']"
#   "['xrfavn', 'vtaetj', 'bxdz', 'xlptfzu'], ['tues 6 PM - 7 PM', 'tues 9 PM - 10 PM', 'thurs 9 PM - 10 PM', 'tues 2 PM - 3 PM']"
def generate_group_pref() -> set:
    with open(f"Group Preferences Test {test_number}.csv", mode="w") as group_pref_csv:
            preformed_groups = []
            grouped_students = []
            for i in range(0, int(NUM_STUDENTS/4), 4):
                group = list(students)[i:i+4]
                
                if(len(group) == 4):
                    preformed_groups.append(group)

            group_pref_writer = csv.writer(group_pref_csv)
            group_pref_writer.writerow(["Member 1, Member 2, Member 3, Member 4, Preferences"])
            for g in preformed_groups:
                preferences = random.sample(ta_group_times, random.randint(3,len(ta_group_times)))
                group_members = ''
                for member in g:
                    grouped_students.append(member)
                    group_members = group_members + member + ", "
                group_pref_writer.writerow([f"{group_members} {preferences}"])
    return grouped_students

# generates past partners
#
# example file content:
#   Past Partners
#   "elau, crusch"
#   "crusch, elau"
def generate_past_partners():
    with open(f"Past Partners {test_number}.csv", mode="w") as past_partners_csv:
        past_partners_writer = csv.writer(past_partners_csv)
        past_partners_writer.writerow(["Student CS Login, Past Partner"])

        previous_student_groups = []
        for i in range(0, NUM_STUDENTS, 4):
            previous_group = list(students)[i:i+4]
            if(len(previous_group) == 4):
                previous_student_groups.append(previous_group)

        for i in range(len(previous_student_groups)):
            for j in range(4):
                student = previous_student_groups[i][j]
                for k in range(4):
                    if previous_student_groups[i][k] != student:
                        prev_partner = previous_student_groups[i][k]
                        past_partners_writer.writerow([f"{student}, {prev_partner}"])

# generates blocklist
#
# example file content:
#   Blocklist
#   "elau, zew"
#   "crusch, fdsaf"
def generate_blocklist():
    with open(f"Blocklist {test_number}.csv", mode="w") as blocklist_csv:
        blocklist_writer = csv.writer(blocklist_csv)
        blocklist_writer.writerow(["TA CS Login, Blocked Student"])
        block_tas = set()
        for i in range(random.randint(1, int(len(tas)/2))):
            ta = random.choice(tuple(tas-block_tas))
            for j in range(1,3):
                random_blocked_student = random.choice(tuple(students))
                blocklist_writer.writerow([f"{ta}, {random_blocked_student}"])

# generates ta groups with TAs and their timeslot
#
# example file content:
#   TA Group Timeslots
#   "iwrlcxhjthurs, 8 PM - 9 PM"
#   "tkhlqvsamon, 9 PM - 10 PM"
def generate_ta_groups():
    days_of_week = ['mon', 'tues', 'weds', 'thurs', 'fri', 'sat', 'sun']
    
    with open(f"TA Groups Test {test_number}.csv", mode="w") as ta_group_csv:
        ta_groups_writer = csv.writer(ta_group_csv)
        ta_groups_writer.writerow(["TA CS Login, Timeslot"])
        if mode == "project":
            for i in range(NUM_TAS):
                random_ta = generate_random_login()
                tas.add(random_ta)

                rand_dow = random.randint(0,6)
                rand_time = random.randint(1,11)

                date_time = f"{days_of_week[rand_dow]} {rand_time} PM - {rand_time + 1} PM"
                ta_group_times.append(date_time)

                ta_groups_writer.writerow([f"{random_ta}, {date_time}"])
        elif mode == "lab":
            # TODO after TP: implement lab test groups based on generated location file
            pass

# generates location 
# TODO after TP: write format + example
def generate_location():
    # # dictionary of cs lab locations and their capacity
    # locations = {"sunlab": 20, "123": 15, "234": 17}

    # TODO after TP: sample an amount of rooms that would fit NUM_STUDENTS
    pass

if mode == 'project':
    generate_project_test()
elif mode == 'lab':
    generate_lab_tests()