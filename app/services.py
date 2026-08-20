BLADDER_SIZES = [1000, 2000, 5000, 10000, 20000, 30000]
RATES = [15, 20, 40]

def active_bladder(site):
    return next((b for b in site.bladders if b.status == "active"), None)

def standby_bladders(site):
    return [b for b in site.bladders if b.status == "standby"]

def full_bladders(site):
    return [b for b in site.bladders if b.status == "full"]

def spare_capacity(site):
    return sum(b.capacity for b in standby_bladders(site))

def fill_pct(bladder):
    if not bladder or not bladder.capacity:
        return 0
    return round((bladder.fill / bladder.capacity) * 100)

def days_left(site, rate=None):
    bladder = active_bladder(site)
    rate = rate or site.rate
    if not bladder or not site.population or not rate:
        return None
    days = (bladder.capacity - bladder.fill) / (site.population * rate)
    return -1 if days < 1 else round(days, 1)

def alert_level(site, rate=None):
    p = fill_pct(active_bladder(site))
    d = days_left(site, rate)
    if p >= 90 or d == -1:
        return 2
    if p >= 70 or (d is not None and d < 2):
        return 1
    return 0

def recommend_capacity(total):
    for size in BLADDER_SIZES:
        if size >= total:
            return [{"size": size, "count": 1, "surplus": size-total}]
    remaining = total
    out = []
    for size in reversed(BLADDER_SIZES):
        count, remaining = divmod(remaining, size)
        if count:
            out.append({"size": size, "count": count, "surplus": 0})
    if remaining:
        size = next((x for x in BLADDER_SIZES if x >= remaining), BLADDER_SIZES[-1])
        out.append({"size": size, "count": 1, "surplus": size-remaining})
    return out
