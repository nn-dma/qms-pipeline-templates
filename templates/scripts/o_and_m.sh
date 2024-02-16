#!/bin/bash

files=$(ls $1/*)

git gc --force --quiet

instScript=()
instScript_files=()

# sha_id=$(git rev-list -n 1 $(git describe --match "*#released" --abbrev=0 --tags $(git rev-list --tags --max-count=1)))
sha_id=""
for tag in $(git tag --sort=-creatordate); do
  if [[ $tag == *#released* ]]; then
    echo "Released tag: $tag"
    sha_id=$(git rev-list -n 1 $tag)
    break
  fi
done

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
