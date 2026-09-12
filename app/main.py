"""Local portfolio API. No patient records or real hospital data."""
import csv
import io
import json
import os
from contextlib import closing
from datetime import date
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from .etl import connect, ingest, inventory, demo_csv

STATIC = Path(__file__).parent / 'static'


def create_app(db_path=None):
    app = FastAPI(title='BioOps Analytics', version='1.0.0', description='ETL e indicadores de mantenimiento con datos sintéticos.')
    app.state.db_path = str(db_path or os.getenv('BIOOPS_DB', 'data/bioops.db'))
    app.mount('/static', StaticFiles(directory=STATIC), name='static')

    @app.get('/', include_in_schema=False)
    def home():
        return FileResponse(STATIC / 'index.html')

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': '1.0.0'}

    @app.post('/api/import', openapi_extra={'requestBody': {'required': True,
        'content': {'text/csv': {'schema': {'type': 'string'},
        'example': 'asset_id,name,category,location,last_service,interval_days,criticality\nBIO-001,Monitor,Monitoreo,Sede Norte,2026-03-01,180,alta'}}}})
    async def import_csv(request: Request):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 2_000_000:
                raise HTTPException(413, 'Máximo 2 MB por archivo')
        try:
            with closing(connect(app.state.db_path)) as db:
                return ingest(db, body.decode('utf-8-sig'))
        except (ValueError, UnicodeDecodeError, csv.Error) as error:
            raise HTTPException(422, str(error)) from error

    @app.post('/api/demo')
    def demo():
        with closing(connect(app.state.db_path)) as db:
            return ingest(db, demo_csv(date.today()))

    @app.get('/api/dashboard')
    def dashboard(as_of: date | None = None, location: str | None = None):
        cut = as_of or date.today()
        with closing(connect(app.state.db_path)) as db:
            assets = inventory(db, cut, location)
            locations = [row[0] for row in db.execute('SELECT DISTINCT location FROM assets ORDER BY location')]
        overdue = sum(a['status'] == 'vencido' for a in assets)
        upcoming = sum(a['status'] == 'próximo' for a in assets)
        unknown = sum(a['status'] == 'sin historial' for a in assets)
        known = len(assets) - unknown
        return dict(as_of=cut.isoformat(), assets=assets, locations=locations,
                    metrics=dict(total=len(assets), overdue=overdue, upcoming=upcoming, unknown=unknown,
                                 current=len(assets)-overdue-upcoming-unknown,
                                 compliance=round(100*(known-overdue)/known,1) if known else None,
                                 critical_overdue=sum(a['status']=='vencido' and a['criticality']=='alta' for a in assets)))

    @app.get('/api/runs')
    def runs():
        with closing(connect(app.state.db_path)) as db:
            return [dict(id=r['id'], created_at=r['created_at'], **json.loads(r['summary']),
                         errors=[dict(e) for e in db.execute('SELECT row_number,reason FROM rejections WHERE run_id=?',(r['id'],))])
                    for r in db.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 20')]

    @app.get('/api/export')
    def export(as_of: date | None = None, location: str | None = None):
        with closing(connect(app.state.db_path)) as db:
            rows = inventory(db, as_of or date.today(), location)
        buffer = io.StringIO()
        fields = ['asset_id','name','category','location','last_service','interval_days','criticality','due_date','days_remaining','status']
        writer = csv.DictWriter(buffer, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            # Neutralize formulas when opening user-supplied labels in Excel/Power BI.
            writer.writerow({key: "'"+value if isinstance(value,str) and value.startswith(('=','+','-','@')) else value for key,value in row.items()})
        return Response('\ufeff'+buffer.getvalue(), media_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition':'attachment; filename=bioops-report.csv'})

    return app


app = create_app()
