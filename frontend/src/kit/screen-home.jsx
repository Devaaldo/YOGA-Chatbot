/* YOGA — Home (Beranda) */
(function () {
	const U = window.JJUI;
	const {
		Icon,
		Btn,
		SearchBar,
		SectionHeader,
		CategoryTile,
		DestinationCard,
		RegencyCard,
		CollectionCard,
		Bubble,
		QuickReply,
		L,
	} = U;

	const CAT_ICON = {
		alam: "mountain",
		kuliner: "fork",
		budaya: "bank",
		buatan: "ferris",
		umum: "compass",
		air: "waves",
	};
	const CAT_TONE = {
		alam: "secondary",
		kuliner: "primary",
		budaya: "accent",
		buatan: "primary",
		umum: "secondary",
		air: "accent",
	};
	const rupiah = (n) =>
		Number.isFinite(n) ? "Rp" + n.toLocaleString("id-ID") : "n/a";

	function Home({ lang, data, saved, onSave, onOpen, onAsk, go, q, setQ }) {
		const { PLACES, CATEGORIES, REGENCIES } = data;
		const total = data.TOTAL;
		const totalLabel = total ? total.toLocaleString("id-ID") : `${PLACES.length}`;
		// A 5.0 from two votes is not "most loved"; require a real review base
		// and fall back to plain rating order only if too few qualify.
		const withVotes = PLACES.filter((p) => (p.votes || 0) >= 100);
		const popularPool = withVotes.length >= 8 ? withVotes : PLACES;
		const popular = [...popularPool]
			.sort((a, b) => (b.rating || 0) - (a.rating || 0) || (b.votes || 0) - (a.votes || 0))
			.slice(0, 8);

		const beaches = PLACES.filter((p) => p.tag === "Pantai");
		const cheap = PLACES.filter(
			(p) => p.priceWeekday != null && p.priceWeekday > 0 && p.priceWeekday <= 20000,
		);
		const temples = PLACES.filter((p) => p.tag === "Candi");
		const collections = [
			{
				eyebrow: L(lang, "Pesisir Selatan", "Southern Coast"),
				title: L(lang, "Pantai di Yogyakarta", "Beaches of Yogyakarta"),
				meta: L(
					lang,
					`${beaches.length} pantai · dari ${rupiah(Math.min(...beaches.map((p) => p.priceWeekday ?? Infinity)))}`,
					`${beaches.length} beaches · from ${rupiah(Math.min(...beaches.map((p) => p.priceWeekday ?? Infinity)))}`,
				),
				scene: "beach",
			},
			{
				eyebrow: L(lang, "Wisata Hemat", "Budget Trips"),
				title: L(lang, "Tiket di Bawah Rp20.000", "Tickets Under Rp20,000"),
				meta: L(lang, `${cheap.length} tempat ramah kantong`, `${cheap.length} wallet-friendly spots`),
				scene: "dusk",
			},
			{
				eyebrow: L(lang, "Warisan Budaya", "Living Heritage"),
				title: L(lang, "Candi & situs sejarah", "Temples & historic sites"),
				meta: L(lang, `${temples.length} candi & situs`, `${temples.length} temples & sites`),
				scene: "nature",
			},
		];
		const askChips =
			lang === "en"
				? [
						"Recommend places in Bantul",
						"Beaches in Gunungkidul",
						"Top rated",
						"Budget-friendly spots",
					]
				: [
						"Rekomendasi wisata di Bantul",
						"Wisata pantai di Gunungkidul",
						"Rating terbaik",
						"Tempat wisata tiket murah",
					];

		return (
			<div>
				{/* Hero */}
				<section className="jjk-hero">
					<div className="jjk-hero__bg" />
					<div className="jjk-hero__batik jj-batik" />
					<div className="jjk-hero__scrim" />
					<div className="jjk-container jjk-hero__inner">
						<div className="jjk-hero__content">
							<div className="jjk-eyebrow jjk-hero__eyebrow">
								{L(
									lang,
									"Daerah Istimewa Yogyakarta",
									"Special Region of Yogyakarta",
								)}
							</div>
							<h1>
								{L(
									lang,
									<>
										Temukan <em>pesona</em> Yogyakarta.
									</>,
									<>
										Discover the <em>soul</em> of Yogyakarta.
									</>,
								)}
							</h1>
							<p className="jjk-hero__sub">
								{L(
									lang,
									`Jelajahi ${totalLabel} tempat wisata, dari candi megah hingga pantai pasir putih, ditemani YOGA, pemandu wisatamu.`,
									`Explore ${totalLabel} destinations, from grand temples to white-sand beaches, guided by YOGA, your local companion.`,
								)}
							</p>
							<div className="jjk-hero__search">
								<div className="jjk-hero__searchrow">
									<SearchBar
										value={q}
										onChange={setQ}
										onSubmit={() =>
											go("chat", q.trim() ? { ask: q } : {})
										}
										placeholder={L(
											lang,
											"Tanya YOGA: pantai murah di Gunungkidul…",
											"Ask YOGA: cheap beaches in Gunungkidul…",
										)}
										action={
											<Btn
												variant="primary"
												iconLeft={<Icon name="sparkles" size={18} />}
												onClick={() =>
													go("chat", q.trim() ? { ask: q } : {})
												}
											>
												{L(lang, "Tanya YOGA", "Ask YOGA")}
											</Btn>
										}
									/>
								</div>
								<div className="jjk-hero__cue">
									<span>
										<Icon
											name="chevronRight"
											size={18}
											style={{ transform: "rotate(90deg)" }}
										/>
									</span>
									{L(lang, "Gulir untuk menjelajah", "Scroll to explore")}
								</div>
							</div>
						</div>
					</div>
				</section>

				{/* Categories */}
				<section className="jjk-section jjk-container">
					<SectionHeader
						eyebrow={L(lang, "Jelajah Kategori", "Browse by Category")}
						title={L(
							lang,
							"Mau wisata seperti apa?",
							"What are you in the mood for?",
						)}
					/>
					<div className="jjk-grid jjk-grid--3" style={{ marginTop: 26 }}>
						{CATEGORIES.map((c) => (
							<CategoryTile
								key={c.key}
								name={lang === "en" ? c.en : c.id}
								count={c.count}
								iconName={CAT_ICON[c.key]}
								tone={CAT_TONE[c.key]}
								lang={lang}
								onClick={() => go("explore", { category: c.id })}
							/>
						))}
					</div>
				</section>

				{/* Popular */}
				<section
					className="jjk-section jjk-container"
					style={{ paddingTop: 0 }}
				>
					<SectionHeader
						eyebrow={L(lang, "Destinasi Populer", "Top Rated")}
						title={L(lang, "Paling dicari di Jogja", "Most loved in Jogja")}
						actionLabel={L(lang, "Lihat semua", "See all")}
						onAction={() => go("explore")}
					/>
					<div className="jjk-carousel" style={{ marginTop: 22 }}>
						{popular.map((p) => (
							<DestinationCard
								key={p.id}
								place={p}
								lang={lang}
								saved={saved.has(p.id)}
								onSave={onSave}
								onOpen={onOpen}
							/>
						))}
					</div>
				</section>

				{/* Regency strip */}
				<section
					className="jjk-section jjk-container"
					style={{ paddingTop: 0 }}
				>
					<SectionHeader
						eyebrow={L(lang, "Jelajah per Daerah", "Explore by Regency")}
						title={L(lang, "Lima wajah Yogyakarta", "Five faces of Yogyakarta")}
						actionLabel={L(lang, "Panduan daerah", "Regency guide")}
						onAction={() => go("regency")}
					/>
					<div className="jjk-grid jjk-grid--5" style={{ marginTop: 22 }}>
						{REGENCIES.map((r) => (
							<RegencyCard
								key={r.key}
								regency={r}
								lang={lang}
								onClick={() => go("regency", { regency: r.key })}
							/>
						))}
					</div>
				</section>

				{/* Collections */}
				<section
					className="jjk-section jjk-container"
					style={{ paddingTop: 0 }}
				>
					<SectionHeader
						eyebrow={L(lang, "Koleksi Pilihan", "Curated Collections")}
						title={L(lang, "Permata tersembunyi", "Hidden gems, handpicked")}
					/>
					<div className="jjk-grid jjk-grid--3" style={{ marginTop: 22 }}>
						{collections.map((c, i) => (
							<CollectionCard key={i} {...c} onClick={() => go("explore")} />
						))}
					</div>
				</section>

				{/* Itinerary band */}
				<section className="jjk-container" style={{ paddingBottom: 24 }}>
					<div className="jjk-band">
						<div
							className="jjk-band__bg"
							style={{ background: "var(--photo-nature)" }}
						/>
						<div className="jjk-band__batik jj-batik" />
						<div className="jjk-band__inner">
							<div>
								<h3>
									{L(
										lang,
										"Susun rencana perjalananmu",
										"Plan your perfect trip",
									)}
								</h3>
								<p>
									{L(
										lang,
										"Tambahkan destinasi ke Hari 1, 2, dan 3. Lihat estimasi anggaran dan rute otomatis, atau minta YOGA membuatkannya.",
										"Add destinations to Day 1, 2 and 3. See an instant budget and route, or let YOGA build it for you.",
									)}
								</p>
							</div>
							<Btn
								variant="light"
								size="lg"
								iconRight={<Icon name="arrowRight" size={18} />}
								onClick={() => go("planner")}
							>
								{L(lang, "Buka Trip Planner", "Open Trip Planner")}
							</Btn>
						</div>
					</div>
				</section>

				{/* Meet YOGA */}
				<section className="jjk-section jjk-container">
					<div className="jjk-yoga">
						<div>
							<SectionHeader
								eyebrow={L(lang, "Kenalan dengan YOGA", "Meet YOGA")}
								title={L(
									lang,
									"Pemandu wisata pribadimu",
									"Your personal Jogja guide",
								)}
								subtitle={L(
									lang,
									"Tanya apa saja: rekomendasi, pantai di daerah tertentu, tiket termurah, atau info sebuah candi. YOGA menjawab dengan tempat sungguhan dari basis data.",
									"Ask anything: recommendations, beaches in a region, the cheapest tickets, or details about a temple. YOGA replies with real places from the database.",
								)}
							/>
							<div className="jjk-yoga__stats">
								{[
									{ n: totalLabel, l: L(lang, "tempat wisata", "places") },
									{ n: "94,6%", l: L(lang, "akurasi uji model", "held-out accuracy") },
									{ n: "ID·EN", l: L(lang, "dwibahasa", "bilingual") },
								].map((s, i) => (
									<div key={i} className="jjk-yoga__stat">
										<span className="jjk-yoga__statn">{s.n}</span>
										<span className="jjk-yoga__statl">{s.l}</span>
									</div>
								))}
							</div>
							<ul className="jjk-yoga__caps">
								{[
									{ icon: "sparkles", t: L(lang, "Rekomendasi cerdas", "Smart recommendations") },
									{ icon: "grid", t: L(lang, "Cari per kategori", "Search by category") },
									{ icon: "star", t: L(lang, "Filter harga & rating", "Price & rating filters") },
									{ icon: "map", t: L(lang, "Lokasi & peta", "Location & maps") },
								].map((c, i) => (
									<li key={i} className="jjk-yoga__cap">
										<span className="jjk-yoga__capicon">
											<Icon name={c.icon} size={15} />
										</span>
										{c.t}
									</li>
								))}
							</ul>
							<div className="jjk-yoga__chips">
								{askChips.map((c, i) => (
									<QuickReply key={i} label={c} onClick={() => go("chat", { ask: c })} />
								))}
							</div>
						</div>
						<div className="jjk-yoga__card">
							<div className="jjk-yoga__head">
								<img
									src={
										(window.__resources && window.__resources.yogaAvatar) ||
										"../../assets/logo/yoga-avatar.svg"
									}
									alt="YOGA"
								/>
								<div>
									<div className="jjk-yoga__name">YOGA</div>
									<div className="jjk-yoga__status">
										{L(
											lang,
											"Asisten wisata Yogyakarta",
											"Yogyakarta travel assistant",
										)}
									</div>
								</div>
							</div>
							<div
								style={{ display: "flex", flexDirection: "column", gap: 12 }}
							>
								<Bubble from="yoga">
									{L(
										lang,
										"Halo! Mau cari pantai, candi, atau tempat dengan tiket murah?",
										"Hi! Looking for beaches, temples, or budget-friendly spots?",
									)}
								</Bubble>
								<Bubble from="user">
									{L(lang, "Pantai murah di Gunungkidul", "Cheap beaches in Gunungkidul")}
								</Bubble>
								<Bubble from="yoga">
									{L(
										lang,
										`Saya carikan dari ${totalLabel} tempat di basis data, lengkap dengan harga tiket dan lokasinya.`,
										`I'll pull matches from all ${totalLabel} places, with ticket prices and locations.`,
									)}
								</Bubble>
							</div>
							<div style={{ marginTop: 16 }}>
								<Btn
									variant="primary"
									block
									iconLeft={<Icon name="sparkles" size={18} />}
									onClick={() => go("chat")}
								>
									{L(lang, "Mulai mengobrol", "Start chatting")}
								</Btn>
							</div>
						</div>
					</div>
				</section>
			</div>
		);
	}
	window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { Home });
})();
