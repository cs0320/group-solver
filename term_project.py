import csv
from lib2to3.pgen2 import grammar
import sys
import random
from pprint import pprint
from collections import defaultdict

from z3 import *

# There are quite a few SMT solvers you might use; here's the start of
# an approach using Z3. But note the SO post below: Z3 may not give you
# a "best so far" result if it times out before returning an optimal solution.
#   - you don't have to use Z3;
#   - if you _do_ use Z3, an iterative-refinement approach seems advisble.

# This model has only boolean variables. Specifically, (N_GROUPS*N_STUDENTS) booleans.
# Other modeling approaches might include using an int->int function or
#   enum datatypes. If you use an unbounded type (like int; SMT ints are actual ints)
#   beware, and try to never use universal quantification; instead repeat constraints.

# Other potential engines:
#   other SMT solvers, like CVC4 (maybe CVC5 now?)
#   OR/optimization engines like
#     Opensource COIN-OR: https://www.coin-or.org
#     Gurobi (should be free for academic use)

# Z3 resources:
# https://theory.stanford.edu/~nikolaj/programmingz3.html
# https://z3prover.github.io/api/html/namespacez3py.html
# https://z3prover.github.io/api/html/classz3py_1_1_optimize.html

# Note: Z3 won't "terminate early with a best-so-far candidate"
#   Thus, this post suggests an iterative-refinement approach:
#   (1) get a result
#   (2) compute the goodness of the result
#   (3) add a requirement that goodness is better than last result, return to (1)
# https://stackoverflow.com/questions/60841582/timeout-for-z3-optimize

# Challenge 1: scaling this!
#   Larger groups are also more likely to be challenging, because cardinality is expensive
#   This expense means that, e.g., might be better to fix a time for every group, and use
#   that to write contraints saying that every student matched with (e.g.) group17 needs
#   to be available at <time for group_17>). Even better, script the intersection and use
#   that to limit the options in constraints, rather than making the solver do it.
# Challenge 3: optimization vs. student preferences
GROUP_SIZES = {0, 4, 5, 6}
GROUP_DEFAULT = 5

# Input CSVs are supplied as command line arguments.
if len(sys.argv) != 6:
    print(
        "Usage: groups.py <student_roster.csv> <blocklist.csv> <ta_slots.csv> "
        "<individual_preferences.csv> <group_preferences.csv>"
    )
    sys.exit(1)

all_students_path = sys.argv[1]
blocklist_path = sys.argv[2]
ta_slots_path = sys.argv[3]
individual_prefs_path = sys.argv[4]
group_prefs_path = sys.argv[5]

# Maps each student id to a set of meeting time preferences.
student_availability = {}

# Maps each student id to their GitHub and Discord logins.
default_map = {"github": "", "discord": ""}
login_to_github_discord = defaultdict(default_map.copy)

# Set of all time slots for students to choose from.
time_slots = set()

# Initialize student_availability by mapping all students to an empty preference set.
with open(all_students_path, mode="r") as all_students_csv:
    all_students_reader = csv.DictReader(all_students_csv)
    for row in all_students_reader:
        student_availability[row["Student CS Login"].lower().strip()] = set()

# Gather student preferences from individual preference CSV.
# Keep track of students and their partner preferences in student_to_partners.
student_to_partners = {}
with open(individual_prefs_path, mode="r") as individual_prefs_csv:
    individual_prefs_reader = csv.DictReader(individual_prefs_csv)
    for row in individual_prefs_reader:
        # Parse CS login and availabilities from CSV.
        cs_login = row["Partner 1 - CS Login"].lower().strip()
        prefs = row[
            "Check all mentor meeting slots for which you will be available each week of the Term Project"
        ].split(", ")

        # Update set of all possible time slots.
        time_slots.update(prefs)

        login_to_github_discord[cs_login] = {
            "github": row["Partner 1 - GitHub Username"],
            "discord": row["Partner 1 - Discord Username"],
        }

        if cs_login in student_availability:
            student_availability[cs_login].update(prefs)

            partner = row["Partner 2 - CS Login [optional]"].lower().strip()
            if partner:
                student_to_partners[cs_login] = {partner}
                login_to_github_discord[partner] = {
                    "github": row["Partner 2 - GitHub Username [optional]"],
                    "discord": row["Partner 2 - Discord Username [optional]"],
                }
        else:
            raise Exception(
                f"ERROR: Student {cs_login} was found in {individual_prefs_path} but was not found in course roster ({all_students_path})"
            )

# Gather student preferences from group preference CSV.
# Keep track of students and their partner preferences in student_to_partners.
with open(group_prefs_path, mode="r") as group_prefs_csv:
    group_prefs_reader = csv.DictReader(group_prefs_csv)
    for row in group_prefs_reader:
        # Parse CSV for CS logins of all group members.
        cs_logins = set()
        for i in range(1, max(GROUP_SIZES) + 1):
            cs_login = row[f"Partner {i} - CS Login"].lower().strip()
            if cs_login:
                cs_logins.add(cs_login)

                login_to_github_discord[cs_login] = {
                    "github": row[f"Partner {i} - GitHub Username"],
                    "discord": row[f"Partner {i} - Discord Username"],
                }

        # Parse CSV for group availabilities.
        prefs = row[
            "Check all mentor meeting slots for which your entire group will be available each week of the Term Project"
        ].split(", ")

        # Update set of all possible time slots.
        time_slots.update(prefs)

        for cs_login in cs_logins:
            if cs_login in student_availability:
                if student_availability[cs_login] != set():
                    # student already has preferences!? (filled out both forms, ugh)
                    print(
                        f"WARNING: Student {cs_login} appears to have both individual and group preferences. Defaulting to group preferences."
                    )
                    student_availability[cs_login] = set()
                student_availability[cs_login].update(prefs)

                partners = {p for p in cs_logins if p != cs_login}
                if cs_login in student_to_partners:
                    student_to_partners[cs_login].update(partners)
                else:
                    student_to_partners[cs_login] = partners
            else:
                raise Exception(
                    f"ERROR: Student {cs_login} was found in {group_prefs_path} but was not found in course roster ({all_students_path})"
                )

for student in student_availability:
    if student_availability[student] == set():
        print(
            f"WARNING: Student {student} has no preferences (either in individual or group form). Defaulting to full availability."
        )
        student_availability[student] = set(time_slots)


# Gather TA to time slot mapping from TA time slot CSV.
slot_to_tas = {}
with open(ta_slots_path, mode="r") as ta_slots_csv:
    ta_slots_reader = csv.DictReader(ta_slots_csv)
    for row in ta_slots_reader:
        ta_login = row["TA CS Login"].lower().strip()
        slot = row["Mentor Meeting Slot"]

        if slot in slot_to_tas:
            slot_to_tas[slot].add(ta_login)
        else:
            slot_to_tas[slot] = set([ta_login])

# Gather TA blocklists.
ta_to_blocklist = {}
with open(blocklist_path, mode="r") as blocklist_csv:
    blocklist_reader = csv.DictReader(blocklist_csv)
    for row in blocklist_reader:
        ta_login = row["TA CS Login"].lower().strip()
        student_login = row["Student CS Login"].lower().strip()

        if ta_login in ta_to_blocklist:
            ta_to_blocklist[ta_login].add(student_login)
        else:
            ta_to_blocklist[ta_login] = set([student_login])

# Convert student availabilities to accommodate for multiple TAs on a single slot.
ta_time_slots = set()
for student in student_availability:
    new_availabilities = set()
    for slot in student_availability[student]:
        if slot in slot_to_tas:
            for ta in slot_to_tas[slot]:
                new_slot = f"{slot} ({ta})"
                if ta not in ta_to_blocklist or student not in ta_to_blocklist[ta]:
                    # Only add slot for student if TA has not blocklisted the student.
                    new_availabilities.add(new_slot)
                ta_time_slots.add(new_slot)
        else:
            print(
                f"WARNING: No TAs found for slot {slot}. Removing slot from student availability."
            )

    student_availability[student] = new_availabilities

# Map each student to a unique integer id.
student_id_map = {idx: student for idx, student in enumerate(student_availability)}
student_to_id = {student_id_map[idx]: idx for idx in student_id_map}
print(len(student_id_map))

# Map each time slot to a unique integer id.
ta_time_slot_id_map = {
    idx: ta_time_slot for idx, ta_time_slot in enumerate(ta_time_slots)
}
slot_to_id = {ta_time_slot_id_map[slot]: slot for slot in ta_time_slot_id_map}

N_STUDENTS = len(student_id_map)
# if N_STUDENTS % max(GROUP_SIZES) != 0:
#     print(
#         "WARNING: Number of students not divisible by group size. Some groups must be larger than others."
#     )

# If not using soft constraints, just use Solver()
# solver = Optimize()
set_param(proof=True)
solver = Solver()
solver.set(unsat_core=True)  # must enable core extraction
solver.set(":core.minimize", True)  # not sure how good this is

# Boolean variables; assignment[s][g] is true IFF s is assigned to g
# Some unused variables, but these shouldn't appear in constraints
assignment = {
    s: {g: z3.Bool(f"assignment_{s}_{g}") for g in ta_time_slot_id_map}
    for s in student_id_map
}

# everybody gets a group
# nobody gets >1 group
for s in student_id_map:
    # Limiting by availability /pre/-solver reduces the problem complexity
    login = student_id_map[s]
    potential_s_assignments = [
        assignment[s][slot_to_id[g]] for g in student_availability[login]
    ]
    solver.assert_and_track(Or(potential_s_assignments), f"{login}_is_assigned")

    # non availability
    impossible_s_assignments = [
        assignment[s][g]
        for g in ta_time_slot_id_map
        if ta_time_slot_id_map[g] not in student_availability[login]
    ]
    for a in impossible_s_assignments:
        solver.assert_and_track(Not(a), f"{login}_is_not_assigned_to_{a}")

    for a in potential_s_assignments:
        # Hack: "a2 != a" produces an error; Z3 tries to protect us from using references to
        #   boolean variables in the *solver* as if they were booleans in the program.
        #   100% sure there is a better way than comparing the string rep of each...
        solver.assert_and_track(
            Implies(
                a, Not(Or([a2 for a2 in potential_s_assignments if str(a2) != str(a)]))
            ),
            f"{login}_assignment_to_{a}_is_unique",
        )

# no group is too big
# cardinality is expensive; Z3 has a built-in pseudo-boolean engine;
# TODO
for g in ta_time_slot_id_map:
    assigned_to_g = [assignment[s][g] for s in student_id_map]
    solver.assert_and_track(
        Or(
            [PbEq([(x, 1) for x in assigned_to_g], size) for size in GROUP_SIZES],
        ),
        f"{ta_time_slot_id_map[g]}_size_is_{max(GROUP_SIZES)}_or_0",
    )

# if student has partners, make sure they are all assigned to the same group
seen = set()
for s in student_id_map:
    cs_login = student_id_map[s]
    if cs_login in student_to_partners:
        for g in ta_time_slot_id_map:
            solver.assert_and_track(
                Implies(
                    assignment[s][g],
                    And(
                        [
                            assignment[student_to_id[p]][g]
                            for p in student_to_partners[cs_login]
                        ]
                    ),
                ),
                f"{cs_login}_partners_all_in_or_out_of_{g}",
            )

        # if the number of partners is a valid group size, no new partners are assigned to the group
        if len(student_to_partners[cs_login]) + 1 in GROUP_SIZES:
            for p in student_id_map:
                if (
                    p != s
                    and student_id_map[p] not in student_to_partners[cs_login]
                    and cs_login not in seen
                ):
                    solver.assert_and_track(
                        Implies(
                            assignment[s][g],
                            Not(assignment[p][g]),
                        ),
                        f"{student_id_map[p]}_not_assigned_to_{g}_cause_full_group_{s}",
                    )
                    seen.update(student_to_partners[cs_login] | {cs_login})
    else:
        # if no partners, the student is assigned to a default sized group
        for g in ta_time_slot_id_map:
            assigned_to_g = [assignment[stu][g] for stu in student_id_map]
            solver.assert_and_track(
                Implies(
                    assignment[s][g],
                    PbEq([(x, 1) for x in assigned_to_g], GROUP_DEFAULT),
                ),
                f"{s}_{g}_default_group_size",
            )


# Uncomment this to view the (verbose) set of solver constraints
# print(solver)

if solver.check() == unsat:
    print("unsat")
    print(solver.unsat_core())
    print(solver.proof())
else:
    # Note this won't include values for un-used variables
    # trying to evaluate an unused variable may produce a confusing error.
    #   We could tell "eval" to enable model completion, but that would just give
    #   a default value (which may not be False!)
    solution = solver.model()
    group_to_students = {}
    for s in student_id_map:
        gs = [g for g in ta_time_slot_id_map if solution.eval(assignment[s][g])]

        # check if the students is assigned to multiple groups
        if len(gs) == 0:
            raise Exception(f"ERROR: {s} not assigned to any groups")
        if len(gs) > 1:
            raise Exception(f"ERROR: {s} assigned to multiple groups: {gs}")

        # print(f"Student {s}: {gs}")
        if ta_time_slot_id_map[gs[0]] in group_to_students:
            group_to_students[ta_time_slot_id_map[gs[0]]].append(student_id_map[s])
        else:
            group_to_students[ta_time_slot_id_map[gs[0]]] = [student_id_map[s]]

    for g in sorted(slot_to_id, key=lambda g: g.split("(")[1]):
        if g not in group_to_students:
            group_to_students[g] = []

    # sort by cs login first, then by date
    for g in sorted(group_to_students, key=lambda g: (g.split("(")[1], g)):
        print(f"{g:<35} {group_to_students[g]}")

    if True:
        with open("solution.csv", mode="w") as solution_file:
            fieldnames = ["Mentor cs login", "Meeting time"]
            for i in range(1, max(GROUP_SIZES) + 1):
                fieldnames += [
                    f"partner {i} - cs login",
                    f"partner {i} - github",
                    f"partner {i} - discord",
                ]
            writer = csv.DictWriter(solution_file, fieldnames=fieldnames)
            writer.writeheader()

            for g in sorted(group_to_students, key=lambda g: (g.split("(")[1], g)):
                mentor_cs_login = g.split("(")[1].replace(")", "")
                meeting_time = g.split("(")[0]
                cs_logins = tuple(group_to_students[g])
                if not cs_logins:
                    continue

                githubs = tuple(
                    login_to_github_discord[cs_login]["github"]
                    for cs_login in cs_logins
                )
                discords = tuple(
                    login_to_github_discord[cs_login]["discord"]
                    for cs_login in cs_logins
                )

                row = {
                    "Mentor cs login": mentor_cs_login,
                    "Meeting time": meeting_time,
                }

                for i in range(1, max(GROUP_SIZES) + 1):
                    if i <= len(cs_logins):
                        cs_login = cs_logins[i - 1]
                    else:
                        cs_login = ""

                    if i <= len(githubs):
                        github = githubs[i - 1]
                    else:
                        github = ""

                    if i <= len(discords):
                        discord = discords[i - 1]
                    else:
                        discord = ""

                    row[f"partner {i} - cs login"] = cs_login
                    row[f"partner {i} - github"] = github
                    row[f"partner {i} - discord"] = discord

                writer.writerow(row)


if __name__ == "__main__":
    print()
