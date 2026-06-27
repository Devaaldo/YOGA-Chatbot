/* Jelajah Jogja — Regency Guide (Panduan Daerah) */
(function () {
	const U = window.JJUI;
	const { Icon, Badge, SectionHeader, RegencyCard, DestinationCard, L } = U;

	const INTRO = {
		kota: {
			id: "Jantung budaya provinsi — tempat Keraton, Malioboro, dan Tugu Pal Putih berpadu dengan denyut kota yang hangat dan ramah.",
			en: "The cultural heart of the province — where the Keraton, Malioboro and Tugu Pal Putih meet a warm, welcoming city life.",
			cats: ["Budaya & Sejarah", "Kuliner", "Buatan"],
		},
		sleman: {
			id: "Di lereng Gunung Merapi, Sleman memadukan candi megah, tebing breksi yang dramatis, dan udara sejuk pegunungan.",
			en: "On the slopes of Mount Merapi, Sleman blends grand temples, dramatic carved cliffs and cool mountain air.",
			cats: ["Budaya & Sejarah", "Alam", "Buatan"],
		},
		bantul: {
			id: "Bantul terkenal dengan pantai selatan yang dramatis, hutan pinus yang sejuk, dan tradisi seni rakyat yang hidup.",
			en: "Bantul is known for its dramatic southern beaches, cool pine forests and a living tradition of folk art.",
			cats: ["Alam", "Budaya & Sejarah"],
		},
		gunungkidul: {
			id: "Pesisir tenggara dengan deretan pantai pasir putih, goa karst, dan gunung api purba yang memesona.",
			en: "A south-eastern coast of white-sand coves, karst caves and mesmerising ancient volcanoes.",
			cats: ["Alam", "Buatan"],
		},
		kulonprogo: {
			id: "Perbukitan Menoreh yang hijau, waduk yang tenang, dan gardu pandang di atas pepohonan menanti di barat DIY.",
			en: "The green Menoreh hills, tranquil reservoirs and treetop viewpoints await in the west of DIY.",
			cats: ["Alam"],
		},
	};
	const NAME = {
		kota: "Kota Yogyakarta",
		sleman: "Sleman",
		bantul: "Bantul",
		gunungkidul: "Gunungkidul",
		kulonprogo: "Kulon Progo",
	};

	function Regency({ lang, data, regencyKey, go, onOpen, saved, onSave }) {
		const { PLACES, REGENCIES } = data;

		if (!regencyKey) {
			return (
				<div className="jjk-section jjk-container">
					<div style={{ marginBottom: 28 }}>
						<SectionHeader
							eyebrow={L(lang, "Panduan Daerah", "Regency Guide")}
							title={L(
								lang,
								"Lima kabupaten & kota DIY",
								"Five regencies of DIY",
							)}
							subtitle={L(
								lang,
								"Setiap daerah punya karakternya sendiri. Pilih satu untuk panduan editorial dan destinasi pilihannya.",
								"Each regency has its own character. Pick one for an editorial guide and its finest destinations.",
							)}
						/>
					</div>
					<div
						className="jjk-grid"
						style={{ gridTemplateColumns: "repeat(5, 1fr)" }}
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
				</div>
			);
		}

		const reg = REGENCIES.find((r) => r.key === regencyKey);
		const intro = INTRO[regencyKey];
		const places = PLACES.filter((p) => p.regency === NAME[regencyKey]);

		return (
			<div>
				<section className="jjk-hero" style={{ minHeight: 380 }}>
					<div className="jjk-hero__bg" style={U.sceneStyle(reg.scene)} />
					<div className="jjk-hero__batik jj-batik" />
					<div className="jjk-hero__scrim" />
					<div
						className="jjk-container jjk-hero__inner"
						style={{ padding: "72px 0 64px" }}
					>
						<button
							className="jj-sechead__action"
							style={{ color: "#fff", marginBottom: 16, fontSize: 14 }}
							onClick={() => go("regency")}
						>
							<span
								aria-hidden="true"
								style={{ transform: "rotate(180deg)", display: "inline-flex" }}
							>
								<Icon name="arrowRight" size={16} />
							</span>{" "}
							{L(lang, "Semua daerah", "All regencies")}
						</button>
						<div className="jjk-hero__content">
							<div className="jjk-eyebrow jjk-hero__eyebrow">
								{L(lang, "Panduan Daerah", "Regency Guide")}
							</div>
							<h1 style={{ fontSize: 54 }}>{reg.name}</h1>
							<p className="jjk-hero__sub">{intro[lang] || intro.id}</p>
							<div
								style={{
									display: "flex",
									gap: 8,
									flexWrap: "wrap",
									marginTop: 6,
								}}
							>
								{intro.cats.map((c) => (
									<span
										key={c}
										className="jj-badge jj-badge--solid"
										style={{
											background: "rgba(255,252,247,0.92)",
											color: "var(--color-primary-press)",
										}}
									>
										{c}
									</span>
								))}
							</div>
						</div>
					</div>
				</section>

				<section className="jjk-section jjk-container">
					<SectionHeader
						eyebrow={L(
							lang,
							reg.count.toLocaleString("id-ID") + " tempat wisata",
							reg.count.toLocaleString("en-US") + " destinations",
						)}
						title={L(
							lang,
							"Destinasi pilihan di " + reg.name,
							"Top picks in " + reg.name,
						)}
						actionLabel={L(lang, "Jelajah semua", "Explore all")}
						onAction={() => go("explore", { category: null })}
					/>
					<div className="jjk-grid jjk-grid--results" style={{ marginTop: 22 }}>
						{places.map((p) => (
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
			</div>
		);
	}
	window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { Regency });
})();
