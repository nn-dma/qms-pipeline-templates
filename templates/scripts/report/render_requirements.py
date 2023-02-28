import sys
import glob
import os
import subprocess

# List of tags that are being removed when rendering the list of requirements, leaving only the unique ID(s)
RESERVED_TAGS = ["URS", "GxP", "non-GxP", "CA"]
class Feature:
    def __init__(self, name, description, tags):
        self.name = name
        self.description = description
        self.tags = tags

    def __repr__(self):
        # Prepare values for rendering
        featureDescription = '\n'.join(self.description)

        # Create rendering
        return f'''<div class="urs">
    <h6>{ self.tags }</h6>
    <h6>{ self.name }</h6>
    <p>{ featureDescription }</p>
</div>'''

def extract_features(lines):
    features = []
    for i, line in enumerate(lines):
        if '@URS' in line:
            fo = Feature(None, description=[], tags=line)
            for j in range(i + 1, len(lines)):
                feature_line = lines[j]
                if 'Feature:' in feature_line:
                    feature_name = feature_line.split('Feature:')[1].strip()
                    feature_description = lines[j + 1:j + 5]
                    fo.name = feature_name
                    fo.description = [desc.strip() for desc in feature_description if desc.strip()]
                    features.append(fo)
                    break

    return features

def extract_current_remote_branch():
    # git branch remote
    result = subprocess.run(['git', 'branch', '-r'], stdout=subprocess.PIPE)
    return result.stdout.decode().strip()

def extract_last_modified_commit_hash(filepath):
    # git log <remote branch> -n 1 --pretty=format:%H -- <filepath>
    #result = subprocess.run(['git', 'log', extract_current_remote_branch(), '-n', '1', '--pretty=format:%H', '--', filepath], stdout=subprocess.PIPE)
    result = subprocess.run(['git', 'log', 'origin/release/service1', '-n', '1', '--pretty=format:%H', '--', filepath], stdout=subprocess.PIPE)
    return result.stdout.decode()

def extract_last_modified_commit_hash_timestamp(commit_hash):
    # git show -s --format=%cd --date=format:'%Y-%m-%d %H:%M:%S' <commit_hash>
    result = subprocess.run(['git', 'show', '-s', '--format=%cd', "--date=format:'%Y-%m-%d %H:%M:%S'", commit_hash], stdout=subprocess.PIPE)
    return result.stdout.decode()

def remove_values_from_string(string, values):
    for value in values:
        string = string.replace(value, '')
    return string

def clean_tags(tags) -> list:
    tags = remove_values_from_string(tags, RESERVED_TAGS)
    tags = tags.replace('@', '')
    tags = tags.strip()
    return tags

# TODO: Add exception handling
def main(argv):
    # Guard clause, no arguments provided
    if len(argv) == 0:
        print("No arguments provided")
        exit(1)

    # 1. Check for the arg pattern:
    #   python3 get_requirements.py -features <filepath> -tags [<tag1>, <tag2> ...]
    #   e.g. 
    #       argv[0] is '-features'
    #       argv[1] is './../features'
    #       argv[2] is '-tags'
    #       argv[3] is 'tag1'
    #       argv[4] is 'tag2'
    # if len(argv) > 3 and argv[2] == '-tags':
    #     # Collect tags to render feature descriptions for
    #     print("Got -tags")
    #     for arg in argv[3:]:
    #         if arg[0] == '-':
    #             print(f"Unexpected argument: {arg}")
    #             exit(1)
    #         print(arg)

    # 2. Check for the arg pattern:
    #   python3 get_requirements.py -folder <filepath>
    #   e.g. 
    #       argv[0] is '-folder'
    #       argv[1] is './../features'
    if len(argv) > 1 and argv[0] == '-folder':
        # Render all feature descriptions
        # Find all .feature files in the folder and subfolders
        path = r'%s/**/*.feature' % argv[1]
        files = glob.glob(path, recursive=True)

        # Render the table header and the table body element
        print('''<figure>
    <table>
        <thead>
            <tr>
                <th scope="col">#</th>
                <th scope="col">Requirement ID</th>
                <th scope="col">Description title</th>
                <th scope="col">Version</th>
                <th scope="col">Last modified</th>
                <th scope="col">File</th>
            </tr>
        </thead>
        <tbody>''')

        count_features = 0
        for file in files:
            #print(f"File: {file}")
            last_modified_commit_hash = extract_last_modified_commit_hash(file)
            last_modified_commit_hash_timestamp = extract_last_modified_commit_hash_timestamp(last_modified_commit_hash).strip().replace("'", "")

            with open(file, mode='r', encoding='utf-8') as file_reader:
                lines = file_reader.read().split('\n')
                features = extract_features(lines)

                for feature in features:
                    count_features += 1
                    print(f'''            <tr>
                <th scope="row">{count_features}</th>
                <td><kbd>{clean_tags(feature.tags)}</kbd></td>
                <td>{feature.name}</td>
                <td>{last_modified_commit_hash}</td>
                <td>{last_modified_commit_hash_timestamp}</td>
                <td>{os.path.basename(file)}</td>
            </tr>''')
                    #print(f'<div><h6>{os.path.basename(file)}</h6>')
                    #print(feature)
                    #print('</div>')

        # Render the table body close elements
        print('''        </tbody>
    </table>
</figure>''')

if __name__ == "__main__":
   main(sys.argv[1:])