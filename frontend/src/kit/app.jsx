/* Jelajah Jogja — App shell: nav, footer, router, language & chat/planner state */
(function () {
	const U = window.JJUI;
	const S = window.JJSCREENS;
	const { Icon, Btn, IconBtn, LangToggle, L } = U;

	const NAV = [
		{ key: "home", id: "Beranda", en: "Home" },
		{ key: "chat", id: "Tanya YOGA", en: "Ask YOGA" },
		{ key: "explore", id: "Jelajah", en: "Explore" },
		{ key: "planner", id: "Rencana Perjalanan", en: "Trip Planner" },
		{ key: "regency", id: "Panduan Daerah", en: "Regency Guide" },
		{ key: "about", id: "Tentang", en: "About" },
	];

	function Nav({ lang, setLang, page, go, onAsk, menuOpen, setMenuOpen }) {
		return (
			<header className="jjk-nav">
				<div className="jjk-container jjk-nav__row">
					<a
						className="jjk-brand"
						onClick={() => go("home")}
						style={{ cursor: "pointer" }}
					>
						<img
							src={
								(window.__resources && window.__resources.jjMark) ||
								"../../assets/logo/jj-mark.svg"
							}
							alt=""
						/>
						<span className="jjk-brand__wm">
							Jelajah <em>Jogja</em>
						</span>
					</a>
					<nav className="jjk-nav__links">
						{NAV.map((n) => (
							<button
								key={n.key}
								className={
									"jjk-nav__link" + (page === n.key ? " is-active" : "")
								}
								onClick={() => go(n.key)}
							>
								{lang === "en" ? n.en : n.id}
							</button>
						))}
					</nav>
					<div className="jjk-nav__right">
						<LangToggle value={lang} onChange={setLang} />
						<span style={{ display: "inline-flex" }} className="jjk-hide-sm">
							<Btn
								variant="primary"
								size="sm"
								iconLeft={<Icon name="sparkles" size={16} />}
								onClick={() => go("chat")}
							>
								{L(lang, "Tanya YOGA", "Ask YOGA")}
							</Btn>
						</span>
						<span className="jjk-nav__menu" style={{ display: "none" }}>
							<IconBtn
								variant="ghost"
								icon={<Icon name={menuOpen ? "x" : "sliders"} size={20} />}
								label="Menu"
								onClick={() => setMenuOpen(!menuOpen)}
							/>
						</span>
					</div>
				</div>
				{menuOpen ? (
					<div
						className="jjk-container"
						style={{
							paddingBottom: 14,
							display: "flex",
							flexDirection: "column",
							gap: 4,
						}}
					>
						{NAV.map((n) => (
							<button
								key={n.key}
								className={
									"jjk-nav__link" + (page === n.key ? " is-active" : "")
								}
								style={{ textAlign: "left" }}
								onClick={() => {
									go(n.key);
									setMenuOpen(false);
								}}
							>
								{lang === "en" ? n.en : n.id}
							</button>
						))}
					</div>
				) : null}
			</header>
		);
	}

	function Footer({ lang, go, data }) {
		return (
			<footer className="jjk-footer">
				<div
					className="jjk-footer__batik jj-batik"
					style={{ "--batik-size": "110px" }}
				/>
				<div className="jjk-container jjk-footer__inner">
					<div className="jjk-footer__brand">
						<span className="jjk-brand">
							<img
								src={
									(window.__resources && window.__resources.jjMark) ||
									"../../assets/logo/jj-mark.svg"
								}
								alt=""
								style={{ width: 32, height: 32 }}
							/>
							<span className="jjk-brand__wm">
								Jelajah <em>Jogja</em>
							</span>
						</span>
						<p className="jjk-footer__blurb">
							{L(
								lang,
								"Temukan pesona Yogyakarta — 3.399 tempat wisata, satu pemandu yang hangat.",
								"Discover the soul of Yogyakarta — 3,399 destinations, one warm guide.",
							)}
						</p>
					</div>
					<div>
						<h5>{L(lang, "Jelajah", "Explore")}</h5>
						<ul>
							<li>
								<a onClick={() => go("home")}>{L(lang, "Beranda", "Home")}</a>
							</li>
							<li>
								<a onClick={() => go("explore")}>
									{L(lang, "Semua destinasi", "All destinations")}
								</a>
							</li>
							<li>
								<a onClick={() => go("planner")}>
									{L(lang, "Trip Planner", "Trip Planner")}
								</a>
							</li>
							<li>
								<a onClick={() => go("about")}>{L(lang, "Tentang", "About")}</a>
							</li>
						</ul>
					</div>
					<div>
						<h5>{L(lang, "Kategori", "Categories")}</h5>
						<ul>
							{data.CATEGORIES.slice(0, 5).map((c) => (
								<li key={c.key}>
									<a onClick={() => go("explore", { category: c.id })}>
										{lang === "en" ? c.en : c.id}
									</a>
								</li>
							))}
						</ul>
					</div>
					<div>
						<h5>{L(lang, "Daerah", "Regencies")}</h5>
						<ul>
							{data.REGENCIES.map((r) => (
								<li key={r.key}>
									<a onClick={() => go("regency", { regency: r.key })}>
										{r.name}
									</a>
								</li>
							))}
						</ul>
					</div>
				</div>
				<div className="jjk-container jjk-footer__bottom">
					<span>
						© 2026 Jelajah Jogja ·{" "}
						{L(lang, "Data: Kaggle + Geoapify", "Data: Kaggle + Geoapify")}
					</span>
					<span className="jjk-footer__social">
						<a aria-label="Instagram">
							<Icon name="instagram" size={17} />
						</a>
						<a aria-label="Maps">
							<Icon name="mapPin" size={17} />
						</a>
						<a aria-label="Share">
							<Icon name="share" size={17} />
						</a>
					</span>
				</div>
			</footer>
		);
	}

	function Launcher({ open, onClick }) {
		return (
			<button
				className="jj-launcher"
				aria-label={open ? "Tutup chat YOGA" : "Buka chat YOGA"}
				onClick={onClick}
			>
				{open ? (
					<Icon name="x" size={26} />
				) : (
					<svg
						viewBox="0 0 48 48"
						fill="none"
						aria-hidden="true"
						width="30"
						height="30"
					>
						<circle cx="29" cy="18" r="5" fill="#f3cf95" />
						<path
							d="M8 33 L19 21 L26 28 L33 18 L40 33"
							stroke="#fdf6ec"
							strokeWidth="2.6"
							strokeLinecap="round"
							strokeLinejoin="round"
						/>
						<path
							d="M9 33 H39"
							stroke="#fdf6ec"
							strokeWidth="2.6"
							strokeLinecap="round"
						/>
					</svg>
				)}
			</button>
		);
	}

	function App() {
		const data = window.JJ;
		const [lang, setLang] = React.useState("id");
		const [page, setPage] = React.useState("home");
		const [params, setParams] = React.useState({});
		const [selected, setSelected] = React.useState(null);
		const [saved, setSaved] = React.useState(() => new Set());
		const [days, setDays] = React.useState({
			1: [data.PLACES[0], data.PLACES[4]],
			2: [data.PLACES[7]],
			3: [],
		});
		const [weekend, setWeekend] = React.useState(false);
		const [chatOpen, setChatOpen] = React.useState(false);
		const [askSignal, setAskSignal] = React.useState({ text: null, n: 0 });
		const [q, setQ] = React.useState("");
		const [menuOpen, setMenuOpen] = React.useState(false);
		const [toast, setToast] = React.useState(null);

		const go = (p, pr = {}) => {
			setParams(pr);
			setPage(p);
			setMenuOpen(false);
			window.scrollTo({ top: 0, behavior: "auto" });
		};
		const openPlace = (place) => {
			setSelected(place);
			setParams({});
			setPage("detail");
			window.scrollTo({ top: 0 });
		};
		const toggleSave = (place) =>
			setSaved((s) => {
				const n = new Set(s);
				n.has(place.id) ? n.delete(place.id) : n.add(place.id);
				return n;
			});
		const ask = (text) => {
			setChatOpen(true);
			setAskSignal((s) => ({ text: text || null, n: s.n + 1 }));
		};
		const showToast = (msg) => {
			setToast(msg);
			setTimeout(() => setToast(null), 2200);
		};
		const addToPlan = (place) => {
			setDays((d) => {
				if ([1, 2, 3].some((k) => d[k].some((p) => p.id === place.id)))
					return d;
				const target =
					d[1].length <= d[2].length && d[1].length <= d[3].length
						? 1
						: d[2].length <= d[3].length
							? 2
							: 3;
				return { ...d, [target]: [...d[target], place] };
			});
			showToast(
				L(
					lang,
					place.name + " ditambahkan ke rencana",
					place.name + " added to your trip",
				),
			);
		};
		const removeFromPlan = (day, id) =>
			setDays((d) => ({ ...d, [day]: d[day].filter((p) => p.id !== id) }));

		const common = {
			lang,
			data,
			saved,
			onSave: toggleSave,
			onOpen: openPlace,
			onAsk: ask,
			go,
		};

		return (
			<div className="jjk-app">
				<Nav
					lang={lang}
					setLang={setLang}
					page={page}
					go={go}
					onAsk={ask}
					menuOpen={menuOpen}
					setMenuOpen={setMenuOpen}
				/>
				<main className="jjk-main">
					{page === "home" && <S.Home {...common} q={q} setQ={setQ} />}
					{page === "chat" && <S.ChatPage {...common} initial={params} />}
					{page === "explore" && <S.Explore {...common} initial={params} />}
					{page === "detail" && (
						<S.Detail {...common} place={selected} onPlan={addToPlan} />
					)}
					{page === "planner" && (
						<S.Planner
							lang={lang}
							days={days}
							onRemove={removeFromPlan}
							onAsk={ask}
							go={go}
							weekend={weekend}
							setWeekend={setWeekend}
						/>
					)}
					{page === "regency" && (
						<S.Regency {...common} regencyKey={params.regency} />
					)}
					{page === "about" && <S.About lang={lang} onAsk={ask} go={go} />}
				</main>
				<Footer lang={lang} go={go} data={data} />
				<Launcher open={chatOpen} onClick={() => setChatOpen((o) => !o)} />
				<S.ChatPanel
					open={chatOpen}
					lang={lang}
					onClose={() => setChatOpen(false)}
					askSignal={askSignal}
					saved={saved}
					onSave={toggleSave}
					onOpen={openPlace}
				/>
				{toast ? <div className="jjk-toast">{toast}</div> : null}
			</div>
		);
	}

	ReactDOM.createRoot(document.getElementById("app")).render(<App />);
})();
