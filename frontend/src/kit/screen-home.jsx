/* Jelajah Jogja — Home (Beranda) */
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

	function Home({ lang, data, saved, onSave, onOpen, onAsk, go, q, setQ }) {
		const { PLACES, CATEGORIES, REGENCIES } = data;
		const popular = [...PLACES]
			.sort((a, b) => (b.rating || 0) - (a.rating || 0))
			.slice(0, 8);
		const collections = [
			{
				eyebrow: L(lang, "Permata Tersembunyi", "Hidden Gems"),
				title: L(
					lang,
					"Sunrise di Perbukitan Menoreh",
					"Sunrise in the Menoreh Hills",
				),
				meta: L(lang, "8 tempat · mulai Rp10.000", "8 spots · from Rp10,000"),
				scene: "nature",
			},
			{
				eyebrow: L(lang, "Wisata Hemat", "Budget Trips"),
				title: L(lang, "Liburan di Bawah Rp20.000", "A Day Out Under Rp20,000"),
				meta: L(lang, "14 tempat ramah kantong", "14 wallet-friendly spots"),
				scene: "dusk",
			},
			{
				eyebrow: L(lang, "Pesisir Selatan", "Southern Coast"),
				title: L(
					lang,
					"Pantai Pasir Putih Gunungkidul",
					"White-Sand Beaches of Gunungkidul",
				),
				meta: L(lang, "11 pantai terbaik", "11 finest beaches"),
				scene: "beach",
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
									"Jelajahi 3.399 tempat wisata — dari candi megah hingga pantai pasir putih — ditemani YOGA, pemandu wisatamu.",
									"Explore 3,399 destinations — from grand temples to white-sand beaches — guided by YOGA, your local companion.",
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
											"Tanya YOGA: pantai murah di Gunungkidul, info Candi Prambanan…",
											"Ask YOGA: cheap beaches in Gunungkidul, about Candi Prambanan…",
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
					<div
						className="jjk-grid"
						style={{ marginTop: 22, gridTemplateColumns: "repeat(5, 1fr)" }}
					>
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
										"Tambahkan destinasi ke Hari 1, 2, dan 3. Lihat estimasi anggaran dan rute otomatis — atau minta YOGA membuatkannya.",
										"Add destinations to Day 1, 2 and 3. See an instant budget and route — or let YOGA build it for you.",
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
									"Tanya apa saja — rekomendasi, pantai di daerah tertentu, tiket termurah, atau info sebuah candi. YOGA menjawab dengan tempat sungguhan dari basis data.",
									"Ask anything — recommendations, beaches in a region, the cheapest tickets, or details about a temple. YOGA replies with real places from the database.",
								)}
							/>
							<div className="jjk-yoga__chips">
								{askChips.map((c, i) => (
									<QuickReply key={i} label={c} onClick={() => onAsk(c)} />
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
								<Bubble from="user" time="09:41">
									{L(lang, "Rating terbaik", "Top rated")}
								</Bubble>
								<Bubble from="yoga">
									{L(
										lang,
										"Tugu Pal Putih (4.8) dan Candi Prambanan (4.7) jadi favorit. Mau lihat detailnya?",
										"Tugu Pal Putih (4.8) and Candi Prambanan (4.7) are favourites. Want the details?",
									)}
								</Bubble>
							</div>
							<div style={{ marginTop: 16 }}>
								<Btn
									variant="primary"
									block
									iconLeft={<Icon name="sparkles" size={18} />}
									onClick={() => onAsk()}
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
