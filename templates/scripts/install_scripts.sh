#!/bin/bash

files=$(ls $1/*)

echo $files

git gc --force --quiet

instScript=false
instScript_files=()

# Get the commit sha_id of the last release
sha_id=""
for tag in $(git tag --sort=-creatordate); do
  if [[ $tag == *#released* ]]; then
    echo "Last released tag: $tag"
    sha_id=$(git rev-list -n 1 $tag)
    break
  fi
done

# If sha_id is still empty, get the first commit's SHA
if [ -z "$sha_id" ]; then
  sha_id=$(git rev-list --max-parents=0 HEAD)  # Get the first commit SHA
  echo "No matching released tags found. Using first commit SHA: $sha_id"
fi

for i in ${files[@]}; do
    code=$(
        git diff --quiet $sha_id HEAD -- $i
        echo $?
    )
    if [ $code == 1 ]; then
        instScript=true
        instScript_files+=($i)
    fi
done

echo $instScript_files

echo "list of Installation Scripts need to be executed: ${instScript_files[@]}"

if [ "$instScript" = true ] ; then
    echo "instScript=true"
else
    echo "instScript=false"
fi

