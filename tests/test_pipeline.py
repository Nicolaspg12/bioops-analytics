import csv
import io
from datetime import date
from fastapi.testclient import TestClient
from app.etl import connect, ingest, inventory, demo_csv, FIELDS
from app.main import create_app


def test_idempotent_and_quarantine(tmp_path):
    db = connect(tmp_path/'test.db')
    text = demo_csv(date(2026,9,12))
    assert ingest(db,text)['inserted'] == 24
    assert ingest(db,text)['unchanged'] == 24
    bad = text.splitlines()[0]+'\nBAD,Invalid,Lab,North,2026-02-30,0,alta\n'
    assert ingest(db,bad)['rejected'] == 1
    assert db.execute('SELECT count(*) FROM assets').fetchone()[0] == 24
    assert db.execute('SELECT count(*) FROM rejections').fetchone()[0] == 1
    db.close()


def test_updates_duplicates_and_dates(tmp_path):
    db = connect(tmp_path/'test.db')
    text = ','.join(FIELDS)+'\nA,Monitor,Lab,North,2026-09-01,11,alta\n'
    assert ingest(db,text+text.splitlines()[1]+'\n')['rejected'] == 1
    assert inventory(db,date(2026,9,12))[0]['status'] == 'próximo'
    assert inventory(db,date(2026,9,13))[0]['status'] == 'vencido'
    assert inventory(db,date(2026,8,1))[0]['status'] == 'sin historial'
    assert ingest(db,text.replace('Monitor','Updated'))['updated'] == 1
    db.close()


def test_api_filters_export_and_invalid_input(tmp_path):
    client = TestClient(create_app(tmp_path/'api.db'))
    assert client.get('/api/dashboard').json()['metrics']['compliance'] is None
    assert client.post('/api/demo').status_code == 200
    result = client.get('/api/dashboard',params={'location':'Sede Norte'}).json()
    assert result['metrics']['total'] == 8
    assert all(a['location']=='Sede Norte' for a in result['assets'])
    exported = client.get('/api/export',params={'location':'Sede Norte'})
    assert len(list(csv.DictReader(io.StringIO(exported.text.lstrip('\ufeff'))))) == 8
    assert client.post('/api/import',content='wrong\nrow').status_code == 422
    assert client.post('/api/import',content=b'\xff').status_code == 422
    assert client.post('/api/import',content=b'x'*2_000_001).status_code == 413
    assert client.get('/api/dashboard?as_of=wrong').status_code == 422
    assert len(client.get('/api/runs').json()) == 1


def test_formula_export_and_sql_filter(tmp_path):
    client = TestClient(create_app(tmp_path/'api.db'))
    data = ','.join(FIELDS)+'\nA,=1+1,Lab,North,2026-01-01,180,alta\n'
    assert client.post('/api/import',content=data).json()['inserted']==1
    assert "'=1+1" in client.get('/api/export').text
    assert client.get('/api/dashboard',params={'location':"' OR 1=1 --"}).json()['assets']==[]
