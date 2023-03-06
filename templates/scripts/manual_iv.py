import sys
import glob
import re
from behave.runner_util import parse_features, collect_feature_locations
from behave.configuration import Configuration


def build_feature_files(feature_files_path):

    # Parse features
    config = Configuration(feature_files_path)
    locations = collect_feature_locations(config.paths)
    features = parse_features(locations)

    return features


def check_for_manual_tags(features):

    # Build list of features in feature files
    allowlist = ["manualIV"]
    taglist = [feature.tags for feature in features]
    manual_tags = [
        tag for tags in taglist for tag in tags if tag in allowlist
    ]

    return manual_tags


if __name__ == "__main__":

    feature_files_path = sys.argv[1]
    
    # Build a list of all URS_IDs in the features files
    features = build_feature_files(feature_files_path)
    feature_tags = check_for_manual_tags(features)
    
    if len(feature_tags) == 0:
        print(f"No manual tags found. This stage can be skipped")        
    else:
        print(f"The following manual tags were found in the .feature files: {feature_tags}")
        sys.exit(100)
