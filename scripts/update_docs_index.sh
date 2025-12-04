#!/bin/bash
# Import utility functions
source ./scripts/util.sh

cat README.md ./docs/*.md > ./docs/combined.md
pandoc ./docs/combined.md -o ./docs/index.html
rm ./docs/combined.md

# Prepend google tag content to the generated index.html
HEAD_CONTENT='<head><!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-CP65J0T1G0"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag("js", new Date());
gtag("config", "G-CP65J0T1G0");
</script></head>'
TEMP_FILE=$(mktemp)
echo "$HEAD_CONTENT" > "$TEMP_FILE"
cat ./docs/index.html >> "$TEMP_FILE"
mv "$TEMP_FILE" ./docs/index.html

print_status "Done updating docs/index.html from README.md and docs/*.md. Make sure to push the updated index to GitHub, to the branch in use under settings/pages."
