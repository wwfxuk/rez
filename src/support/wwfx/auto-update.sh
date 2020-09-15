#!/bin/bash
set -eux -o pipefail

FAILED=()
REBASED=()
MERGED_TEXT=""
WWFX_REMOTE="${WWFX_REMOTE:-wwfxuk}"
WWFX_MASTER="$WWFX_REMOTE"/master
WWFX_REMOTE_REPO="$(git remote get-url $WWFX_REMOTE | sed -n '/.*github\.com/ { s|.*github.com.||; s/\.git.*//p; q}')"

# Get git tag of latest nerdvegas release
LATEST_TAG=${LATEST_TAG:-$(curl -H "Accept: application/vnd.github.v3+json" https://api.github.com/repos/nerdvegas/rez/releases/latest | grep -oP '(?<="tag_name": ")[^"]+')}
: "Currently at: " "$(git show --no-patch --format='%h')"
: "$WWFX_MASTER" "$(git show --no-patch --format='%h' $WWFX_MASTER)"
: "$LATEST_TAG" "$(git show --no-patch --format='%h' $LATEST_TAG)"

[ $(git rev-list --left-right --count "$LATEST_TAG"..."$WWFX_MASTER" | cut -f1) -eq 0 ] && {
    set +x
    echo "No new releases since $LATEST_TAG"
    exit
} || COMMON_PARENT="$(git merge-base $LATEST_TAG $WWFX_MASTER)"

readarray -t MERGES < <(
    git log --format="%D" "$COMMON_PARENT".."$WWFX_MASTER" \
    | sed -n '/tag/d; /^$/d; s/, /,/;p'
)

fix_interactively() {
    set +x
    echo "Fix and continue rebasing until finished"
    echo "      If finished successfully, run: exit"
    echo "                          else, run: exit 100"
    bash -i
    set -x
}

push_force() {
    if [ "${NO_PUSH:-FALSE}" == "FALSE" ]
    then
        git push -uf "$@"
    else
        echo "NO_PUSH: git push -uf" "$@"
    fi
}

post_rebase_success() {
    local BRANCH
    local UPSTREAM
    local REMOTE
    local COMMIT
    local BRANCH_MERGED_TEXT
    local GITHUB_REPO

    BRANCH="$1"
    UPSTREAM="$2"
    REMOTE="$3"

    REBASED+=("$BRANCH")
    COMMIT="$(git rev-parse --short ${BRANCH})"
    BRANCH_MERGED_TEXT="- ${COMMIT} from \`${BRANCH}\`.\n"

    # Push if remote available, setup GitHub link as required
    [ -z "$REMOTE" ] || {
        push_force "$REMOTE" "$BRANCH":"${UPSTREAM#*/}"

        GITHUB_REPO="$(git remote get-url ${REMOTE} | sed -n '/.*github\.com/ { s|.*github.com.||; s/\.git.*//p; q}')"
	[ -z "$GITHUB_REPO" ] || BRANCH_MERGED_TEXT="- [${COMMIT}](https://github.com/${WWFX_REMOTE_REPO}/compare/${LATEST_TAG}...${COMMIT}) from [${BRANCH}](https://github.com/${GITHUB_REPO}/tree/${BRANCH}).\n"
    }
    MERGED_TEXT+="$BRANCH_MERGED_TEXT"
}


for MERGE_BRANCH in "${MERGES[@]}"
do
    BRANCH="${MERGE_BRANCH##*,}"
    UPSTREAM="${MERGE_BRANCH%%,*}"
    REMOTE="${UPSTREAM%%/*}"

    # Set branch to upstream if empty or same, also check upstream has branch name
    [ "${BRANCH:-$UPSTREAM}" != "$UPSTREAM" ] || [ -z "${UPSTREAM#*/}" ] || {
        BRANCH="${UPSTREAM#*/}"
        git checkout -B "$BRANCH" "$UPSTREAM"
    }

    # Rebase branch, if any
    [ -z "$BRANCH" ] || if git rebase --onto "$LATEST_TAG" "$COMMON_PARENT" "$BRANCH"
    then
        post_rebase_success "$BRANCH" "$UPSTREAM" "$REMOTE"
    else
        [ -t 0 ] && [ -t 1 ] && fix_interactively && post_rebase_success "$BRANCH" "$UPSTREAM" "$REMOTE" || {
            git rebase --abort || :
            FAILED+=("$BRANCH")
        }
    fi
done

[ "${#FAILED[@]}" -eq 0 ] || {
    set +x
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

    # Setup sed expression for inserting changelog
    NEW_CHANGELOG_ENTRY="## ${LATEST_TAG}+wwfx.1.0.0 ($(date +%Y-%m-%d))\n\
[Source](https://github.com/${WWFX_REMOTE_REPO}/tree/${LATEST_TAG}+wwfx.1.0.0) | [Diff](https://github.com/${WWFX_REMOTE_REPO}/compare/${LATEST_TAG}...${LATEST_TAG}+wwfx.1.0.0)\n\n\
**Merged**\n\n${MERGED_TEXT}"
    WWFX_CHANGELOG_COMMIT=$(git log --all -G'.*\+wwfx' --format="%h" -- CHANGELOG.md | head -1)

    # Setup latest official version that WWFX forked from
    # e.g. "## 2.58.0"
    # If error, print changelog entry to add to stdout
    WWFX_CHANGELOG_ENTRY="$(git show ${WWFX_CHANGELOG_COMMIT}:CHANGELOG.md | grep -m 1 -oP '.*(?=\+wwfx)')" || {
        set +x
        EXIT_CODE="$?"
        echo -e "\n---- Manually add this to CHANGELOG.md ----\n" | sed "$ a \
$NEW_CHANGELOG_ENTRY"
	    exit "$EXIT_CODE"
    }

    # Splice in WWFX specific CHANGELOG.md entries
    # 1. Print current CHANGELOG up till before latest version WWFX forked from
    # 2. Add latest WWFX CHANGELOG for that version and till end of file
    # 3. Insert new changelog entry for WWFX changes.
    cat \
        <(git show HEAD:CHANGELOG.md | sed "/${WWFX_CHANGELOG_ENTRY}/ q" | head -n-1) \
        <(git show ${WWFX_CHANGELOG_COMMIT}:CHANGELOG.md | sed -n '/+wwfx/,$ p') \
    | sed "/^## ${LATEST_TAG}/ i \
${NEW_CHANGELOG_ENTRY}" > CHANGELOG.md

    # Commit, tag and push to WWFX master
    git commit --all -m "Updated Changelogs, version to ${LATEST_TAG}+wwfx.1.0.0"
    git tag "${LATEST_TAG}+wwfx.1.0.0"
    push_force "$WWFX_REMOTE" "${LATEST_TAG}+wwfx.1.0.0" master:master
}
