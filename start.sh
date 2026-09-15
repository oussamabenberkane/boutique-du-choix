#!/bin/sh
set -e
cd /app

echo "=== BDC STARTUP DIAGNOSTICS ==="
echo "=== WHOAMI ==="
id
echo "=== MOUNTS (non-overlay) ==="
mount | grep -Ev "overlay|proc|sys|tmpfs|cgroup" | head -30 || true
echo "=== DF ==="
df -h /app /tmp 2>/dev/null || true

# Pick the first writable directory for the SQLite database.
# Prefer persistent volume locations, fall back to /tmp (ephemeral).
echo "=== PROBE WRITABLE DIRS ==="
DB_DIR=""
for d in /data /var/lib/data /storage /persistent /mnt/data /tmp; do
  if [ -d "$d" ] && [ -w "$d" ]; then DB_DIR="$d"; break; fi
  if mkdir -p "$d" 2>/dev/null && touch "$d/.belmo_t" 2>/dev/null; then
    DB_DIR="$d"; rm -f "$d/.belmo_t"; break
  fi
done
[ -z "$DB_DIR" ] && DB_DIR="/tmp"

echo "=== USING DB_DIR=$DB_DIR ==="

# Seed a fresh writable DB from the baked-in image DB (keeps products/data).
if [ ! -f "$DB_DIR/db.sqlite3" ] && [ -f /app/db.sqlite3 ]; then
  echo "=== COPYING SEEDED DB TO $DB_DIR ==="
  cp /app/db.sqlite3 "$DB_DIR/db.sqlite3"
fi

echo "=== MIGRATE ==="
export DB_DIR DB_PATH="$DB_DIR/db.sqlite3"
python manage.py migrate --noinput

echo "=== STARTING SERVER ==="
python manage.py runserver 0.0.0.0:${PORT:-3000}