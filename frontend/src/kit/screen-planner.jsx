/* Jelajah Jogja — Trip Planner (Rencana Perjalanan) */
(function () {
	const U = window.JJUI;
	const { Icon, Btn, IconBtn, Toggle, SectionHeader, L, fmtIDR } = U;

	function Planner({ lang, days, onRemove, onAsk, go, weekend, setWeekend }) {
		const priceOf = (p) => (weekend ? p.priceWeekend : p.priceWeekday) || 0;
		const dayTotal = (arr) => arr.reduce((s, p) => s + priceOf(p), 0);
		const all = [days[1], days[2], days[3]].flat();
		const grandTotal = all.reduce((s, p) => s + priceOf(p), 0);
		const count = all.length;

		const DayCol = ({ n }) => {
			const arr = days[n] || [];
			return (
				<div className="jjk-day">
					<div className="jjk-day__head">
						<span className="jjk-day__title">
							{L(lang, "Hari ", "Day ")}
							{n}
						</span>
						<span className="jjk-day__budget">
							{arr.length ? fmtIDR(dayTotal(arr)) : "—"}
						</span>
					</div>
					{arr.length === 0 ? (
						<div
							style={{
								border: "1.5px dashed var(--color-border-strong)",
								borderRadius: "var(--radius-md)",
								padding: "20px",
								textAlign: "center",
								color: "var(--color-text-muted)",
								fontSize: 14,
							}}
						>
							{L(
								lang,
								"Belum ada destinasi. Tambahkan dari halaman Jelajah.",
								"No destinations yet. Add some from Explore.",
							)}
						</div>
					) : (
						<div className="jjk-day__items">
							{arr.map((p, i) => (
								<div className="jjk-pitem" key={p.id}>
									<span className="jjk-pitem__drag">
										<Icon name="grip" size={18} />
									</span>
									<span className="jjk-pitem__num">{i + 1}</span>
									<span className="jjk-pitem__media">
										<span
											style={{
												position: "absolute",
												inset: 0,
												...U.sceneStyle(p.scene),
											}}
										/>
									</span>
									<div style={{ flex: 1, minWidth: 0 }}>
										<div className="jjk-pitem__name">{p.name}</div>
										<div className="jjk-pitem__sub">
											{p.regency} ·{" "}
											{priceOf(p) === 0
												? L(lang, "Gratis", "Free")
												: fmtIDR(priceOf(p))}
										</div>
									</div>
									<IconBtn
										size="sm"
										variant="ghost"
										icon={<Icon name="x" size={16} />}
										label="Remove"
										onClick={() => onRemove(n, p.id)}
									/>
								</div>
							))}
						</div>
					)}
				</div>
			);
		};

		return (
			<div className="jjk-section jjk-container">
				<div style={{ marginBottom: 28 }}>
					<SectionHeader
						eyebrow={L(lang, "Rencana Perjalanan", "Trip Planner")}
						title={L(
							lang,
							"Susun perjalanan tiga harimu",
							"Build your three-day trip",
						)}
						subtitle={L(
							lang,
							"Tambahkan destinasi ke tiap hari, lihat estimasi anggaran, dan biarkan YOGA menyusun rute.",
							"Add destinations to each day, see the running budget, and let YOGA plan the route.",
						)}
						actionLabel={L(lang, "Tambah destinasi", "Add destinations")}
						onAction={() => go("explore")}
					/>
				</div>
				<div className="jjk-planner">
					<div className="jjk-days">
						<DayCol n={1} />
						<DayCol n={2} />
						<DayCol n={3} />
					</div>
					<aside className="jjk-summary">
						<div
							style={{
								fontFamily: "var(--font-display)",
								fontWeight: 600,
								fontSize: 20,
								color: "var(--color-text)",
								marginBottom: 4,
							}}
						>
							{L(lang, "Ringkasan", "Summary")}
						</div>
						<div
							style={{
								display: "flex",
								alignItems: "center",
								justifyContent: "space-between",
								padding: "12px 0",
								fontSize: 14,
								color: "var(--color-text-secondary)",
							}}
						>
							<span>{L(lang, "Total destinasi", "Total places")}</span>
							<b
								style={{
									fontFamily: "var(--font-mono)",
									color: "var(--color-text)",
								}}
							>
								{count}
							</b>
						</div>
						<div
							style={{
								display: "flex",
								alignItems: "center",
								justifyContent: "space-between",
								paddingBottom: 12,
							}}
						>
							<Toggle
								checked={weekend}
								onChange={setWeekend}
								label={L(lang, "Harga akhir pekan", "Weekend pricing")}
							/>
						</div>
						<div className="jjk-summary__total">
							<span
								style={{
									fontFamily: "var(--font-sans)",
									fontWeight: 600,
									color: "var(--color-text-secondary)",
								}}
							>
								{L(lang, "Estimasi tiket", "Est. tickets")}
							</span>
							<b>{fmtIDR(grandTotal)}</b>
						</div>
						<div className="jjk-route">
							<div
								className="jjk-map__bg"
								style={{ position: "absolute", inset: 0 }}
							/>
							<div
								className="jjk-map__grid"
								style={{ position: "absolute", inset: 0 }}
							/>
							{all.slice(0, 5).map((p, i) => (
								<span
									key={p.id}
									className="jjk-pin"
									style={{
										left: 18 + i * 16 + "%",
										top: 30 + (i % 3) * 18 + "%",
										transform: "translate(-50%,-100%) scale(0.8)",
									}}
								>
									<span className="jjk-pin__dot" />
								</span>
							))}
						</div>
						<div
							style={{
								display: "flex",
								flexDirection: "column",
								gap: 10,
								marginTop: 16,
							}}
						>
							<Btn
								variant="primary"
								block
								iconLeft={<Icon name="sparkles" size={18} />}
								onClick={() =>
									onAsk(
										L(
											lang,
											"Buatkan rencana perjalanan 3 hari di Jogja",
											"Plan me a 3-day trip in Jogja",
										),
									)
								}
							>
								{L(lang, "Buatkan rencana untukku", "Plan it for me")}
							</Btn>
							<Btn
								variant="outline"
								block
								iconLeft={<Icon name="share" size={18} />}
								onClick={() => window.print()}
							>
								{L(lang, "Bagikan / Cetak", "Share / Print")}
							</Btn>
						</div>
					</aside>
				</div>
			</div>
		);
	}
	window.JJSCREENS = Object.assign(window.JJSCREENS || {}, { Planner });
})();
