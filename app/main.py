import os, math
from datetime import datetime
from pathlib import Path
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .security import verify_password
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from .database import Base, engine, get_db
from .models import Bladder, ManualSection, Site, Transfer, User, VacuumVendor
from .services import *

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="SONAE")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-only-change-me"), same_site="lax", https_only=False)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
Base.metadata.create_all(engine)

templates.env.globals.update(active_bladder=active_bladder, standby_bladders=standby_bladders, full_bladders=full_bladders, spare_capacity=spare_capacity, fill_pct=fill_pct, days_left=days_left, alert_level=alert_level)

def require_login(request: Request):
    if not request.session.get("role"):
        raise HTTPException(status_code=401)

def redirect_login(): return RedirectResponse("/login", status_code=303)

@app.exception_handler(401)
async def unauthorized(request, exc): return redirect_login()

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if request.session.get("role") == "city": return RedirectResponse("/city",303)
    if request.session.get("role") == "building": return RedirectResponse(f"/sites/{request.session['site_id']}",303)
    return RedirectResponse("/login",303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request): return templates.TemplateResponse(request, "login.html", {"error": None})

@app.post("/login")
def login(request: Request, account_type: str=Form(...), pin: str=Form(""), username: str=Form(""), password: str=Form(""), db: Session=Depends(get_db)):
    error = None
    if account_type == "building":
        site = db.query(Site).filter(Site.pin == pin.strip()).first()
        if site:
            request.session.clear(); request.session.update({"role":"building","site_id":site.id}); return RedirectResponse(f"/sites/{site.id}",303)
        error = "PINコードが正しくありません"
    else:
        user = db.query(User).filter(User.username == username.strip()).first()
        if user and verify_password(password, user.password_hash):
            request.session.clear(); request.session.update({"role":"city","user_id":user.id}); return RedirectResponse("/city",303)
        error = "ユーザー名またはパスワードが正しくありません"
    return templates.TemplateResponse(request, "login.html", {"error": error}, status_code=400)

@app.post("/logout")
def logout(request: Request): request.session.clear(); return RedirectResponse("/login",303)

@app.get("/city", response_class=HTMLResponse)
def city(request: Request, db: Session=Depends(get_db)):
    require_login(request)
    if request.session.get("role") != "city": return RedirectResponse(f"/sites/{request.session['site_id']}",303)
    sites = db.query(Site).order_by(Site.id).all(); transfers = db.query(Transfer).order_by(Transfer.created_at.desc()).all()
    return templates.TemplateResponse(request, "city.html", {"sites":sites,"transfers":transfers,"total_spare":sum(spare_capacity(s) for s in sites),"critical":sum(alert_level(s)==2 for s in sites),"pending":sum(t.status=="pending" for t in transfers),"rates":RATES})

@app.get("/sites/{site_id}", response_class=HTMLResponse)
def site_detail(site_id:int, request:Request, db:Session=Depends(get_db)):
    require_login(request)
    if request.session.get("role") == "building" and request.session.get("site_id") != site_id: return RedirectResponse(f"/sites/{request.session['site_id']}",303)
    site=db.get(Site,site_id)
    if not site: raise HTTPException(404)
    transfers=db.query(Transfer).filter((Transfer.from_site_id==site_id)|(Transfer.to_site_id==site_id)).order_by(Transfer.created_at.desc()).all()
    vendors=db.query(VacuumVendor).all(); manuals=db.query(ManualSection).all(); sites=db.query(Site).all()
    return templates.TemplateResponse(request,"site.html",{"site":site,"transfers":transfers,"vendors":vendors,"manuals":manuals,"sites":sites,"sizes":BLADDER_SIZES,"rates":RATES})

@app.post("/sites/{site_id}/rate")
def set_rate(site_id:int, request:Request, rate:int=Form(...), db:Session=Depends(get_db)):
    require_login(request); site=db.get(Site,site_id); site.rate=rate if rate in RATES else site.rate; db.commit(); return RedirectResponse(request.headers.get("referer",f"/sites/{site_id}"),303)

@app.post("/sites/{site_id}/system/{field}")
def toggle_system(site_id:int, field:str, request:Request, db:Session=Depends(get_db)):
    require_login(request); site=db.get(Site,site_id); allowed={"blocked","generator_on","pump_on","sewer_ok"}
    if field not in allowed: raise HTTPException(400)
    setattr(site,field,not getattr(site,field)); db.commit(); return RedirectResponse(f"/sites/{site_id}#system",303)

@app.post("/sites/{site_id}/bladders/add")
def add_bladder(site_id:int, request:Request, capacity:int=Form(...), label:str=Form(""), db:Session=Depends(get_db)):
    require_login(request); site=db.get(Site,site_id)
    if capacity not in BLADDER_SIZES: raise HTTPException(400,"Unsupported bladder size")
    if not label.strip(): label=f"B-{len(site.bladders)+1:02d}"
    db.add(Bladder(site_id=site_id,label=label.strip(),capacity=capacity,fill=0,status="standby")); db.commit(); return RedirectResponse(f"/sites/{site_id}#inventory",303)

@app.post("/sites/{site_id}/bladders/{bladder_id}/switch")
def switch_bladder(site_id:int, bladder_id:int, request:Request, db:Session=Depends(get_db)):
    require_login(request); site=db.get(Site,site_id); target=db.get(Bladder,bladder_id)
    if not target or target.site_id!=site_id or target.status!="standby": raise HTTPException(400)
    active=active_bladder(site)
    if active: active.status="full"; active.fill=active.capacity
    target.status="active"; db.commit(); return RedirectResponse(f"/sites/{site_id}#inventory",303)

@app.post("/sites/{site_id}/bladders/{bladder_id}/dispose")
def dispose(site_id:int, bladder_id:int, request:Request, method:str=Form(...), note:str=Form(""), db:Session=Depends(get_db)):
    require_login(request); b=db.get(Bladder,bladder_id)
    if not b or b.site_id!=site_id or b.status!="full": raise HTTPException(400)
    site=db.get(Site,site_id)
    if method=="本管圧送" and not site.sewer_ok: raise HTTPException(400,"Sewer is not restored")
    b.disposal_method=method; b.disposal_note=note; b.disposed_at=datetime.utcnow(); db.commit(); return RedirectResponse(f"/sites/{site_id}#inventory",303)

@app.post("/transfers")
def create_transfer(request:Request, from_site_id:int=Form(...), to_site_id:int=Form(...), size:int=Form(...), count:int=Form(1), note:str=Form(""), db:Session=Depends(get_db)):
    require_login(request)
    if from_site_id==to_site_id: raise HTTPException(400)
    available=db.query(Bladder).filter(Bladder.site_id==from_site_id,Bladder.status=="standby",Bladder.capacity==size).count()
    if count<1 or count>available: raise HTTPException(400,"Insufficient standby inventory")
    db.add(Transfer(from_site_id=from_site_id,to_site_id=to_site_id,size=size,count=count,status="pending",note=note)); db.commit(); return RedirectResponse(request.headers.get("referer","/city")+"#transfers",303)

@app.post("/transfers/{transfer_id}/status")
def transfer_status(transfer_id:int, request:Request, status:str=Form(...), db:Session=Depends(get_db)):
    require_login(request)
    if request.session.get("role")!="city": raise HTTPException(403)
    if status not in {"approved","rejected","intransit","completed"}: raise HTTPException(400)
    t=db.get(Transfer,transfer_id); t.status=status; db.commit(); return RedirectResponse("/city#transfers",303)

@app.get("/manual/{slug}", response_class=HTMLResponse)
def manual(slug:str, request:Request, db:Session=Depends(get_db)):
    require_login(request); section=db.query(ManualSection).filter(ManualSection.slug==slug).first()
    if not section: raise HTTPException(404)
    return templates.TemplateResponse(request,"manual.html",{"section":section})

@app.get("/capacity", response_class=HTMLResponse)
def capacity(request:Request, population:int|None=None, days:int=3, rate:int=20):
    require_login(request); total=None; recommendation=None
    if population and population>0 and days>0 and rate in RATES:
        total=math.ceil(population*rate*days); recommendation=recommend_capacity(total)
    return templates.TemplateResponse(request,"capacity.html",{"population":population,"days":days,"rate":rate,"total":total,"recommendation":recommendation,"rates":RATES})
