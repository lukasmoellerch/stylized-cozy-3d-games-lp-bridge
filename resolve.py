import json, urllib.request, urllib.parse, time
out=open('resolved.tsv','w')
for line in open('games.txt'):
    if not line.strip() or line.startswith('#'): continue
    slug,term,cat=line.strip().split('|')
    u='https://store.steampowered.com/api/storesearch/?cc=US&l=english&term='+urllib.parse.quote(term)
    r=json.load(urllib.request.urlopen(u))
    items=r.get('items',[])[:3]
    cands=' ;; '.join(f"{i['id']}:{i['name']}" for i in items)
    print(slug,'=>',cands); out.write(f"{slug}\t{cat}\t{cands}\n"); time.sleep(0.3)
