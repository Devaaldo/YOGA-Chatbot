/* Jelajah Jogja — YOGA chat.
   Talks to the real YOGA NLU backend (api/server.py). One shared <ChatThread>
   powers both the floating panel and the full-page /tanya-yoga experience.
   respond() is only an offline fallback when the API is unreachable. */
(function () {
  const U = window.JJUI;
  const { Icon, IconBtn, Bubble, QuickReply, DestinationCard, L } = U;
  const API = (typeof window !== 'undefined' && window.__API__) || 'http://localhost:8000';
  const AVATAR = (window.__resources && window.__resources.yogaAvatar) || '/assets/logo/yoga-avatar.svg';

  const norm = (s) => (s || '').toLowerCase();
  const REGIONS = [
    { keys: ['bantul'], name: 'Bantul' }, { keys: ['sleman'], name: 'Sleman' },
    { keys: ['gunungkidul', 'gunung kidul'], name: 'Gunungkidul' },
    { keys: ['kulon progo', 'kulonprogo'], name: 'Kulon Progo' },
    { keys: ['kota', 'yogyakarta', 'jogja', 'malioboro'], name: 'Kota Yogyakarta' },
  ];
  const topRated = (list, n = 3) => [...list].sort((a, b) => (b.rating || 0) - (a.rating || 0)).slice(0, n);

  // Offline fallback responder (used only if the API is unreachable).
  function respond(text, lang) {
    const PLACES = window.JJ.PLACES;
    const t = norm(text);
    if (/\b(halo|hai|hi|hello|hey|selamat)\b/.test(t) && t.split(' ').length <= 3)
      return { reply: L(lang, 'Halo! Saya YOGA, asisten wisata Yogyakarta. Mau cari wisata apa hari ini?', "Hi! I'm YOGA, your Yogyakarta travel assistant. What would you like to find today?"), places: [] };
    if (/\binfo\b|tentang|about|detail/.test(t)) {
      const hit = PLACES.find((p) => t.includes(norm(p.name)) || norm(p.name).split(' ').some((w) => w.length > 4 && t.includes(w)));
      if (hit) return { reply: L(lang, `Ini ${hit.name}:`, `Here's ${hit.name}:`), places: [hit] };
    }
    if (/lokasi|location|di mana|dimana|where/.test(t)) {
      const hit = PLACES.find((p) => t.includes(norm(p.name)) || norm(p.name).split(' ').some((w) => w.length > 4 && t.includes(w)));
      if (hit) return { reply: L(lang, `${hit.name} ada di ${hit.regency}.`, `${hit.name} is in ${hit.regency}.`), places: [hit] };
    }
    const region = REGIONS.find((r) => r.keys.some((k) => t.includes(k)));
    if (/pantai|beach/.test(t)) {
      let list = PLACES.filter((p) => p.tag === 'Pantai');
      if (region) list = list.filter((p) => p.regency === region.name);
      if (list.length) return { reply: L(lang, `Pantai terbaik${region ? ' di ' + region.name : ''}:`, `Top beaches${region ? ' in ' + region.name : ''}:`), places: topRated(list) };
    }
    if (/candi|temple/.test(t)) {
      const list = PLACES.filter((p) => p.tag === 'Candi');
      if (list.length) return { reply: L(lang, 'Candi & situs bersejarah pilihan:', 'Top temples & historic sites:'), places: topRated(list) };
    }
    if (/murah|hemat|budget|cheap|tiket/.test(t)) {
      const list = [...PLACES].filter((p) => p.priceWeekday != null && p.priceWeekday > 0).sort((a, b) => a.priceWeekday - b.priceWeekday);
      return { reply: L(lang, 'Wisata dengan tiket paling ramah kantong:', 'The most budget-friendly spots:'), places: list.slice(0, 3) };
    }
    if (/rating|terbaik|top|bagus|best/.test(t))
      return { reply: L(lang, 'Wisata dengan rating terbaik di Jogja:', 'The highest-rated places in Jogja:'), places: topRated(PLACES) };
    if (region || /rekomendasi|recommend|wisata|saran/.test(t)) {
      let list = PLACES;
      if (region) list = list.filter((p) => p.regency === region.name);
      return { reply: L(lang, `Rekomendasi wisata${region ? ' di ' + region.name : ' terbaik'}:`, `Recommended places${region ? ' in ' + region.name : ''}:`), places: topRated(list.length ? list : PLACES) };
    }
    return { reply: L(lang, 'Maaf, saya kurang paham. Coba tanya rekomendasi, pantai di suatu daerah, tiket murah, atau info sebuah tempat.', "Sorry, I didn't quite get that. Try recommendations, beaches in a region, budget tickets, or info about a place."), places: [] };
  }

  const QUICK = (lang) => lang === 'en'
    ? ['Beaches in Gunungkidul', 'Top rated', 'Budget tickets', 'Plan a 2-day trip', 'About Candi Prambanan']
    : ['Wisata pantai di Gunungkidul', 'Rating terbaik', 'Tiket murah', 'Buatkan itinerary 2 hari', 'Info Candi Prambanan'];

  const greeting = (lang) => L(lang,
    'Halo! Saya YOGA, pemandu wisata Yogyakarta. Tanyakan rekomendasi, pantai di daerah tertentu, tiket termurah, atau info sebuah tempat.',
    "Hi! I'm YOGA, your Yogyakarta guide. Ask for recommendations, beaches in a region, the cheapest tickets, or details about a place.");

  // ---- Shared conversation core (state + body + quick replies + input) ----
  function ChatThread({ lang, saved, onSave, onOpen, onClose, askSignal, variant }) {
    const [msgs, setMsgs] = React.useState([{ from: 'yoga', text: greeting(lang) }]);
    const [input, setInput] = React.useState('');
    const [typing, setTyping] = React.useState(false);
    const bodyRef = React.useRef(null);

    const send = React.useCallback((text) => {
      if (!text || !text.trim()) return;
      setMsgs((m) => [...m, { from: 'user', text, time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) }]);
      setInput('');
      setTyping(true);
      fetch(API + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, lang }),
      })
        .then((res) => { if (!res.ok) throw new Error('api'); return res.json(); })
        .then((r) => { setTyping(false); setMsgs((m) => [...m, { from: 'yoga', text: r.reply, places: r.places || [] }]); })
        .catch(() => { const r = respond(text, lang); setTyping(false); setMsgs((m) => [...m, { from: 'yoga', text: r.reply, places: r.places }]); });
    }, [lang]);

    React.useEffect(() => { if (askSignal && askSignal.text) send(askSignal.text); }, [askSignal && askSignal.n]);
    React.useEffect(() => { if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight; }, [msgs, typing]);

    const openCard = (pl) => { if (onClose) onClose(); onOpen(pl); };
    const cardWidth = variant === 'page' ? { width: '100%', maxWidth: 460 } : { width: '88%' };

    return (
      <React.Fragment>
        <div className={'jjk-chat__body' + (variant === 'page' ? ' jjk-chatpage__body' : '')} ref={bodyRef}>
          {msgs.map((m, i) => (
            <React.Fragment key={i}>
              <Bubble from={m.from} time={m.time}>{m.text}</Bubble>
              {m.places && m.places.length ? m.places.map((p) => (
                <div key={p.id} style={{ alignSelf: 'flex-start', ...cardWidth }}>
                  <DestinationCard place={p} variant="mini" lang={lang} saved={saved.has(p.id)} onSave={onSave} onOpen={openCard} />
                </div>
              )) : null}
            </React.Fragment>
          ))}
          {typing ? <Bubble from="yoga" typing /> : null}
        </div>
        {msgs.length <= 1 ? (
          <div className="jjk-chat__qr">{QUICK(lang).map((q, i) => <QuickReply key={i} label={q} onClick={() => send(q)} />)}</div>
        ) : null}
        <form className="jjk-chat__foot" onSubmit={(e) => { e.preventDefault(); send(input); }}>
          <input className="jjk-chat__input" value={input} onChange={(e) => setInput(e.target.value)} placeholder={L(lang, 'Tulis pesan…', 'Type a message…')} aria-label={L(lang, 'Tulis pesan', 'Type a message')} />
          <IconBtn variant="soft" icon={<Icon name="send" size={18} />} label="Kirim" onClick={() => send(input)} />
        </form>
      </React.Fragment>
    );
  }

  // ---- Floating panel ----
  function ChatPanel({ open, lang, onClose, askSignal, saved, onSave, onOpen }) {
    if (!open) return null;
    return (
      <div className="jjk-chat" role="dialog" aria-label="YOGA chat">
        <div className="jjk-chat__head">
          <img src={AVATAR} alt="YOGA" />
          <div><div className="jjk-chat__name">YOGA</div><div className="jjk-chat__status">{L(lang, 'Asisten wisata Yogyakarta', 'Yogyakarta travel assistant')}</div></div>
          <span className="jjk-chat__close"><IconBtn variant="ghost" size="sm" icon={<Icon name="x" size={18} />} label="Tutup" onClick={onClose} /></span>
        </div>
        <ChatThread lang={lang} saved={saved} onSave={onSave} onOpen={onOpen} onClose={onClose} askSignal={askSignal} variant="panel" />
      </div>
    );
  }

  // ---- Full-page experience (/tanya-yoga) ----
  function ChatPage({ lang, saved, onSave, onOpen, askSignal }) {
    return (
      <div className="jjk-chatpage">
        <div className="jjk-container jjk-chatpage__inner">
          <header className="jjk-chatpage__hero">
            <img src={AVATAR} alt="YOGA" className="jjk-chatpage__avatar" />
            <div>
              <span className="jjk-chatpage__badge">{L(lang, 'Asisten AI', 'AI assistant')}</span>
              <h1 className="jjk-chatpage__title">{L(lang, 'Ngobrol dengan ', 'Chat with ')}<em>YOGA</em></h1>
              <p className="jjk-chatpage__sub">{L(lang,
                'Pemandu wisata bertenaga AI. Tanya rekomendasi, kategori, harga, rating, lokasi, atau rencana perjalanan di Yogyakarta — dijawab dari 3.399 tempat wisata.',
                'An AI-powered guide. Ask for recommendations, categories, prices, ratings, locations, or trip plans around Yogyakarta — answered from 3,399 real places.')}</p>
            </div>
          </header>
          <div className="jjk-chatpage__card">
            <ChatThread lang={lang} saved={saved} onSave={onSave} onOpen={onOpen} askSignal={askSignal} variant="page" />
          </div>
        </div>
      </div>
    );
  }

  window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { ChatPanel, ChatPage });
})();
