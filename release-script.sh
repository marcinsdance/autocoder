#!/bin/bash

set -e

# Configuration
AUTOCODER_REPO="$HOME/git/autocoder"
HOMEBREW_REPO="$HOME/git/homebrew-autocoder"
GITHUB_USERNAME="marcinsdance"

# Check if version is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <new-version>"
    exit 1
fi

NEW_VERSION="$1"

echo "Starting release process for version $NEW_VERSION"

# Update Autocoder repository
cd "$AUTOCODER_REPO"
git checkout develop
echo "$NEW_VERSION" > version.txt
git add version.txt
git commit -m "Bump version to $NEW_VERSION"
git push origin develop

# Create and push release branch
git checkout -b "release/$NEW_VERSION"
git push -u origin "release/$NEW_VERSION"

# Merge release branch to master
git checkout master
git merge --no-ff "release/$NEW_VERSION" -m "Merge release $NEW_VERSION"

# Create and push tag
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
git push origin master --tags

# Merge release branch back to develop
git checkout develop
git merge --no-ff "release/$NEW_VERSION" -m "Merge release $NEW_VERSION back to develop"
git push origin develop

# Delete release branch
git branch -d "release/$NEW_VERSION"
git push origin --delete "release/$NEW_VERSION"

echo "Autocoder repository updated. Please create a GitHub release manually."
echo "Press any key to continue when the GitHub release is created..."
read -n 1 -s

# Update Homebrew formula
cd "$HOMEBREW_REPO"
git checkout master

# Download new release and calculate SHA
TARBALL_URL="https://github.com/$GITHUB_USERNAME/autocoder/archive/refs/tags/v$NEW_VERSION.tar.gz"
wget "$TARBALL_URL" -O "v$NEW_VERSION.tar.gz"
NEW_SHA256=$(shasum -a 256 "v$NEW_VERSION.tar.gz" | cut -d' ' -f1)

# Update formula file
sed -i '' "s/version \".*\"/version \"$NEW_VERSION\"/" Formula/autocoder.rb
sed -i '' "s|url \".*\"|url \"$TARBALL_URL\"|" Formula/autocoder.rb
sed -i '' "s/sha256 \".*\"/sha256 \"$NEW_SHA256\"/" Formula/autocoder.rb

# Commit and push changes
git add Formula/autocoder.rb
git commit -m "Update Autocoder formula to version $NEW_VERSION"
git push origin master

echo "Homebrew formula updated."

# Test the formula
brew update
brew uninstall autocoder || true
brew install --build-from-source ./Formula/autocoder.rb

echo "Release process completed. New version $NEW_VERSION is now available."
