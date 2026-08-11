#!/bin/bash

# Create beta testing user accounts
# Usage: ./create_beta_users.sh

set -e

echo "======================================================================"
echo "SellIA v1.0.0 - BETA USER ACCOUNT CREATION"
echo "======================================================================"
echo ""

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-sellia_user}
DB_NAME=${DB_NAME:-sellia}

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "Database: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo ""

# Create credentials file
CREDS_FILE="beta_credentials_$(date +%s).txt"
> "$CREDS_FILE"

echo -e "${BLUE}Creating beta user accounts...${NC}\n"

# Function to create user
create_beta_user() {
  local cohort=$1
  local number=$2
  local cohort_name=$3

  local user_id="beta_${cohort,,}_$(printf "%03d" $number)"
  local email="${user_id}@company.com"
  local password=$(openssl rand -base64 12)

  # Create user in database
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
INSERT INTO users (
  id, email, password_hash, first_name, last_name,
  role, beta_flag, status, created_at
)
VALUES (
  '$user_id',
  '$email',
  crypt('$password', gen_salt('bf')),
  '$cohort_name',
  'Beta User $number',
  'sales',
  true,
  'active',
  NOW()
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO beta_participants (
  user_id, cohort, email, onboarded_at
)
VALUES (
  '$user_id',
  '$cohort',
  '$email',
  NOW()
)
ON CONFLICT (user_id) DO NOTHING;
EOF

  # Log credentials
  echo "$user_id | $email | $password | $cohort" >> "$CREDS_FILE"

  echo -e "${GREEN}✅${NC} $user_id ($cohort) - $email"
}

# Cohort A: Enterprise Sales (20 users)
echo "Cohort A: Enterprise Sales (20 users)"
for i in $(seq 1 20); do
  create_beta_user "A" "$i" "Sales Manager"
done
echo ""

# Cohort B: Sales Operations (15 users)
echo "Cohort B: Sales Operations (15 users)"
for i in $(seq 1 15); do
  create_beta_user "B" "$i" "Operations"
done
echo ""

# Cohort C: Mobile Power Users (15 users)
echo "Cohort C: Mobile Power Users (15 users)"
for i in $(seq 1 15); do
  create_beta_user "C" "$i" "Mobile User"
done
echo ""

# Cohort D: Voice/Integration Team (10 users)
echo "Cohort D: Voice/Integration Team (10 users)"
for i in $(seq 1 10); do
  create_beta_user "D" "$i" "Voice Specialist"
done
echo ""

# Verify creation
echo "======================================================================"
echo "VERIFICATION"
echo "======================================================================"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
SELECT
  cohort,
  count(*) as user_count,
  min(onboarded_at) as first_onboarded,
  max(onboarded_at) as last_onboarded
FROM beta_participants
GROUP BY cohort
ORDER BY cohort;
EOF

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ BETA USER ACCOUNTS CREATED${NC}"
echo "======================================================================"
echo ""
echo "Credentials saved to: $CREDS_FILE"
echo ""
echo "Next steps:"
echo "  1. Copy credentials to secure location"
echo "  2. Send welcome emails to beta users"
echo "  3. Create #beta-testing Slack channel"
echo "  4. Post launch announcement"
echo "  5. Host kickoff call (Aug 12, 2:00 PM UTC)"
echo ""
