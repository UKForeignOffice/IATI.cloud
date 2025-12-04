#!/bin/bash
# Import utility functions
source ./scripts/util.sh

cat README.MD ./docs/*.md > ./docs/combined.md
pandoc ./docs/combined.md -o ./docs/index.html
rm ./docs/combined.md

print_status "Done updating docs/index.html from README.MD and docs/*.md. Make sure to push the updated index to GitHub, to the branch in use under settings/pages."