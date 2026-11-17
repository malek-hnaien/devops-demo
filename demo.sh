#!/bin/bash
echo "1. Updating health status in app.py..."
sed -i 's/"ok"/"healthy"/' app.py
echo "2. Creating feature branch, committing, and pushing..."
BRANCH="feature/demo-$(date +%s)"
git checkout -b $BRANCH
git add app.py
git commit -m "feat: update health status for live demo"
git push -u origin $BRANCH
echo "3. Open a Pull Request at:"
echo "   https://github.com/malek-hnaien/devops-demo/pulls"