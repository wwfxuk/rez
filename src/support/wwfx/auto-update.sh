#!/bin/bash
set -eux -o pipefail

FAILED=()
REBASED=()
MERGED_TEXT=""
WWFX_REMOTE="${WWFX_REMOTE:-wwfxuk}"
WWFX_REMOTE_REPO="$(git remote get-url $WWFX_REMOTE | sed -n '/.*github\.com/ { s|.*github.com.||; s/\.git.*//p; q}')"
LATEST_TAG="${LATEST_TAG:-2.60.0}"
WWFX_MASTER="$WWFX_REMOTE"/master
COMMON_PARENT="$(git merge-base $LATEST_TAG $WWFX_MASTER)"

readarray -t MERGES < <(
    git log --format="%D" "$COMMON_PARENT".."$WWFX_MASTER" \
    | sed -n "/tag/d; s/, /,/p"
)

fix_interactively() {
    echo "Fix and continue rebasing until finished"
    echo "      If finished successfully, run: exit"
    echo "                          else, run: exit 100"
    bash -i
}

for MERGE_BRANCH in "${MERGES[@]}"
do
    BRANCH="${MERGE_BRANCH##*,}"
    UPSTREAM="${MERGE_BRANCH%%,*}"
    REMOTE="${UPSTREAM%%/*}"
    # Set branch to upstream if empty, also check upstream has branch name
    [ -n "$BRANCH" ] || [ -z "${UPSTREAM#*/}" ] || {
        BRANCH="${UPSTREAM#*/}"
        git checkout -B "$BRANCH" "$UPSTREAM"
    }

    [ -z "$BRANCH" ] || if git rebase --onto "$LATEST_TAG" "$COMMON_PARENT" "$BRANCH"
    then
        REBASED+=("$BRANCH")
        COMMIT="$(git rev-parse --short ${BRANCH})"
        [ -z "$REMOTE" ] && MERGED_TEXT+="- ${COMMIT} from \`${BRANCH}\`.\n" || {
            echo git push -uf "$REMOTE" "$BRANCH":"${UPSTREAM#*/}" && {
                GITHUB_REPO="$(git remote get-url ${REMOTE} | sed -n '/.*github\.com/ { s|.*github.com.||; s/\.git.*//p; q}')"
                [ -z "$GITHUB_REPO" ] || MERGED_TEXT+="- ${COMMIT} from [${BRANCH}](https://github.com/${GITHUB_REPO}/tree/${BRANCH}).\n"
            }
        }
    else
        [ -t 0 ] && [ -t 1 ] && fix_interactively && REBASED+=("$BRANCH") || {
            git rebase --abort || :
            FAILED+=("$BRANCH")
        }
    fi
done

[ "${#FAILED[@]}" -eq 0 ] || {
    echo "(git rebase --onto $LATEST_TAG $COMMON_PARENT *)"
    echo "Please try manually fix rebasing these branches:"
    for BRANCH in "${FAILED[@]}"
    do
        echo "- $BRANCH"
    done
    exit 1
}

[ "${#REBASED[@]}" -eq 0 ] || {
    git checkout -B master "$LATEST_TAG"
    git merge --no-edit "${REBASED[@]}"

    sed -i 's/"$/+wwfx.1.0.0"/' src/rez/utils/_version.py
    WWFX_CHANGELOG_ENTRY="$(git show ${WWFX_MASTER}:CHANGELOG.md | grep -m 1 -oP '.*(?=\+wwfx)')"
    # e.g. ## 2.58.0

    cat \
        <(git show HEAD:CHANGELOG.md | sed "/${WWFX_CHANGELOG_ENTRY}/ q" | head -n-1) \
        <(git show ${WWFX_REMOTE}:CHANGELOG.md | sed -n '/+wwfx/,$ p') \
    | sed "/^## ${LATEST_TAG}/ i \
    ## ${LATEST_TAG}+wwfx.1.0.0 ($(date +%Y-%m-%d))\n\
    [Source](https://github.com/${WWFX_REMOTE}/rez/tree/${LATEST_TAG}+wwfx.1.0.0) | [Diff](https://github.com/${WWFX_REMOTE}/rez/compare/${LATEST_TAG}...${LATEST_TAG}+wwfx.1.0.0)\n\n\
    **Merged**\n${MERGED_TEXT}\n\n" > CHANGELOG.md
    git commit --all -m "Updated Changelogs, version to ${LATEST_TAG}+wwfx.1.0.0"
    echo git push --force -u "$WWFX_REMOTE" master:master
}
