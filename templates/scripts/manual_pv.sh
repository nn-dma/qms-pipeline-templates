!/bin/bash

files=$(find $1 -name "*.feature")

git gc --force --quiet

instScript=false
instScript_files=()

first_commit=$(git describe --match "*#released" --abbrev=0 --tags $(git rev-list --tags --max-count=1))

# If no release tags are found, then search for initial commit
if [  -z $first_commit ]
then
    first_commit=$(git rev-list --max-parents=0 HEAD)
fi

sha_id=$(git rev-list -n 1 $first_commit)

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

