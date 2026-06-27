/* Jelajah Jogja — YOGA chat panel.
   Talks to the real YOGA NLU backend (api/server.py). The built-in respond()
   below is kept ONLY as an offline fallback when the API is unreachable. */
(function () {
  const U = window.JJUI;
  const { Icon, IconBtn, Bubble, QuickReply, DestinationCard, L } = U;
  const API = (typeof window !== 'undefined' && window.__API__) || 'http://localhost:8000';

  const norm = (s) => (s || '').toLowerCase();
  const REGIONS = [
    { keys: ['bantul'], name: 'Bantul' }, { keys: ['sleman'], name: 'Sleman' },
    { keys: ['gunungkidul', 'gunung kidul'], name: 'Gunungkidul' },
    { keys: ['kulon progo', 'kulonprogo'], name: 'Kulon Progo' },
    { keys: ['kota', 'yogyakarta', 'jogja', 'malioboro'], name: 'Kota Yogyakarta' },
  ];
  const topRated = (list, n = 3) => [...list].sort((a, b) => (b.rating || 0) - (a.rating || 0)).slice(0, n);

  function respond(text, lang) {
    const PLACES = window.JJ.PLACES;
    const t = norm(text);
    // greeting
    if (/\b(halo|hai|hi|hello|hey|selamat)\b/.test(t) && t.split(' ').length <= 3)
      return { reply: L(lang, 'Halo! Saya YOGA, asisten wisata Yogyakarta. Mau cari wisata apa hari ini?', "Hi! I'm YOGA, your Yogyakarta travel assistant. What would you like to find today?"), places: [] };
    // info detail
    if (/\binfo\b|tentang|about|detail/.test(t)) {
      const hit = PLACES.find((p) => t.includes(norm(p.name)) || norm(p.name).split(' ').some((w) => w.length > 4 && t.includes(w)));
      if (hit) return { reply: L(lang, `Ini ${hit.name}:`, `Here's ${hit.name}:`), places: [hit] };
    }
    // location
    if (/lokasi|location|di mana|dimana|where/.test(t)) {
      const hit = PLACES.find((p) => t.includes(norm(p.name)) || norm(p.name).split(' ').some((w) => w.length > 4 && t.includes(w)));
      if (hit) return { reply: L(lang, `${hit.name} ada di ${hit.regency}. Ketuk untuk peta & koordinat:`, `${hit.name} is in ${hit.regency}. Tap for the map & coordinates:`), places: [hit] };
    }
    const region = REGIONS.find((r) => r.keys.some((k) => t.includes(k)));
    // beach / category
    if (/pantai|beach/.test(t)) {
      let list = PLACES.filter((p) => p.tag === 'Pantai');
      if (region) list = list.filter((p) => p.regency === region.name);
      if (list.length) return { reply: L(lang, `Pantai terbaik${region ? ' di ' + region.name : ''}:`, `Top beaches${region ? ' in ' + region.name : ''}:`), places: topRated(list) };
    }
    if (/candi|temple/.test(t)) {
      const list = PLACES.filter((p) => p.tag === 'Candi' || p.tag === 'Situs');
      if (list.length) return { reply: L(lang, 'Candi & situs bersejarah pilihan:', 'Top temples & historic sites:'), places: topRated(list) };
    }
    // budget
    if (/murah|hemat|budget|cheap|tiket/.test(t)) {
      const list = [...PLACES].filter((p) => p.priceWeekday != null && p.priceWeekday > 0).sort((a, b) => a.priceWeekday - b.priceWeekday);
      return { reply: L(lang, 'Wisata dengan tiket paling ramah kantong:', 'The most budget-friendly spots:'), places: list.slice(0, 3) };
    }
    // rating
    if (/rating|terbaik|top|bagus|best/.test(t))
      return { reply: L(lang, 'Wisata dengan rating terbaik di Jogja:', 'The highest-rated places in Jogja:'), places: topRated(PLACES) };
    // recommendation (with region)
    if (region || /rekomendasi|recommend|wisata|saran/.test(t)) {
      let list = PLACES;
      if (region) list = list.filter((p) => p.regency === region.name);
      return { reply: L(lang, `Rekomendasi wisata${region ? ' di ' + region.name : ' terbaik'}:`, `Recommended places${region ? ' in ' + region.name : ''}:`), places: topRated(list.length ? list : PLACES) };
    }
    // planner
    if (/rencana|itinerary|plan|hari/.test(t))
      return { reply: L(lang, 'Untuk hari pertama, coba Tugu Pal Putih lalu Malioboro, lalu senja di Tebing Breksi. Mau saya tambahkan ke Trip Planner?', 'For day one, try Tugu Pal Putih then Malioboro, and sunset at Tebing Breksi. Want me to add these to your Trip Planner?'), places: topRated(PLACES, 2) };
    // fallback
    return { reply: L(lang, 'Maaf, saya kurang paham. Saya spesialis wisata Yogyakarta — coba tanya rekomendasi, pantai di suatu daerah, tiket murah, atau info sebuah tempat.', "Sorry, I didn't quite get that. I specialise in Yogyakarta travel — try asking for recommendations, beaches in a region, budget tickets, or info about a place."), places: [] };
  }

  function ChatPanel({ open, lang, onClose, askSignal, saved, onSave, onOpen }) {
    const [msgs, setMsgs] = React.useState([]);
    const [input, setInput] = React.useState('');
    const [typing, setTyping] = React.useState(false);
    const bodyRef = React.useRef(null);
    const seeded = React.useRef(false);

    React.useEffect(() => {
      if (open && !seeded.current) {
        seeded.current = true;
        setMsgs([{ from: 'yoga', text: L(lang, 'Halo! Saya YOGA, pemandu wisata Yogyakarta. Tanyakan rekomendasi, pantai di daerah tertentu, tiket termurah, atau info sebuah tempat.', "Hi! I'm YOGA, your Yogyakarta guide. Ask for recommendations, beaches in a region, the cheapest tickets, or details about a place.") }]);
      }
    }, [open, lang]);

    const send = React.useCallback((text) => {
      if (!text || !text.trim()) return;
      setMsgs((m) => [...m, { from: 'user', text, time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) }]);
      setInput('');
      setTyping(true);
      // Call the real YOGA NLU backend; fall back to the local sample responder
      // if the API is offline so the design still demos without a server.
      fetch(API + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, lang }),
      })
        .then((res) => { if (!res.ok) throw new Error('api'); return res.json(); })
        .then((r) => {
          setTyping(false);
          setMsgs((m) => [...m, { from: 'yoga', text: r.reply, places: r.places || [] }]);
        })
        .catch(() => {
          const r = respond(text, lang);
          setTyping(false);
          setMsgs((m) => [...m, { from: 'yoga', text: r.reply, places: r.places }]);
        });
    }, [lang]);

    React.useEffect(() => { if (askSignal && askSignal.text) send(askSignal.text); }, [askSignal && askSignal.n]);
    React.useEffect(() => { if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight; }, [msgs, typing]);

    if (!open) return null;
    const quick = lang === 'en'
      ? ['Beaches in Gunungkidul', 'Top rated', 'Budget tickets', 'About Candi Prambanan']
      : ['Wisata pantai di Gunungkidul', 'Rating terbaik', 'Tiket murah', 'Info Candi Prambanan'];

    return (
      <div className="jjk-chat" role="dialog" aria-label="YOGA chat">
        <div className="jjk-chat__head">
          <img src={(window.__resources && window.__resources.yogaAvatar) || "../../assets/logo/yoga-avatar.svg"} alt="YOGA" />
          <div><div className="jjk-chat__name">YOGA</div><div className="jjk-chat__status">{L(lang, 'Asisten wisata Yogyakarta', 'Yogyakarta travel assistant')}</div></div>
          <span className="jjk-chat__close"><IconBtn variant="ghost" size="sm" icon={<Icon name="x" size={18} />} label="Tutup" onClick={onClose} /></span>
        </div>
        <div className="jjk-chat__body" ref={bodyRef}>
          {msgs.map((m, i) => (
            <React.Fragment key={i}>
              <Bubble from={m.from} time={m.time}>{m.text}</Bubble>
              {m.places && m.places.length ? m.places.map((p) => (
                <div key={p.id} style={{ alignSelf: 'flex-start', width: '88%' }}>
                  <DestinationCard place={p} variant="mini" lang={lang} saved={saved.has(p.id)} onSave={onSave} onOpen={(pl) => { onClose(); onOpen(pl); }} />
                </div>
              )) : null}
            </React.Fragment>
          ))}
          {typing ? <Bubble from="yoga" typing /> : null}
        </div>
        {msgs.length <= 1 ? (
          <div className="jjk-chat__qr">{quick.map((q, i) => <QuickReply key={i} label={q} onClick={() => send(q)} />)}</div>
        ) : null}
        <form className="jjk-chat__foot" onSubmit={(e) => { e.preventDefault(); send(input); }}>
          <input className="jjk-chat__input" value={input} onChange={(e) => setInput(e.target.value)} placeholder={L(lang, 'Tulis pesan…', 'Type a message…')} aria-label={L(lang, 'Tulis pesan', 'Type a message')} />
          <IconBtn variant="soft" icon={<Icon name="send" size={18} />} label="Kirim" onClick={() => send(input)} />
        </form>
      </div>
    );
  }
  window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { ChatPanel });
})();
