/* Jelajah Jogja — Destination Detail (Detail Destinasi) */
(function () {
	const U = window.JJUI;
	const {
		Icon,
		Btn,
		IconBtn,
		Badge,
		Stars,
		Price,
		Heart,
		SectionHeader,
		DestinationCard,
		L,
		fmtIDR,
	} = U;

	const priceText = (n, lang) =>
		n == null
			? L(lang, "Tidak tersedia", "Unavailable")
			: n === 0
				? L(lang, "Gratis", "Free")
				: fmtIDR(n);

	function Detail({
		lang,
		data,
		place,
		saved,
		onSave,
		onOpen,
		onAsk,
		onPlan,
		go,
	}) {
		if (!place) return null;
		const { PLACES } = data;
		const similar = PLACES.filter(
			(p) => p.category === place.category && p.id !== place.id,
		).slice(0, 4);
		const mapsUrl = `https://www.google.com/maps?q=${place.lat},${place.lng}`;
		const isSaved = saved.has(place.id);

		return (
			<div className="jjk-section jjk-container">
				<button
					className="jj-sechead__action"
					style={{ marginBottom: 18, fontSize: 14 }}
					onClick={() => go("explore")}
				>
					<span
						aria-hidden="true"
						style={{ transform: "rotate(180deg)", display: "inline-flex" }}
					>
						<Icon name="arrowRight" size={16} />
					</span>{" "}
					{L(lang, "Kembali ke Jelajah", "Back to Explore")}
				</button>

				{/* Hero gallery */}
				<div className="jjk-detail__hero">
					<div className="jjk-detail__main">
						<div
							className="jjk-detail__img"
							style={U.sceneStyle(place.scene)}
						/>
						<div className="jjk-detail__batik jj-batik" />
						<div className="jjk-detail__heart">
							<Heart saved={isSaved} onChange={() => onSave(place)} />
						</div>
					</div>
					<div className="jjk-detail__side">
						<div className="jjk-detail__thumb">
							<div
								className="jjk-detail__img"
								style={U.sceneStyle(
									place.scene === "beach" ? "water" : "nature",
								)}
							/>
							<div className="jjk-detail__batik jj-batik" />
						</div>
						<div className="jjk-detail__thumb">
							<div className="jjk-detail__img" style={U.sceneStyle("dusk")} />
							<div className="jjk-detail__batik jj-batik" />
						</div>
					</div>
				</div>

				{/* Head */}
				<div className="jjk-detail__head">
					<div>
						<div style={{ marginBottom: 10 }}>
							<Badge variant="primary">{place.tag}</Badge>
						</div>
						<h1 className="jjk-detail__title">{place.name}</h1>
						<div className="jjk-detail__meta">
							<Stars
								value={place.rating}
								count={place.votes}
								lang={lang}
								size={17}
							/>
							<span style={{ color: "var(--color-text-muted)" }}>·</span>
							<span
								style={{
									display: "inline-flex",
									alignItems: "center",
									gap: 6,
									color: "var(--color-text-secondary)",
									fontSize: 14.5,
								}}
							>
								<Icon name="mapPin" size={16} />{" "}
								{place.address || place.regency}
							</span>
						</div>
					</div>
					<div style={{ display: "flex", gap: 10 }}>
						<Btn
							variant={isSaved ? "secondary" : "outline"}
							iconLeft={
								<Icon
									name="heart"
									size={18}
									fill={isSaved ? "currentColor" : "none"}
									stroke={1.9}
								/>
							}
							onClick={() => onSave(place)}
						>
							{isSaved
								? L(lang, "Tersimpan", "Saved")
								: L(lang, "Simpan", "Save")}
						</Btn>
						<IconBtn
							variant="outline"
							icon={<Icon name="share" size={18} />}
							label="Share"
						/>
					</div>
				</div>

				{/* Key facts */}
				<div className="jjk-facts">
					<div className="jjk-fact">
						<span className="jjk-fact__k">
							{L(lang, "Tiket Weekday", "Weekday")}
						</span>
						<span className="jjk-fact__v">
							{priceText(place.priceWeekday, lang)}
						</span>
					</div>
					<div className="jjk-fact">
						<span className="jjk-fact__k">
							{L(lang, "Tiket Weekend", "Weekend")}
						</span>
						<span className="jjk-fact__v">
							{priceText(place.priceWeekend, lang)}
						</span>
					</div>
					<div className="jjk-fact">
						<span className="jjk-fact__k">
							{L(lang, "Kategori", "Category")}
						</span>
						<span
							className="jjk-fact__v"
							style={{ fontFamily: "var(--font-sans)", fontSize: 15 }}
						>
							{place.category}
						</span>
					</div>
					<div className="jjk-fact">
						<span className="jjk-fact__k">{L(lang, "Daerah", "Regency")}</span>
						<span
							className="jjk-fact__v"
							style={{ fontFamily: "var(--font-sans)", fontSize: 15 }}
						>
							{place.regency}
						</span>
					</div>
				</div>

				{/* Body */}
				<div className="jjk-detail__body">
					<div className="jjk-detail__desc">
						<h3>{L(lang, "Tentang tempat ini", "About this place")}</h3>
						<p>{place.desc[lang] || place.desc.id}</p>
						<div
							style={{
								marginTop: 22,
								padding: 18,
								background: "var(--color-primary-soft)",
								borderRadius: "var(--radius-lg)",
								display: "flex",
								alignItems: "center",
								justifyContent: "space-between",
								gap: 16,
								flexWrap: "wrap",
							}}
						>
							<div style={{ display: "flex", alignItems: "center", gap: 12 }}>
								<img
									src={
										(window.__resources && window.__resources.yogaAvatar) ||
										"../../assets/logo/yoga-avatar.svg"
									}
									alt="YOGA"
									style={{ width: 40, height: 40, borderRadius: "50%" }}
								/>
								<span
									style={{
										fontFamily: "var(--font-sans)",
										fontSize: 14.5,
										color: "var(--color-text)",
										fontWeight: 500,
									}}
								>
									{L(
										lang,
										"Punya pertanyaan tentang tempat ini?",
										"Questions about this place?",
									)}
								</span>
							</div>
							<Btn
								variant="primary"
								iconLeft={<Icon name="sparkles" size={18} />}
								onClick={() =>
									onAsk(
										L(
											lang,
											"Info " + place.name,
											"Tell me about " + place.name,
										),
									)
								}
							>
								{L(lang, "Tanya YOGA", "Ask YOGA")}
							</Btn>
						</div>
					</div>

					{/* Location card */}
					<div>
						<div className="jjk-loccard">
							<div className="jjk-loccard__map">
								<div
									className="jjk-map__bg"
									style={{ position: "absolute", inset: 0 }}
								/>
								<div
									className="jjk-map__grid"
									style={{ position: "absolute", inset: 0 }}
								/>
								<span className="jjk-pin" style={{ left: "50%", top: "52%" }}>
									<span className="jjk-pin__dot" />
								</span>
							</div>
							<div className="jjk-loccard__inner">
								<div className="jjk-loccard__row">
									<Icon name="mapPin" size={17} />
									<span>{place.address || place.regency + ", DIY"}</span>
								</div>
								<div className="jjk-loccard__row">
									<Icon name="compass" size={17} />
									<span className="jjk-loccard__coord">
										{place.lat.toFixed(5)}, {place.lng.toFixed(5)}
									</span>
								</div>
								{place.website ? (
									<div className="jjk-loccard__row">
										<Icon name="link" size={17} />
										<a
											href={place.website}
											target="_blank"
											rel="noreferrer"
											style={{
												color: "var(--color-primary)",
												wordBreak: "break-all",
											}}
										>
											{place.website.replace(/^https?:\/\//, "")}
										</a>
									</div>
								) : null}
								{place.phone ? (
									<div className="jjk-loccard__row">
										<Icon name="phone" size={17} />
										<span>{place.phone}</span>
									</div>
								) : null}
								<a
									className="jj-btn jj-btn--outline jj-btn--block"
									href={mapsUrl}
									target="_blank"
									rel="noreferrer"
									style={{ marginTop: 4 }}
								>
									<span className="jj-btn__i">
										<Icon name="mapPin" size={18} />
									</span>
									<span>
										{L(lang, "Buka di Google Maps", "Open in Google Maps")}
									</span>
								</a>
							</div>
						</div>
						<Btn
							variant="primary"
							block
							size="lg"
							iconLeft={<Icon name="plus" size={18} />}
							onClick={() => onPlan(place)}
							className=""
						>
							{L(lang, "Tambah ke rencana", "Add to trip")}
						</Btn>
					</div>
				</div>

				{/* Similar */}
				<section style={{ marginTop: 56 }}>
					<SectionHeader
						eyebrow={L(lang, "Rekomendasi Serupa", "You may also like")}
						title={L(
							lang,
							"Tempat lain yang mungkin kamu suka",
							"More places to discover",
						)}
					/>
					<div
						className="jjk-grid jjk-grid--results"
						style={{ marginTop: 22, gridTemplateColumns: "repeat(4, 1fr)" }}
					>
						{similar.map((p) => (
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
	window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { Detail });
})();
