/* Jelajah Jogja UI Kit — shared primitives (kit-local recreations of the DS
   components, using the same jj-* classes). Exposed on window for the screens.
   In production import the real components from window.JelajahJogjaDesignSystem_… */

/* ---------- icons (Lucide-style) ---------- */
const ICON = {
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  heart: '<path d="M20.8 6.6a5 5 0 0 0-7.1 0L12 8.3l-1.7-1.7a5 5 0 1 0-7.1 7.1L12 22l8.8-8.3a5 5 0 0 0 0-7.1z"/>',
  sliders: '<line x1="4" y1="8" x2="20" y2="8"/><line x1="4" y1="16" x2="20" y2="16"/><circle cx="9" cy="8" r="2.4" fill="currentColor"/><circle cx="15" cy="16" r="2.4" fill="currentColor"/>',
  mapPin: '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  map: '<path d="M9 4 2 7v13l7-3 6 3 7-3V4l-7 3-6-3Z"/><path d="M9 4v13M15 7v13"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  send: '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18Z"/>',
  chevronRight: '<path d="m9 6 6 6-6 6"/>',
  mountain: '<path d="m8 3 4 8 5-5 5 14H2L8 3z"/>',
  fork: '<path d="M3 2v7a3 3 0 0 0 6 0V2M6 9v13M21 2v20M18 2c-1.7 0-3 2-3 5s1.3 5 3 5"/>',
  bank: '<path d="M3 21h18M5 21V10M19 21V10M3 10l9-7 9 7M9 21v-6h6v6"/>',
  ferris: '<circle cx="12" cy="9" r="7"/><path d="M12 9v13M5.5 5.5 12 9l6.5-3.5M5.5 12.5 12 9l6.5 3.5M12 2v3"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5 5-2Z"/>',
  waves: '<path d="M2 7c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2 2 2 4 2M2 13c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2 2 2 4 2M2 19c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
  phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>',
  link: '<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1.5 1.5M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1.5-1.5"/>',
  sparkles: '<path d="M12 3v4M12 17v4M5 12H1M23 12h-4M6.3 6.3 4 4M20 20l-2.3-2.3M6.3 17.7 4 20M20 4l-2.3 2.3"/><circle cx="12" cy="12" r="3"/>',
  route: '<circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M9 19h6a4 4 0 0 0 0-8H9a4 4 0 0 1 0-8h0"/>',
  wallet: '<path d="M3 7a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2v3M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3M21 10h-5a2 2 0 0 0 0 4h5"/>',
  arrowRight: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  star: '<path d="M12 2.2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.27l-5.9 3.1 1.13-6.57L2.45 9.14l6.6-.96L12 2.2z"/>',
  grip: '<circle cx="9" cy="6" r="1.3"/><circle cx="9" cy="12" r="1.3"/><circle cx="9" cy="18" r="1.3"/><circle cx="15" cy="6" r="1.3"/><circle cx="15" cy="12" r="1.3"/><circle cx="15" cy="18" r="1.3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  instagram: '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/>',
  send2: '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/>',
};
function Icon({ name, size = 20, stroke = 1.75, fill = 'none', style }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke="currentColor" strokeWidth={stroke}
    strokeLinecap="round" strokeLinejoin="round" style={style} dangerouslySetInnerHTML={{ __html: ICON[name] || '' }} />;
}

/* ---------- helpers ---------- */
const fmtIDR = (n) => 'Rp' + Number(n).toLocaleString('id-ID');
const L = (lang, id, en) => (lang === 'en' ? en : id);
const sceneStyle = (scene) => ({ background: `var(--photo-${scene || 'culture'})` });

/* ---------- buttons ---------- */
function Btn({ children, variant = 'primary', size = 'md', iconLeft, iconRight, block, onClick, ...r }) {
  const cls = ['jj-btn', `jj-btn--${variant}`, size !== 'md' ? `jj-btn--${size}` : '', block ? 'jj-btn--block' : ''].filter(Boolean).join(' ');
  return <button className={cls} onClick={onClick} {...r}>
    {iconLeft ? <span className="jj-btn__i">{iconLeft}</span> : null}{children ? <span>{children}</span> : null}
    {iconRight ? <span className="jj-btn__i">{iconRight}</span> : null}
  </button>;
}
function IconBtn({ icon, variant = 'ghost', size = 'md', label, onClick, ...r }) {
  const cls = ['jj-iconbtn', `jj-iconbtn--${variant}`, size !== 'md' ? `jj-iconbtn--${size}` : ''].filter(Boolean).join(' ');
  return <button className={cls} aria-label={label} onClick={onClick} {...r}>{icon}</button>;
}

/* ---------- chips / badges ---------- */
function Chip({ label, selected, onClick, icon, count, size }) {
  return <button className={['jj-chip', size === 'sm' ? 'jj-chip--sm' : ''].filter(Boolean).join(' ')} aria-pressed={!!selected} onClick={onClick}>
    {icon ? <span className="jj-chip__i">{icon}</span> : null}<span>{label}</span>
    {count != null ? <span className="jj-chip__count">{Number(count).toLocaleString('id-ID')}</span> : null}
  </button>;
}
function Badge({ children, variant = 'neutral', dot }) {
  return <span className={`jj-badge jj-badge--${variant}`}>{dot ? <span className="jj-badge__dot" /> : null}{children}</span>;
}

/* ---------- stars / price / heart ---------- */
function Star({ fill, size }) {
  const svg = <Icon name="star" size={size} fill="currentColor" stroke={0} />;
  return <span className="jj-star" style={{ width: size, height: size }}>{svg}
    <span className="jj-star__fill" style={{ width: `${Math.max(0, Math.min(1, fill)) * 100}%` }}>
      <span style={{ display: 'block', width: size, height: size }}>{svg}</span>
    </span></span>;
}
function Stars({ value, count, size = 15, lang = 'id', showValue = true }) {
  if (value == null || value === 0) return <span className="jj-stars"><span className="jj-stars__empty">{L(lang, 'Belum ada rating', 'No rating yet')}</span></span>;
  const arr = []; for (let i = 0; i < 5; i++) arr.push(<Star key={i} fill={value - i} size={size} />);
  return <span className="jj-stars"><span className="jj-stars__row">{arr}</span>
    {showValue ? <span className="jj-stars__val">{value.toFixed(1)}</span> : null}
    {count != null ? <span className="jj-stars__count">({Number(count).toLocaleString(lang === 'en' ? 'en-US' : 'id-ID')})</span> : null}</span>;
}
function Price({ weekday, lang = 'id', variant = 'inline', showFrom }) {
  let kind = 'paid', body;
  if (weekday == null) { kind = 'na'; body = <span>{L(lang, 'Harga tidak tersedia', 'Price unavailable')}</span>; }
  else if (weekday === 0) { kind = 'free'; body = <span>{L(lang, 'Gratis', 'Free')}</span>; }
  else body = <>{showFrom ? <span className="jj-price__from">{L(lang, 'mulai', 'from')}</span> : null}<span>{fmtIDR(weekday)}</span></>;
  return <span className={['jj-price', `jj-price--${kind}`, variant === 'badge' ? 'jj-price--badge' : ''].filter(Boolean).join(' ')}>{body}</span>;
}
function Heart({ saved, onChange, size }) {
  return <button className={['jj-heart', size === 'sm' ? 'jj-heart--sm' : ''].filter(Boolean).join(' ')} aria-pressed={!!saved}
    aria-label="Simpan" onClick={(e) => { e.preventDefault(); e.stopPropagation(); onChange && onChange(!saved); }}>
    <Icon name="heart" size={18} fill={saved ? 'currentColor' : 'none'} stroke={1.9} /></button>;
}

/* ---------- inputs ---------- */
function SearchBar({ value, onChange, onSubmit, placeholder, size = 'lg', action }) {
  return <form className={['jj-search', size === 'sm' ? 'jj-search--sm' : ''].filter(Boolean).join(' ')} role="search"
    onSubmit={(e) => { e.preventDefault(); onSubmit && onSubmit(value); }}>
    <span className="jj-search__icon"><Icon name="search" size={size === 'sm' ? 18 : 20} stroke={1.9} /></span>
    <input className="jj-search__input" type="search" value={value || ''} placeholder={placeholder}
      onChange={(e) => onChange && onChange(e.target.value)} aria-label={placeholder} />
    {action}</form>;
}
function Select({ value, onChange, options = [], placeholder, fullWidth }) {
  const opts = options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o));
  return <span className="jj-select" style={fullWidth ? { display: 'flex', width: '100%' } : null}>
    <select value={value} onChange={(e) => onChange && onChange(e.target.value)}>
      {placeholder ? <option value="">{placeholder}</option> : null}
      {opts.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select><span className="jj-select__chev"><Icon name="chevronRight" size={18} style={{ transform: 'rotate(90deg)' }} /></span></span>;
}
function Range({ label, min = 0, max = 100000, step = 5000, value = 50000, onChange }) {
  const pct = max > min ? ((value - min) / (max - min)) * 100 : 0;
  const shown = value === 0 ? 'Gratis' : fmtIDR(value) + (value >= max ? '+' : '');
  return <div className="jj-range">
    <div className="jj-range__head"><span className="jj-range__label">{label}</span><span className="jj-range__val">{shown}</span></div>
    <input type="range" min={min} max={max} step={step} value={value} style={{ '--jj-pct': pct + '%' }}
      onChange={(e) => onChange && onChange(Number(e.target.value))} aria-label={label} /></div>;
}
function Toggle({ checked, onChange, label }) {
  return <label className="jj-switch"><input type="checkbox" checked={!!checked} onChange={(e) => onChange && onChange(e.target.checked)} />
    <span className="jj-switch__track"><span className="jj-switch__thumb" /></span>{label ? <span>{label}</span> : null}</label>;
}
function LangToggle({ value = 'id', onChange }) {
  return <div className="jj-lang" role="group" aria-label="Language">
    <button className="jj-lang__btn" aria-pressed={value === 'id'} onClick={() => onChange('id')}>ID</button>
    <button className="jj-lang__btn" aria-pressed={value === 'en'} onClick={() => onChange('en')}>EN</button></div>;
}

/* ---------- cards ---------- */
function DestinationCard({ place, lang = 'id', saved, onSave, onOpen, variant = 'grid' }) {
  const mini = variant === 'mini';
  const open = (e) => { if (e) e.preventDefault(); onOpen && onOpen(place); };
  return <article className={['jj-dcard', mini ? 'jj-dcard--mini' : ''].filter(Boolean).join(' ')}>
    <a className="jj-dcard__media" onClick={open} aria-label={place.name}>
      <span className="jj-dcard__img" style={sceneStyle(place.scene)} /><span className="jj-dcard__batik jj-batik" />
      {place.tag ? <span className="jj-dcard__tag"><Badge variant="solid">{place.tag}</Badge></span> : null}
      <span className="jj-dcard__heart"><Heart saved={saved} size={mini ? 'sm' : 'md'} onChange={() => onSave && onSave(place)} /></span>
    </a>
    <div className="jj-dcard__body">
      <div className="jj-dcard__loc">{place.regency}</div>
      <a className="jj-dcard__name" onClick={open}>{place.name}</a>
      <Stars value={place.rating} count={place.votes} lang={lang} size={mini ? 13 : 15} />
      <div className="jj-dcard__foot">
        <Price weekday={place.priceWeekday} lang={lang} showFrom variant="badge" />
        {!mini ? <span className="jj-dcard__detail" onClick={open} style={{ cursor: 'pointer' }}>{L(lang, 'Detail', 'Detail')} <span aria-hidden="true">→</span></span> : null}
      </div>
    </div></article>;
}
function CategoryTile({ name, count, iconName, tone = 'primary', lang = 'id', onClick }) {
  return <a className={['jj-cattile', tone !== 'primary' ? `jj-cattile--${tone}` : ''].filter(Boolean).join(' ')} onClick={onClick}>
    <span className="jj-cattile__icon"><Icon name={iconName} size={24} /></span>
    <span className="jj-cattile__name">{name}</span>
    {count != null ? <span className="jj-cattile__count">{Number(count).toLocaleString(lang === 'en' ? 'en-US' : 'id-ID')} {L(lang, 'tempat', 'places')}</span> : null}
  </a>;
}
function RegencyCard({ regency, lang = 'id', onClick }) {
  return <a className="jj-regcard" onClick={onClick} aria-label={regency.name}>
    <span className="jj-regcard__img" style={sceneStyle(regency.scene)} /><span className="jj-regcard__batik jj-batik" /><span className="jj-regcard__scrim" />
    <span className="jj-regcard__body"><span className="jj-regcard__name">{regency.name}</span>
      <span className="jj-regcard__blurb">{regency.blurb[lang] || regency.blurb.id}</span>
      <span className="jj-regcard__count">{Number(regency.count).toLocaleString(lang === 'en' ? 'en-US' : 'id-ID')} {L(lang, 'tempat', 'places')}</span></span></a>;
}
function CollectionCard({ eyebrow, title, meta, scene = 'dusk', onClick }) {
  return <a className="jj-coll" onClick={onClick} aria-label={title}>
    <span className="jj-coll__img" style={sceneStyle(scene)} /><span className="jj-coll__batik jj-batik" /><span className="jj-coll__scrim" />
    <span className="jj-coll__body">{eyebrow ? <span className="jj-coll__eyebrow">{eyebrow}</span> : null}
      <span className="jj-coll__title">{title}</span>{meta ? <span className="jj-coll__meta">{meta}</span> : null}</span></a>;
}
function SectionHeader({ eyebrow, title, subtitle, actionLabel, onAction }) {
  return <div className="jj-sechead"><div className="jj-sechead__main">
    {eyebrow ? <span className="jj-sechead__eyebrow">{eyebrow}</span> : null}
    {title ? <h2 className="jj-sechead__title">{title}</h2> : null}
    {subtitle ? <p className="jj-sechead__sub">{subtitle}</p> : null}</div>
    {actionLabel ? <a className="jj-sechead__action" onClick={onAction}>{actionLabel} <span aria-hidden="true">→</span></a> : null}</div>;
}
function Bubble({ from = 'yoga', children, time, typing }) {
  return <div className={`jj-bubble jj-bubble--${from}`}><div className="jj-bubble__body">
    {typing ? <span className="jj-bubble__dots"><i /><i /><i /></span> : children}</div>
    {time && !typing ? <span className="jj-bubble__time">{time}</span> : null}</div>;
}
function QuickReply({ label, onClick }) {
  return <button className="jj-qreply" onClick={onClick}>{label}</button>;
}

Object.assign(window, {
  JJUI: { Icon, fmtIDR, L, sceneStyle, Btn, IconBtn, Chip, Badge, Stars, Price, Heart, SearchBar, Select, Range, Toggle, LangToggle, DestinationCard, CategoryTile, RegencyCard, CollectionCard, SectionHeader, Bubble, QuickReply },
});
