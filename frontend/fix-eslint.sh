#!/bin/bash
# Quick ESLint auto-fix
npx eslint --fix src/ --max-warnings 50 2>&1 | head -10
echo "Fixed common issues (auto-fixable only)"
