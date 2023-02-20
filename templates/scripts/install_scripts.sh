#!/bin/bash

files=$(ls $1/*)

echo $files

git gc --force --quiet

instScript=()
instScript_files=()

sha_id=$(git rev-list -n 1 $(git describe --match "*#released" --abbrev=0 --tags $(git rev-list --tags --max-count=1)))

for i in ${files[@]}; do
    code=$(
        git diff --quiet $sha_id HEAD -- $i
        echo $?
    )
    if [ $code == 1 ]; then
        instScript='true'
        instScript_files+=($i)
    fi
done

echo $instScript_files

echo "list of Installation Scripts need to be executed: ${instScript_files[@]}"

if [[ " ${instScript[*]} " =~ " true " ]]; then
    echo "instScript=true"
fi

if [[ ! " ${instScript[*]} " =~ " true " ]]; then
    echo "instScript=false"
fi
