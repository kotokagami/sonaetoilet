from .security import hash_password
from .database import Base, engine, SessionLocal
from .models import User, Site, Bladder, VacuumVendor, ManualSection, ManualStep, Transfer


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.query(Site).first():
            return
        db.add(User(username="admin", password_hash=hash_password("sonae2026"), role="city"))
        sites = [
            Site(id=1,name="登戸レジデンス",location="川崎市多摩区",site_type="マンション",population=120,mode="disaster",rate=20,contact_name="管理組合",contact_phone="044-XXX-XXXX",pin="1001",blocked=True,generator_on=True,pump_on=True,sewer_ok=False,map_x=27,map_y=46),
            Site(id=2,name="新横浜オフィスビル",location="横浜市港北区",site_type="オフィス",population=280,mode="disaster",rate=20,contact_name="ビル管理室",contact_phone="045-XXX-XXXX",pin="2002",blocked=True,generator_on=True,pump_on=True,sewer_ok=False,map_x=64,map_y=34),
            Site(id=3,name="多摩区公衆トイレ",location="川崎市多摩区",site_type="公衆トイレ",population=40,mode="disaster",rate=40,contact_name="川崎市施設管理",contact_phone="044-XXX-XXXX",pin="3003",blocked=True,generator_on=True,pump_on=False,sewer_ok=False,map_x=38,map_y=63),
            Site(id=4,name="港北区避難所（小学校）",location="横浜市港北区",site_type="避難所",population=450,mode="normal",rate=20,contact_name="港北区役所",contact_phone="045-XXX-XXXX",pin="4004",blocked=False,generator_on=False,pump_on=False,sewer_ok=True,map_x=70,map_y=27),
        ]
        bladder_rows = {
            1:[("B-01",5000,5000,"full"),("B-02",5000,2840,"active"),("B-03",5000,0,"standby"),("B-04",5000,0,"standby")],
            2:[("B-01",10000,10000,"full"),("B-02",10000,8900,"active"),("B-03",10000,0,"standby")],
            3:[("B-01",2000,1600,"active"),("B-02",2000,0,"standby")],
            4:[("B-01",20000,0,"standby"),("B-02",20000,0,"standby")],
        }
        for site in sites:
            for label, cap, fill, status in bladder_rows[site.id]:
                site.bladders.append(Bladder(label=label, capacity=cap, fill=fill, status=status))
            db.add(site)
        db.add_all([
            VacuumVendor(company="川崎環境サービス株式会社",phone="044-XXX-1111",area="川崎市全域",response_time="2〜4時間",contracted=True,available=True),
            VacuumVendor(company="横浜衛生車両株式会社",phone="045-XXX-2222",area="横浜市全域",response_time="3〜5時間",contracted=True,available=False),
            VacuumVendor(company="神奈川緊急対応センター",phone="0120-XXX-333",area="神奈川県全域",response_time="要確認",contracted=False,available=True),
        ])
        manual = [
          ("act","⚡","起動手順","Activation","接続全体図（図面追加予定）",[("排水管の閉塞","排水管下流側の開口部を間詰材（土嚢等）で確実に閉塞する。"),("ブラダーの設置","収納場所からブラダーを取り出し、地上の平坦な場所に展開・設置する。"),("排水パイプの接続","集水ピットとブラダーの接続口に排水パイプを接続し、締付けを確認する。"),("非常用発電機の起動","発電機を起動し、汚水ポンプに電力が供給されていることを確認する。"),("ポンプ作動の確認","集水ピット内の汚水が一定量に達するとポンプが自動作動する。")]),
          ("con","🔗","接続手順","Connection","接続部詳細図（図面追加予定）",[("接続口の確認","集水ピット側とブラダー側の接続口の口径・規格を確認する。"),("ホースの接続","排水パイプを集水ピット→ブラダーの方向に接続する。逆方向不可。"),("漏れ確認","バンドクランプで締付け、試運転時に接続部からの漏れがないか確認する。"),("ブラダー展開確認","ブラダーが完全に展開されており、折りたたまれた部分がないことを確認する。")]),
          ("sw","🔄","満杯時の切替","Bladder Switchover","切替手順図（図面追加予定）",[("ポンプの停止","汚水ポンプを停止し、排水パイプ内の圧力を抜く。"),("満杯ブラダーの切離し","満杯ブラダーから排水パイプを取り外す。端部をキャップで閉じる。"),("次のブラダーへ接続","待機中のブラダーに排水パイプを接続し、ポンプを再起動する。"),("満杯ブラダーの封止","全接続口を封止し、回収・処分まで安全な場所に保管する。")]),
          ("dis","↩","排出・回収手順","Discharge","排出フロー図（図面追加予定）",[("本管復旧の確認","行政・管理者より下水本管の復旧が通知されたことを確認する。"),("ポンプ逆送","汚水ポンプを逆転させ、ブラダー内の汚水を下水本管へ直接圧送する。"),("バキューム車（代替）","本管未復旧の場合、契約済みバキューム車に回収を依頼する。"),("ブラダーの洗浄・収納","ブラダーを水で洗浄・乾燥させてから折りたたんで収納する。")]),
        ]
        for slug, icon, title, subtitle, diag, steps in manual:
            sec = ManualSection(slug=slug, icon=icon, title=title, subtitle=subtitle, diagram_note=diag)
            for i, (t,d) in enumerate(steps,1): sec.steps.append(ManualStep(step_no=i,title=t,description=d))
            db.add(sec)
        db.add_all([
            Transfer(id=1,from_site_id=4,to_site_id=1,size=20000,count=1,status="pending",note="B-02が満杯間近"),
            Transfer(id=2,from_site_id=2,to_site_id=3,size=5000,count=1,status="approved",note="公衆トイレ補充"),
            Transfer(id=3,from_site_id=4,to_site_id=2,size=10000,count=1,status="completed",note=""),
        ])
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
