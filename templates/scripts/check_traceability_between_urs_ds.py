import sys
import glob
import re
import json
from behave.runner_util import parse_features, collect_feature_locations
from behave.configuration import Configuration


def build_feature_files(feature_files_path):

    # Parse features
    config = Configuration(feature_files_path)
    locations = collect_feature_locations(config.paths)
    features = parse_features(locations)

    return features


def construct_non_generic_tag_list(features, exclude_list):

    # Build list of features in feature files
    allowlist = ["URS", "GxP", "non-GxP", "CA", "IV"] + exclude_list
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
        matches = re.findall(
            r"/---\ntags:\n\s+-\s+(\w+)\n(?:\s+-\s+(\w+)\n)*---/g", text
        )
        print(matches)
        for match in matches:
            print(match)
            tags = [tag for tag in match if tag]
            print(tags)
            taglist.extend(tags)

        # print(matches)

        # if len(matches) != 0:
        #     tags = [ii for ii in (matches)]
        #     taglist.extend(tags)

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

    print(sys.argv[3])

    if len(sys.argv) > 2:
        exclude_tags = json.loads(sys.argv[3])
    else:
        exclude_tags = []

    print(exclude_tags)

    # Build a list of all URS_IDs in the features files
    features = build_feature_files(feature_files_path)
    feature_tags = construct_non_generic_tag_list(features, exclude_tags)
    print(f"The following URS IDs were found in the .feature files: {feature_tags}")

    # Check for duplicates in the URS_IDs
    unique = check_uniqueness_of_requirements(feature_tags)

    if not unique:
        raise Exception("Duplicates in identifiers")

    # Build a list of all the tags used in the design
    docs_tags = get_tags_of_markdown_files(docs_path)
    print(f"The following URS IDs are referenced in the documentation: {docs_tags}")

    # Verify that all urs_ids have references to design - i.e. all urs_ids need to be in design tags
    in_ds, check_list = check_mention_of_tags_in_ds(docs_tags, feature_tags)
    bad_list = [kk for ii, kk in enumerate(feature_tags) if not check_list[ii]]

    if not in_ds:
        raise Exception(f"Unique IDs: {bad_list} not in design specification")
    else:
        print(
            "Traceability check successful. All URS IDs are unique and referenced in the documentation."
        )
