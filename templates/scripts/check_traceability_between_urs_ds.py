import sys
import glob
import re
import json

from behave.runner_util import (
    parse_features,
    collect_feature_locations,
)
from behave.configuration import Configuration


def build_feature_files(feature_files_path):

    # Parse features
    config = Configuration(feature_files_path)
    locations = collect_feature_locations(config.paths)

    features = parse_features(locations)

    return features, locations


def ensure_id(features, allowlist):
    """
    Check that every feature has an ID, outside the allowlist
    """
    for ii in features:

        # Only check URS features
        if "URS" not in ii.tags:
            continue

        tag_on_feature = [tag for tag in ii.tags if tag not in allowlist]

        if len(tag_on_feature) < 1:
            raise Exception(f"Every feature needs unique ID: {ii} does not contain ID")

    print("ID check successful. All URSs have IDs.")


def ensure_tag_coverage(features):
    """
    Check presence of IV and pIV tags
    """
    # Nested comprehension to pick out all tag combinations for all scenarios
    tags = [
        tags
        for feature in features
        for scenario in feature.scenarios
        for tags in scenario.tags
    ]
    assert "IV" in tags, "IV must be among scenario tags"

    assert "pIV" in tags, "pIV must be among scenario tags"

    print("IV and pIV are both mentioned in .feature files")


def ensure_urs_scenarios(features):
    """
    Ensure URS features have test cases
    """
    for feature in features:
        if "URS" in feature.tags:
            assert len(feature.scenarios) > 0, "URS features must have test cases"
            tagged_pv = [
                scenario.tags for scenario in feature.scenarios if "PV" in scenario.tags
            ]
            assert (
                len(tagged_pv) > 0
            ), "URS features must have at least one test case tagged with PV"

    print("URS features have test cases")


def ensure_review_by_exception_rationale(features, locations):
    """
    Check that a rationale have been provided for @ReviewByException tags
    """
    for location, feature in zip(locations, features):

        # Get nr of scenarios tagged with ReviewByException
        nr_exceptions = len(
            [
                tag
                for scenario in feature.scenarios
                for tag in scenario.tags
                if tag == "ReviewByException"
            ]
        )

        if nr_exceptions > 0:

            f = open(location.filename, "r")
            text = f.read()

            # Regex to capture comment block between tags and Scenario
            rationale = re.findall(
                r".*@ReviewByException.*\n(?:\s*#.*\n)+\s*Scenario:", text
            )
            assert nr_exceptions == len(
                rationale
            ), "Every ReviewByException needs a rationale"
    print("All ReviewByException scenarios have rationales")


def ensure_step_implementations(features):

    """
    This is probably not feasible, as we need to actually load the step implementation,
    which means we would need to inherit transitive dependencies of the consuming project.
    """
    pass


def construct_non_generic_tag_list(features, allowlist):

    # Build list of features in feature files
    taglist = [feature.tags for feature in features]

    non_classification_tags = [
        tag for tags in taglist for tag in tags if tag not in allowlist
    ]

    return non_classification_tags


def check_uniqueness_of_requirements(tags):

    # Check if the length is the same
    if len(tags) == len(set(tags)):
        return True
    else:
        return False


def get_tags_of_markdown_files(docs_path):

    markdown_files = glob.glob(docs_path + "/**/*.md", recursive=True)

    taglist = []
    for file in markdown_files:
        f = open(file, "r")
        text = f.read()
        tags = [ii.replace("  - ", "") for ii in re.findall(r"  - \w\S*", text)]
        taglist.extend(tags)

    # print(taglist)
    return taglist


def check_mention_of_tags_in_ds(tags, req_tags):

    in_requirements = []
    for ii in req_tags:
        if ii in tags:
            in_requirements.append(True)
        else:
            in_requirements.append(False)

    return all(x in tags for x in req_tags), in_requirements


if __name__ == "__main__":

    feature_files_path = sys.argv[1]
    docs_path = sys.argv[2]

    # print(sys.argv[3])

    # if len(sys.argv) > 2:
    try:
        exclude_tags = json.loads(sys.argv[3])
    except:
        exclude_tags = []

    allowlist = ["URS", "GxP", "non-GxP", "CA", "IV"] + exclude_tags

    # print(exclude_tags)

    # Build a list of all URS_IDs in the features files
    features, locations = build_feature_files(feature_files_path)

    # Ensure all features have IDs
    ensure_id(features, allowlist)

    # Ensure IV
    ensure_tag_coverage(features)

    # Ensure every URS feature has at least one scenario
    ensure_urs_scenarios(features)

    # Ensure rationale for @ReviewByException
    ensure_review_by_exception_rationale(features, locations)

    feature_tags = construct_non_generic_tag_list(features, allowlist)
    # print(f"The following URS IDs were found in the .feature files: {feature_tags}")

    # Check for duplicates in the URS_IDs
    unique = check_uniqueness_of_requirements(feature_tags)

    if not unique:
        raise Exception("Duplicates in identifiers")

    # Build a list of all the tags used in the design
    docs_tags = get_tags_of_markdown_files(docs_path)
    # print(f"The following URS IDs are referenced in the documentation: {docs_tags}")

    # Verify that all urs_ids have references to design - i.e. all urs_ids need to be in design tags
    in_ds, check_list = check_mention_of_tags_in_ds(docs_tags, feature_tags)
    bad_list = [kk for ii, kk in enumerate(feature_tags) if not check_list[ii]]

    if not in_ds:
        raise Exception(f"Unique IDs: {bad_list} not in design specification")
    else:
        print(
            "Traceability check successful. All URS IDs are unique and referenced in the documentation."
        )
