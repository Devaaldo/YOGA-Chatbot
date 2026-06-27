/* Jelajah Jogja — About (Tentang) */
(function () {
  const U = window.JJUI;
  const { Icon, Btn, SectionHeader, L } = U;

  function About({ lang, onAsk, go }) {
    const steps = [
      { icon: 'bank', t: L(lang, 'Kategori', 'Categories'), d: L(lang, 'Alam, Kuliner, Budaya & Sejarah, Buatan, Wisata Air, dan Wisata Umum — enam kategori untuk setiap suasana hati.', 'Nature, Culinary, Culture & History, Recreation, Water and General — six categories for every mood.') },
      { icon: 'star', t: L(lang, 'Rating', 'Ratings'), d: L(lang, 'Urutkan berdasarkan rating dan jumlah ulasan asli dari ribuan wisatawan.', 'Sort by real ratings and review counts from thousands of travellers.') },
      { icon: 'wallet', t: L(lang, 'Anggaran', 'Budget'), d: L(lang, 'Saring berdasarkan harga tiket — termasuk yang Gratis — agar pas dengan kantong.', 'Filter by ticket price — including Free spots — to fit any budget.') },
      { icon: 'mapPin', t: L(lang, 'Lokasi', 'Location'), d: L(lang, 'Cari per kabupaten/kota dan kecamatan, lengkap dengan koordinat dan tautan peta.', 'Search by regency and sub-district, complete with coordinates and map links.') },
    ];
    const stats = [
      { n: '3.399', l: L(lang, 'Tempat wisata', 'Destinations') },
      { n: '5', l: L(lang, 'Kabupaten / Kota', 'Regencies') },
      { n: '78', l: L(lang, 'Kecamatan', 'Sub-districts') },
      { n: '6', l: L(lang, 'Kategori', 'Categories') },
    ];

    return (
      <div className="jjk-section jjk-container">
        <div className="jjk-about__hero">
          <div className="jjk-eyebrow" style={{ marginBottom: 16 }}>{L(lang, 'Tentang Jelajah Jogja', 'About Jelajah Jogja')}</div>
          <h1>{L(lang, <>Pemandu wisata Yogyakarta, <em>untuk semua</em>.</>, <>A guide to Yogyakarta, <em>for everyone</em>.</>)}</h1>
          <p className="jj-prose" style={{ margin: '0 auto', textAlign: 'center', fontSize: 18 }}>
            {L(lang,
              'Jelajah Jogja menyatukan 3.399 tempat wisata Daerah Istimewa Yogyakarta dalam satu pengalaman yang hangat dan mudah — ditemani YOGA, asisten yang memberi rekomendasi, menyaring berdasarkan kategori, harga, dan rating, serta menjawab pertanyaan lokasi dan detail.',
              'Jelajah Jogja brings all 3,399 destinations of the Special Region of Yogyakarta into one warm, effortless experience — guided by YOGA, an assistant that recommends places, filters by category, price and rating, and answers location and detail questions.')}
          </p>
        </div>

        <section style={{ marginTop: 56 }}>
          <SectionHeader eyebrow={L(lang, 'Cara Kerja', 'How it works')} title={L(lang, 'Empat cara menemukan tempat', 'Four ways to find your place')} />
          <div className="jjk-steps" style={{ marginTop: 24 }}>
            {steps.map((s, i) => (
              <div className="jjk-step" key={i}>
                <span className="jjk-step__icon"><Icon name={s.icon} size={22} fill={s.icon === 'star' ? 'currentColor' : 'none'} stroke={s.icon === 'star' ? 0 : 1.75} /></span>
                <div><h4>{s.t}</h4><p>{s.d}</p></div>
              </div>
            ))}
          </div>
        </section>

        <section style={{ marginTop: 56 }}>
          <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-2xl)', padding: '40px 32px', boxShadow: 'var(--shadow-sm)' }}>
            <div className="jjk-stats">
              {stats.map((s, i) => <div className="jjk-stat" key={i}><div className="jjk-stat__n">{s.n}</div><div className="jjk-stat__l">{s.l}</div></div>)}
            </div>
            <p style={{ textAlign: 'center', marginTop: 26, fontFamily: 'var(--font-sans)', fontSize: 13.5, color: 'var(--color-text-muted)', maxWidth: 620, marginInline: 'auto', lineHeight: 1.6 }}>
              {L(lang, 'Data wisata bersumber dari dataset Kaggle Indonesia Tourism dan pengayaan Geoapify Places. Sebagian tempat belum memiliki rating, harga, atau kontak — kami menampilkan hanya yang tersedia.',
                'Tourism data is sourced from the Kaggle Indonesia Tourism dataset enriched with the Geoapify Places API. Some places have no rating, price or contact yet — we only show what exists.')}
            </p>
          </div>
        </section>

        <section style={{ marginTop: 48, textAlign: 'center' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 28, color: 'var(--color-text)', marginBottom: 14 }}>{L(lang, 'Siap menjelajah?', 'Ready to explore?')}</h3>
          <div style={{ display: 'inline-flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Btn variant="primary" size="lg" iconRight={<Icon name="arrowRight" size={18} />} onClick={() => go('explore')}>{L(lang, 'Mulai Jelajah', 'Start exploring')}</Btn>
            <Btn variant="outline" size="lg" iconLeft={<Icon name="sparkles" size={18} />} onClick={() => onAsk()}>{L(lang, 'Tanya YOGA', 'Ask YOGA')}</Btn>
          </div>
        </section>
      </div>
    );
  }
  window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { About });
})();
