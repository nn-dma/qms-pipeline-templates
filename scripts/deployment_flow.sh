#!/bin/bash
set -e
echo
echo "We assume you are running macOS. If not, please amend the sed command in this script (sed -i '' -> sed -i)."
echo

last_tag=$(git describe --tags --abbrev=0)
last_number=$(echo $last_tag | grep -E -o "[0-9]*$")
next_number=$(($last_number + 1))
next_tag=$(echo ${last_tag} | sed -n "/[0-9]*$/s/[0-9]*$//p")$next_number
echo
echo "The latest qms-cli tag is $last_tag. Do you want to push the subsequent tag (y/n)?"
echo ${next_tag}
read var
if [ $var == "n" ]; then
 echo "If not, please provide your tag with format [0-9]+.[0-9]+.[0-9]+"
 read tag
else
  tag=$next_tag
fi

echo
echo "Tagging and pushing to origin.."
echo
git tag $tag
git push origin $tag
