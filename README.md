# README

## Problem Description
A common time sink for HTAs in Brown's CS department is generating project groups for students based on student availabilities. Sometimes students may want to be matched with a certain set of partners, but other times 
students would prefer to be matched with a random partner. For cs0320 in particular, we need to match students
together based on their availability for certain mentor meeting time slots that correspond to some set of TAs.
We must also manage blocklists to ensure that no student is matched with a TA's timeslot where the TA has
blocklisted the student. This model can be generalized for other similar tasks, too, such as for assigning
submissions for TAs to grade, generating project groups without any mentor meetings attached, or assigning students to lab sections.

Overall, our goal is to take all student availabilities as input and generate a set of project groups that 
respects all student availabilities and preferences.

## Design Choices + Challenges
This model uses Z3 and has only boolean variables. Specifically, `N_GROUPS * N_STUDENTS` booleans. We keep track
of them in a map `assignment`, where `assignment[s][g]` is true IFF s is assigned to g.

### Constraints
We check the following constraints:
- All students are assigned a group
- No student is assigned more than one group
- All students are not assigned to groups that they are not available for
- All groups have either 0 or 3 students
- If a student has preferred partners, that student is assigned to a group with them

Where possible, we limit by availability pre-solver to reduce the problem complexity. For instance,
when checking if all students are assigned a group, we do not check all groups to see if that student
has been assigned to it; instead, we check all groups _for which the student was available_. This
suffices because we explicitly ensure that they are not assigned to any groups for which they are not
available, overall reducing the problem complexity.

### Challenges + Future Work

One case that this script is not yet equipped to handle is when the number of students is not divisible by group
size (so some groups must be larger than others). When using this script in practice, we'll likely opt to deal 
with those cases manually; however, if we have time, we'll update it in the future to acommodate for this case.

We also plan in the future to add a constraint for cases where repeating partners is not allowed, as is the policy
for some Brown CS classes. The model currently does not support this feature.

You can find a beta implementation of these features in `term_project.py`.


### Input / Output Format
Mock input data is provided in `data/`. This script takes multiple CSVs as input, all of
which are described below.

After running the model, it prints out each mentor meeting time slot and the group that corresponds to that 
time slot (either a group of 3 students or an empty group). A group is represented as a list of student CS
logins.

## Input CSV Format (current solver)
1. Group preferences. At least the following columns:
    
    "Partner 1 - CS Login"
    
    "Partner 2 - CS Login"
    
    "Partner 3 - CS Login"
    
    "Check all mentor meeting slots for which your entire group will be available each week of Project 2"  
    - EX: "Tues 8-9pm, Weds 9-10pm"

2. Individual preferences. At least the following columns:
    
    "Your CS Login"
    
    "Check all mentor meeting slots for which you will be available each week of Project 2"
    - EX: "Tues 8-9pm, Weds 9-10pm"

3. Mappings between TAs and meeting slots. At least the following columns:
    
    "TA CS Login"
    
    "Mentor Meeting Slot"
    - EX: "Tues 8-9pm"
    - (should correspond to some slot offered in other forms)

4. TA Blocklists. TA fills out form once for each student on their mentee blocklist. 
   At least the following columns:
    
    "TA CS Login"
    
    "Student CS Login"

5. All student CS logins. At least the following columns:
    
    "Student CS Login"

## Input CSV Format (tests)

1. Student Roster: All student CS logins. Required columns: 

    "Student CS Login"

2. Individual Preferences: All student CS logins not in a group and their preferences. Required columns: 
    
    "Student CS Login"
    
    "Preferences"
    - EX: "mon 1 PM - 2 PM, weds 2 PM - 3 PM"

3. Group Preferences: Pre formed groups with members' CS logins and their preferences. Required columns:

    "Member 1"

    "Member 2"

    "Member 3"

    "Member 4"
    
    "Preferences"
    - EX: "mon 1 PM - 2 PM, weds 2 PM - 3 PM"

4. Past Partners: Each student followed by another student they've worked with previously. Required columns:
    
    "Student CS Login"
    
    "Past Partner"

5. Blocklist: TA login followed a student on their block list. Required columns:
    
    "TA CS Login"
    
    "Blocked Student"

6. ta_group: TA login followed by a timeslot. Required columns:
    
    "TA CS Login"
    
    "Timeslot"

## How to Run
Install requirements:

`pip3 install -r requirements.txt`

Run on small dataset (<1 sec runtime):

`python3 groups.py data/small/Student\ Roster.csv data/small/TA\ blocklist.csv data/small/TA\ time\ slots.csv data/small/Form\ B\ Response.csv data/small/Form\ A\ Response.csv`

Run on big dataset (<1 min runtime):

`python3 groups.py data/big/Student\ Roster.csv data/big/TA\ blocklist.csv data/big/TA\ time\ slots.csv data/big/Form\ B\ Response.csv data/big/Form\ A\ Response.csv`

To generate tests files:

`python3 generate_tests.py -t='project' --past_partners=y --blocklist=y --ta_group=y`
tests will be generated with a unique number

        


