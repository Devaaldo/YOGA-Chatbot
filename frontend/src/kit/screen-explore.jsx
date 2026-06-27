/* Jelajah Jogja — Explore (Jelajah) */
(function () {
  const U = window.JJUI;
  const { Icon, Btn, IconBtn, Chip, Badge, SearchBar, Select, Range, Toggle, SectionHeader, DestinationCard, L } = U;

  const MAP_B = { latMin: -8.22, latMax: -7.54, lngMin: 110.0, lngMax: 110.86 };
  const pinPos = (p) => ({
    left: Math.max(4, Math.min(96, ((p.lng - MAP_B.lngMin) / (MAP_B.lngMax - MAP_B.lngMin)) * 100)) + '%',
    top: Math.max(6, Math.min(94, ((MAP_B.latMax - p.lat) / (MAP_B.latMax - MAP_B.latMin)) * 100)) + '%',
  });

  function Explore({ lang, data, saved, onSave, onOpen, initial }) {
    const { PLACES, CATEGORIES } = data;
    const [query, setQuery] = React.useState('');
    const [cats, setCats] = React.useState(() => new Set(initial && initial.category ? [initial.category] : []));
    const [regency, setRegency] = React.useState('');
    const [budget, setBudget] = React.useState(100000);
    const [freeOnly, setFreeOnly] = React.useState(false);
    const [minRating, setMinRating] = React.useState(0);
    const [sort, setSort] = React.useState('rating');
    const [view, setView] = React.useState('grid');
    const [activePin, setActivePin] = React.useState(null);

    React.useEffect(() => { if (initial && initial.category) setCats(new Set([initial.category])); }, [initial]);

    const toggleCat = (id) => setCats((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

    let list = PLACES.filter((p) => {
      if (cats.size && !cats.has(p.category)) return false;
      if (regency && p.regency !== regency) return false;
      if (freeOnly && p.priceWeekday !== 0) return false;
      if (budget < 100000) { if (p.priceWeekday == null || p.priceWeekday > budget) return false; }
      if (minRating && (p.rating || 0) < minRating) return false;
      if (query && !p.name.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
    list = list.sort((a, b) => {
      if (sort === 'price') return (a.priceWeekday == null ? 1e9 : a.priceWeekday) - (b.priceWeekday == null ? 1e9 : b.priceWeekday);
      if (sort === 'pop') return (b.votes || 0) - (a.votes || 0);
      if (sort === 'az') return a.name.localeCompare(b.name);
      return (b.rating || 0) - (a.rating || 0);
    });

    const activeFilters = [];
    cats.forEach((c) => activeFilters.push({ k: 'cat:' + c, label: c, clear: () => toggleCat(c) }));
    if (regency) activeFilters.push({ k: 'reg', label: regency, clear: () => setRegency('') });
    if (freeOnly) activeFilters.push({ k: 'free', label: L(lang, 'Gratis', 'Free'), clear: () => setFreeOnly(false) });
    if (budget < 100000) activeFilters.push({ k: 'bud', label: '≤ ' + U.fmtIDR(budget), clear: () => setBudget(100000) });
    if (minRating) activeFilters.push({ k: 'rat', label: '★ ' + minRating.toFixed(1) + '+', clear: () => setMinRating(0) });

    const resetAll = () => { setCats(new Set()); setRegency(''); setBudget(100000); setFreeOnly(false); setMinRating(0); setQuery(''); };

    return (
      <div className="jjk-section jjk-container">
        <div style={{ marginBottom: 28 }}>
          <SectionHeader eyebrow={L(lang, 'Jelajah', 'Explore')} title={L(lang, 'Temukan tempat sempurnamu', 'Find your perfect spot')}
            subtitle={L(lang, 'Saring 3.399 destinasi berdasarkan kategori, daerah, harga tiket, dan rating.', 'Filter 3,399 destinations by category, regency, ticket price and rating.')} />
        </div>
        <div className="jjk-explore">
          {/* Filter rail */}
          <aside className="jjk-rail">
            <SearchBar size="sm" value={query} onChange={setQuery} placeholder={L(lang, 'Cari nama tempat…', 'Search by name…')} />
            <div className="jjk-rail__group">
              <span className="jjk-rail__label">{L(lang, 'Kategori', 'Category')}</span>
              <div className="jjk-rail__chips">
                {CATEGORIES.map((c) => <Chip key={c.key} size="sm" label={lang === 'en' ? c.en : c.id} selected={cats.has(c.id)} onClick={() => toggleCat(c.id)} />)}
              </div>
            </div>
            <div className="jjk-rail__divider" />
            <div className="jjk-rail__group">
              <span className="jjk-rail__label">{L(lang, 'Daerah', 'Regency')}</span>
              <Select value={regency} onChange={setRegency} fullWidth placeholder={L(lang, 'Semua daerah', 'All regencies')}
                options={['Kota Yogyakarta', 'Sleman', 'Bantul', 'Gunungkidul', 'Kulon Progo']} />
            </div>
            <div className="jjk-rail__group">
              <Range label={L(lang, 'Harga tiket maks.', 'Max ticket price')} value={budget} onChange={setBudget} />
              <Toggle checked={freeOnly} onChange={setFreeOnly} label={L(lang, 'Hanya yang Gratis', 'Free only')} />
            </div>
            <div className="jjk-rail__divider" />
            <div className="jjk-rail__group">
              <span className="jjk-rail__label">{L(lang, 'Rating minimum', 'Minimum rating')}</span>
              <div className="jjk-rail__chips">
                {[{ v: 0, l: L(lang, 'Semua', 'Any') }, { v: 4.0, l: '4.0+' }, { v: 4.5, l: '4.5+' }].map((o) =>
                  <Chip key={o.v} size="sm" label={o.l} selected={minRating === o.v} onClick={() => setMinRating(o.v)} />)}
              </div>
            </div>
          </aside>

          {/* Results */}
          <div className="jjk-results">
            <div className="jjk-results__top">
              <div className="jjk-results__count"><b>{list.length}</b> {L(lang, 'tempat ditemukan', 'places found')}</div>
              <div className="jjk-results__tools">
                <Select value={sort} onChange={setSort} options={[
                  { value: 'rating', label: L(lang, 'Rating tertinggi', 'Highest rated') },
                  { value: 'price', label: L(lang, 'Harga termurah', 'Cheapest') },
                  { value: 'pop', label: L(lang, 'Paling populer', 'Most popular') },
                  { value: 'az', label: 'A–Z' }]} />
                <div className="jjk-viewtoggle">
                  <button className={view === 'grid' ? 'is-active' : ''} onClick={() => setView('grid')}><Icon name="grid" size={15} />{L(lang, 'Grid', 'Grid')}</button>
                  <button className={view === 'map' ? 'is-active' : ''} onClick={() => setView('map')}><Icon name="map" size={15} />{L(lang, 'Peta', 'Map')}</button>
                </div>
              </div>
            </div>
            {activeFilters.length ? (
              <div className="jjk-activechips">
                {activeFilters.map((f) => (
                  <button key={f.k} className="jj-chip jj-chip--sm" aria-pressed="true" onClick={f.clear}>
                    {f.label}<span className="jj-chip__x"><Icon name="x" size={14} /></span></button>))}
                <button className="jj-sechead__action" style={{ fontSize: 13 }} onClick={resetAll}>{L(lang, 'Hapus semua', 'Clear all')}</button>
              </div>
            ) : null}

            {list.length === 0 ? (
              <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)' }}>
                <div className="jj-empty">
                  <span className="jj-empty__icon"><Icon name="search" size={28} /></span>
                  <div className="jj-empty__title">{L(lang, 'Tidak ada hasil', 'No results')}</div>
                  <p className="jj-empty__msg">{L(lang, 'Maaf, tidak ada tempat yang cocok. Coba ubah atau hapus sebagian filter.', 'Sorry, nothing matched. Try changing or clearing some filters.')}</p>
                  <Btn variant="outline" size="sm" onClick={resetAll}>{L(lang, 'Reset filter', 'Reset filters')}</Btn>
                </div>
              </div>
            ) : view === 'grid' ? (
              <div className="jjk-grid jjk-grid--results">
                {list.map((p) => <DestinationCard key={p.id} place={p} lang={lang} saved={saved.has(p.id)} onSave={onSave} onOpen={onOpen} />)}
              </div>
            ) : (
              <div className="jjk-map">
                <div className="jjk-map__bg" /><div className="jjk-map__grid" />
                {list.map((p) => (
                  <button key={p.id} className="jjk-pin" style={pinPos(p)} onClick={() => setActivePin(p)} aria-label={p.name}>
                    <span className="jjk-pin__dot" />
                  </button>
                ))}
                {activePin ? (
                  <div className="jjk-mapcard">
                    <DestinationCard place={activePin} variant="mini" lang={lang} saved={saved.has(activePin.id)} onSave={onSave} onOpen={onOpen} />
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
  window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { Explore });
})();
