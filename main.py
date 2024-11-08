# Jira-Organize handling projects and bugs
from jira import JIRA
import random
import re   # for searching srv- (regular expression)
from collections import Counter  # to count elements
import matplotlib.pyplot as plt  # to plot graphs
# to handle files and signals
import os
import signal
import sys
import json
# to save the secret API
from dotenv import load_dotenv
# jira issue is a task need to be done like fix a bug

# connections
# jira settings- global variables
server = "https://galgreen03-1730896188250.atlassian.net"
user = "galgreen03@gmail.com"
load_dotenv()
jira_api = os.getenv("API_KEY")
# create jira object
jira = JIRA(server=server, basic_auth=(user, jira_api))
project_key = "MFLP"

# global legal predefined server list:
servers = ["srv-data", "srv-web", "srv-backup", "srv-fun"]

# Global variable to store the current progress
progress_file = 'progress.json'

# global issues varible in case of exit in the middle of the program
issues_global = []
last_requ = 0


# phase 1   !!!
# create 200 issues
def create_issues():
    # unvalid servers names
    unvalid_srv = ["srv-d", "srv-we", "srv-back", "srv-n", ""]
    predefined_srv=unvalid_srv+servers
    # and problems:
    problems = [
        "Tonic",
        "running time",
        "storage is full",
        "security",
        "Network"
    ]

    # create 200 issues-with random srv(sometimes in big letters) and random problem
    # sometimes people will write in valid name srv or won't write srv name at all
    for i in range(1, 201):
        server_name = random.choice(predefined_srv)
        # change in random the name to big letters or dont
        # change only if a name is not None
        if server_name:
            if random.choice([True,False]):
                server_name = server_name.upper()
                # else the name in small letters like in the list
        # description = f"{random.choice(problems)} on {server_name}" if server_name else random.choice(problems)
        description = f"{random.choice(problems)} on {server_name}"
        issue_dict = {
            'project': {'key': project_key},
            'summary': f"Support case #{i}",
            'description': description,
            'issuetype': {'name': 'Task'},
        }
        try:
            new_issue = jira.create_issue(fields=issue_dict)
            print(f"Created issue {new_issue.key}")
        except Exception as e:
            print(f"Failed to create issue {i}: {e}")


# delete issues if the build went wrong:
def delete_issues():
    issues = jira.search_issues(f'project = {project_key}', maxResults=False)
    for issue in issues:
       try:
           issue.delete()
           print(f"Issue {issue.key} deleted successfully")
       except Exception as e:
           print(f"Failed to delete issue {issue.key}: {e}")


# phase 2!!!!
# count the number of tickets associated with each server
def analyze_issues():
    # find all the issues in the project
    query = f'project = {project_key}'
    issues = jira.search_issues(query, maxResults=False)

    server_counter = Counter()
    # count issues for each server
    # if there is unvalid server name add that to the unvalid count
    for issue in issues:
        server_name = extract_server_name(issue.fields.description)
        server_counter[server_name] += 1  # if the name isnt valid add 1 to unvalid

    display_results(server_counter)


# get description and extract the server name
def extract_server_name(description):
    match = re.search(r"\b(srv-[\w-]+)\b", description, re.IGNORECASE)

    if match:
        match=match.group(0).lower()  # make sure to return the name in small letters
        if match in servers:
            server_name = match

            return server_name
        else:
            return "invalid"
    else:
        return "invalid"


# display the result count in graphic way
def display_results(server_counter):
    server_names = list(server_counter.keys())
    ticket_counts = list(server_counter.values())

    plt.figure(figsize=(10, 6))
    plt.bar(server_names, ticket_counts, color='skyblue')
    plt.xlabel("Server Names")
    plt.ylabel("Number of Tickets")
    plt.title("Number of Tickets per Server")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


    # now instead of pull all the issues at once, we will pull 8 issues in each req
    # by giving the value 8 to maxResult in the jira search issue


# phase 3!!
# count the number of tickets associated with each server-ask for 8 issues in each pull
def analyze_issues_8():
    # find all the issues in the project

   # num of reqs that need to be done
    num_reqs=200//8
    issues=[]

    for i in range(num_reqs):
        start=i*8   # start index to pull
        issue_var = jira.search_issues(
            f'project={project_key}',
            startAt=start,
            maxResults=8
            )
        issues.extend(issue_var)


    server_counter = Counter()
    # count issues for each server
    # if there is unvalid server name add that to the unvalid count
    for issue in issues:
        server_name = extract_server_name(issue.fields.description)
        server_counter[server_name] += 1  # if the name isnt valid add 1 to unvalid

    display_results(server_counter)


# phase 4!!!
# now we will add a coping mechanism for failure for phase 3


# read the progress of the last program from the file
def read_saved_progress():
    if os.path.exists(progress_file):
        if os.stat(progress_file).st_size == 0:
            print("Progress file is empty. Starting from scratch.")
            os.remove(progress_file)  # Remove empty file
            return 0, []  # Start from scratch
        try:
            with open(progress_file, 'r') as f:  # open for reading and save as f
                progress_data = json.load(f)
                if progress_data.get('sucess', True):
                    print('True')
                    with open(progress_file, 'w') as f:
                        f.truncate(0)  # clean it for new run

                    return 0, []
                issues=[]
                print('False')
                count=0
                data_json=progress_data.get('issues', [])
                # for data in data_json:
                if isinstance(data_json, str):
                    data_json = json.loads(data_json)
                print(type(data_json))


                # issue_a=json.loads(data_json)
                issue_a=data_json
                #issue_a =json.loads(progress_data['issues'])
                print(issue_a)
                for issue_data in issue_a:
                    print("restoring")
                    print(count)
                    count+=1
                    print(type(issue_data))
                    # issue = dict_to_issue(json.loads(issue_data))
                    issue = dict_to_issue(issue_data)
                    print(type(issue))
                    #print(issue)
                    issues.append(issue)
                print("done restore")
                return progress_data.get('last_request', 0),issues  # defult values 0 and empty list
        except json.JSONDecodeError:
            # if there was a problem with the file delete it and start over
            print("Error decoding issue_data" )
            os.remove(progress_file)

    return 0, []  # f there isnt a file we will start from zero


# save the issues we pulled and the num req
def save_progress(last_request, issues,sucess=True):
    issues_dict=[]
    for issue in issues:
        issues_dict.append(issue_to_dict(issue))
    issue_dict_json=json.dumps(issues_dict)
    with open(progress_file, 'w') as f:  #open for writing
        json.dump({'last_request': last_request, 'issues': issue_dict_json, 'sucess': sucess}, f)
       # f.flush()


# a program might stop run and signal( intentional termination) or by exception
def analyze_issues_8_secure():
    # global variables
    global issues_global
    global last_requ

    # num of reqs that need to be done
    max_req=8
    issue_num=200
    num_reqs=issue_num//max_req  # round up
    last_request, issues = read_saved_progress()
    issues_global=issues
    last_requ = last_request

    try:
        for i in range(last_request, num_reqs):
            start = i * 8  # start index to pull
            issue_var = jira.search_issues(
                f'project={project_key}',
                startAt=start,
                maxResults=8
            )
            issues.extend(issue_var)
            issues_global = issues
            last_requ = i
            save_progress(i, issues, True)
            print(i)
        server_counter = Counter()
        # count issues for each server
        # if there is unvalid server name add that to the unvalid count
        for issue in issues:
            server_name = extract_server_name(issue.fields.description)
            server_counter[server_name] += 1  # if the name isnt valid add 1 to unvalid

        display_results(server_counter)
    except Exception as e:
        print(f"Error processing issue #{i}: {e}")
        save_progress(i, issues, sucess=False)


# to save in the json file we can only save dict and convert to string
def issue_to_dict(issue):

    return {
        'project': issue.fields.project.key,
        'summary': issue.fields.summary,
        'description': issue.fields.description,
        'issuetype': {'name':issue.fields.issuetype.name},
    }


# to convert the dict from the json file back to issue
def dict_to_issue(issue_dict):
    issue1 = jira.create_issue(fields=issue_dict)
    print('issue1')
    print(issue1)
    return issue1


# make sure the issues are kept in the file if the write was stopped in the middle
def handle_interrupt(signal,frame):
    print("\nProcess interrupted. Saving progress...")
    issues_dict = []
    for issue in issues_global:
        issues_dict.append(issue_to_dict(issue))
    issue_dict_json = json.dumps(issues_dict)
    with open(progress_file, 'w') as f:  # open for writing
        json.dump({'last_request': last_requ, 'issues': issue_dict_json, 'sucess': False}, f)
    sys.exit(0)


# catch a stop signal and handle by handle func
signal.signal(signal.SIGINT, handle_interrupt)


if __name__ == '__main__':
    # phase 1
    # to create issues run create issues func:
    create_issues()
    # 200 issues were created!

    # if you want to delete the issues use the delete func:
    # delete_issues()

    # phase 2
    # to analyze the issues run the analysis func
    # analyze_issues()

    # phase 3
    # to analyze the issues run the analysis func that pull 8 issues in each req
    # analyze_issues_8()

    # phase 4
    # to analyze the issues run the analysis func that pull 8 issues in each req
    # if you stop the program in the middle of the run the issues you already pulled will be saved
    # analyze_issues_8_secure()
