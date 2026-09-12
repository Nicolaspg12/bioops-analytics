"""Validated CSV ingestion with row quarantine and transactional SQLite upserts."""
import csv
import io
import json
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FIELDS = ['asset_id', 'name', 'category', 'location', 'last_service', 'interval_days', 'criticality']


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS assets (
            asset_id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
            location TEXT NOT NULL, last_service TEXT NOT NULL,
            interval_days INTEGER NOT NULL CHECK(interval_days BETWEEN 1 AND 3650),
            criticality TEXT NOT NULL CHECK(criticality IN ('alta','media','baja')));
        CREATE INDEX IF NOT EXISTS ix_assets_location ON assets(location);
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, summary TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS rejections (
            run_id INTEGER NOT NULL, row_number INTEGER NOT NULL, reason TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES runs(id));
    ''')
    db.execute('PRAGMA foreign_keys=ON')
    return db


def validate(row):
    if None in row or any(row.get(k) is None for k in FIELDS):
        raise ValueError('Número de columnas incorrecto')
    item = {k: row[k].strip() for k in FIELDS}
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', item['asset_id']):
        raise ValueError('asset_id: usa letras, números, guion o guion bajo; máximo 40')
    for field in ['name', 'category', 'location']:
        if not item[field] or len(item[field]) > 100 or any(ord(c) < 32 for c in item[field]):
            raise ValueError(f'{field}: texto obligatorio de 1 a 100 caracteres')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', item['last_service']):
        raise ValueError('last_service: formato YYYY-MM-DD requerido')
    service = date.fromisoformat(item['last_service'])
    interval = int(item['interval_days'])
    if not 1 <= interval <= 3650:
        raise ValueError('interval_days debe estar entre 1 y 3650')
    service + timedelta(days=interval)  # Reject date overflow before storage.
    item['interval_days'] = interval
    item['criticality'] = item['criticality'].lower()
    if item['criticality'] not in ('alta', 'media', 'baja'):
        raise ValueError('criticality debe ser alta, media o baja')
    return item


def ingest(db, text):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    if reader.fieldnames != FIELDS:
        raise ValueError('Encabezado requerido: ' + ','.join(FIELDS))
    rows = list(reader)
    if not rows or len(rows) > 10000:
        raise ValueError('El archivo debe tener de 1 a 10.000 filas')
    summary = dict(received=len(rows), inserted=0, updated=0, unchanged=0, rejected=0)
    rejected, seen = [], set()
    with db:
        for number, row in enumerate(rows, start=2):
            try:
                item = validate(row)
                if item['asset_id'] in seen:
                    raise ValueError('asset_id duplicado dentro del archivo')
                seen.add(item['asset_id'])
            except (ValueError, OverflowError) as error:
                rejected.append({'row': number, 'reason': str(error)})
                summary['rejected'] += 1
                continue
            old = db.execute('SELECT * FROM assets WHERE asset_id=?', (item['asset_id'],)).fetchone()
            if old and dict(old) == item:
                summary['unchanged'] += 1
                continue
            key = 'updated' if old else 'inserted'
            db.execute('''INSERT INTO assets VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(asset_id) DO UPDATE SET name=excluded.name,
                category=excluded.category, location=excluded.location,
                last_service=excluded.last_service, interval_days=excluded.interval_days,
                criticality=excluded.criticality''', tuple(item[k] for k in FIELDS))
            summary[key] += 1
        run = db.execute('INSERT INTO runs(created_at,summary) VALUES (?,?)',
                         (datetime.now(timezone.utc).isoformat(), json.dumps(summary))).lastrowid
        db.executemany('INSERT INTO rejections VALUES (?,?,?)',
                       [(run, row['row'], row['reason']) for row in rejected])
    return {'run_id': run, **summary, 'errors': rejected}


def inventory(db, as_of, location=None):
    query, params = 'SELECT * FROM assets', ()
    if location:
        query, params = query + ' WHERE location=?', (location,)
    items = []
    for row in db.execute(query, params):
        item = dict(row)
        due = date.fromisoformat(item['last_service']) + timedelta(days=item['interval_days'])
        days = (due - as_of).days
        # A service dated after the reporting cut-off cannot describe historical state.
        status = ('sin historial' if date.fromisoformat(item['last_service']) > as_of else
                  'vencido' if days < 0 else 'próximo' if days <= 30 else 'al día')
        item.update(due_date=due.isoformat(), days_remaining=days, status=status)
        items.append(item)
    return sorted(items, key=lambda item: (item['days_remaining'], item['asset_id']))


def demo_csv(as_of):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(FIELDS)
    names = ['Monitor multiparámetro', 'Bomba de infusión', 'Electrocardiógrafo',
             'Centrífuga', 'Desfibrilador', 'Autoclave', 'Báscula digital', 'Oxímetro']
    for i in range(24):
        days = [-42, -18, -7, 0, 8, 18, 25, 45, 65, 90, 110, 130][i % 12]
        writer.writerow([f'BIO-{i+1:03}', names[i % 8], ['Monitoreo','Terapia','Laboratorio'][i % 3],
                         ['Sede Norte','Sede Centro','Sede Sur'][i % 3],
                         (as_of + timedelta(days=days-180)).isoformat(), 180,
                         ['alta','media','baja'][i % 3]])
    return stream.getvalue()
