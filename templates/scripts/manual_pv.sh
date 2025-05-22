#!/bin/bash

files=$(find $1 -name "*.feature")

git gc --force --quiet

instScript=false
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
    code=`git diff $sha_id HEAD -- $i | grep ^'+' | grep -v "#" | grep "@PV" | grep -c "@manual"`
    if [ $code -ge 1 ]; then
        instScript=true
        instScript_files+=($i)
    fi
done

if [ "$instScript" = true ] ; then
    echo "list of files with new manual PV tags: ${instScript_files[@]}"
fi

