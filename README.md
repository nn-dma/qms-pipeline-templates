## CONTRIBUTORS ZONE - Submitting a PR to the QMS Team 

## Update cli code
 
> NOTE: We use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/), which means [semantic commit messages](https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716). Please adhere to these prefixes. Pull requests must also have a semantic prefix, e.g. 'feat:' or 'fix:'. If you are doing multiple changes at once, you are probably doing too much at once. Opt for smaller but more pull requests.

1. Fork this repo. 
2. If you are changing of the go code, please recompile the code according to
   your local machine architecture:

```
make build-linux-amd64 -- Linux
make build-darwin-arm64 -- MacOS
```
3. If your changes modify in any way the scaffolding of the generated ADO
   pipeline, you need to test that the generated pipeline looks as expected and
that you can run both CI and CD flow. There are more then one way of doing this, but here is an [automated way](https://github.com/innersource-nn/qms-cli/blob/main/TESTING_CLI_CHANGES.md). 
5. Commit and push to your forked repo.
6. Create a PR, contact the [QMS TEAM](https://docs.qms.novonordisk.cloud/Guides/reference/QMS_team) and actively ask for code review. Please, briefly provide testing evidence of your changes. 
7. The PR creation will trigger the [PR pipeline](https://github.com/innersource-nn/qms-cli/actions/workflows/pr_flow.yml) that simply tests that the go code can be executed. 
8. QMS Team will review the changes and possibly merge them.
9. QMS team will bump the qms-cli version as described in the following. 

> NOTE The following guide is showing a manual process. Some minimal automation for publishing a new cli version is available [here](https://github.com/innersource-nn/qms-cli/blob/main/RELEASE_AUTOMATION.md)

# QMS TEAM ZONE - Publishing new version
 
We distinguish two cases that are meant to be kept separated at all times:

- [Update qms-cli code and publish a new cli](https://github.com/innersource-nn/qms-cli?tab=readme-ov-file#update-cli-code-and-publish-a-new-qms-cli).

- [Point to latest qms-pipeline-templates tag and publish a new qms-cli](https://github.com/innersource-nn/qms-cli?tab=readme-ov-file#point-to-latest-qms-pipeline-templates-tag-and-publish-a-new-qms-cli).

## Publish the latest cli version

After you completed the development on main branch or merged a PR to main,
ensure your git status is clean and that everything has been pushed to main.
Then follow the steps:

1. Amend the version.txt file and bump the version, or edit the version to your
   liking
2. Add version.txt to staging area
```
git add version.txt
```
3. Commit the change with the following commit message:
```
git commit -m "feat: bumping cli to version <your version>"
```
4. Push to origin
```
git push origin
```
5. Tag the latest commit with the same version as in the version file
```
git tag <your version>
```
6. Push the tag to origin

After pushing the tag, the release flow will be initiated. A desciption os such flow is available at the end of this page in the section called [release flow](https://github.com/innersource-nn/qms-cli?tab=readme-ov-file#release-flow).


## Point to latest qms-pipeline-templates tag and publish a new qms-cli
>WARNING: Please, carefully test your changes before pointing to new pipeline
>templates tag and publishing a new cli version as you will be affecting all
>QMS pipeline adopters.

In case you applied some changes to the pipeline templates, you need the qms cli to point
to the latest templates tag in this very repo.

Ensure your git status is clean and that you are aligned with origin.
Then follow the steps:

1. Amend the version.txt file and bump the qms-cli version, or edit the version to your
   liking
2. Add version.txt to staging area
```
git add version.txt
```
3. Edit the file cmd/generators/service.go and go to line containing the
   pipeline template version and bump it or edit it to your liking

4. Add cmd/generators/service.go
```
git add cmd/generators/service.go
```

> NOTE: please, keep in mind that pipeline templates version and qms-cli
> versions are different!!

5. Commit the change with the following commit message:
```
git commit -m "feat: point to pipeline templates <your_pipeline_templates_version>"
```
4. Push to origin
```
git push origin
```
5. Tag the latest commit with the same version as in the version file i.e. the
   qms-cli version
```
git tag <your_cli_version>
```
6. Push the tag to origin

After completion of the script, the release flow will be initiated. A desciption os such flow is available at the end of this page in the section called [release flow](https://github.com/innersource-nn/qms-cli?tab=readme-ov-file#release-flow).

## Release flow

The code and tags will be pushed to origin. This will trigger first the [release action](https://github.com/innersource-nn/qms-cli/actions/workflows/release.yml) (code is available [here](https://github.com/innersource-nn/qms-cli/blob/main/.github/workflows/release.yml)). The downstream will trigger the following [deployment flow](https://github.com/innersource-nn/qms-cli/actions/workflows/deploy.yml) which will publish the newest compiled executables and deploy them to S3 bucket (qms-cli-bucket). Upon completion, the new version is ready to be promoted to latest. For doing so, go to [tag](https://github.com/innersource-nn/qms-cli/tags), edit the specific tag, edit, uncheck "Set as pre-release" and check "Set as the latest release", then click on "Update release". This will trigger the [promotion flow](https://github.com/innersource-nn/qms-cli/actions/workflows/latest.yml).
Upon successful completion, the newest version can be installed with the
following curl command.

```
/bin/bash -c "$(curl -fsSL http://d2riyn1pwby5r0.cloudfront.net/install-qms-cli.sh)"
```

After installation, verify that the cli version is correct by running 

```
qms-cli version
```

Congratulations, you published the latest qms-cli!
