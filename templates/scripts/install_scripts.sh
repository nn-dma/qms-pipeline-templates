#!/bin/bash

files=$(ls $1/*)

echo $files

git gc --force --quiet

instScript=false
instScript_files=()

sha_id=""
for tag in $(git tag --sort=-creatordate); do
  if [[ $tag == *#released* ]]; then
    echo "Last released tag: $tag"
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

