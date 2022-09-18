import sys
import csv

individual_prefs_path = sys.argv[1]
group_prefs_path = sys.argv[2]

students = set()

with open(individual_prefs_path, mode="r") as individual_prefs_csv:
    individual_prefs_reader = csv.DictReader(individual_prefs_csv)
    for row in individual_prefs_reader:
        students.add(row["Your CS Login"])

with open(group_prefs_path, mode="r") as group_prefs_csv:
    group_prefs_reader = csv.DictReader(group_prefs_csv)
    for row in group_prefs_reader:
        # Parse CSV for CS logins of all group members.
        for i in range(1, 4):
            students.add(row[f"Partner {i} - CS Login"])

with open("Student Roster.csv", mode="w") as student_roster_csv:
    student_roster_writer = csv.writer(student_roster_csv)
    student_roster_writer.writerow(["Student CS Login"])
    for student in students:
        student_roster_writer.writerow([student])
