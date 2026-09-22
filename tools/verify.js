/* ぽよんダンジョンの総当たり検査（ブラウザのコンソールで使う）
   使い方：ゲームを開いて
     await import("./tools/verify.js")   または   eval(await (await fetch("tools/verify.js")).text())
     __check("slime", 3, 0, 60)   // 系統・段階・何番目の区切りから・いくつ
   ステージをゴールまで先に作り、障害物のすきま（区切り）ごとに、
   跳ぶ／跳ばない／攻撃／すいよせ の組み合わせを全部ためして
   「通れるか」「その区間のクリスタルを全部取れるか」を調べる。 */
window.__build = (line, stage) => {
  const r = makeRun({ goal: true, seed: stage === 1 ? "cave" : `${line}_${stage}`, plat: PLAT_STAGES.indexOf(stage) >= 0,
                      foe: line === "beast" && stage >= 3, fork: line.indexOf("human") === 0 && stage >= 3,
                      mag: (line === "slime" || line === "slime_hard") && stage >= 3 });
  generate(r, r.goalX + 2000); fixGems(r, GEM_TARGET[stage]); return r;
};
window.__spots = run => {
  const iv = [];
  for(const o of run.obs) iv.push([o.x - 10, o.x + (o.w || 12) + 10]);
  for(const p of run.plats) iv.push([p.x0 - 10, p.x1 + 10]);
  for(const p of run.pits) iv.push([p.x0 - 10, p.x1 + 10]);
  iv.sort((a, b) => a[0] - b[0]);
  const m = []; let cur = null;
  for(const v of iv){ if(!cur){ cur = [v[0], v[1]]; continue; } if(v[0] > cur[1]){ m.push(cur); cur = [v[0], v[1]]; } else cur[1] = Math.max(cur[1], v[1]); }
  if(cur) m.push(cur);
  const sp = [];
  for(let i = 0; i + 1 < m.length; i++){ if(m[i + 1][0] - m[i][1] > 120) sp.push((m[i][1] + m[i + 1][0]) / 2); }
  return sp;
};
window.__win = (run, startX, xe, gems, noMag) => {
  const obs = run.obs.filter(o => o.x > startX - 200 && o.x < xe + 400);
  const plats = run.plats.filter(p => p.x1 > startX - 200 && p.x0 < xe + 400);
  const pits = run.pits.filter(p => p.x1 > startX - 200 && p.x0 < xe + 400);
  const startCam = startX - PX;
  const base = makeRun({ gen: false, foe: run.foeOn, fork: run.forkOn, plat: run.platOn, mag: run.magOn && !noMag, seed: "w" });
  base.obs = obs; base.plats = plats; base.pits = pits; base.cam = startCam; base.goalX = 0;
  const mk = s => {
    const r = Object.assign(Object.create(null), base);
    r.cam = s.cam; r.P = { ...s.P }; r.ev = []; r.gotQ = []; r.inv = 0; r.atk = s.atk; r.atkCd = s.atkCd; r.mag = s.mag; r.magCd = s.magCd;
    r.gems = gems.map((g, i) => ({ x: g.x, y: g.y, got: !!(s.got >> i & 1), gid: g.gid, set: g.set }));
    r.obs = obs.map((o, i) => Object.assign({}, o, { alive: o.k === "foe" ? !(s.dead >> i & 1) : o.alive, passed: o.k === "gate" ? !!(s.pas >> i & 1) : o.passed }));
    return r;
  };
  let states = [{ cam: startCam, P: { y: -R, vy: 0, onGround: true, jumps: 0, coy: 0, fallen: false, dead: null }, atk: 0, atkCd: 0, mag: 0, magCd: 0, got: 0, dead: 0, pas: 0 }];
  let best = -1;
  for(let tick = 0; tick < 2500 && states.length; tick++){
    const next = new Map();
    for(const s of states){
      for(const act of [0, 1, 2, 3]){
        const r = mk(s);
        if(act === 1 && !tryJump(r)) continue;
        if(act === 2 && (!run.foeOn || !tryAttack(r))) continue;
        if(act === 3 && (!base.magOn || !tryMagnet(r))) continue;
        let dead = false;
        for(let k = 0; k < 4; k++){ stepRun(r, STEP); if(r.P.dead){ dead = true; break; } }
        if(dead) continue;
        let got = 0; r.gems.forEach((g, i) => { if(g.got) got |= 1 << i; });
        if(r.cam + PX > xe){ const n = r.gems.filter(g => g.got).length; if(n > best) best = n; continue; }
        let dm = 0, pm = 0; r.obs.forEach((o, i) => { if(o.k === "foe" && !o.alive) dm |= 1 << i; if(o.k === "gate" && o.passed) pm |= 1 << i; });
        const key = `${Math.round(r.P.y)}|${Math.round(r.P.vy / 15)}|${r.P.jumps}|${r.P.onGround}|${r.P.fallen}|${got}|${dm}|${pm}|${Math.round(r.atkCd * 20)}|${Math.round(r.atk * 20)}|${Math.round(r.mag * 10)}|${Math.round(r.magCd * 10)}`;
        if(!next.has(key)) next.set(key, { cam: r.cam, P: { ...r.P }, atk: r.atk, atkCd: r.atkCd, mag: r.mag, magCd: r.magCd, got, dead: dm, pas: pm });
      }
    }
    states = [...next.values()];
    if(states.length > 6000) states = states.slice(0, 6000);
  }
  return { pass: best >= 0, gems: best, want: gems.length };
};
window.__check = (line, stage, from, n) => {
  const run = __build(line, stage), sp = __spots(run), bad = [];
  let magOnly = 0; const t0 = performance.now(); let i = from;
  for(; i + 1 < sp.length && i < from + n; i++){
    const xs = sp[i], xe = sp[i + 1];
    const inWin = run.gems.filter(g => g.x > xs && g.x < xe + 30);
    const full = inWin.filter(g => run.gems.filter(q => q.gid === g.gid).every(q => q.x > xs && q.x < xe + 30));
    let res = __win(run, xs, xe, full.slice(0, 12));
    if(res.pass && res.gems < res.want) res = __win(run, sp[Math.max(0, i - 3)], xe, full.slice(0, 12));   // 助走をつけてもう一度
    if(!res.pass) bad.push(`x${Math.round(xs)} 通れない`);
    else if(res.gems < res.want) bad.push(`x${Math.round(xs)} 💎${res.gems}/${res.want}`);
    if(full.some(g => g.mag)){ const r2 = __win(run, sp[Math.max(0, i - 3)], xe, full.slice(0, 12), true); if(r2.gems < r2.want) magOnly++; }
  }
  return JSON.stringify({ stage: `${line}_${stage}`, spots: sp.length, upto: i, gems: run.gemTotal, magGems: run.gems.filter(g => g.mag).length, magOnlyWindows: magOnly, bad, ms: Math.round(performance.now() - t0) });
};
