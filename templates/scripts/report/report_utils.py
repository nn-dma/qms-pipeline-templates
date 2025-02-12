import subprocess

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
