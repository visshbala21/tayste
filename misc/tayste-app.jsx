import { useState } from "react";

const NAV_LINKS = ["Home", "Search", "Collections", "Catalogue", "Contact"];

const PAGES = {
  HOME: "home",
  SEARCH: "search",
  RESULTS: "results",
  COLLECTIONS: "collections",
  CATALOGUE: "catalogue",
  ARTIST: "artist",
  CONTACT: "contact",
};

// ── shared styles ──────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Verdana&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --black: #0a0a0a;
    --white: #f5f5f0;
    --accent: #7c5cfc;
    --accent2: #c45cfc;
    --mid: #1e1e28;
    --border: rgba(255,255,255,0.12);
    --font-display: 'Bebas Neue', sans-serif;
    --font-body: Verdana, Geneva, sans-serif;
  }

  body { background: var(--black); color: var(--white); font-family: var(--font-body); font-size: 13px; line-height: 1.6; overflow-x: hidden; }

  /* NAV */
  .nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px; height: 54px;
    background: rgba(10,10,10,0.92); border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100; backdrop-filter: blur(12px);
  }
  .nav-logo { font-family: var(--font-display); font-size: 28px; letter-spacing: 2px; cursor: pointer; color: var(--white); }
  .nav-links { display: flex; gap: 4px; }
  .nav-btn {
    background: rgba(255,255,255,0.07); border: 1px solid var(--border);
    color: var(--white); font-family: var(--font-body); font-size: 11px;
    padding: 5px 14px; cursor: pointer; border-radius: 3px;
    transition: background .2s, border-color .2s;
    font-style: italic;
  }
  .nav-btn:hover, .nav-btn.active { background: var(--accent); border-color: var(--accent); }

  /* HERO WORDMARK */
  .wordmark {
    font-family: var(--font-display); font-size: clamp(72px, 18vw, 140px);
    letter-spacing: 4px; line-height: 1; color: var(--white);
  }
  .wordmark.inverted { transform: scaleX(-1) scaleY(-1); display: inline-block; opacity: 0.18; }

  /* SECTION LABEL */
  .section-label {
    font-family: var(--font-display); font-size: 22px; letter-spacing: 1px;
    padding: 14px 24px; border-bottom: 1px dashed var(--border);
    color: var(--white);
  }

  /* PILL BUTTONS */
  .pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--accent); color: var(--white);
    border: none; border-radius: 30px; padding: 8px 20px;
    font-family: var(--font-body); font-size: 12px; cursor: pointer;
    transition: background .2s, transform .15s;
  }
  .pill:hover { background: var(--accent2); transform: translateY(-1px); }
  .pill.outline { background: transparent; border: 1px solid var(--accent); color: var(--accent); }
  .pill.outline:hover { background: var(--accent); color: var(--white); }

  /* CARDS */
  .card {
    background: var(--mid); border: 1px solid var(--border);
    border-radius: 8px; padding: 20px; position: relative; overflow: hidden;
  }
  .card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
  }

  /* FLOW STEPS */
  .steps { display: flex; align-items: center; gap: 0; flex-wrap: wrap; }
  .step {
    background: var(--accent); color: var(--white); padding: 8px 20px;
    font-size: 11px; text-align: center; border-radius: 4px;
    font-family: var(--font-body);
  }
  .step-arrow { color: rgba(255,255,255,0.4); font-size: 20px; padding: 0 6px; }

  /* FEATURE BAR */
  .feat-bar {
    background: rgba(255,255,255,0.06); border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 10px 24px; font-size: 11px; color: rgba(255,255,255,0.5);
    letter-spacing: 0.5px;
  }

  /* PHOTO PLACEHOLDER */
  .photo {
    background: rgba(255,255,255,0.06); border: 1px solid var(--border);
    border-radius: 8px; display: flex; align-items: center; justify-content: center;
    color: rgba(255,255,255,0.25); font-size: 11px; font-style: italic;
  }

  /* INPUT */
  .inp {
    background: rgba(255,255,255,0.06); border: 1px solid var(--border);
    color: var(--white); font-family: var(--font-body); font-size: 13px;
    padding: 10px 14px; border-radius: 4px; outline: none; width: 100%;
    transition: border-color .2s;
  }
  .inp:focus { border-color: var(--accent); }
  .inp::placeholder { color: rgba(255,255,255,0.3); font-style: italic; }

  /* TAG */
  .tag {
    display: inline-block; background: rgba(124,92,252,0.2);
    border: 1px solid rgba(124,92,252,0.4); border-radius: 20px;
    padding: 3px 12px; font-size: 10px; color: rgba(200,180,255,0.9);
    margin: 3px;
  }

  /* ARTIST CARD */
  .artist-card {
    background: var(--mid); border: 1px solid var(--border); border-radius: 8px;
    overflow: hidden; cursor: pointer; transition: border-color .2s, transform .15s;
  }
  .artist-card:hover { border-color: var(--accent); transform: translateY(-2px); }
  .artist-card-img { background: linear-gradient(135deg, #2a1a4a, #1a2a4a); height: 140px; position: relative; }
  .artist-card-body { padding: 12px 14px; }
  .artist-name { font-family: var(--font-display); font-size: 18px; letter-spacing: 1px; }
  .match-score {
    position: absolute; top: 10px; right: 10px;
    background: var(--accent); color: #fff; font-size: 11px; font-family: var(--font-display);
    padding: 3px 10px; border-radius: 20px; letter-spacing: 1px;
  }

  /* SCROLLBAR */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--black); }
  ::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 3px; }

  /* FOOTER BAND */
  .footer-band {
    background: var(--black); border-top: 1px dashed var(--border);
    padding: 14px 24px; display: flex; justify-content: space-between;
    align-items: center; font-size: 10px; color: rgba(255,255,255,0.3);
  }

  /* PAGE FADE */
  .page-fade { animation: fadeIn .35s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

  /* STAT BADGE */
  .stat-badge {
    border: 1px solid var(--border); border-radius: 6px;
    padding: 12px 16px; text-align: center; background: rgba(255,255,255,0.03);
  }
  .stat-num { font-family: var(--font-display); font-size: 32px; color: var(--accent); }
  .stat-label { font-size: 10px; color: rgba(255,255,255,0.4); letter-spacing: 1px; text-transform: uppercase; }

  /* COLLECTION ROW */
  .col-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 0; border-bottom: 1px solid var(--border);
  }
  .col-row:last-child { border-bottom: none; }

  /* CONTACT TEXTAREA */
  textarea.inp { resize: vertical; min-height: 120px; }

  /* VINYL DECO */
  .vinyl {
    width: 90px; height: 90px; border-radius: 50%;
    background: conic-gradient(from 0deg, #1a1a2e, #2a1a4e, #1a2a3e, #1e1e28, #1a1a2e);
    border: 2px solid var(--border); flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    position: relative; box-shadow: 0 0 30px rgba(124,92,252,0.25);
  }
  .vinyl::after {
    content: ''; width: 18px; height: 18px; border-radius: 50%;
    background: var(--black); border: 2px solid var(--border);
  }

  /* WAVEFORM DECO */
  .wave { display: flex; align-items: flex-end; gap: 3px; height: 40px; }
  .wave-bar {
    width: 4px; background: var(--accent); border-radius: 2px;
    opacity: 0.6;
  }

  /* HORIZONTAL SCROLL ROW */
  .hscroll { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 4px; }
  .hscroll::-webkit-scrollbar { height: 3px; }
`;

// ── WAVEFORM decorative component ─────────────────────────────────────────
function Waveform({ heights = [20,35,15,40,25,38,12,30,42,18,35,28,10,36,22] }) {
  return (
    <div className="wave" style={{ height: 40 }}>
      {heights.map((h, i) => (
        <div key={i} className="wave-bar" style={{ height: h, opacity: 0.4 + (i % 3) * 0.15 }} />
      ))}
    </div>
  );
}

// ── NAV ───────────────────────────────────────────────────────────────────
function Nav({ page, setPage }) {
  return (
    <nav className="nav">
      <span className="nav-logo" onClick={() => setPage(PAGES.HOME)}>TAYSTE</span>
      <div className="nav-links">
        {NAV_LINKS.map(l => {
          const key = l.toLowerCase() === "home" ? PAGES.HOME
            : l.toLowerCase() === "search" ? PAGES.SEARCH
            : l.toLowerCase() === "collections" ? PAGES.COLLECTIONS
            : l.toLowerCase() === "catalogue" ? PAGES.CATALOGUE
            : PAGES.CONTACT;
          return (
            <button key={l} className={`nav-btn${page === key ? " active" : ""}`} onClick={() => setPage(key)}>
              {l}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

// ── FOOTER ────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <>
      <div style={{ textAlign: "center", padding: "32px 24px 8px", overflow: "hidden" }}>
        <span className="wordmark inverted">TAYSTE</span>
      </div>
      <div className="footer-band">
        <span>Copyright ©</span>
        <span>PLTR Style Generic.</span>
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PAGE 1 — USER HOMEPAGE
// ─────────────────────────────────────────────────────────────────────────
function HomePage({ setPage }) {
  const recentSearches = ["shoegaze, lo-fi, bedroom pop", "afrobeats fusion, 50k-500k streams", "jazz-rap, college radio presence"];
  const savedCount = 14;

  return (
    <div className="page-fade">
      {/* HERO BAND */}
      <div style={{ background: "var(--black)", padding: "32px 24px 20px", borderBottom: "1px dashed var(--border)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 20 }}>
          <div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", letterSpacing: 2, marginBottom: 8, textTransform: "uppercase" }}>Welcome back,</div>
            <div className="wordmark" style={{ fontSize: "clamp(48px, 12vw, 96px)", lineHeight: 1 }}>ALEX R.</div>
            <div style={{ color: "rgba(255,255,255,0.45)", marginTop: 8, fontStyle: "italic" }}>A&R · Independent Label · NYC</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, minWidth: 180 }}>
            <button className="pill" onClick={() => setPage(PAGES.SEARCH)}>+ New Search</button>
            <button className="pill outline" onClick={() => setPage(PAGES.CATALOGUE)}>Update Catalogue</button>
          </div>
        </div>
      </div>

      {/* STATS ROW */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 1, borderBottom: "1px solid var(--border)" }}>
        {[["14","Saved Artists"],["6","Active Lists"],["23","Searches Run"],["87%","Avg Match Score"]].map(([n,l]) => (
          <div key={l} className="stat-badge" style={{ borderRadius: 0, border: "none", borderRight: "1px solid var(--border)" }}>
            <div className="stat-num">{n}</div>
            <div className="stat-label">{l}</div>
          </div>
        ))}
      </div>

      {/* RECENT SEARCHES */}
      <div className="section-label">Recent Searches:</div>
      <div style={{ padding: "0 24px 24px" }}>
        {recentSearches.map((s, i) => (
          <div key={i} className="col-row" style={{ cursor: "pointer" }} onClick={() => setPage(PAGES.RESULTS)}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <Waveform heights={[12,25,18,32,14,28,10,22,36,16]} />
              <div>
                <div style={{ color: "var(--white)", marginBottom: 2 }}>{s}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>{["2 days ago — 18 results", "1 week ago — 31 results", "2 weeks ago — 9 results"][i]}</div>
              </div>
            </div>
            <button className="pill outline" style={{ fontSize: 10, padding: "4px 12px" }}>Re-run →</button>
          </div>
        ))}
      </div>

      {/* SAVED ARTISTS PREVIEW */}
      <div className="feat-bar">Pinned Artists — from your saved collections</div>
      <div style={{ padding: "20px 24px" }}>
        <div className="hscroll">
          {["MAVI","Ethel Cain","bdrmm","Mura Masa","Bartees Strange","Klein"].map((name, i) => (
            <div key={name} className="artist-card" style={{ minWidth: 140 }} onClick={() => setPage(PAGES.ARTIST)}>
              <div className="artist-card-img" style={{
                background: `linear-gradient(135deg, hsl(${i*40+220},60%,18%), hsl(${i*40+260},50%,12%))`,
                height: 100
              }}>
                <span className="match-score">{88 - i * 3}%</span>
              </div>
              <div className="artist-card-body">
                <div className="artist-name">{name}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginTop: 3 }}>
                  {["indie rap","gothic folk","shoegaze","electronic","indie rock","experimental"][i]}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PAGE 2 — CATALOGUE / INTAKE PAGE
// ─────────────────────────────────────────────────────────────────────────
function CataloguePage() {
  const [section, setSection] = useState(0);
  const sections = ["Label Context", "Current Roster", "A&R Brief", "Preferences"];

  return (
    <div className="page-fade">
      <div style={{ padding: "28px 24px 16px", borderBottom: "1px dashed var(--border)" }}>
        <div className="wordmark" style={{ fontSize: 42 }}>YOUR CATALOGUE</div>
        <div style={{ color: "rgba(255,255,255,0.4)", fontStyle: "italic", marginTop: 4 }}>
          Shape how TAYSTE understands your label & taste.
        </div>
      </div>

      {/* TAB BAR */}
      <div style={{ display: "flex", borderBottom: "1px solid var(--border)", overflowX: "auto" }}>
        {sections.map((s, i) => (
          <button key={s} onClick={() => setSection(i)} style={{
            background: section === i ? "var(--accent)" : "transparent",
            border: "none", borderRight: "1px solid var(--border)",
            color: "var(--white)", padding: "10px 20px", cursor: "pointer",
            fontFamily: "var(--font-body)", fontSize: 11, whiteSpace: "nowrap",
            transition: "background .2s"
          }}>{s}</button>
        ))}
      </div>

      <div style={{ padding: "24px" }}>
        {section === 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Label Name</div>
              <input className="inp" defaultValue="Outer Rim Records" />
            </div>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Label Bio / Mission</div>
              <textarea className="inp" defaultValue="Independent label based in Brooklyn. We focus on left-of-center indie, experimental pop, and hybrid rap projects with strong conceptual identities." />
            </div>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Primary Markets</div>
              <input className="inp" defaultValue="North America, UK, Europe" />
            </div>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Deal Types You Offer</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {["Distribution Deal","50/50 Net","360 Deal","Licensing Only","Joint Venture"].map(t => (
                  <label key={t} style={{ display:"flex",alignItems:"center",gap:6,cursor:"pointer",fontSize:12 }}>
                    <input type="checkbox" defaultChecked={t !== "360 Deal"} style={{ accentColor:"var(--accent)" }} />
                    {t}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {section === 1 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ color: "rgba(255,255,255,0.4)", fontStyle: "italic", marginBottom: 4 }}>
              Current signed artists — TAYSTE uses this to understand your existing sound.
            </div>
            {["MAVI","Ethel Cain","bdrmm"].map((a, i) => (
              <div key={a} className="card" style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div className="vinyl" style={{ width: 50, height: 50 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--black)", border: "1px solid var(--border)" }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: 18, letterSpacing: 1 }}>{a}</div>
                  <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)" }}>{["indie rap · signed 2022","gothic folk · signed 2023","shoegaze · signed 2021"][i]}</div>
                </div>
                <button className="pill outline" style={{ fontSize: 10, padding: "4px 10px" }}>Edit</button>
              </div>
            ))}
            <button className="pill" style={{ alignSelf: "flex-start", marginTop: 8 }}>+ Add Artist</button>
          </div>
        )}

        {section === 2 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>What are you looking for right now?</div>
              <textarea className="inp" placeholder="e.g. Looking for a female-led project that can crossover between indie rock and pop. Should have strong touring history and online presence..." />
            </div>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Genres of Interest</div>
              <div>
                {["shoegaze","indie pop","bedroom pop","lo-fi","experimental","hip-hop","R&B","jazz-adjacent","neo-soul","ambient"].map(g => (
                  <span key={g} className="tag" style={{ cursor: "pointer" }}>{g}</span>
                ))}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Stream Range Target</div>
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <input className="inp" defaultValue="10,000" style={{ width: 100 }} />
                <span style={{ color: "rgba(255,255,255,0.3)" }}>to</span>
                <input className="inp" defaultValue="500,000" style={{ width: 120 }} />
                <span style={{ color: "rgba(255,255,255,0.3)", fontSize: 11 }}>monthly listeners</span>
              </div>
            </div>
          </div>
        )}

        {section === 3 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="card">
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 }}>Match Priorities</div>
              {["Sonic similarity to roster","Growth trajectory","Live performance potential","Online community engagement","Critical / press reception","Compositional originality"].map((item, i) => (
                <div key={item} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontSize: 12 }}>{item}</span>
                  <input type="range" min="0" max="10" defaultValue={10 - i} style={{ width: 100, accentColor: "var(--accent)" }} />
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: 24 }}>
          <button className="pill">Save Changes</button>
        </div>
      </div>
      <Footer />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PAGE 3 — SEARCH + INPUTS
// ─────────────────────────────────────────────────────────────────────────
function SearchPage({ setPage }) {
  const [query, setQuery] = useState("");

  return (
    <div className="page-fade">
      <div style={{ padding: "28px 24px 16px", borderBottom: "1px dashed var(--border)" }}>
        <div className="wordmark" style={{ fontSize: 42 }}>FIND ARTISTS</div>
        <div style={{ color: "rgba(255,255,255,0.4)", fontStyle: "italic", marginTop: 4 }}>
          Describe what you're looking for. The more specific, the better.
        </div>
      </div>

      <div style={{ padding: "24px" }}>
        {/* MAIN QUERY */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Natural Language Query</div>
          <textarea
            className="inp"
            placeholder="e.g. indie rock singer-songwriter with shoegaze influences, 50k–300k monthly listeners, strong college radio presence, releasing music consistently..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            style={{ minHeight: 90 }}
          />
          <div style={{ fontSize: 10, color: "rgba(255,255,255,0.25)", marginTop: 6 }}>
            Tip: Mention genre, vibe, audience size, touring, press, region — anything that matters.
          </div>
        </div>

        {/* FILTERS GRID */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 20 }}>
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Genre Tags</div>
            <input className="inp" placeholder="shoegaze, indie pop, lo-fi..." />
          </div>
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Location</div>
            <input className="inp" placeholder="NYC, London, anywhere..." />
          </div>
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Monthly Listeners</div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input className="inp" placeholder="10k" style={{ width: "45%" }} />
              <span style={{ color: "rgba(255,255,255,0.3)" }}>–</span>
              <input className="inp" placeholder="500k" style={{ width: "45%" }} />
            </div>
          </div>
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Career Stage</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {["Emerging","Rising","Mid-level","Established"].map(s => (
                <label key={s} style={{ display:"flex",alignItems:"center",gap:5,fontSize:11,cursor:"pointer" }}>
                  <input type="checkbox" style={{ accentColor:"var(--accent)" }} defaultChecked={s !== "Established"} />
                  {s}
                </label>
              ))}
            </div>
          </div>
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Platform Presence</div>
            {["Spotify","SoundCloud","Bandcamp","TikTok","YouTube"].map(p => (
              <label key={p} style={{ display:"flex",alignItems:"center",gap:8,marginBottom:4,fontSize:11,cursor:"pointer" }}>
                <input type="checkbox" style={{ accentColor:"var(--accent)" }} defaultChecked />
                {p}
              </label>
            ))}
          </div>
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Reference Artists</div>
            <input className="inp" placeholder="Sounds like Phoebe Bridgers, or Animal Collective..." />
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 4 }}>Signed? Label pref:</div>
              <select className="inp" style={{ appearance: "none" }}>
                <option>Unsigned only</option>
                <option>Indie label OK</option>
                <option>All (including major)</option>
              </select>
            </div>
          </div>
        </div>

        {/* SORT / RANK */}
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Rank Results By</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["Match Score","Stream Growth","Engagement Rate","Press Coverage","Originality"].map(r => (
              <button key={r} className={`pill outline`} style={{ fontSize: 10, padding: "4px 14px" }}>{r}</button>
            ))}
          </div>
        </div>

        <button className="pill" style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: 14 }}
          onClick={() => setPage(PAGES.RESULTS)}>
          Run TAYSTE Search →
        </button>
      </div>
      <Footer />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PAGE 4 — SEARCH RESULTS / ARTIST OUTPUT
// ─────────────────────────────────────────────────────────────────────────
const MOCK_ARTISTS = [
  { name: "MAVI", genre: "Indie Rap / Conceptual", location: "Charlotte, NC", streams: "220k", score: 94, tags: ["lyricism","college radio","underground cred"] },
  { name: "Saya Gray", genre: "Art Pop / Avant-Folk", location: "Toronto, ON", streams: "95k", score: 91, tags: ["experimental","visual art","Decca adjacent"] },
  { name: "Lael Neale", genre: "Dream Folk / Minimal", location: "LA, CA", streams: "68k", score: 87, tags: ["Sub Pop sound","intimate","press darling"] },
  { name: "Joseph Shabason", genre: "Ambient Sax / Jazz-Adjacent", location: "Toronto, ON", streams: "44k", score: 83, tags: ["instrumental","licensing potential","critical fav"] },
  { name: "Wunderhorse", genre: "Grunge / Post-Rock", location: "London, UK", streams: "310k", score: 89, tags: ["live energy","growing fast","UK tastemakers"] },
  { name: "Mssingno", genre: "Electronic / Bass Music", location: "London, UK", streams: "130k", score: 80, tags: ["club crossover","DJ friendly","XL-adjacent"] },
];

function ResultsPage({ setPage }) {
  const [saved, setSaved] = useState([]);

  const toggle = (name) => setSaved(s => s.includes(name) ? s.filter(x => x !== name) : [...s, name]);

  return (
    <div className="page-fade">
      <div style={{ padding: "20px 24px 14px", borderBottom: "1px dashed var(--border)", display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="wordmark" style={{ fontSize: 38 }}>RESULTS</div>
          <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 11, fontStyle: "italic", marginTop: 2 }}>
            "shoegaze, indie pop, 50k–300k, unsigned" · 6 matches
          </div>
        </div>
        <button className="pill outline" onClick={() => setPage(PAGES.SEARCH)} style={{ fontSize: 10 }}>← Refine</button>
      </div>

      <div className="feat-bar">Sorted by: Match Score · AI-curated · {new Date().toLocaleDateString()}</div>

      {/* FLOW STEPS reminder */}
      <div style={{ padding: "12px 24px", borderBottom: "1px solid var(--border)" }}>
        <div className="steps">
          <div className="step">Intake<br /><span style={{fontSize:9, opacity:.7}}>Done</span></div>
          <div className="step-arrow">→</div>
          <div className="step">Search<br /><span style={{fontSize:9, opacity:.7}}>Done</span></div>
          <div className="step-arrow">→</div>
          <div className="step" style={{ background: "var(--accent2)" }}>Refine<br /><span style={{fontSize:9, opacity:.7}}>Now</span></div>
        </div>
      </div>

      <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 14 }}>
        {MOCK_ARTISTS.map((a, i) => (
          <div key={a.name} className="card" style={{ display: "flex", gap: 16, alignItems: "center", cursor: "pointer" }}
            onClick={() => setPage(PAGES.ARTIST)}>
            {/* mini vinyl */}
            <div className="vinyl" style={{ flexShrink: 0 }}>
              <div style={{ position: "absolute", inset: 0, borderRadius: "50%",
                background: `conic-gradient(from ${i*60}deg, hsl(${240+i*25},60%,18%), hsl(${260+i*20},50%,12%), hsl(${240+i*25},60%,18%))` }} />
              <div style={{ width: 18, height: 18, borderRadius: "50%", background: "var(--black)", border: "2px solid var(--border)", zIndex: 2 }} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <div className="artist-name">{a.name}</div>
                <div style={{ background: "var(--accent)", color: "#fff", fontSize: 11, fontFamily: "var(--font-display)", padding: "2px 10px", borderRadius: 20, letterSpacing: 1 }}>
                  {a.score}%
                </div>
              </div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", margin: "2px 0" }}>{a.genre} · {a.location} · {a.streams}/mo</div>
              <div>
                {a.tags.map(t => <span key={t} className="tag">{t}</span>)}
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end", flexShrink: 0 }}>
              <button
                className={saved.includes(a.name) ? "pill" : "pill outline"}
                style={{ fontSize: 10, padding: "4px 12px" }}
                onClick={e => { e.stopPropagation(); toggle(a.name); }}
              >
                {saved.includes(a.name) ? "✓ Saved" : "+ Save"}
              </button>
              <Waveform heights={[8,18,12,24,10,20,8,16,22,12]} />
            </div>
          </div>
        ))}
      </div>

      {saved.length > 0 && (
        <div style={{ margin: "0 24px 24px", padding: "12px 16px", background: "rgba(124,92,252,0.12)", border: "1px solid rgba(124,92,252,0.3)", borderRadius: 8 }}>
          <div style={{ fontSize: 11, color: "rgba(200,180,255,0.9)" }}>
            {saved.length} artist{saved.length > 1 ? "s" : ""} saved →{" "}
            <span style={{ textDecoration: "underline", cursor: "pointer" }} onClick={() => setPage(PAGES.COLLECTIONS)}>
              View Collections
            </span>
          </div>
        </div>
      )}
      <Footer />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PAGE 5 — COLLECTIONS / SAVED LISTS
// ─────────────────────────────────────────────────────────────────────────
const LISTS = [
  { name: "PRIORITY WATCH", count: 6, updated: "2 days ago", artists: ["MAVI","Saya Gray","Wunderhorse"] },
  { name: "SHOEGAZE PIPELINE", count: 4, updated: "1 week ago", artists: ["bdrmm","Lael Neale","Whitelands"] },
  { name: "OVERSEAS TARGETS", count: 8, updated: "3 weeks ago", artists: ["Mssingno","Wunderhorse","Klein"] },
];

function CollectionsPage({ setPage }) {
  const [open, setOpen] = useState(0);

  return (
    <div className="page-fade">
      <div style={{ padding: "28px 24px 16px", borderBottom: "1px dashed var(--border)" }}>
        <div className="wordmark" style={{ fontSize: 42 }}>COLLECTIONS</div>
        <div style={{ color: "rgba(255,255,255,0.4)", fontStyle: "italic", marginTop: 4 }}>
          Your saved artist lists & watchlists.
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 24px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>{LISTS.length} lists · 18 artists total</div>
        <button className="pill" style={{ fontSize: 10, padding: "5px 14px" }}>+ New List</button>
      </div>

      {LISTS.map((list, i) => (
        <div key={list.name}>
          <div style={{ padding: "16px 24px", borderBottom: "1px solid var(--border)", cursor: "pointer", background: open === i ? "rgba(124,92,252,0.07)" : "transparent" }}
            onClick={() => setOpen(open === i ? -1 : i)}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 22, letterSpacing: 1 }}>{list.name}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", marginTop: 2 }}>{list.count} artists · updated {list.updated}</div>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <button className="pill outline" style={{ fontSize: 10, padding: "4px 10px" }}>Export</button>
                <span style={{ color: "rgba(255,255,255,0.3)", fontSize: 18 }}>{open === i ? "▲" : "▼"}</span>
              </div>
            </div>
          </div>

          {open === i && (
            <div style={{ padding: "0 24px 20px", background: "rgba(255,255,255,0.02)" }}>
              {list.artists.map((name, j) => (
                <div key={name} className="col-row" style={{ cursor: "pointer" }} onClick={() => setPage(PAGES.ARTIST)}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: "50%",
                      background: `linear-gradient(135deg, hsl(${(j+i)*40+220},60%,20%), hsl(${(j+i)*40+260},50%,14%))`,
                      border: "1px solid var(--border)", flexShrink: 0 }} />
                    <div>
                      <div style={{ fontFamily: "var(--font-display)", fontSize: 16, letterSpacing: 0.5 }}>{name}</div>
                      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)" }}>Added {["2 days","1 week","2 weeks"][j]} ago</div>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <button className="pill outline" style={{ fontSize: 10, padding: "3px 10px" }}>View →</button>
                    <button className="pill outline" style={{ fontSize: 10, padding: "3px 10px", color: "rgba(255,80,80,0.7)", borderColor: "rgba(255,80,80,0.3)" }}>✕</button>
                  </div>
                </div>
              ))}
              <button className="pill outline" style={{ fontSize: 10, padding: "4px 12px", marginTop: 8 }}>+ Add Artist to List</button>
            </div>
          )}
        </div>
      ))}
      <Footer />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PAGE 6 — ARTIST LANDING PAGE
// ─────────────────────────────────────────────────────────────────────────
function ArtistPage({ setPage }) {
  const artist = MOCK_ARTISTS[0];

  return (
    <div className="page-fade">
      {/* HERO */}
      <div style={{
        background: "linear-gradient(160deg, #1a1028, #0f1a28, #0a0a0a)",
        padding: "40px 24px 28px",
        borderBottom: "1px solid var(--border)",
        position: "relative", overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: -40, right: -40, width: 220, height: 220, borderRadius: "50%",
          background: "radial-gradient(circle, rgba(124,92,252,0.2) 0%, transparent 70%)" }} />
        <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", letterSpacing: 2, marginBottom: 6, textTransform: "uppercase" }}>
          ← <span style={{ cursor: "pointer", textDecoration: "underline" }} onClick={() => setPage(PAGES.RESULTS)}>Back to results</span>
        </div>
        <div style={{ display: "flex", gap: 20, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div className="vinyl" style={{ width: 110, height: 110 }}>
            <div style={{ position: "absolute", inset: 0, borderRadius: "50%",
              background: "conic-gradient(from 30deg, #2a1a4a, #1a2a4a, #1a1a3a, #2a1a4a)" }} />
            <div style={{ width: 22, height: 22, borderRadius: "50%", background: "var(--black)", border: "2px solid var(--border)", zIndex: 2 }} />
          </div>
          <div>
            <div className="wordmark" style={{ fontSize: "clamp(48px, 14vw, 96px)", lineHeight: 0.9 }}>{artist.name}</div>
            <div style={{ color: "rgba(255,255,255,0.5)", marginTop: 8, fontStyle: "italic" }}>{artist.genre} · {artist.location}</div>
            <div style={{ marginTop: 8 }}>
              {artist.tags.map(t => <span key={t} className="tag">{t}</span>)}
            </div>
          </div>
          <div style={{ marginLeft: "auto" }}>
            <div style={{ textAlign: "center", marginBottom: 6 }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 52, color: "var(--accent)", lineHeight: 1 }}>{artist.score}%</div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", letterSpacing: 1 }}>MATCH SCORE</div>
            </div>
          </div>
        </div>
      </div>

      {/* ACTION BAR */}
      <div style={{ display: "flex", gap: 8, padding: "12px 24px", borderBottom: "1px solid var(--border)", flexWrap: "wrap" }}>
        <button className="pill">+ Save to List</button>
        <button className="pill outline">Share Profile</button>
        <button className="pill outline">Open Spotify</button>
        <button className="pill outline">Contact via TAYSTE</button>
      </div>

      {/* STATS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 1, borderBottom: "1px solid var(--border)" }}>
        {[["220k","Monthly Listeners"],["62%","6mo Growth"],["4.1%","Eng. Rate"],["18","Press Hits"]].map(([n,l]) => (
          <div key={l} className="stat-badge" style={{ borderRadius: 0, border: "none", borderRight: "1px solid var(--border)" }}>
            <div className="stat-num" style={{ fontSize: 26 }}>{n}</div>
            <div className="stat-label">{l}</div>
          </div>
        ))}
      </div>

      <div style={{ padding: "24px" }}>
        {/* AI SYNOPSIS */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>TAYSTE Analysis</div>
          <p style={{ lineHeight: 1.7, color: "rgba(255,255,255,0.8)" }}>
            {artist.name} represents a rare intersection of lyrical density and melodic accessibility in the independent rap space. Their conceptual approach and strong critical backing suggest a sustainable career arc well-suited to a boutique independent label. Growing audience skews 18–28, highly engaged on social platforms with strong college radio penetration in the Southeast and Northeast.
          </p>
        </div>

        {/* DISCOGRAPHY */}
        <div className="section-label" style={{ padding: "0 0 12px" }}>Discography:</div>
        {[["Laughing Until We Cry","2023","Album","Def Jam"],["LIFTOFF","2022","EP","Self-released"],["You Feel Good","2021","Single","Self-released"]].map(([title, year, type, label]) => (
          <div key={title} className="col-row">
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ width: 40, height: 40, borderRadius: 4, background: "linear-gradient(135deg, #2a1a4a, #1a2a3a)", border: "1px solid var(--border)" }} />
              <div>
                <div style={{ fontSize: 13 }}>{title}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)" }}>{year} · {type} · {label}</div>
              </div>
            </div>
            <Waveform heights={[8,14,10,18,8,16,10,14,20,10]} />
          </div>
        ))}

        {/* PRESS */}
        <div className="section-label" style={{ padding: "20px 0 12px" }}>Press & Tastemakers:</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {["Pitchfork 8.1","The FADER","Bandcamp Daily","NPR Music","The Wire"].map(p => (
            <span key={p} className="tag" style={{ fontSize: 11 }}>{p}</span>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PAGE 7 — CONTACT / SEND INPUT
// ─────────────────────────────────────────────────────────────────────────
function ContactPage() {
  const [sent, setSent] = useState(false);

  return (
    <div className="page-fade">
      <div style={{ padding: "28px 24px 16px", borderBottom: "1px dashed var(--border)" }}>
        <div className="wordmark" style={{ fontSize: 42 }}>REACH OUT</div>
        <div style={{ color: "rgba(255,255,255,0.4)", fontStyle: "italic", marginTop: 4 }}>
          Feedback, partnerships, artist submissions, or just saying hi.
        </div>
      </div>

      {sent ? (
        <div style={{ padding: "60px 24px", textAlign: "center" }}>
          <div className="wordmark" style={{ fontSize: 56, color: "var(--accent)" }}>SENT.</div>
          <div style={{ color: "rgba(255,255,255,0.4)", fontStyle: "italic", marginTop: 12 }}>
            We'll get back to you within 48 hours.
          </div>
        </div>
      ) : (
        <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: 16 }}>
          {/* REASON */}
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>What's this about?</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {["Product Feedback","Bug Report","Artist Submission","Partnership","Press Inquiry","Other"].map(r => (
                <button key={r} className="pill outline" style={{ fontSize: 10, padding: "4px 12px" }}>{r}</button>
              ))}
            </div>
          </div>

          {/* CONTACT INFO */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div className="card">
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Name</div>
              <input className="inp" placeholder="Your name" />
            </div>
            <div className="card">
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Email</div>
              <input className="inp" placeholder="you@label.com" type="email" />
            </div>
          </div>

          {/* ARTIST SUBMISSION (contextual) */}
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Artist / Project (if applicable)</div>
            <input className="inp" placeholder="Artist name, Spotify link, etc." />
          </div>

          {/* MESSAGE */}
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Message</div>
            <textarea className="inp" placeholder="Tell us what's on your mind..." style={{ minHeight: 140 }} />
          </div>

          {/* SOCIAL LINKS (optional) */}
          <div className="card">
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Links (optional)</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <input className="inp" placeholder="Instagram" />
              <input className="inp" placeholder="Spotify / Bandcamp / SoundCloud" />
            </div>
          </div>

          <button className="pill" style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: 14 }}
            onClick={() => setSent(true)}>
            Send It →
          </button>

          {/* DIRECT CONTACTS */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 8 }}>
            {[["Email","hello@tayste.io"],["Press","press@tayste.io"]].map(([label, val]) => (
              <div key={label} className="card">
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>{label}</div>
                <div style={{ fontStyle: "italic", color: "rgba(255,255,255,0.7)" }}>{val}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      <Footer />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState(PAGES.HOME);

  return (
    <>
      <style>{css}</style>
      <div style={{ maxWidth: 480, margin: "0 auto", minHeight: "100vh", background: "var(--black)", position: "relative" }}>
        <Nav page={page} setPage={setPage} />
        {page === PAGES.HOME && <HomePage setPage={setPage} />}
        {page === PAGES.CATALOGUE && <CataloguePage />}
        {page === PAGES.SEARCH && <SearchPage setPage={setPage} />}
        {page === PAGES.RESULTS && <ResultsPage setPage={setPage} />}
        {page === PAGES.COLLECTIONS && <CollectionsPage setPage={setPage} />}
        {page === PAGES.ARTIST && <ArtistPage setPage={setPage} />}
        {page === PAGES.CONTACT && <ContactPage />}
      </div>
    </>
  );
}
