import json, sys, time
sys.path.insert(0,"scripts")
from creative_line import run
SPREAD = [
  ("albaik","national_day"),("albaik","daily_post"),("barnscoffee","ramadan"),
  ("barnscoffee","weekly_offer"),("herfyfsc","eid_al_fitr"),("mcdonaldsksa","summer_campaign"),
  ("altazaj_fakieh","founding_day"),("shawarmersa","new_product"),("namshi","white_friday"),
  ("maxfashionmena","eid_al_adha"),("lcwaikiki","back_to_school"),("zara","new_product"),
  ("mikyajy","eid_al_fitr"),("bathandbodyworksarabia","ramadan"),("ajmalperfumes","national_day"),
  ("niceonesa","weekly_offer"),("noon","white_friday"),("tamimimarkets","ramadan"),
  ("roshnksa","national_day"),("kyancafe","daily_post"),
]
out=[]
for i,(br,occ) in enumerate(SPREAD):
    try:
        r=run(br,occ)
        out.append(r)
        print(f"[{i+1}/20] {br}×{occ}: {len(r['candidates'])} candidates",flush=True)
    except Exception as e:
        print(f"[{i+1}/20] ✗ {br}×{occ}: {str(e)[:70]}",flush=True)
        out.append({"brand":br,"brand_en":br,"occasion":occ,"candidates":[],"error":str(e)[:100]})
    time.sleep(0.5)
json.dump(out,open("logs/batch20_candidates.json","w"),ensure_ascii=False,indent=2)
print(f"\nDONE — {sum(len(x['candidates']) for x in out)} total candidates across {len(out)} briefs")
