import sys
import glob
import os
import subprocess


def extract_design_specification_tags(lines):
    tags = []
    readTags = False
    for i, line in enumerate(lines):
        if 'tags:' in line:
            # tags:
            readTags = True
        if readTags:
            #   - service_now_integration
            if '- ' in line:
                tags.append(line.split('- ')[1].strip())
    #print(tags)
    return tags

# def extract_current_remote_branch():
#     # git branch remote
#     result = subprocess.run(['git', 'branch', '-r'], stdout=subprocess.PIPE)
#     return result.stdout.decode().strip()

def extract_last_modified_commit_hash(filepath, branch):
    # git log <remote branch> -n 1 --pretty=format:%H -- <filepath>
    #result = subprocess.run(['git', 'log', extract_current_remote_branch(), '-n', '1', '--pretty=format:%H', '--', filepath], stdout=subprocess.PIPE)
    result = subprocess.run(['git', 'log', branch, '-n', '1', '--pretty=format:%H', '--', filepath], stdout=subprocess.PIPE)
    return result.stdout.decode()

def extract_last_modified_commit_hash_timestamp(commit_hash):
    # git show -s --format=%cd --date=format:'%Y-%m-%d %H:%M:%S' <commit_hash>
    result = subprocess.run(['git', 'show', '-s', '--format=%cd', "--date=format:'%Y-%m-%d %H:%M:%S'", commit_hash], stdout=subprocess.PIPE)
    return result.stdout.decode()

# TODO: Add exception handling
def main(argv):
    # Guard clause, no arguments provided
    if len(argv) == 0:
        print("No arguments provided")
        exit(1)

    # 2. Check for the arg pattern:
    #   python3 render_design_specifications.py -folder <filepath>
    #   e.g. 
    #       argv[0] is '-folder'
    #       argv[1] is './system_documentation/docs/design'
    if len(argv) > 1 and argv[0] == '-folder' and argv[2] == '-branch':
        # Render all design specifications
        # Find all .md files in the folder and subfolders
        path = r'%s/**/*.md' % argv[1]
        files = glob.glob(path, recursive=True)

        # Get the current branch
        branch = argv[3]

        # Render the table header and the table body element
        print('''<figure>
    <table>
        <thead>
            <tr>
                <th scope="col">#</th>
                <th scope="col">Design specification</th>
                <th scope="col">Version</th>
                <th scope="col">Last modified</th>
                <th scope="col">Trace to requirements</th>
            </tr>
        </thead>
        <tbody>''')

        count_design_specifications = 0
        for file in files:
            #print(f"File: {file}")
            last_modified_commit_hash = extract_last_modified_commit_hash(file, branch)
            last_modified_commit_hash_timestamp = extract_last_modified_commit_hash_timestamp(last_modified_commit_hash).strip().replace("'", "")

            with open(file, mode='r', encoding='utf-8') as file_reader:
                lines = file_reader.read().split('\n')
                design_specification_tags = extract_design_specification_tags(lines)

                count_design_specifications += 1
                print(f'''            <tr>
                <th scope="row">{count_design_specifications}</th>
                <td>{os.path.abspath(file).replace(os.getcwd(), "")}</td>
                <td>{last_modified_commit_hash}</td>
                <td>{last_modified_commit_hash_timestamp}</td>
                <td>{ '<kbd>' + '</kbd><kbd>'.join(design_specification_tags) + '</kbd>' if design_specification_tags else '' }</td>
            </tr>''')

        # Render the table body close elements
        print('''        </tbody>
    </table>
</figure>''')

if __name__ == "__main__":
   main(sys.argv[1:])