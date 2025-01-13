import json
import requests
import base64
from datetime import datetime
import sys
import os
from pprint import pprint


def link_work_item(work_item, auth_method, access_token, organization):
    url = f"https://dev.azure.com/{organization}/_apis/wit/workitems/{work_item}?api-version=7.0"  # noqa

    payload = [
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "ArtifactLink",
                "url": f"vstfs:///Build/Build/{os.getenv('BUILD_ID')}",
                "attributes": {
                    "comment": "Making a new link for the build",
                    "name": "Build",
                },
            },
        }
    ]
    print("************************************************")
    print("")
    print("Work Item:" + work_item)
    print("")
    print("Here is the payload used to query the work item:")
    print("")
    print(payload)

    headers = {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"{auth_method} {access_token}",
    }

    response = requests.request("GET", url, headers=headers, json=payload)
    print("")
    print("Here is the response from the work item query:")
    print("")
    pprint(response.json())
    print("")


# TODO: Add exception handling
def get_pull_request(
    commit_hash, auth_method, access_token, organization, project, repository
):
    url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/pullrequestquery?api-version=7.0"  # noqa
    payload = json.dumps(
        {"queries": [{"items": [f"{commit_hash}"], "type": "lastMergeCommit"}]}
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{auth_method} {access_token}",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def get_work_item_with_it_change_tag(
    commit_hash,
    auth_method,
    access_token,
    organization,
    project,
    repository,
    work_items,
):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{auth_method} {access_token}",
    }
    tagged_work_item_list = []
    for work_item in work_items:
        url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item}?api-version=7.0"  # noqa

        response = requests.request("GET", url, headers=headers)
        r = json.loads(response.text, strict=False)
        if ("System.Tags" in r["fields"].keys()) and (
            "IT Change" in r["fields"]["System.Tags"]
        ):
            tagged_work_item_list.append(r["_links"]["html"]["href"])
    return tagged_work_item_list


def work_item_sanity_check(tagged_work_item_list, verbose=False):
    if len(tagged_work_item_list) > 1:
        print(
            """
                There are more than one work item with IT Change tag.
                Exiting with failure.
            """
        ) if verbose else None
        sys.exit(1)
    elif len(tagged_work_item_list) == 0:
        print(
            "No work item with IT Change tag found. Exiting with failure."
        ) if verbose else None
        sys.exit(1)
    else:
        print(
            f"Work item with IT Change tag found: {tagged_work_item_list[0]}"
        ) if verbose else None


# TODO: Add exception handling
def get_pull_request_id(response, commit_hash):
    r = json.loads(response, strict=False)
    pull_request = r["results"][0][commit_hash][0]
    mergeCommitMessage = pull_request["completionOptions"][
        "mergeCommitMessage"
    ]
    pullRequestId = pull_request["pullRequestId"]
    return pullRequestId


def get_work_items(
    response,
    auth_method,
    access_token,
    commit_hash,
    organization,
    project,
    repository,
    pullRequestId,
):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{auth_method} {access_token}",
    }

    payload = json.dumps(
        {"queries": [{"items": [f"{commit_hash}"], "type": "lastMergeCommit"}]}
    )

    url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/pullRequests/{pullRequestId}/workitems?api-version=7.0"  # noqa
    response = requests.request("GET", url, headers=headers, data=payload)
    workItem = []
    for wi in response.json()["value"]:
        workItem.append(wi["id"])
    return workItem


# TODO: Add exception handling
def get_pull_request_closed_timestamp(response, commit_hash):
    r = json.loads(response, strict=False)
    pull_request = r["results"][0][commit_hash][0]
    pull_request_closed_timestamp = pull_request["closedDate"]
    return pull_request_closed_timestamp


def format_pull_request_timestamp(dt_string: str) -> str:
    # Remove precision
    # NOTE: This is done because Python .strptime supports 6 digit
    # precision on datetime strings,
    # but the one we get from Azure DevOps has 7 digits
    dt_string = dt_string.split(".")[0]
    # Convert to datetime object
    dt_object = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")
    # Format datetime object as string
    formatted_string = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_string


# TODO: Add exception handling
def main(argv):
    if (
        len(argv) == 12
        and argv[0] == "-commit"
        and argv[2] == "-accesstoken"
        and argv[4] == "-organization"
        and argv[6] == "-project"
        and argv[8] == "-repository"
        and argv[10] == "-result"
    ):
        # Create rendering for the test result
        commit_hash = argv[1]
        access_token = argv[3]
        organization = argv[5]
        project = argv[7]
        repository = argv[9]
        result = argv[11]

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
            access_token = base64.b64encode(
                f":{access_token}".encode()
            ).decode()

        response = get_pull_request(
            commit_hash,
            auth_method,
            access_token,
            organization,
            project,
            repository,
        )
        pull_request_id = get_pull_request_id(response, commit_hash)
        work_items = get_work_items(
            response,
            auth_method,
            access_token,
            commit_hash,
            organization,
            project,
            repository,
            pull_request_id,
        )
        pull_request_closed_timestamp = get_pull_request_closed_timestamp(
            response, commit_hash
        )
        tagged_work_item = get_work_item_with_it_change_tag(
            commit_hash,
            auth_method,
            access_token,
            organization,
            project,
            repository,
            work_items,
        )

        if result == "pull_request_id":
            print(pull_request_id)
        elif result == "pull_request_closed_timestamp":
            print(format_pull_request_timestamp(pull_request_closed_timestamp))
        elif result == "work_item_with_tag_link":
            if len(tagged_work_item) == 0:
                print("<kbd>!MISSING!</kbd>")
            else:
                print(
                    f"<kbd><a href=\"{tagged_work_item[0]}\">{tagged_work_item[0].rsplit('/',1)[1]}</a></kbd>"  # noqa
                )
        elif result == "work_item_with_tag":
            work_item_sanity_check(tagged_work_item, verbose=True)
        elif result == "work_item_list":
            [
                link_work_item(
                    work_item_id,
                    auth_method,
                    access_token,
                    organization,
                )
                for work_item_id in work_items
            ]
        else:
            print("Invalid result argument")


if __name__ == "__main__":
    main(sys.argv[1:])
