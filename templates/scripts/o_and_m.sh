#!/bin/bash

files=$(ls $1/*)

git gc --force --quiet

instScript=()
instScript_files=()


# Get the commit sha_id of the last release
sha_id=""
for tag in $(git tag --sort=-creatordate); do
  if [[ $tag == *#released* ]]; then
    # echo "Last released tag: $tag"
    sha_id=$(git rev-list -n 1 $tag)
    break
  fi
done

# If sha_id is still empty, get the first commit's SHA
if [ -z "$sha_id" ]; then
  sha_id=$(git rev-list --max-parents=0 HEAD)  # Get the first commit SHA
  # echo "No matching released tags found. Using first commit SHA: $sha_id"
fi

for i in ${files[@]}; do
    code=$(
        git diff --quiet $sha_id HEAD -- $i
        echo $?
    )
    if [ $code == 1 ]; then
        instScript='true'
        instScript_files+=("$i\n")
    fi
done

if [ "$instScript" = true ] ; then
    echo -e "Please verify the following list of operation files:\n ${instScript_files[@]}"
fi
