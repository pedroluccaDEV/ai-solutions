import { useState, useEffect, useRef } from "react";
import * as THREE from "three";
import * as math from "mathjs";
import {
  Zap, MessageSquare, ArrowRight, CheckCircle2, XCircle,
  BarChart3, Users, ChevronRight, Mail, Phone,
  Building2, ShoppingBag, GraduationCap, Wrench, HeartPulse,
  Send, Check, Bot, Sparkles, TrendingUp, Shield,
  Globe, Activity, Target, MousePointerClick, Layers, ExternalLink,
  Play, Pause
} from "lucide-react";

// ─── GradualBlur ─────────────────────────────────────────────────────────────
const CURVE_FUNCTIONS = {
  linear: p => p,
  bezier: p => p * p * (3 - 2 * p),
  "ease-in": p => p * p,
  "ease-out": p => 1 - Math.pow(1 - p, 2),
  "ease-in-out": p => p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2
};

function GradualBlur({ position = "bottom", strength = 2, height = "6rem", divCount = 5, exponential = false, zIndex = 10, opacity = 1, curve = "linear" }) {
  const divs = [];
  const increment = 100 / divCount;
  const curveFunc = CURVE_FUNCTIONS[curve] || CURVE_FUNCTIONS.linear;
  const dir = { top: "to top", bottom: "to bottom", left: "to left", right: "to right" }[position] || "to bottom";
  for (let i = 1; i <= divCount; i++) {
    let progress = curveFunc(i / divCount);
    let blurValue = exponential
      ? Number(math.pow(2, progress * 4)) * 0.0625 * strength
      : 0.0625 * (progress * divCount + 1) * strength;
    const p1 = Math.round((increment * i - increment) * 10) / 10;
    const p2 = Math.round(increment * i * 10) / 10;
    const p3 = Math.round((increment * i + increment) * 10) / 10;
    const p4 = Math.round((increment * i + increment * 2) * 10) / 10;
    let gradient = `transparent ${p1}%, black ${p2}%`;
    if (p3 <= 100) gradient += `, black ${p3}%`;
    if (p4 <= 100) gradient += `, transparent ${p4}%`;
    divs.push(
      <div key={i} style={{ position:"absolute", inset:0, maskImage:`linear-gradient(${dir}, ${gradient})`, WebkitMaskImage:`linear-gradient(${dir}, ${gradient})`, backdropFilter:`blur(${blurValue.toFixed(3)}rem)`, WebkitBackdropFilter:`blur(${blurValue.toFixed(3)}rem)`, opacity }} />
    );
  }
  const isVertical = ["top","bottom"].includes(position);
  const posStyle = isVertical
    ? { height, width:"100%", left:0, right:0, [position]:0 }
    : { width:height, height:"100%", top:0, bottom:0, [position]:0 };
  return (
    <div style={{ position:"absolute", pointerEvents:"none", zIndex, isolation:"isolate", ...posStyle }}>
      <div style={{ position:"relative", width:"100%", height:"100%" }}>{divs}</div>
    </div>
  );
}

// ─── CountUp ─────────────────────────────────────────────────────────────────
function CountUp({ from = 0, to, duration = 1.5, prefix = "", suffix = "", decimals = 0 }) {
  const [val, setVal] = useState(from);
  const elRef = useRef(null);
  const started = useRef(false);
  useEffect(() => {
    const el = elRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !started.current) {
        started.current = true;
        const start = performance.now();
        const update = (now) => {
          const p = Math.min((now - start) / (duration * 1000), 1);
          const eased = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
          setVal(parseFloat((from + (to - from) * eased).toFixed(decimals)));
          if (p < 1) requestAnimationFrame(update);
        };
        requestAnimationFrame(update);
      }
    }, { threshold: 0.5 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [from, to, duration, decimals]);
  return <span ref={elRef}>{prefix}{val.toFixed(decimals)}{suffix}</span>;
}

// ─── SplitText ────────────────────────────────────────────────────────────────
function SplitText({ text, delay = 42, duration = 1.1, tag: Tag = "span", style = {} }) {
  const [visible, setVisible] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // small timeout so font renders before measuring
    const timer = setTimeout(() => {
      const obs = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) { setVisible(true); obs.disconnect(); }
      }, { threshold: 0.05 });
      obs.observe(el);
      return () => obs.disconnect();
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <Tag ref={ref} aria-label={text} style={{ display:"inline-block", ...style }}>
      {text.split("").map((ch, i) => (
        <span key={i} aria-hidden="true" style={{
          display: "inline-block",
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(30px)",
          transition: `opacity ${duration}s cubic-bezier(.22,1,.36,1) ${i * delay}ms, transform ${duration}s cubic-bezier(.22,1,.36,1) ${i * delay}ms`,
          whiteSpace: ch === " " ? "pre" : "normal",
          willChange: "opacity,transform"
        }}>{ch}</span>
      ))}
    </Tag>
  );
}

// ─── ColorBends ──────────────────────────────────────────────────────────────
const MAX_COLORS = 8;
const FRAG = `
#define MAX_COLORS ${MAX_COLORS}
uniform vec2 uCanvas;uniform float uTime;uniform float uSpeed;uniform vec2 uRot;
uniform int uColorCount;uniform vec3 uColors[MAX_COLORS];uniform int uTransparent;
uniform float uScale;uniform float uFrequency;uniform float uWarpStrength;
uniform vec2 uPointer;uniform float uMouseInfluence;uniform float uParallax;uniform float uNoise;
varying vec2 vUv;
void main(){
  float t=uTime*uSpeed;
  vec2 p=vUv*2.0-1.0;p+=uPointer*uParallax*0.1;
  vec2 rp=vec2(p.x*uRot.x-p.y*uRot.y,p.x*uRot.y+p.y*uRot.x);
  vec2 q=vec2(rp.x*(uCanvas.x/uCanvas.y),rp.y);
  q/=max(uScale,0.0001);q/=0.5+0.2*dot(q,q);q+=0.2*cos(t)-7.56;
  q+=(uPointer-rp)*uMouseInfluence*0.2;
  vec3 col=vec3(0.0);float a=1.0;
  vec2 s=q;vec3 sumCol=vec3(0.0);float cover=0.0;
  for(int i=0;i<MAX_COLORS;++i){
    if(i>=uColorCount)break;s-=0.01;
    vec2 r=sin(1.5*(s.yx*uFrequency)+2.0*cos(s*uFrequency));
    float m0=length(r+sin(5.0*r.y*uFrequency-3.0*t+float(i))/4.0);
    float kb=clamp(uWarpStrength,0.0,1.0);float km=pow(kb,0.3);
    float gain=1.0+max(uWarpStrength-1.0,0.0);
    vec2 w2=s+(r-s)*kb*gain;
    float m1=length(w2+sin(5.0*w2.y*uFrequency-3.0*t+float(i))/4.0);
    float m=mix(m0,m1,km);float w=1.0-exp(-6.0/exp(6.0*m));
    sumCol+=uColors[i]*w;cover=max(cover,w);
  }
  col=clamp(sumCol,0.0,1.0);a=uTransparent>0?cover:1.0;
  if(uNoise>0.0001){
    float n=fract(sin(dot(gl_FragCoord.xy+vec2(uTime),vec2(12.9898,78.233)))*43758.5453123);
    col+=(n-0.5)*uNoise;col=clamp(col,0.0,1.0);
  }
  gl_FragColor=vec4(uTransparent>0?col*a:col,a);
}`;
const VERT = `varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position,1.0);}`;

function ColorBends({ rotation=0, speed=0.2, colors=[], transparent=true, autoRotate=0, scale=1, frequency=1, warpStrength=1, mouseInfluence=1, parallax=0.5, noise=0.1, style }) {
  const cRef = useRef(null);
  const matRef = useRef(null);
  const rafRef = useRef(null);
  const rotRef = useRef(rotation);
  const arRef = useRef(autoRotate);
  const ptRef = useRef(new THREE.Vector2(0,0));
  const pcRef = useRef(new THREE.Vector2(0,0));

  useEffect(() => {
    const el = cRef.current;
    const scene = new THREE.Scene();
    const cam = new THREE.OrthographicCamera(-1,1,1,-1,0,1);
    const geo = new THREE.PlaneGeometry(2,2);
    const uC = Array.from({length:MAX_COLORS},()=>new THREE.Vector3(0,0,0));
    const mat = new THREE.ShaderMaterial({
      vertexShader:VERT, fragmentShader:FRAG,
      uniforms:{ uCanvas:{value:new THREE.Vector2(1,1)}, uTime:{value:0}, uSpeed:{value:speed}, uRot:{value:new THREE.Vector2(1,0)}, uColorCount:{value:0}, uColors:{value:uC}, uTransparent:{value:transparent?1:0}, uScale:{value:scale}, uFrequency:{value:frequency}, uWarpStrength:{value:warpStrength}, uPointer:{value:new THREE.Vector2(0,0)}, uMouseInfluence:{value:mouseInfluence}, uParallax:{value:parallax}, uNoise:{value:noise} },
      premultipliedAlpha:true, transparent:true
    });
    matRef.current = mat;
    const mesh = new THREE.Mesh(geo, mat);
    scene.add(mesh);
    const rend = new THREE.WebGLRenderer({antialias:false,powerPreference:"high-performance",alpha:true});
    rend.outputColorSpace = THREE.SRGBColorSpace;
    rend.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
    rend.setClearColor(0,transparent?0:1);
    rend.domElement.style.cssText="width:100%;height:100%;display:block;";
    el.appendChild(rend.domElement);
    const clk = new THREE.Clock();
    const resize = () => { const w=el.clientWidth||1,h=el.clientHeight||1; rend.setSize(w,h,false); mat.uniforms.uCanvas.value.set(w,h); };
    resize();
    const ro = new ResizeObserver(resize); ro.observe(el);
    const loop = () => {
      const dt=clk.getDelta(), elapsed=clk.elapsedTime;
      mat.uniforms.uTime.value=elapsed;
      const rad=((rotRef.current%360)+arRef.current*elapsed)*Math.PI/180;
      mat.uniforms.uRot.value.set(Math.cos(rad),Math.sin(rad));
      pcRef.current.lerp(ptRef.current,Math.min(1,dt*8));
      mat.uniforms.uPointer.value.copy(pcRef.current);
      rend.render(scene,cam);
      rafRef.current=requestAnimationFrame(loop);
    };
    rafRef.current=requestAnimationFrame(loop);
    return ()=>{ cancelAnimationFrame(rafRef.current); ro.disconnect(); geo.dispose(); mat.dispose(); rend.dispose(); rend.forceContextLoss(); if(rend.domElement.parentElement===el) el.removeChild(rend.domElement); };
  }, [frequency,mouseInfluence,noise,parallax,scale,speed,transparent,warpStrength]);

  useEffect(() => {
    const mat=matRef.current; if(!mat) return;
    rotRef.current=rotation; arRef.current=autoRotate;
    mat.uniforms.uSpeed.value=speed; mat.uniforms.uScale.value=scale;
    mat.uniforms.uFrequency.value=frequency; mat.uniforms.uWarpStrength.value=warpStrength;
    mat.uniforms.uMouseInfluence.value=mouseInfluence; mat.uniforms.uParallax.value=parallax;
    mat.uniforms.uNoise.value=noise;
    const tv=hex=>{const h=hex.replace("#","");return new THREE.Vector3(parseInt(h.slice(0,2),16)/255,parseInt(h.slice(2,4),16)/255,parseInt(h.slice(4,6),16)/255);};
    const arr=(colors||[]).filter(Boolean).slice(0,MAX_COLORS).map(tv);
    for(let i=0;i<MAX_COLORS;i++){const v=mat.uniforms.uColors.value[i];if(i<arr.length)v.copy(arr[i]);else v.set(0,0,0);}
    mat.uniforms.uColorCount.value=arr.length;
    mat.uniforms.uTransparent.value=transparent?1:0;
  }, [rotation,autoRotate,speed,scale,frequency,warpStrength,mouseInfluence,parallax,noise,colors,transparent]);

  useEffect(() => {
    const el=cRef.current; if(!el) return;
    const onMove=e=>{const r=el.getBoundingClientRect();ptRef.current.set(((e.clientX-r.left)/(r.width||1))*2-1,-(((e.clientY-r.top)/(r.height||1))*2-1));};
    el.addEventListener("pointermove",onMove);
    return ()=>el.removeEventListener("pointermove",onMove);
  },[]);

  return <div ref={cRef} style={{position:"relative",width:"100%",height:"100%",overflow:"hidden",...style}}/>;
}

// ─── PhoneDemo ────────────────────────────────────────────────────────────────
function PhoneDemo() {
  const [step, setStep] = useState(0);
  const msgs = [
    { out:false, text:"Oi! Tenho interesse no plano empresarial." },
    { out:true,  text:"Olá! Você representa uma empresa ou atua individualmente?" },
    { out:false, text:"Empresa. Clínica com 3 unidades." },
    { out:true,  text:"Perfeito! Vou agendar uma demo exclusiva. Qual o melhor horário?" },
  ];
  useEffect(()=>{
    if(step>=msgs.length) return;
    const t=setTimeout(()=>setStep(s=>s+1),step===0?800:2200);
    return()=>clearTimeout(t);
  },[step]);

  return (
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",perspective:"900px",position:"relative"}}>
      {/* Glow behind phone */}
      <div style={{position:"absolute",width:"340px",height:"340px",borderRadius:"50%",background:"radial-gradient(circle,rgba(0,255,98,0.28) 0%,rgba(0,255,98,0.08) 50%,transparent 72%)",filter:"blur(20px)",zIndex:0,animation:"glowPulse 4s ease-in-out infinite",pointerEvents:"none"}}/>
      <div style={{transformStyle:"preserve-3d",animation:"phoneFloat 6s ease-in-out infinite",position:"relative",zIndex:1}}>
        <div style={{width:"238px",background:"linear-gradient(160deg,#0d0d0d 0%,#111 100%)",borderRadius:"40px",border:"1.5px solid rgba(0,255,98,0.2)",boxShadow:"0 0 0 1px rgba(0,0,0,0.9),0 48px 96px rgba(0,0,0,0.7),0 0 70px rgba(0,255,98,0.12),inset 0 1px 0 rgba(255,255,255,0.04)",overflow:"hidden"}}>
          <div style={{width:"68px",height:"24px",margin:"0 auto",background:"#080808",borderRadius:"0 0 16px 16px",display:"flex",alignItems:"center",justifyContent:"center",gap:"5px"}}>
            <div style={{width:"7px",height:"7px",borderRadius:"50%",background:"#0d0d0d"}}/>
            <div style={{width:"10px",height:"10px",borderRadius:"50%",background:"#0d0d0d",border:"1px solid rgba(0,255,98,0.14)"}}/>
            <div style={{width:"7px",height:"7px",borderRadius:"50%",background:"#0d0d0d"}}/>
          </div>
          <div style={{padding:"0 13px 18px",display:"flex",flexDirection:"column",gap:"7px",minHeight:"390px"}}>
            <div style={{display:"flex",alignItems:"center",gap:"9px",padding:"10px 0 8px",borderBottom:"1px solid rgba(0,255,98,0.07)",marginBottom:"3px"}}>
              <div style={{width:"28px",height:"28px",borderRadius:"50%",background:"linear-gradient(135deg,#00ff62,#00c84a)",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,boxShadow:"0 0 14px rgba(0,255,98,0.45)"}}>
                <Bot size={13} color="#000"/>
              </div>
              <div>
                <div style={{fontSize:".73rem",fontWeight:700,color:"rgba(255,255,255,.88)"}}>Atendimento</div>
                <div style={{fontSize:".59rem",color:"#00ff62",display:"flex",alignItems:"center",gap:"3px"}}>
                  <div style={{width:"4px",height:"4px",borderRadius:"50%",background:"#00ff62",animation:"pulse 2s infinite",boxShadow:"0 0 6px #00ff62"}}/>Online
                </div>
              </div>
            </div>
            {msgs.slice(0,step).map((m,i)=>(
              <div key={i} style={{maxWidth:"87%",padding:"7px 11px",borderRadius:"11px",fontSize:".7rem",lineHeight:"1.52",animation:"msgIn .3s ease both",...(m.out?{background:"linear-gradient(135deg,#00c84a,#009638)",color:"white",borderBottomRightRadius:"3px",alignSelf:"flex-end",boxShadow:"0 0 18px rgba(0,255,98,0.22)"}:{background:"rgba(255,255,255,0.07)",color:"rgba(255,255,255,.8)",borderBottomLeftRadius:"3px",alignSelf:"flex-start"})}}>{m.text}</div>
            ))}
            {step<msgs.length&&(
              <div style={{display:"flex",gap:"3px",padding:"7px 11px",alignSelf:"flex-start",background:"rgba(255,255,255,0.07)",borderRadius:"11px",borderBottomLeftRadius:"3px"}}>
                {[0,150,300].map(d=><div key={d} style={{width:"4px",height:"4px",borderRadius:"50%",background:"rgba(255,255,255,.4)",animation:`blink 1s ${d}ms infinite`}}/>)}
              </div>
            )}
            {step>=msgs.length&&(
              <div style={{display:"flex",gap:"5px",flexWrap:"wrap",marginTop:"3px",alignSelf:"flex-end"}}>
                {[["rgba(0,255,98,.12)","#00ff62","✓ Qualificado"],["rgba(56,189,248,.12)","#7dd3fc","Clínica · 3 und."],["rgba(196,181,253,.12)","#c4b5fd","Alta intenção"]].map(([bg,c,label])=>(
                  <span key={label} style={{fontSize:".58rem",fontWeight:700,padding:"2px 7px",borderRadius:"100px",background:bg,color:c}}>{label}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── DemoSection ─────────────────────────────────────────────────────────────
function DemoSection() {
  const steps = [
    { id:1, icon:<MessageSquare size={16}/>, label:"Lead chega", desc:"WhatsApp · Site · Instagram", color:"#00ff62" },
    { id:2, icon:<Bot size={16}/>, label:"IA lê e entende", desc:"Intenção identificada em ms", color:"#00e5ff" },
    { id:3, icon:<Send size={16}/>, label:"Resposta enviada", desc:"Personalizada, no tom certo", color:"#a78bfa" },
    { id:4, icon:<TrendingUp size={16}/>, label:"Lead qualificado", desc:"Pronto para você fechar", color:"#fb923c" },
  ];
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(()=>{
    if(!playing) return;
    const t=setInterval(()=>setActive(a=>(a+1)%steps.length),2400);
    return()=>clearInterval(t);
  },[playing,steps.length]);

  const convMsgs = [
    {out:false, text:"Boa noite! Vi o anúncio de vocês. Quanto custa o plano mensal?", time:"23:47"},
    {out:true,  text:"Boa noite! Fico feliz 😊 Temos planos a partir de R$ 297/mês. Você atende qual segmento?", time:"23:47", bot:true},
    {out:false, text:"Sou dono de uma barbearia com 2 cadeiras.", time:"23:48"},
    {out:true,  text:"Perfeito! Para barbearias temos agendamento automático incluso. Posso te enviar uma demo amanhã?", time:"23:48", bot:true},
    {out:false, text:"Sim! Manda por favor", time:"23:49"},
  ];

  const msgThreshold = [0,1,2,2,3];

  return (
    <section id="demo" className="sec" style={{background:"#0a0a0a",position:"relative",overflow:"hidden"}}>
      <div style={{position:"absolute",top:"50%",left:"50%",transform:"translate(-50%,-50%)",width:"700px",height:"500px",background:"radial-gradient(ellipse,rgba(0,255,98,0.04) 0%,transparent 70%)",pointerEvents:"none"}}/>
      <div className="w" style={{position:"relative",zIndex:2}}>
        <div style={{textAlign:"center",maxWidth:"520px",margin:"0 auto 56px"}}>
          <div className="stag"><Play size={11}/> Funcionamento</div>
          <h2 className="sh">Veja como <em>funciona na prática</em></h2>
          <p className="sub" style={{margin:"0 auto"}}>Do primeiro contato ao lead qualificado — tudo automático, em segundos.</p>
        </div>

        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"40px",alignItems:"start"}}>
          {/* Left — step tracker */}
          <div>
            <div style={{display:"flex",flexDirection:"column"}}>
              {steps.map((s,i)=>(
                <div key={s.id} onClick={()=>{setActive(i);setPlaying(false);}} style={{cursor:"pointer",display:"flex",gap:"16px",alignItems:"stretch"}}>
                  <div style={{display:"flex",flexDirection:"column",alignItems:"center",width:"44px",flexShrink:0}}>
                    <div style={{width:"44px",height:"44px",borderRadius:"12px",flexShrink:0,display:"flex",alignItems:"center",justifyContent:"center",background:active===i?`${s.color}18`:"rgba(255,255,255,0.04)",border:active===i?`1px solid ${s.color}55`:"1px solid rgba(255,255,255,0.07)",color:active===i?s.color:"rgba(255,255,255,0.28)",transition:"all .3s",boxShadow:active===i?`0 0 24px ${s.color}25`:"none"}}>
                      {s.icon}
                    </div>
                    {i<steps.length-1&&<div style={{width:"1px",flex:1,minHeight:"18px",background:i<active?"rgba(0,255,98,0.3)":"rgba(255,255,255,0.06)",transition:"background .4s",margin:"4px 0"}}/>}
                  </div>
                  <div style={{paddingBottom:i<steps.length-1?"20px":"0",paddingTop:"10px"}}>
                    <div style={{fontSize:".88rem",fontWeight:700,color:active===i?"rgba(255,255,255,0.95)":"rgba(255,255,255,0.38)",transition:"color .3s",marginBottom:"2px"}}>{s.label}</div>
                    <div style={{fontSize:".74rem",color:"rgba(255,255,255,0.28)"}}>{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{marginTop:"28px",display:"flex",alignItems:"center",gap:"10px"}}>
              <button onClick={()=>setPlaying(p=>!p)} style={{display:"flex",alignItems:"center",gap:"7px",padding:"9px 18px",background:playing?"rgba(0,255,98,0.1)":"rgba(255,255,255,0.05)",border:playing?"1px solid rgba(0,255,98,0.25)":"1px solid rgba(255,255,255,0.1)",borderRadius:"100px",cursor:"pointer",fontFamily:"inherit",fontSize:".78rem",fontWeight:600,color:playing?"#00ff62":"rgba(255,255,255,0.45)",transition:"all .2s"}}>
                {playing?<><Pause size={12}/>Pausar</>:<><Play size={12}/>Reproduzir</>}
              </button>
              <div style={{fontSize:".72rem",color:"rgba(255,255,255,0.2)"}}>Passo {active+1} de {steps.length}</div>
            </div>

            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"10px",marginTop:"20px"}}>
              {[["< 3s","tempo de resposta"],["91%","intenção identificada"],["72%","leads qualificados"],["0","mensagens perdidas"]].map(([n,l])=>(
                <div key={l} style={{background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.07)",borderRadius:"12px",padding:"14px 16px"}}>
                  <div style={{fontSize:"1.2rem",fontWeight:700,color:"#00ff62",letterSpacing:"-.03em",textShadow:"0 0 20px rgba(0,255,98,0.4)"}}>{n}</div>
                  <div style={{fontSize:".7rem",color:"rgba(255,255,255,0.28)",marginTop:"3px"}}>{l}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right — live chat window */}
          <div style={{background:"rgba(255,255,255,0.02)",border:"1px solid rgba(255,255,255,0.07)",borderRadius:"20px",overflow:"hidden"}}>
            <div style={{padding:"14px 18px",borderBottom:"1px solid rgba(255,255,255,0.06)",display:"flex",alignItems:"center",gap:"10px"}}>
              <div style={{width:"8px",height:"8px",borderRadius:"50%",background:"#00ff62",boxShadow:"0 0 8px #00ff62",animation:"pulse 2s infinite"}}/>
              <span style={{fontSize:".78rem",color:"rgba(255,255,255,0.4)",fontWeight:600}}>WhatsApp — 23h47</span>
              <div style={{marginLeft:"auto",display:"flex",gap:"5px"}}>
                {["#ff5f57","#febc2e","#28c840"].map(c=><div key={c} style={{width:"10px",height:"10px",borderRadius:"50%",background:c}}/>)}
              </div>
            </div>

            <div style={{padding:"20px 18px",display:"flex",flexDirection:"column",gap:"10px",minHeight:"280px"}}>
              {convMsgs.map((m,i)=>(
                <div key={i} style={{display:"flex",justifyContent:m.out?"flex-end":"flex-start",opacity:active>=msgThreshold[i]?1:0.08,transform:active>=msgThreshold[i]?"translateY(0)":"translateY(8px)",transition:`opacity .5s ${i*0.08}s, transform .5s ${i*0.08}s`}}>
                  {m.bot&&<div style={{width:"22px",height:"22px",borderRadius:"50%",background:"linear-gradient(135deg,#00ff62,#00c84a)",display:"flex",alignItems:"center",justifyContent:"center",marginRight:"7px",flexShrink:0,marginTop:"2px",boxShadow:"0 0 10px rgba(0,255,98,0.3)"}}><Bot size={10} color="#000"/></div>}
                  <div style={{maxWidth:"78%",padding:"8px 12px",borderRadius:"12px",fontSize:".75rem",lineHeight:"1.55",...(m.out&&m.bot?{background:"rgba(0,255,98,0.09)",border:"1px solid rgba(0,255,98,0.18)",color:"rgba(255,255,255,0.85)",borderBottomLeftRadius:"3px"}:{background:"rgba(255,255,255,0.07)",color:"rgba(255,255,255,0.72)",borderBottomRightRadius:"3px"})}}>
                    {m.text}
                    <div style={{fontSize:".62rem",color:"rgba(255,255,255,0.22)",marginTop:"4px",textAlign:"right"}}>{m.time}</div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{padding:"12px 18px",borderTop:"1px solid rgba(255,255,255,0.05)",display:"flex",alignItems:"center",gap:"8px"}}>
              <div style={{width:"6px",height:"6px",borderRadius:"50%",background:steps[active].color,boxShadow:`0 0 8px ${steps[active].color}`}}/>
              <span style={{fontSize:".72rem",color:"rgba(255,255,255,0.38)",fontWeight:600}}>{steps[active].label} — {steps[active].desc}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── ContactForm ──────────────────────────────────────────────────────────────
function ContactForm() {
  const [sent,setSent]=useState(false);
  const [v,setV]=useState({name:"",company:"",email:"",msg:""});
  const upd=k=>e=>setV(x=>({...x,[k]:e.target.value}));
  const inp={fontFamily:"inherit",fontSize:".84rem",border:"1px solid rgba(255,255,255,0.08)",borderRadius:"10px",padding:"10px 13px",background:"rgba(255,255,255,0.04)",color:"rgba(255,255,255,0.88)",outline:"none",width:"100%",resize:"none",transition:"border-color .15s,box-shadow .15s"};
  const focus=e=>{e.target.style.borderColor="#00ff62";e.target.style.boxShadow="0 0 0 3px rgba(0,255,98,.09)";};
  const blur=e=>{e.target.style.borderColor="rgba(255,255,255,0.08)";e.target.style.boxShadow="none";};
  if(sent) return(
    <div style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:"20px",padding:"40px",textAlign:"center",display:"flex",flexDirection:"column",alignItems:"center",gap:"13px"}}>
      <div style={{width:"52px",height:"52px",borderRadius:"50%",background:"rgba(0,255,98,0.1)",display:"flex",alignItems:"center",justifyContent:"center",boxShadow:"0 0 24px rgba(0,255,98,0.2)"}}><Check size={22} color="#00ff62"/></div>
      <strong style={{fontSize:"1rem",color:"#fff"}}>Mensagem enviada!</strong>
      <span style={{fontSize:".84rem",color:"rgba(255,255,255,0.4)"}}>Retornamos em até 2 horas úteis.</span>
    </div>
  );
  return(
    <form onSubmit={e=>{e.preventDefault();setSent(true);}} style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:"20px",padding:"30px"}}>
      <div style={{fontWeight:700,fontSize:"1rem",marginBottom:"20px",color:"rgba(255,255,255,0.9)"}}>Enviar mensagem</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"12px"}}>
        {[["name","Seu nome","João Silva"],["company","Empresa","Clínica Exemplo"]].map(([k,label,ph])=>(
          <div key={k} style={{display:"flex",flexDirection:"column",gap:"5px"}}>
            <label style={{fontSize:".71rem",fontWeight:600,color:"rgba(255,255,255,0.35)"}}>{label}</label>
            <input required={k==="name"} placeholder={ph} value={v[k]} onChange={upd(k)} style={inp} onFocus={focus} onBlur={blur}/>
          </div>
        ))}
        <div style={{display:"flex",flexDirection:"column",gap:"5px",gridColumn:"1/-1"}}>
          <label style={{fontSize:".71rem",fontWeight:600,color:"rgba(255,255,255,0.35)"}}>E-mail</label>
          <input required type="email" placeholder="joao@empresa.com.br" value={v.email} onChange={upd("email")} style={inp} onFocus={focus} onBlur={blur}/>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:"5px",gridColumn:"1/-1"}}>
          <label style={{fontSize:".71rem",fontWeight:600,color:"rgba(255,255,255,0.35)"}}>Como podemos ajudar?</label>
          <textarea rows={4} placeholder="Conte um pouco sobre seu negócio..." value={v.msg} onChange={upd("msg")} style={inp} onFocus={focus} onBlur={blur}/>
        </div>
      </div>
      <button type="submit" style={{width:"100%",marginTop:"16px",padding:"13px",background:"#00ff62",color:"#000",border:"none",borderRadius:"12px",fontFamily:"inherit",fontSize:".9rem",fontWeight:700,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",gap:"7px",transition:"all .18s",boxShadow:"0 0 32px rgba(0,255,98,0.28)"}}
        onMouseEnter={e=>{e.currentTarget.style.boxShadow="0 0 48px rgba(0,255,98,0.45)";e.currentTarget.style.transform="translateY(-1px)";}}
        onMouseLeave={e=>{e.currentTarget.style.boxShadow="0 0 32px rgba(0,255,98,0.28)";e.currentTarget.style.transform="none";}}>
        <Send size={14}/> Enviar mensagem
      </button>
    </form>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const scroll=id=>document.getElementById(id)?.scrollIntoView({behavior:"smooth"});
  const segs=[
    {i:<HeartPulse size={18}/>,t:"Clínicas e consultórios",d:"Muitos contatos por dia, equipe sobrecarregada, dificuldade em organizar agendamentos."},
    {i:<Building2 size={18}/>,t:"Imobiliárias e corretores",d:"Leads que precisam de resposta imediata antes de ir para a concorrência."},
    {i:<Sparkles size={18}/>,t:"Salões e estúdios",d:"Atendimento no WhatsApp caótico, reservas perdidas, clientes sem retorno."},
    {i:<GraduationCap size={18}/>,t:"Escolas e cursos",d:"Dúvidas repetitivas tomando tempo de quem deveria focar em ensinar."},
    {i:<Wrench size={18}/>,t:"Prestadores de serviço",d:"Orçamentos lentos, clientes que somem, oportunidades perdidas."},
    {i:<ShoppingBag size={18}/>,t:"E-commerce e varejo",d:"Perguntas sobre produto, entrega e troca que consomem horas desnecessárias."},
  ];
  return(
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Lora:ital,wght@1,400&display=swap');
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
        html{scroll-behavior:smooth;}
        body{font-family:'Geist','Inter',sans-serif;background:#0a0a0a;color:#e5e7eb;-webkit-font-smoothing:antialiased;overflow-x:hidden;}
        ::placeholder{color:rgba(255,255,255,0.2)!important;}

        @keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
        @keyframes phoneFloat{0%,100%{transform:rotateY(-14deg) rotateX(5deg) translateY(0)}50%{transform:rotateY(-8deg) rotateX(3deg) translateY(-12px)}}
        @keyframes msgIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
        @keyframes blink{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-4px)}}
        @keyframes glowPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.65;transform:scale(1.15)}}

        nav{position:fixed;top:0;left:0;right:0;z-index:200;}
        .npill{max-width:1080px;margin:14px auto;padding:10px 18px;background:rgba(8,8,8,0.82);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border:1px solid rgba(0,255,98,0.12);border-radius:18px;display:flex;align-items:center;gap:6px;box-shadow:0 2px 32px rgba(0,0,0,0.6);}
        .nlogo{font-weight:700;font-size:.97rem;color:#f0fdf4;display:flex;align-items:center;gap:8px;letter-spacing:-.025em;margin-right:auto;}
        .lmark{width:28px;height:28px;border-radius:8px;background:#00ff62;display:flex;align-items:center;justify-content:center;box-shadow:0 0 16px rgba(0,255,98,0.4);}
        .nl{font-size:.83rem;font-weight:500;color:rgba(255,255,255,0.38);padding:6px 13px;border-radius:10px;border:none;background:transparent;cursor:pointer;transition:all .15s;font-family:inherit;}
        .nl:hover{color:#00ff62;background:rgba(0,255,98,0.07);}
        .nc{font-size:.83rem;font-weight:700;color:#000;padding:8px 17px;border-radius:10px;border:none;background:#00ff62;cursor:pointer;transition:all .18s;font-family:inherit;box-shadow:0 0 20px rgba(0,255,98,0.32);}
        .nc:hover{background:#00e558;box-shadow:0 0 36px rgba(0,255,98,0.5);}

        .hero{position:relative;min-height:100vh;display:flex;align-items:center;overflow:hidden;background:#030a04;}
        .hero-bg{position:absolute;inset:0;z-index:0;}
        .hero::after{content:'';position:absolute;bottom:0;left:0;right:0;height:320px;background:linear-gradient(to bottom,transparent,rgba(10,10,10,0.9) 55%,#0a0a0a);z-index:1;pointer-events:none;}
        .hero-content{position:relative;z-index:2;max-width:1080px;margin:0 auto;padding:130px 28px 110px;width:100%;}
        .hero-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:64px;align-items:center;}

        .hero-badge{display:inline-flex;align-items:center;gap:7px;font-size:.71rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#00ff62;background:rgba(0,255,98,0.08);border:1px solid rgba(0,255,98,0.22);padding:5px 13px;border-radius:100px;margin-bottom:22px;box-shadow:0 0 18px rgba(0,255,98,0.1);}
        .hero-h1{font-size:clamp(2.3rem,4.6vw,3.6rem);font-weight:700;line-height:1.1;letter-spacing:-.038em;margin-bottom:18px;color:#f0fdf4;}
        .hero-p{font-size:1.03rem;color:rgba(255,255,255,0.48);line-height:1.74;max-width:430px;margin-bottom:36px;}
        .hero-ctas{display:flex;gap:12px;flex-wrap:wrap;}

        .btn-p{display:inline-flex;align-items:center;gap:8px;background:#00ff62;color:#000;padding:13px 24px;border-radius:12px;border:none;font-family:inherit;font-size:.9rem;font-weight:700;cursor:pointer;transition:all .18s;box-shadow:0 0 36px rgba(0,255,98,0.38);}
        .btn-p:hover{background:#00e558;transform:translateY(-2px);box-shadow:0 0 56px rgba(0,255,98,0.55);}
        .btn-g{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.05);color:rgba(255,255,255,0.65);padding:13px 24px;border-radius:12px;border:1px solid rgba(255,255,255,0.1);font-family:inherit;font-size:.9rem;font-weight:500;cursor:pointer;transition:all .18s;}
        .btn-g:hover{background:rgba(255,255,255,0.09);border-color:rgba(255,255,255,0.18);}

        .sec{padding:96px 0;position:relative;}
        .sec-alt{background:#0d0d0d;}
        .w{max-width:1080px;margin:0 auto;padding:0 28px;}

        .metrics{background:#0d0d0d;border-top:1px solid rgba(255,255,255,0.05);border-bottom:1px solid rgba(255,255,255,0.05);}
        .mgrid{display:grid;grid-template-columns:repeat(4,1fr);}
        .mitem{padding:36px 24px;text-align:center;border-right:1px solid rgba(255,255,255,0.05);}
        .mitem:last-child{border-right:none;}
        .mnum{font-size:2.2rem;font-weight:700;letter-spacing:-.04em;color:#00ff62;line-height:1;text-shadow:0 0 28px rgba(0,255,98,0.45);}
        .mlbl{font-size:.78rem;color:rgba(255,255,255,0.28);margin-top:6px;}

        .stag{display:inline-flex;align-items:center;gap:6px;font-size:.7rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#00ff62;margin-bottom:12px;}
        h2.sh{font-size:clamp(1.72rem,3.4vw,2.5rem);font-weight:700;letter-spacing:-.032em;line-height:1.1;margin-bottom:14px;color:#f0fdf4;}
        h2.sh em{font-family:'Lora',Georgia,serif;font-style:italic;font-weight:400;color:#00ff62;text-shadow:0 0 32px rgba(0,255,98,0.38);}
        .sub{color:rgba(255,255,255,0.38);font-size:1rem;line-height:1.72;max-width:490px;}

        .card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:18px;transition:all .22s;}
        .card:hover{background:rgba(255,255,255,0.05);border-color:rgba(0,255,98,0.22);transform:translateY(-2px);box-shadow:0 12px 40px rgba(0,0,0,0.4),0 0 32px rgba(0,255,98,0.06);}

        .agrid{display:grid;grid-template-columns:1fr 1fr;gap:52px;align-items:center;}
        .pillar-list{display:flex;flex-direction:column;gap:11px;margin-top:30px;}
        .pillar{padding:17px 20px;display:flex;align-items:flex-start;gap:14px;}
        .pico{width:38px;height:38px;border-radius:10px;flex-shrink:0;display:flex;align-items:center;justify-content:center;}
        .pg{background:rgba(0,255,98,0.08);color:#00ff62;}
        .pt{background:rgba(0,229,255,0.08);color:#00e5ff;}
        .pe{background:rgba(52,211,153,0.08);color:#34d399;}
        .ptxt strong{display:block;font-size:.86rem;font-weight:600;color:rgba(255,255,255,0.88);margin-bottom:2px;}
        .ptxt span{font-size:.78rem;color:rgba(255,255,255,0.36);}

        .funnel{padding:28px;overflow:visible;}
        .flbl{font-size:.7rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:rgba(255,255,255,0.26);margin-bottom:16px;}
        .fbar{border-radius:9px;padding:10px 14px;font-size:.81rem;font-weight:500;display:flex;align-items:center;gap:8px;margin-bottom:6px;}
        .fpct{margin-left:auto;font-size:.7rem;font-weight:700;opacity:.45;}
        .fnote{font-size:.73rem;color:rgba(255,255,255,0.26);margin-top:14px;text-align:center;}
        .fbadge{background:rgba(0,255,98,0.06);border:1px solid rgba(0,255,98,0.14);border-radius:11px;padding:12px 16px;margin-top:18px;font-size:.78rem;color:#86efac;display:flex;align-items:center;gap:8px;}

        .sgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:52px;}
        .step{padding:30px 24px;}
        .snum{width:44px;height:44px;border-radius:12px;margin-bottom:18px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.95rem;background:rgba(0,255,98,0.07);color:#00ff62;border:1px solid rgba(0,255,98,0.2);box-shadow:0 0 18px rgba(0,255,98,0.12);}
        .step h3{font-size:.93rem;font-weight:700;margin-bottom:7px;color:rgba(255,255,255,0.88);}
        .step p{font-size:.8rem;color:rgba(255,255,255,0.36);line-height:1.62;}

        .bagrid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:52px;}
        .ba{border-radius:18px;padding:28px 26px;border:1px solid;}
        .ba-b{background:rgba(220,38,38,0.04);border-color:rgba(220,38,38,0.12);}
        .ba-a{background:rgba(0,255,98,0.04);border-color:rgba(0,255,98,0.16);}
        .balbl{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;display:flex;align-items:center;gap:7px;margin-bottom:20px;}
        .ba-b .balbl{color:#f87171;}.ba-a .balbl{color:#00ff62;}
        .bai{display:flex;align-items:flex-start;gap:9px;font-size:.84rem;line-height:1.52;margin-bottom:11px;}
        .ba-b .bai{color:rgba(248,113,113,0.65);}.ba-a .bai{color:rgba(0,255,98,0.65);}

        .wgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:52px;}
        .wcard{padding:22px 20px;}
        .wico{width:42px;height:42px;border-radius:12px;background:rgba(0,255,98,0.07);display:flex;align-items:center;justify-content:center;color:#00ff62;margin-bottom:12px;}
        .wcard h4{font-size:.88rem;font-weight:700;color:rgba(255,255,255,0.88);margin-bottom:5px;}
        .wcard p{font-size:.78rem;color:rgba(255,255,255,0.36);line-height:1.58;}

        .mband{background:#111;border-top:1px solid rgba(255,255,255,0.05);border-bottom:1px solid rgba(255,255,255,0.05);padding:22px 0;}
        .minner{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;}
        .mtxt{font-size:.85rem;color:rgba(255,255,255,0.36);display:flex;align-items:center;gap:10px;}
        .mtxt strong{color:rgba(255,255,255,0.8);font-weight:600;}
        .mbtn{display:inline-flex;align-items:center;gap:7px;font-size:.82rem;font-weight:700;color:#000;background:#00ff62;border:none;padding:9px 18px;border-radius:100px;cursor:pointer;font-family:inherit;transition:all .18s;box-shadow:0 0 20px rgba(0,255,98,0.28);}
        .mbtn:hover{background:#00e558;box-shadow:0 0 32px rgba(0,255,98,0.42);}

        .cgrid{display:grid;grid-template-columns:1fr 1fr;gap:52px;align-items:start;}
        .clist{display:flex;flex-direction:column;gap:11px;margin-top:30px;}
        .clink{padding:16px 18px;display:flex;align-items:center;gap:14px;text-decoration:none;color:inherit;}
        .cico{width:40px;height:40px;border-radius:12px;flex-shrink:0;display:flex;align-items:center;justify-content:center;}
        .ci-w{background:rgba(0,255,98,0.1);color:#00ff62;}
        .ci-e{background:rgba(0,255,98,0.08);color:#00ff62;}
        .ci-p{background:rgba(0,229,255,0.08);color:#00e5ff;}
        .ctxt strong{display:block;font-size:.85rem;font-weight:700;color:rgba(255,255,255,0.88);}
        .ctxt span{font-size:.76rem;color:rgba(255,255,255,0.3);}

        footer{padding:32px 0;border-top:1px solid rgba(255,255,255,0.05);background:#0a0a0a;}
        .fi{display:flex;align-items:center;justify-content:space-between;}
        .flogo{font-weight:700;font-size:.92rem;display:flex;align-items:center;gap:8px;color:rgba(255,255,255,0.88);}
        .fcopy{font-size:.76rem;color:rgba(255,255,255,0.2);}
        .flinks{display:flex;gap:18px;}
        .flk{font-size:.76rem;color:rgba(255,255,255,0.26);cursor:pointer;background:none;border:none;font-family:inherit;transition:color .15s;}
        .flk:hover{color:#00ff62;}

        @media(max-width:768px){
          .hero-grid,.agrid,.bagrid,.cgrid{grid-template-columns:1fr;gap:36px;}
          .sgrid,.wgrid{grid-template-columns:1fr;}
          .mgrid{grid-template-columns:repeat(2,1fr);}
          .mitem{border-right:none;border-bottom:1px solid rgba(255,255,255,0.05);}
          .mitem:nth-child(odd){border-right:1px solid rgba(255,255,255,0.05);}
          .hero-phone{display:none;}
          nav .nl{display:none;}
          .fi{flex-direction:column;gap:14px;text-align:center;}
          .minner{flex-direction:column;align-items:flex-start;}
        }
      `}</style>

      {/* NAV */}
      <nav>
        <div className="npill">
          <div className="nlogo">
            <div className="lmark"><Zap size={13} color="#000"/></div>
            Responde.Já
          </div>
          <button className="nl" onClick={()=>scroll("sobre")}>Sobre</button>
          <button className="nl" onClick={()=>scroll("demo")}>Demonstração</button>
          <button className="nl" onClick={()=>scroll("como")}>Como funciona</button>
          <button className="nl" onClick={()=>scroll("quem")}>Para quem</button>
          <button className="nl" onClick={()=>scroll("contato")}>Contato</button>
          <button className="nc" onClick={()=>scroll("contato")}>Falar com especialista</button>
        </div>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-bg">
          <ColorBends
            rotation={0} speed={0.2}
            colors={["#00ff62","#d6ffe4","#183922","#14ffb1"]}
            transparent={true} autoRotate={0} scale={1}
            frequency={1} warpStrength={1} mouseInfluence={1}
            parallax={0.5} noise={0.1}
          />
        </div>
        <GradualBlur position="bottom" height="20rem" strength={3.5} divCount={9} curve="bezier" exponential zIndex={2}/>

        <div className="hero-content">
          <div className="hero-grid">
            <div>
              <div className="hero-badge" style={{animation:"fadeUp .5s ease both"}}>
                <Activity size={11}/> Atendimento automatizado e inteligente
              </div>

              <h1 className="hero-h1" style={{animation:"fadeUp .5s .1s ease both"}}>
                Pare de perder leads por<br/>
                {/* SplitText: Lora italic, bright #00ff62 green, textShadow glow */}
                <span style={{
                  display:"inline-block",
                  fontFamily:"'Lora',Georgia,serif",
                  fontStyle:"italic",
                  fontWeight:400,
                  color:"#00ff62",
                  textShadow:"0 0 40px rgba(0,255,98,0.7),0 0 90px rgba(0,255,98,0.3)",
                  lineHeight:1.15
                }}>
                  <SplitText
                    text="falta de resposta"
                    delay={42}
                    duration={1.1}
                    tag="span"
                    style={{fontFamily:"'Lora',Georgia,serif",fontStyle:"italic",fontWeight:400,color:"#00ff62"}}
                  />
                </span>
              </h1>

              <p className="hero-p" style={{animation:"fadeUp .5s .2s ease both"}}>
                Seu negócio responde, qualifica e organiza cada contato automaticamente — no tom certo, na hora certa, sem você digitar nada.
              </p>
              <div className="hero-ctas" style={{animation:"fadeUp .5s .3s ease both"}}>
                <button className="btn-p" onClick={()=>scroll("contato")}>
                  Ver funcionando <ArrowRight size={14}/>
                </button>
                <button className="btn-g" onClick={()=>scroll("demo")}>
                  Como funciona
                </button>
              </div>
            </div>
            <div className="hero-phone">
              <PhoneDemo/>
            </div>
          </div>
        </div>
      </section>

      {/* METRICS */}
      <div className="metrics">
        <div className="w">
          <div className="mgrid">
            <div className="mitem"><div className="mnum">{"< "}<CountUp from={0} to={3} duration={1.2} suffix="s"/></div><div className="mlbl">Tempo médio de resposta</div></div>
            <div className="mitem"><div className="mnum">+<CountUp from={0} to={68} duration={1.6} suffix="%"/></div><div className="mlbl">Aumento na conversão</div></div>
            <div className="mitem"><div className="mnum"><CountUp from={0} to={24} duration={1.4} suffix="h"/></div><div className="mlbl">Atendimento ininterrupto</div></div>
            <div className="mitem"><div className="mnum"><CountUp from={100} to={0} duration={1.8}/></div><div className="mlbl">Mensagens sem resposta</div></div>
          </div>
        </div>
      </div>

      {/* ABOUT */}
      <section id="sobre" className="sec">
        <div className="w">
          <div className="agrid">
            <div>
              <div className="stag"><Sparkles size={11}/> O que é</div>
              <h2 className="sh">Seu atendimento no <em>piloto automático</em></h2>
              <p className="sub">Toda vez que alguém entra em contato, uma resposta personalizada já sai — sem você mexer em nada.</p>
              <div className="pillar-list">
                {[
                  {c:"pg",i:<Zap size={15}/>,t:"Resposta em segundos, não horas",s:"Nenhum lead fica esperando — e leads que esperam, vão embora."},
                  {c:"pt",i:<Target size={15}/>,t:"Entende o que o lead quer",s:"Não manda resposta genérica — responde com contexto e intenção."},
                  {c:"pe",i:<BarChart3 size={15}/>,t:"Organiza tudo automaticamente",s:"Veja quem tem interesse real e onde cada lead está no funil."},
                ].map((p,i)=>(
                  <div key={i} className="card pillar">
                    <div className={`pico ${p.c}`}>{p.i}</div>
                    <div className="ptxt"><strong>{p.t}</strong><span>{p.s}</span></div>
                  </div>
                ))}
              </div>
            </div>
            {/* Funnel card — NO GradualBlur as requested */}
            <div className="card funnel">
              <div className="flbl">Funil de atendimento</div>
              {[
                {bg:"rgba(0,255,98,0.06)",tc:"#86efac",i:<MessageSquare size={12}/>,t:"Mensagem recebida",p:"100%",w:"100%"},
                {bg:"rgba(0,255,98,0.05)",tc:"#6ee7b7",i:<Bot size={12}/>,t:"Intenção identificada",p:"91%",w:"91%"},
                {bg:"rgba(0,255,98,0.05)",tc:"#6ee7b7",i:<Send size={12}/>,t:"Resposta enviada",p:"91%",w:"85%"},
                {bg:"rgba(0,255,98,0.08)",tc:"#86efac",i:<TrendingUp size={12}/>,t:"Lead qualificado",p:"72%",w:"72%"},
              ].map((f,i)=>(
                <div key={i} className="fbar" style={{background:f.bg,color:f.tc,width:f.w}}>
                  {f.i}{f.t}<span className="fpct">{f.p}</span>
                </div>
              ))}
              <p className="fnote">Tudo em menos de 3 segundos, automaticamente.</p>
              <div className="fbadge"><Activity size={12}/>Hoje: 12 contatos · 7 qualificados · 3 prontos para fechar</div>
            </div>
          </div>
        </div>
      </section>

      {/* DEMO */}
      <DemoSection/>

      {/* HOW */}
      <section id="como" className="sec sec-alt">
        <div className="w">
          <div style={{textAlign:"center",maxWidth:"500px",margin:"0 auto"}}>
            <div className="stag"><MousePointerClick size={11}/> Como funciona</div>
            <h2 className="sh">3 passos. <em>Simples assim.</em></h2>
            <p className="sub" style={{margin:"0 auto"}}>Você não precisa mudar nada. A solução se encaixa no que você já usa.</p>
          </div>
          <div className="sgrid">
            {[
              {n:"1",t:"Lead manda mensagem",p:"WhatsApp, site, Instagram — não importa de onde vem o contato, tudo é capturado."},
              {n:"2",t:"Resposta vai na hora",p:"Uma resposta personalizada é enviada automaticamente no tom do seu negócio."},
              {n:"3",t:"Você só aparece pra fechar",p:"Receba o lead qualificado e entre em cena quando o contato está quente."},
            ].map((s,i)=>(
              <div key={i} className="card step">
                <div className="snum">{s.n}</div>
                <h3>{s.t}</h3><p>{s.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* BEFORE/AFTER */}
      <section className="sec" style={{position:"relative",overflow:"hidden"}}>
        <GradualBlur position="top" height="5rem" strength={1.5} divCount={5} curve="ease-out" zIndex={2}/>
        <GradualBlur position="bottom" height="5rem" strength={1.5} divCount={5} curve="ease-out" zIndex={2}/>
        <div className="w" style={{position:"relative",zIndex:3}}>
          <div style={{textAlign:"center",maxWidth:"460px",margin:"0 auto"}}>
            <div className="stag"><Shield size={11}/> Transformação</div>
            <h2 className="sh">O antes e o <em>depois</em></h2>
          </div>
          <div className="bagrid">
            <div className="ba ba-b">
              <div className="balbl"><XCircle size={13}/> Sem a solução</div>
              {["Lead manda mensagem às 22h e vai embora sem resposta","Horas gastas repetindo as mesmas informações","Impossível saber quem tem interesse real","Oportunidades escapam por falta de acompanhamento","Atendimento inconsistente nos momentos decisivos"].map((t,i)=>(
                <div key={i} className="bai"><XCircle size={13} style={{flexShrink:0,marginTop:2}}/>{t}</div>
              ))}
            </div>
            <div className="ba ba-a">
              <div className="balbl"><CheckCircle2 size={13}/> Com a solução</div>
              {["Resposta em segundos, a qualquer hora — inclusive de madrugada","Zero tempo gasto com mensagens repetitivas","Visão clara de quem está pronto para fechar","Nenhum lead cai no esquecimento ou sem retorno","Atendimento profissional e consistente sempre"].map((t,i)=>(
                <div key={i} className="bai"><CheckCircle2 size={13} style={{flexShrink:0,marginTop:2}}/>{t}</div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* WHO */}
      <section id="quem" className="sec sec-alt">
        <div className="w">
          <div style={{textAlign:"center",maxWidth:"460px",margin:"0 auto"}}>
            <div className="stag"><Users size={11}/> Para quem é</div>
            <h2 className="sh">Isso é pra você <em>se...</em></h2>
          </div>
          <div className="wgrid">
            {segs.map((w,i)=>(
              <div key={i} className="card wcard">
                <div className="wico">{w.i}</div>
                <h4>{w.t}</h4><p>{w.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* MORE BAND */}
      <div className="mband">
        <div className="w">
          <div className="minner">
            <div className="mtxt">
              <Layers size={15} color="#00ff62"/>
              <span><strong>Isso é só o começo.</strong> Temos mais soluções para automatizar outras partes do seu negócio.</span>
            </div>
            <button 
              className="mbtn" 
              onClick={() => window.location.href = "/"}
            >
              Ver todas as soluções <ExternalLink size={12}/>
            </button>
          </div>
        </div>
      </div>

      {/* CONTACT */}
      <section id="contato" className="sec">
        <div className="w">
          <div className="cgrid">
            <div>
              <div className="stag"><Globe size={11}/> Fale conosco</div>
              <h2 className="sh">Quer isso no seu <em>negócio?</em></h2>
              <p className="sub">Mostre como você recebe seus contatos hoje e montamos uma demonstração personalizada — sem compromisso.</p>
              <div className="clist">
                {[
                  {href:"https://wa.me/5541988327983",ico:<MessageSquare size={16}/>,cls:"ci-w",t:"WhatsApp",s:"Resposta em até 5 minutos"},
                  {href:"mailto:ola@respondeja.com.br",ico:<Mail size={16}/>,cls:"ci-e",t:"E-mail",s:"ola@respondeja.com.br"},
                  {href:"tel:+554199999999",ico:<Phone size={16}/>,cls:"ci-p",t:"Telefone",s:"(41) 9 9999-9999 · Seg–Sex, 9h–18h"},
                ].map((c,i)=>(
                  <a key={i} href={c.href} target="_blank" rel="noreferrer" className="card clink">
                    <div className={`cico ${c.cls}`}>{c.ico}</div>
                    <div className="ctxt"><strong>{c.t}</strong><span>{c.s}</span></div>
                    <ChevronRight size={14} style={{marginLeft:"auto",color:"rgba(255,255,255,0.14)"}}/>
                  </a>
                ))}
              </div>
            </div>
            <ContactForm/>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <div className="w">
          <div className="fi">
            <div className="flogo">
              <div className="lmark" style={{width:"22px",height:"22px",borderRadius:"7px"}}><Zap size={11} color="#000"/></div>
              Responde.Já
            </div>
            <div className="fcopy">© 2026 Responde.Já — Todos os direitos reservados</div>
            <div className="flinks">
              <button className="flk">Privacidade</button>
              <button className="flk">Termos</button>
              <button className="flk" onClick={()=>scroll("contato")}>Suporte</button>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}