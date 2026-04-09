import { useState, useEffect } from "react";
import {
  Shield, FileText, CheckCircle2, XCircle, ChevronRight,
  MessageSquare, Mail, Phone, Layers, ExternalLink, Zap,
  AlertTriangle, Clock, TrendingUp, Users, Building2,
  BarChart3, Target, ArrowRight, Check, Activity,
  BookOpen, Scale, Briefcase, Globe, Star, Search,
  FileBadge, FileCheck, FileWarning
} from "lucide-react";

const FontLink = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@1&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --white:    #ffffff;
      --off:      #f6f7f9;
      --surf:     #eef0f4;
      --bdr:      rgba(60,70,90,0.10);
      --bdr2:     rgba(60,70,90,0.18);
      --text:     #0d1117;
      --muted:    #4a5568;
      --subt:     #8895aa;
      --acc:      #334155;
      --acc2:     #1e293b;
      --acc3:     #475569;
      --acc-rgb:  51,65,85;
      --acc-dark: #0f172a;
      --red:      #dc2626;
      --green:    #16a34a;
      --amber:    #d97706;
      --font:     'Instrument Sans', 'Inter', sans-serif;
      --serif:    'Instrument Serif', Georgia, serif;
    }

    html { scroll-behavior: smooth; }
    body { font-family: var(--font); color: var(--text); background: var(--white); overflow-x: hidden; line-height: 1.6; }
    h1,h2,h3,h4,h5 { line-height: 1.15; }
    .w { max-width: 1060px; margin: 0 auto; padding: 0 28px; }
    section { padding: 88px 0; position: relative; z-index: 1; }
    .sec-alt { background: var(--off); }

    /* Aurora — slate tones */
    .aurora { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
    .ab { position: absolute; border-radius: 50%; animation: af linear infinite; will-change: transform; }
    .ab1 { width:820px;height:520px;top:-180px;left:-160px;filter:blur(72px);animation-duration:26s;background:radial-gradient(ellipse,rgba(148,163,184,0.18) 0%,transparent 70%); }
    .ab2 { width:600px;height:460px;top:50px;right:-100px;filter:blur(80px);animation-duration:33s;animation-delay:-10s;background:radial-gradient(ellipse,rgba(100,116,139,0.14) 0%,transparent 70%); }
    .ab3 { width:680px;height:400px;top:260px;left:25%;filter:blur(90px);animation-duration:21s;animation-delay:-6s;background:radial-gradient(ellipse,rgba(71,85,105,0.12) 0%,transparent 70%); }
    .ab4 { width:480px;height:360px;bottom:160px;right:12%;filter:blur(70px);animation-duration:29s;animation-delay:-16s;background:radial-gradient(ellipse,rgba(148,163,184,0.16) 0%,transparent 70%); }
    @keyframes af { 0%{transform:translate(0,0)scale(1)}25%{transform:translate(32px,-44px)scale(1.06)}50%{transform:translate(58px,-6px)scale(0.94)}75%{transform:translate(18px,30px)scale(1.05)}100%{transform:translate(0,0)scale(1)} }

    /* Nav */
    .nav-pill { position:fixed;top:14px;left:50%;transform:translateX(-50%);width:calc(100% - 40px);max-width:1060px;background:rgba(255,255,255,0.82);backdrop-filter:blur(28px);border:1px solid var(--bdr2);border-radius:18px;padding:10px 20px;display:flex;align-items:center;gap:20px;z-index:999;box-shadow:0 2px 24px rgba(51,65,85,0.08); }
    .nav-logo { display:flex;align-items:center;gap:8px;font-weight:700;font-size:0.95rem;color:var(--text);text-decoration:none; }
    .nav-logo-icon { width:28px;height:28px;background:linear-gradient(135deg,var(--acc),var(--acc2));border-radius:8px;display:flex;align-items:center;justify-content:center;color:white; }
    .nav-links { display:flex;gap:6px;flex:1;margin-left:12px; }
    .nav-links a { font-size:0.82rem;font-weight:500;color:var(--muted);text-decoration:none;padding:5px 10px;border-radius:8px;transition:all .18s; }
    .nav-links a:hover { color:var(--text);background:var(--surf); }
    .nav-cta { margin-left:auto;background:var(--acc2);color:white;border:none;padding:8px 18px;border-radius:10px;font-size:0.82rem;font-weight:700;cursor:pointer;font-family:var(--font);transition:all .2s;white-space:nowrap; }
    .nav-cta:hover { background:var(--acc-dark);transform:translateY(-1px);box-shadow:0 8px 20px rgba(51,65,85,0.25); }

    /* Eyebrow */
    .ep { display:inline-flex;align-items:center;gap:7px;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--acc);background:rgba(51,65,85,0.06);border:1px solid rgba(51,65,85,0.18);padding:5px 13px;border-radius:100px;margin-bottom:18px; }

    /* Hero */
    .hero { padding:148px 0 80px;min-height:100vh;display:flex;align-items:center; }
    .hero-g { display:grid;grid-template-columns:1.05fr 0.95fr;gap:56px;align-items:center; }
    .hero h1 { font-size:clamp(2.1rem,4.4vw,3.3rem);font-weight:700;line-height:1.08;margin-bottom:18px;letter-spacing:-0.02em; }
    .hero h1 em { font-style:italic;font-family:var(--serif);color:var(--acc);font-weight:400; }
    .hero p { font-size:1.05rem;color:var(--muted);margin-bottom:32px;line-height:1.65;max-width:420px; }
    .ctas { display:flex;gap:12px;flex-wrap:wrap; }
    .bp { background:var(--acc2);color:white;border:none;padding:13px 24px;border-radius:11px;font-size:0.9rem;font-weight:700;cursor:pointer;font-family:var(--font);transition:all .22s;display:inline-flex;align-items:center;gap:8px;text-decoration:none; }
    .bp:hover { background:var(--acc-dark);transform:translateY(-2px);box-shadow:0 10px 26px rgba(51,65,85,0.28); }
    .bo { background:transparent;color:var(--text);border:1px solid var(--bdr2);padding:13px 24px;border-radius:11px;font-size:0.9rem;font-weight:600;cursor:pointer;font-family:var(--font);transition:all .22s;text-decoration:none;display:inline-flex;align-items:center;gap:8px; }
    .bo:hover { background:var(--surf); }

    /* Hero visual */
    .hero-visual-wrap { position:relative;display:flex;justify-content:center; }
    .hero-glow { position:absolute;width:340px;height:340px;border-radius:50%;background:radial-gradient(ellipse,rgba(148,163,184,0.28) 0%,transparent 70%);top:50%;left:50%;transform:translate(-50%,-50%);animation:glowPulse 4s ease-in-out infinite; }
    .hero-visual { animation:heroFloat 6s ease-in-out infinite;position:relative;z-index:1; }
    @keyframes heroFloat { 0%,100%{transform:rotateY(-14deg)rotateX(5deg)translateY(0px)}50%{transform:rotateY(-8deg)rotateX(3deg)translateY(-12px)} }
    @keyframes glowPulse { 0%,100%{opacity:.7;transform:translate(-50%,-50%)scale(1)}50%{opacity:1;transform:translate(-50%,-50%)scale(1.15)} }

    /* Contract mockup */
    .ct-card { background:white;border-radius:20px;box-shadow:0 24px 60px rgba(0,0,0,0.1);width:310px;overflow:hidden;border:1px solid var(--bdr2); }
    .ct-header { background:linear-gradient(135deg,var(--acc),var(--acc2));padding:16px 18px;color:white;display:flex;align-items:center;justify-content:space-between; }
    .ct-header-left { display:flex;align-items:center;gap:10px; }
    .ct-header-icon { width:32px;height:32px;background:rgba(255,255,255,0.15);border-radius:8px;display:flex;align-items:center;justify-content:center; }
    .ct-header-title { font-size:0.85rem;font-weight:700; }
    .ct-header-sub { font-size:0.68rem;opacity:.75;margin-top:1px; }
    .ct-status { font-size:0.65rem;font-weight:700;padding:3px 8px;border-radius:20px;letter-spacing:.06em;text-transform:uppercase; }
    .ct-body { padding:14px; }
    .ct-section { margin-bottom:10px; }
    .ct-section-label { font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--subt);margin-bottom:6px; }
    .ct-risk { display:flex;align-items:flex-start;gap:8px;padding:9px 10px;border-radius:9px;margin-bottom:6px;font-size:0.75rem;line-height:1.4; }
    .ct-risk-high { background:rgba(220,38,38,0.06);border:1px solid rgba(220,38,38,0.18);color:#7c2020; }
    .ct-risk-mid  { background:rgba(217,119,6,0.06);border:1px solid rgba(217,119,6,0.18);color:#7c3d00; }
    .ct-risk-ok   { background:rgba(22,163,74,0.05);border:1px solid rgba(22,163,74,0.15);color:#1a5c30; }
    .ct-risk-icon { flex-shrink:0;margin-top:1px; }
    .ct-divider { height:1px;background:var(--bdr);margin:10px 0; }
    .ct-score { display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:var(--off);border-radius:10px;border:1px solid var(--bdr2); }
    .ct-score-label { font-size:0.72rem;font-weight:600;color:var(--muted); }
    .ct-score-num { font-size:1.4rem;font-weight:700;color:var(--acc2);font-family:var(--serif);font-style:italic; }
    .ct-footer { padding:0 14px 14px;display:flex;gap:8px; }
    .ct-btn-p { flex:1;background:var(--acc2);color:white;border:none;padding:9px;border-radius:9px;font-size:0.75rem;font-weight:700;cursor:pointer;font-family:var(--font); }
    .ct-btn-s { background:var(--surf);color:var(--muted);border:1px solid var(--bdr2);padding:9px 12px;border-radius:9px;font-size:0.75rem;font-weight:600;cursor:pointer;font-family:var(--font); }
    .ct-analyzing { padding:12px 14px;display:flex;flex-direction:column;gap:8px; }
    .ct-analyzing-label { font-size:0.67rem;font-weight:700;color:var(--acc);text-transform:uppercase;letter-spacing:.07em;display:flex;align-items:center;gap:6px; }
    .ct-bar { height:4px;border-radius:20px;background:var(--surf);overflow:hidden; }
    .ct-bar-fill { height:100%;border-radius:20px;background:linear-gradient(90deg,var(--acc3),var(--acc2));animation:barFill 1.8s ease-in-out infinite alternate; }
    @keyframes barFill { from{width:20%}to{width:90%} }
    .dot-pulse { display:flex;gap:3px;align-items:center; }
    .dot-pulse span { width:4px;height:4px;border-radius:50%;background:var(--acc);animation:dotBounce 1.2s ease-in-out infinite; }
    .dot-pulse span:nth-child(2){animation-delay:.2s}
    .dot-pulse span:nth-child(3){animation-delay:.4s}
    @keyframes dotBounce{0%,80%,100%{transform:scale(.6);opacity:.4}40%{transform:scale(1);opacity:1}}

    /* Section header */
    .sh { display:inline-flex;align-items:center;gap:6px;font-size:0.7rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--acc);margin-bottom:13px; }
    h2 { font-size:clamp(1.65rem,3.4vw,2.45rem);font-weight:700;letter-spacing:-.02em;margin-bottom:16px; }
    h2 em { font-style:italic;font-family:var(--serif);color:var(--acc);font-weight:400; }

    /* Glass card */
    .g { background:rgba(255,255,255,0.78);backdrop-filter:blur(22px);border:1px solid var(--bdr2);border-radius:18px;box-shadow:0 2px 16px rgba(51,65,85,0.04);transition:all .22s; }
    .g:hover { transform:translateY(-2px);box-shadow:0 8px 28px rgba(51,65,85,0.1);border-color:rgba(51,65,85,0.25); }

    /* Metrics */
    .met-box { display:grid;grid-template-columns:repeat(4,1fr);gap:18px; }
    .met-item { text-align:center;padding:28px 16px; }
    .met-num { font-size:2.5rem;font-weight:700;color:var(--acc2);line-height:1;font-family:var(--serif);font-style:italic; }
    .met-label { font-size:0.78rem;color:var(--muted);margin-top:6px;font-weight:600; }

    /* Sobre */
    .two-col { display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center; }
    .sobre-cards { display:flex;flex-direction:column;gap:14px; }
    .sobre-card { padding:18px 20px;display:flex;align-items:flex-start;gap:14px; }
    .sobre-icon { width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(51,65,85,0.07);color:var(--acc);flex-shrink:0; }
    .sobre-card h4 { font-size:0.88rem;font-weight:700;margin-bottom:4px; }
    .sobre-card p { font-size:0.82rem;color:var(--muted);line-height:1.5; }

    /* Steps */
    .three-col { display:grid;grid-template-columns:repeat(3,1fr);gap:18px;position:relative; }
    .three-col::before { content:'';position:absolute;top:36px;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--bdr2),transparent);z-index:0; }
    .step-card { padding:28px 22px;position:relative;z-index:1; }
    .step-num { width:42px;height:42px;border-radius:12px;background:rgba(51,65,85,0.07);border:1px solid rgba(51,65,85,0.15);color:var(--acc);font-size:0.8rem;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:16px; }
    .step-card h3 { font-size:0.95rem;font-weight:700;margin-bottom:8px; }
    .step-card p { font-size:0.82rem;color:var(--muted);line-height:1.55; }

    /* Antes depois */
    .ad-grid { display:grid;grid-template-columns:1fr 1fr;gap:24px; }
    .ad-card { padding:28px;border-radius:18px; }
    .ad-antes { background:rgba(220,38,38,0.04);border:1px solid rgba(220,38,38,0.15); }
    .ad-depois { background:rgba(51,65,85,0.04);border:1px solid rgba(51,65,85,0.18); }
    .ad-title { display:flex;align-items:center;gap:8px;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;margin-bottom:18px; }
    .ad-antes .ad-title { color:var(--red); }
    .ad-depois .ad-title { color:var(--acc2); }
    .ad-item { display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;font-size:0.85rem;line-height:1.5; }
    .ad-antes .ad-item { color:#7c2020; }
    .ad-depois .ad-item { color:#2d3748; }

    /* Para quem */
    .quem-grid { display:grid;grid-template-columns:repeat(3,1fr);gap:16px; }
    .quem-card { padding:22px;display:flex;align-items:flex-start;gap:14px; }
    .quem-icon { width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(51,65,85,0.07);color:var(--acc);flex-shrink:0; }
    .quem-card h4 { font-size:0.87rem;font-weight:700;margin-bottom:4px; }
    .quem-card p { font-size:0.78rem;color:var(--muted);line-height:1.45; }

    /* Band */
    .band { background:rgba(238,240,244,0.7);backdrop-filter:blur(14px);border-top:1px solid var(--bdr2);border-bottom:1px solid var(--bdr2);padding:28px 0; }
    .band-inner { display:flex;align-items:center;gap:16px; }
    .band-icon { width:40px;height:40px;border-radius:10px;background:rgba(51,65,85,0.08);display:flex;align-items:center;justify-content:center;color:var(--acc);flex-shrink:0; }
    .band-text { flex:1; }
    .band-text strong { font-size:0.9rem;font-weight:700;display:block;margin-bottom:2px; }
    .band-text span { font-size:0.8rem;color:var(--muted); }
    .band-btn { background:var(--white);border:1px solid var(--bdr2);color:var(--text);padding:8px 16px;border-radius:100px;font-size:0.8rem;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:6px;transition:all .18s;white-space:nowrap;font-family:var(--font); }
    .band-btn:hover { background:var(--surf); }

    /* Contact */
    .contact-grid { display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:start; }
    .channel-list { display:flex;flex-direction:column;gap:12px;margin-top:28px; }
    .channel { padding:16px 18px;display:flex;align-items:center;gap:14px;text-decoration:none;cursor:pointer; }
    .channel-icon { width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(51,65,85,0.07);color:var(--acc);flex-shrink:0; }
    .channel-info { flex:1; }
    .channel-info strong { font-size:0.85rem;font-weight:700;display:block;color:var(--text); }
    .channel-info span { font-size:0.75rem;color:var(--muted); }
    .channel svg:last-child { color:var(--subt); }

    .form-card { padding:28px; }
    .form-title { font-size:1rem;font-weight:700;margin-bottom:20px; }
    .form-row { display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:0; }
    .form-field { display:flex;flex-direction:column;gap:5px;margin-bottom:12px; }
    .form-field label { font-size:0.75rem;font-weight:600;color:var(--muted); }
    .form-field input,.form-field textarea { padding:10px 14px;border-radius:10px;border:1px solid var(--bdr2);background:var(--white);font-family:var(--font);font-size:0.85rem;color:var(--text);outline:none;transition:border-color .18s; }
    .form-field input:focus,.form-field textarea:focus { border-color:var(--acc); }
    .form-field textarea { resize:vertical;min-height:90px; }
    .form-submit { width:100%;background:var(--acc2);color:white;border:none;padding:13px;border-radius:11px;font-size:0.9rem;font-weight:700;cursor:pointer;font-family:var(--font);display:flex;align-items:center;justify-content:center;gap:8px;transition:all .22s; }
    .form-submit:hover { background:var(--acc-dark);transform:translateY(-1px);box-shadow:0 10px 26px rgba(51,65,85,0.22); }
    .form-success { text-align:center;padding:32px;display:flex;flex-direction:column;align-items:center;gap:12px; }
    .form-success-icon { width:52px;height:52px;border-radius:50%;background:rgba(22,163,74,0.1);display:flex;align-items:center;justify-content:center;color:var(--green); }
    .form-success h4 { font-size:1rem;font-weight:700; }
    .form-success p { font-size:0.83rem;color:var(--muted); }

    footer { background:var(--off);border-top:1px solid var(--bdr2);padding:32px 0; }
    .footer-inner { display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px; }
    .footer-logo { display:flex;align-items:center;gap:8px;font-weight:700;font-size:0.88rem; }
    .footer-logo-icon { width:26px;height:26px;background:linear-gradient(135deg,var(--acc),var(--acc2));border-radius:7px;display:flex;align-items:center;justify-content:center;color:white; }
    .footer-links { display:flex;gap:18px; }
    .footer-links a { font-size:0.78rem;color:var(--muted);text-decoration:none;transition:color .15s; }
    .footer-links a:hover { color:var(--text); }
    .footer-copy { font-size:0.75rem;color:var(--subt); }

    .rev { opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s ease; }
    .rev.vis { opacity:1;transform:translateY(0); }

    @keyframes up { from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)} }
    .anim-ep   { animation:up .6s .0s ease both; }
    .anim-h1   { animation:up .6s .1s ease both; }
    .anim-sub  { animation:up .6s .2s ease both; }
    .anim-ctas { animation:up .6s .3s ease both; }

    /* Risk badge */
    .risk-badge { display:inline-flex;align-items:center;gap:4px;font-size:0.65rem;font-weight:700;padding:2px 7px;border-radius:20px;text-transform:uppercase;letter-spacing:.05em; }
    .rb-high { background:rgba(220,38,38,0.1);color:#b91c1c; }
    .rb-mid  { background:rgba(217,119,6,0.1);color:#b45309; }
    .rb-ok   { background:rgba(22,163,74,0.1);color:#15803d; }

    @media(max-width:768px){
      .hero-g,.two-col,.contact-grid{grid-template-columns:1fr;gap:32px}
      .hero-visual-wrap{display:none}
      .three-col,.quem-grid{grid-template-columns:1fr}
      .met-box{grid-template-columns:repeat(2,1fr)}
      .ad-grid{grid-template-columns:1fr}
      .form-row{grid-template-columns:1fr}
      .nav-links{display:none}
      .footer-inner{flex-direction:column;align-items:flex-start}
    }
  `}</style>
);

/* ─── Hero Visual — Contract Analyzer ─── */
const HeroVisual = () => {
  const [phase, setPhase] = useState(0); // 0=idle, 1=analyzing, 2=report
  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 2000);
    const t2 = setTimeout(() => setPhase(2), 4200);
    const t3 = setTimeout(() => setPhase(0), 8500);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [phase]);

  return (
    <div className="hero-visual-wrap">
      <div className="hero-glow" />
      <div className="hero-visual">
        <div className="ct-card">
          <div className="ct-header">
            <div className="ct-header-left">
              <div className="ct-header-icon"><FileText size={16} /></div>
              <div>
                <div className="ct-header-title">Contrato de Prestação de Serviços</div>
                <div className="ct-header-sub">NDA_ClienteABC_2024.pdf · 12 páginas</div>
              </div>
            </div>
            <span className="ct-status" style={{
              background: phase === 0 ? 'rgba(255,255,255,0.15)' : phase === 1 ? 'rgba(255,255,255,0.2)' : 'rgba(22,163,74,0.9)',
              color: 'white'
            }}>
              {phase === 0 ? 'Aguardando' : phase === 1 ? 'Analisando...' : '✓ Revisado'}
            </span>
          </div>

          {phase === 0 && (
            <>
              <div className="ct-body">
                <div className="ct-section">
                  <div className="ct-section-label">Aguardando análise</div>
                  {[
                    { label: "Cláusula de rescisão", cls: "ct-risk-mid", icon: <AlertTriangle size={12} style={{color:'#b45309'}} /> },
                    { label: "Prazo de entrega indefinido", cls: "ct-risk-high", icon: <XCircle size={12} style={{color:'#b91c1c'}} /> },
                    { label: "Multa por atraso", cls: "ct-risk-mid", icon: <AlertTriangle size={12} style={{color:'#b45309'}} /> },
                  ].map(({ label, cls, icon }, i) => (
                    <div key={i} className={`ct-risk ${cls}`} style={{opacity:0.4}}>
                      <span className="ct-risk-icon">{icon}</span>
                      <span>{label}</span>
                    </div>
                  ))}
                </div>
                <div style={{textAlign:'center',padding:'8px 0',fontSize:'0.75rem',color:'var(--subt)'}}>
                  Envie o contrato para iniciar a análise
                </div>
              </div>
              <div className="ct-footer">
                <button className="ct-btn-p">Analisar contrato →</button>
                <button className="ct-btn-s">Ver exemplo</button>
              </div>
            </>
          )}

          {phase === 1 && (
            <div className="ct-analyzing">
              <div className="ct-analyzing-label">
                <div className="dot-pulse"><span /><span /><span /></div>
                Analisando documento
              </div>
              {[
                "Lendo cláusulas e obrigações...",
                "Verificando riscos jurídicos...",
                "Comparando padrões legais...",
                "Gerando relatório de riscos...",
              ].map((t, i) => (
                <div key={i}>
                  <div style={{fontSize:'0.72rem',color:'var(--muted)',marginBottom:'4px'}}>{t}</div>
                  <div className="ct-bar">
                    <div className="ct-bar-fill" style={{animationDelay:`${i*0.25}s`}} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {phase === 2 && (
            <>
              <div className="ct-body">
                <div className="ct-section">
                  <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'8px'}}>
                    <div className="ct-section-label">Riscos identificados</div>
                    <div style={{display:'flex',gap:'4px'}}>
                      <span className="risk-badge rb-high">2 alto</span>
                      <span className="risk-badge rb-mid">1 médio</span>
                    </div>
                  </div>
                  {[
                    { label: "Prazo de entrega indefinido — risco de litígio", cls: "ct-risk-high", icon: <XCircle size={12} style={{color:'#b91c1c'}} /> },
                    { label: "Cláusula de exclusividade abusiva (art. 421)", cls: "ct-risk-high", icon: <XCircle size={12} style={{color:'#b91c1c'}} /> },
                    { label: "Multa rescisória acima do padrão de mercado", cls: "ct-risk-mid", icon: <AlertTriangle size={12} style={{color:'#b45309'}} /> },
                    { label: "Foro e jurisdição — conforme legislação", cls: "ct-risk-ok", icon: <CheckCircle2 size={12} style={{color:'#15803d'}} /> },
                  ].map(({ label, cls, icon }, i) => (
                    <div key={i} className={`ct-risk ${cls}`}>
                      <span className="ct-risk-icon">{icon}</span>
                      <span>{label}</span>
                    </div>
                  ))}
                </div>
                <div className="ct-divider" />
                <div className="ct-score">
                  <div>
                    <div className="ct-score-label">Score de risco</div>
                    <div style={{fontSize:'0.7rem',color:'var(--subt)'}}>Requer ajustes antes de assinar</div>
                  </div>
                  <div className="ct-score-num" style={{color:'#b45309'}}>6.2/10</div>
                </div>
              </div>
              <div className="ct-footer">
                <button className="ct-btn-p">Ver versão otimizada</button>
                <button className="ct-btn-s">Exportar</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

/* ─── Reveal ─── */
const useReveal = () => {
  useEffect(() => {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('vis'); });
    }, { threshold: 0.1 });
    document.querySelectorAll('.rev').forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
};

/* ─── App ─── */
export default function ContratoIA() {
  const [form, setForm] = useState({ nome:'', empresa:'', email:'', msg:'' });
  const [sent, setSent] = useState(false);
  useReveal();

  return (
    <>
      <FontLink />

      <div className="aurora">
        <div className="ab ab1" /><div className="ab ab2" />
        <div className="ab ab3" /><div className="ab ab4" />
      </div>

      {/* Nav */}
      <nav className="nav-pill">
        <a href="#hero" className="nav-logo">
          <div className="nav-logo-icon"><Scale size={14} /></div>
          ContratoIA
        </a>
        <div className="nav-links">
          <a href="#sobre">Sobre</a>
          <a href="#como">Como funciona</a>
          <a href="#quem">Para quem</a>
        </div>
        <button className="nav-cta" onClick={() => document.getElementById('contato')?.scrollIntoView({behavior:'smooth'})}>
          Falar com especialista
        </button>
      </nav>

      {/* Hero */}
      <section className="hero" id="hero">
        <div className="w">
          <div className="hero-g">
            <div>
              <div className="ep anim-ep">
                <Shield size={11} />
                Revisão automática de contratos
              </div>
              <h1 className="anim-h1">
                Feche contratos <em>mais rápido</em><br />
                sem risco jurídico
              </h1>
              <p className="anim-sub">
                Você envia o contrato — em minutos recebe um relatório completo com os riscos, os erros e as sugestões de ajuste. Sem esperar dias. Sem depender de revisão manual.
              </p>
              <div className="ctas anim-ctas">
                <a href="#contato" className="bp">
                  Quero ver na prática <ArrowRight size={15} />
                </a>
                <a href="#como" className="bo">
                  Como funciona
                </a>
              </div>
            </div>
            <HeroVisual />
          </div>
        </div>
      </section>

      {/* Métricas */}
      <section style={{padding:'48px 0',background:'var(--off)',borderTop:'1px solid var(--bdr2)',borderBottom:'1px solid var(--bdr2)'}}>
        <div className="w">
          <div className="met-box">
            {[
              { num:"85%", label:"redução no tempo de revisão" },
              { num:"3min", label:"para analisar um contrato completo" },
              { num:"10×", label:"mais contratos fechados no prazo" },
              { num:"Zero", label:"riscos ocultos passando despercebidos" },
            ].map((m, i) => (
              <div className="met-item g rev" key={i} style={{transitionDelay:`${i*0.1}s`}}>
                <div className="met-num">{m.num}</div>
                <div className="met-label">{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sobre */}
      <section id="sobre">
        <div className="w">
          <div className="two-col">
            <div>
              <div className="sh rev"><Shield size={11} /> O que é</div>
              <h2 className="rev">Seu sistema de <em>análise</em><br />e validação de contratos</h2>
              <p className="rev" style={{color:'var(--muted)',fontSize:'0.95rem',lineHeight:1.7,marginBottom:20}}>
                Não é um advogado digital — é uma camada de segurança que analisa cada cláusula antes de você assinar ou enviar. Identifica riscos, sinaliza inconsistências e sugere ajustes em minutos.
              </p>
              <p className="rev" style={{color:'var(--muted)',fontSize:'0.95rem',lineHeight:1.7}}>
                Você mantém o controle e a decisão final. O sistema cuida da parte demorada: leitura linha a linha, comparação com padrões legais e geração do relatório de risco.
              </p>
            </div>
            <div className="sobre-cards">
              {[
                { icon:<Clock size={16}/>, title:"Análise em minutos", desc:"Contratos de 10, 20 ou 50 páginas revisados em menos tempo do que levaria para fazer a primeira leitura." },
                { icon:<AlertTriangle size={16}/>, title:"Riscos destacados com clareza", desc:"Cláusulas problemáticas, inconsistências e pontos críticos identificados e explicados em linguagem simples." },
                { icon:<FileCheck size={16}/>, title:"Versão otimizada incluída", desc:"Além do relatório, você recebe sugestões de melhoria e uma versão ajustada pronta para usar." },
              ].map((c, i) => (
                <div className="sobre-card g rev" key={i} style={{transitionDelay:`${i*0.1}s`}}>
                  <div className="sobre-icon">{c.icon}</div>
                  <div>
                    <h4>{c.title}</h4>
                    <p>{c.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Como funciona */}
      <section id="como" className="sec-alt">
        <div className="w">
          <div style={{textAlign:'center',marginBottom:48}}>
            <div className="sh rev" style={{justifyContent:'center'}}><Zap size={11} /> Como funciona</div>
            <h2 className="rev">3 passos. <em>Contrato seguro.</em></h2>
          </div>
          <div className="three-col">
            {[
              { num:"01", icon:<FileText size={16}/>, title:"Envie o contrato", desc:"PDF, Word ou texto colado diretamente. Qualquer formato, qualquer tamanho. Leva segundos para fazer o envio." },
              { num:"02", icon:<Search size={16}/>, title:"O sistema analisa tudo", desc:"Cada cláusula é lida, comparada com padrões legais e avaliada quanto a riscos, inconsistências e pontos críticos ocultos." },
              { num:"03", icon:<FileCheck size={16}/>, title:"Receba o relatório completo", desc:"Problemas encontrados, sugestões de melhoria, alertas de risco e a versão otimizada do contrato — tudo em minutos." },
            ].map((s, i) => (
              <div className="step-card g rev" key={i} style={{transitionDelay:`${i*0.12}s`}}>
                <div className="step-num">{s.num}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Antes × Depois */}
      <section>
        <div className="w">
          <div style={{textAlign:'center',marginBottom:40}}>
            <div className="sh rev" style={{justifyContent:'center'}}><Activity size={11} /> Antes × Depois</div>
            <h2 className="rev">O que <em>muda</em> no dia a dia</h2>
          </div>
          <div className="ad-grid">
            <div className="ad-card ad-antes rev">
              <div className="ad-title"><XCircle size={14} /> Sem o sistema</div>
              {[
                "Contrato espera 3 dias na fila do jurídico",
                "Cliente esfria, negocia com concorrente, negócio perdido",
                "Erros só aparecem depois da assinatura — tarde demais",
                "Alto custo com revisões manuais de advogados externos",
                "Nenhuma padronização — cada contrato é um risco diferente",
              ].map((t, i) => (
                <div className="ad-item" key={i}>
                  <XCircle size={14} style={{color:'var(--red)',flexShrink:0,marginTop:2}} />
                  <span>{t}</span>
                </div>
              ))}
            </div>
            <div className="ad-card ad-depois rev" style={{transitionDelay:'0.1s'}}>
              <div className="ad-title"><CheckCircle2 size={14} /> Com o sistema</div>
              {[
                "Análise completa em menos de 3 minutos",
                "Time fecha o negócio no mesmo dia com contrato validado",
                "Riscos identificados antes de qualquer assinatura",
                "Redução drástica de custos com revisões repetitivas",
                "Padronização automática — compliance garantido em todos os contratos",
              ].map((t, i) => (
                <div className="ad-item" key={i}>
                  <CheckCircle2 size={14} style={{color:'var(--acc)',flexShrink:0,marginTop:2}} />
                  <span>{t}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Para quem */}
      <section id="quem" className="sec-alt">
        <div className="w">
          <div style={{textAlign:'center',marginBottom:40}}>
            <div className="sh rev" style={{justifyContent:'center'}}><Users size={11} /> Para quem é</div>
            <h2 className="rev">Para quem assina ou <em>revisa</em><br />contratos no dia a dia</h2>
          </div>
          <div className="quem-grid">
            {[
              { icon:<Building2 size={16}/>, title:"Departamentos jurídicos", desc:"Reduza o backlog de revisões e libere o time para o que exige raciocínio estratégico, não leitura repetitiva." },
              { icon:<TrendingUp size={16}/>, title:"Times comerciais (closers)", desc:"Pare de perder negócios por gargalo jurídico. Analise, ajuste e feche contratos no mesmo dia." },
              { icon:<Globe size={16}/>, title:"Startups sem jurídico interno", desc:"Tenha a segurança de uma revisão especializada sem o custo de um advogado para cada contrato." },
              { icon:<BarChart3 size={16}/>, title:"Alto volume de contratos", desc:"Se sua empresa lida com dezenas ou centenas de contratos por mês, escalabilidade sem custo proporcional." },
              { icon:<Scale size={16}/>, title:"Escritórios de advocacia", desc:"Automatize a triagem e revisão inicial — seu time foca em análise estratégica e relacionamento com cliente." },
              { icon:<Briefcase size={16}/>, title:"Empresas SaaS e tech", desc:"Contratos recorrentes, termos de uso e acordos comerciais revisados e padronizados automaticamente." },
            ].map((c, i) => (
              <div className="quem-card g rev" key={i} style={{transitionDelay:`${i*0.08}s`}}>
                <div className="quem-icon">{c.icon}</div>
                <div>
                  <h4>{c.title}</h4>
                  <p>{c.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Band */}
      <div className="band">
        <div className="w">
          <div className="band-inner">
            <div className="band-icon"><Layers size={18} /></div>
            <div className="band-text">
              <strong>Mais de 20 soluções de automação disponíveis</strong>
              <span>Atendimento, vendas, conteúdo, prescrição, CRM e muito mais — cada uma adaptada ao seu setor.</span>
            </div>
            <button className="band-btn">Ver todas as soluções <ExternalLink size={13} /></button>
          </div>
        </div>
      </div>

      {/* Contato */}
      <section id="contato">
        <div className="w">
          <div style={{marginBottom:40}}>
            <div className="sh rev"><MessageSquare size={11} /> Fale com a gente</div>
            <h2 className="rev">Quer isso no seu <em>negócio?</em></h2>
            <p className="rev" style={{color:'var(--muted)',maxWidth:420,fontSize:'0.95rem',lineHeight:1.65}}>
              Conta como é a sua operação de contratos hoje — mostramos exatamente onde e quanto você pode ganhar com a automação.
            </p>
          </div>
          <div className="contact-grid">
            <div>
              <div className="channel-list">
                {[
                  { icon:<MessageSquare size={16}/>, label:"WhatsApp", detail:"Resposta em até 1 hora · Seg–Sex" },
                  { icon:<Mail size={16}/>, label:"E-mail", detail:"contato@contratoai.com.br" },
                  { icon:<Phone size={16}/>, label:"Telefone", detail:"(11) 9 9999-0000 · Horário comercial" },
                ].map((c, i) => (
                  <div className="channel g rev" key={i} style={{transitionDelay:`${i*0.1}s`}}>
                    <div className="channel-icon">{c.icon}</div>
                    <div className="channel-info">
                      <strong>{c.label}</strong>
                      <span>{c.detail}</span>
                    </div>
                    <ChevronRight size={14} />
                  </div>
                ))}
              </div>
            </div>
            <div className="form-card g rev">
              {!sent ? (
                <>
                  <div className="form-title">Enviar mensagem</div>
                  <div className="form-row">
                    <div className="form-field">
                      <label>Nome</label>
                      <input placeholder="Seu nome" value={form.nome} onChange={e=>setForm(p=>({...p,nome:e.target.value}))} />
                    </div>
                    <div className="form-field">
                      <label>Empresa</label>
                      <input placeholder="Nome da empresa" value={form.empresa} onChange={e=>setForm(p=>({...p,empresa:e.target.value}))} />
                    </div>
                  </div>
                  <div className="form-field">
                    <label>E-mail</label>
                    <input type="email" placeholder="seu@email.com" value={form.email} onChange={e=>setForm(p=>({...p,email:e.target.value}))} />
                  </div>
                  <div className="form-field">
                    <label>Como podemos ajudar?</label>
                    <textarea placeholder="Conta como funciona a revisão de contratos hoje na sua empresa..." value={form.msg} onChange={e=>setForm(p=>({...p,msg:e.target.value}))} />
                  </div>
                  <button className="form-submit" onClick={e=>{e.preventDefault();setSent(true);}}>
                    Enviar mensagem <ArrowRight size={15} />
                  </button>
                </>
              ) : (
                <div className="form-success">
                  <div className="form-success-icon"><Check size={24} /></div>
                  <h4>Mensagem enviada!</h4>
                  <p>Entraremos em contato em até 1 hora nos dias úteis. Obrigado!</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer>
        <div className="w">
          <div className="footer-inner">
            <div className="footer-logo">
              <div className="footer-logo-icon"><Scale size={13} /></div>
              ContratoIA
            </div>
            <div className="footer-links">
              <a href="#">Privacidade</a>
              <a href="#">Termos de uso</a>
              <a href="#">Cookies</a>
            </div>
            <div className="footer-copy">© 2025 ContratoIA · Todos os direitos reservados</div>
          </div>
        </div>
      </footer>
    </>
  );
}