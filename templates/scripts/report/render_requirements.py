import base64
import glob
import os
import subprocess
import sys

import requests
import yaml


# List of tags that are being removed when rendering the list of requirements, leaving only the unique ID(s)
RESERVED_TAGS = ["URS", "GxP", "non-GxP", "CA"]


class Feature:
    def __init__(self, name, description, tags):
        self.name = name
        self.description = description
        self.tags = tags


def extract_features(lines):
    features = []
    for i, line in enumerate(lines):
        if "@URS" in line:
            fo = Feature(None, description=[], tags=line)
            for j in range(i + 1, len(lines)):
                feature_line = lines[j]
                if "Feature:" in feature_line:
                    feature_name = feature_line.split("Feature:")[1].strip()
                    feature_description = lines[j + 1 : j + 5]
                    fo.name = feature_name
                    fo.description = [
                        desc.strip() for desc in feature_description if desc.strip()
                    ]
                    features.append(fo)
                    break

    return features


def extract_last_modified_commit_hash(filepath, branch):
    # git log <remote branch> -n 1 --pretty=format:%H -- <filepath>
    result = subprocess.run(
        ["git", "log", branch, "-n", "1", "--pretty=format:%H", "--", filepath],
        stdout=subprocess.PIPE,
    )
    return result.stdout.decode()


def extract_last_modified_commit_hash_timestamp(commit_hash):
    # git show -s --format=%cd --date=format:'%Y-%m-%d %H:%M:%S' <commit_hash>
    result = subprocess.run(
        [
            "git",
            "show",
            "-s",
            "--format=%cd",
            "--date=format:'%Y-%m-%d %H:%M:%S'",
            commit_hash,
        ],
        stdout=subprocess.PIPE,
    )
    return result.stdout.decode()


def remove_values_from_string(string, values):
    for value in values:
        string = string.replace(value, "")
    return string


def clean_tags(tags) -> list:
    tags = remove_values_from_string(tags, RESERVED_TAGS)
    tags = tags.replace("@", "")
    tags = tags.strip()
    return tags


def render_tags(tags) -> str:
    tags = clean_tags(tags)
    tags = tags.split(" ")
    tags = [f"<kbd>{tag}</kbd>" for tag in tags]
    return "".join(tags)


def get_pull_requests(
    base_url: str,
    auth_method: str,
    access_token: str,
    branch: str,
    api_version: str = "7.1",
) -> list[dict]:
    """Get all pull requests which have the current branch as target."""

    url = f"{base_url}/pullRequests?searchCriteria.status=completed&api-version={api_version}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{auth_method} {access_token}",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        pull_requests = response.json().get("value", [])
        # Remove the origin/ from the branch name
        branch = branch.replace("origin/", "")
        # Filter for only the ones into the current (release) branch
        pull_requests = [
            pr for pr in pull_requests if pr["targetRefName"] == f"refs/heads/{branch}"
        ]
        # TODO: Sort by time? Or maybe just PR ID?
        return pull_requests
    else:
        return []


def match_commit_with_pr(
    base_url: str,
    auth_method: str,
    access_token: str,
    pull_requests: list[dict],
    commit_id: str,
    api_version: str = "7.1",
) -> tuple[str, str] | None:
    """Find the pull request which contains a given commit id."""

    # Go through PRs
    for pr in pull_requests:
        # Get all commits for the PR
        url = f"{base_url}/pullRequests/{pr['pullRequestId']}/commits?api-version={api_version}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{auth_method} {access_token}",
        }
        response = requests.get(url, headers=headers)
        pr_commits = response.json().get("value", [])
        # If the commit id is in the PR commits, return the PR id and completion date
        if any(commit["commitId"] == commit_id for commit in pr_commits):
            # Remove milliseconds
            completion_date = pr["closedDate"].split(".")[0] + "Z"
            return (pr["pullRequestId"], completion_date)
    return None


def get_approvers(pr_id: str, pull_requests: list[dict]) -> list[str]:
    """Get the approvers for a given pull request."""

    for pr in pull_requests:

        if pr["pullRequestId"] == pr_id:
            reviewers = pr["reviewers"]
            approvers = [
                reviewer["uniqueName"]
                for reviewer in reviewers
                if reviewer["vote"] == 10
            ]
            return approvers
    else:
        return []


def get_approver_roles(approvers: list[str], roles: dict) -> list[str]:
    """Get the roles of the approvers by matching initials in the roles.yml
    file.
    """
    approvers_with_roles = []
    for approver in approvers:
        # Try to get the roles of the approvers
        if (initials := approver.split("@")[0].lower()) in roles:
            approvers_with_roles.append(
                f"{roles[initials]['name']}, {roles[initials]['role']}"
            )
        else:
            approvers_with_roles.append(approver)
    return approvers_with_roles


# TODO: Add exception handling
def main(argv):
    # Guard clause, no arguments provided
    if len(argv) == 0:
        print("No arguments provided")
        exit(1)
    # Guard clause, too few arguments provided
    if len(argv) < 14:
        print("Not all required arguments provided")
        exit(1)

    # 1. Check for the arg pattern:
    #   python3 get_requirements.py -folder <filepath> -branch <remote branch> -organization <organization> -project <project> -repository <repository> -accesstoken <access token> -roles <roles file>
    #   e.g.
    #       argv[0] is '-folder'
    #       argv[1] is './../features'
    #       argv[2] is '-branch'
    #       argv[3] is 'origin/release/service1'
    #       argv[4] is '-organization'
    #       argv[5] is 'novonordiskit'
    #       argv[6] is '-project'
    #       argv[7] is 'Data Management and Analytics'
    #       argv[8] is '-repository'
    #       argv[9] is 'QMS-TEMPLATE'
    #       argv[10] is '-accesstoken'
    #       argv[11] is 'USE_ENV_VARIABLE'
    #       argv[12] is '-roles'
    #       argv[13] is 'roles.yml'
    if (
        len(argv) == 14
        and argv[0] == "-folder"
        and argv[2] == "-branch"
        and argv[4] == "-organization"
        and argv[6] == "-project"
        and argv[8] == "-repository"
        and argv[10] == "-accesstoken"
        and argv[12] == "-roles"
    ):

        # Render all feature descriptions
        # Find all .feature files in the folder and subfolders
        path = r"%s/**/*.feature" % argv[1]
        files = glob.glob(path, recursive=True)

        # Get the current branch
        branch = argv[3]
        organization = argv[5]
        project = argv[7]
        repository = argv[9]
        access_token = argv[11]
        role_file = argv[13] if argv[13] != "" else None

        # URL encode the project name
        project = project.replace(" ", "%20")

        # Use environment variable to read the protected access token
        # if we are running in Azure DevOps
        auth_method = "Basic"
        if access_token == "USE_ENV_VARIABLE":
            access_token = os.environ["SYSTEM_ACCESSTOKEN"]
            auth_method = "Bearer"
        # If auth method is "Basic", we are most likely running
        # outside Azure DevOps, so we need to encode the
        # access token as password in a Basic HTTP Auth header format
        if auth_method == "Basic":
            # Base64 encode userid:password, which is empty (no user id) and
            # the access_token value in a string "<user_id>:<access_token>",
            # e.g. ":12345678".
            access_token = base64.b64encode(f":{access_token}".encode()).decode()

        # Render the table header and the table body element
        print(
            """<figure>
    <table>
        <thead>
            <tr>
                <th scope="col">#</th>
                <th scope="col">Requirement ID</th>
                <th scope="col">Descriptive title</th>
                <th scope="col">Version</th>
                <th scope="col">Last modified</th>
                <th scope="col">File</th>
            </tr>
        </thead>
        <tbody>"""
        )

        # Part 1: Get table with requirement details
        count_features = 0
        for file in files:
            last_modified_commit_hash = extract_last_modified_commit_hash(file, branch)
            last_modified_commit_hash_timestamp = (
                extract_last_modified_commit_hash_timestamp(last_modified_commit_hash)
                .strip()
                .replace("'", "")
            )

            with open(file, mode="r", encoding="utf-8") as file_reader:
                lines = file_reader.read().split("\n")
                features = extract_features(lines)
                # Extract the path to the feature file, e.g.:
                # /requirements/features/urs/functionality1.feature
                repository_file_path = os.path.abspath(file).replace(os.getcwd(), "")
                # Create link to path for file, e.g.:
                # https://dev.azure.com/novonordiskit/Data%20Management%20and%20Analytics/_git/QMS-TEMPLATE/commit/d78d1bf6bd41b07f654c6b8178fb85b4490853f3?path=/requirements/features/urs/reverse-string-feat.feature
                repository_file_link = f"https://dev.azure.com/{organization}/{project}/_git/{repository}/commit/{last_modified_commit_hash}?path={repository_file_path}"

                for feature in features:
                    count_features += 1
                    print(
                        f"""            <tr>
                <th scope="row">{count_features}</th>
                <td>{render_tags(feature.tags)}</td>
                <td>{feature.name}</td>
                <td>{last_modified_commit_hash}</td>
                <td>{last_modified_commit_hash_timestamp}</td>
                <td><a href="{repository_file_link}" target="_blank">{repository_file_path}</a></td>
            </tr>"""
                    )

        # Render the table body close elements
        print(
            """        </tbody>
    </table>"""
        )

        # Part 2: Print feature files with approvers

        # Load role yaml file if provided
        if role_file:
            with open(role_file, "r") as file:
                roles = yaml.safe_load(file)

        # Base URL for Azure DevOps REST API
        base_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}"

        pull_requests = get_pull_requests(base_url, auth_method, access_token, branch)

        for file in files:

            with open(file, mode="r", encoding="utf-8") as file_reader:
                lines_raw = file_reader.read()
                lines = lines_raw.split("\n")
                features = extract_features(lines)

            pr_id, completion_date = match_commit_with_pr(
                base_url,
                auth_method,
                access_token,
                pull_requests,
                last_modified_commit_hash,
            )
            approvers = get_approvers(pr_id, pull_requests)

            if role_file:
                approvers = get_approver_roles(approvers, roles)

            for feature in features:
                print(
                    f"""    <h4>{render_tags(feature.tags)}</h4>
    <pre>{lines_raw}</pre>
    <p>Approved at: {completion_date}</p>
    <p>Approvers:</p>
    <ul>"""
                )
                for approver in approvers:
                    print(f"        <li>{approver}</li>")
                print("""    </ul>""")
        print("</figure>")


if __name__ == "__main__":
    main(sys.argv[1:])
