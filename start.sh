#!/bin/sh
set -e
cd /app

echo "=== BDC STARTUP ==="
DB_DIR="/tmp"
mkdir -p "$DB_DIR"
export DB_DIR DB_PATH="$DB_DIR/db.sqlite3"

# Seed a fresh writable DB from the baked-in image DB (keeps products/data).
if [ ! -f "$DB_PATH" ] && [ -f /app/db.sqlite3 ]; then
  echo "=== SEEDING DB FROM IMAGE ==="
  cp /app/db.sqlite3 "$DB_PATH"
fi

echo "=== MIGRATE ==="
python manage.py migrate --noinput

echo "=== WRITE TEST ==="
python - <<'EOF'
import os, sqlite3
p = os.environ["DB_PATH"]
c = sqlite3.connect(p)
c.execute("create table if not exists _write_test(x)")
c.execute("insert into _write_test values (1)")
c.commit()
print("WRITE OK:", p)
EOF

echo "=== DJANGO DB PATH ==="
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['NAME'])" 2>&1

echo "=== STARTING SERVER ON /tmp DB ==="
exec python manage.py runserver 0.0.0.0:${PORT:-3000}