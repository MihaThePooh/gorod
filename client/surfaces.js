// Ground material, road geometry and wear are separate, deterministic layers.
export function createGround(ctx, images, houses = []) {
  let seed = 39017;
  const random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
  const pattern = (name, metres = 4) => {
    const p = ctx.createPattern(images[name], 'repeat');
    p.setTransform(new DOMMatrix().scale(metres / images[name].width));
    return p;
  };
  const materials = { grass: pattern('grass', 6), asphalt: pattern('asphalt', 5), dirt: pattern('dirt', 5), paving: pattern('paving', 4) };
  const road = new Path2D();
  const edge = x => .07 * Math.sin(x * 1.8) + .035 * Math.sin(x * 4.9);
  road.moveTo(-72, -18);
  for (let x = -72; x <= 72; x += .8) road.lineTo(x, -18 + edge(x));
  for (let x = 72; x >= -72; x -= .8) road.lineTo(x, -10 + edge(x + 11));
  road.closePath();
  const dirt = new Path2D();
  dirt.moveTo(-30.5, -10.1);
  for (let y = -10; y <= 72; y += .8) dirt.lineTo(-30.5 + .18 * Math.sin(y * .7) + edge(y), y);
  for (let y = 72; y >= -10; y -= .8) dirt.lineTo(-25.5 + .16 * Math.sin(y * .85) + edge(y + 5), y);
  dirt.closePath();
  const cracks = new Path2D(), repairs = new Path2D(), holes = new Path2D(), wet = new Path2D();
  const blob = (path, x, y, radius) => {
    const points = Array.from({ length: 12 }, (_, i) => {
      const angle = i / 12 * Math.PI * 2, r = radius * (.7 + random() * .45);
      return [x + Math.cos(angle) * r, y + Math.sin(angle) * r * .7];
    });
    const last = points.at(-1), first = points[0];
    path.moveTo((last[0] + first[0]) / 2, (last[1] + first[1]) / 2);
    points.forEach((p, i) => {
      const next = points[(i + 1) % points.length];
      path.quadraticCurveTo(p[0], p[1], (p[0] + next[0]) / 2, (p[1] + next[1]) / 2);
    });
    path.closePath();
  };
  for (let i = 0; i < 45; i++) {
    let x = -70 + random() * 57, y = -17.6 + random() * 7.1;
    cracks.moveTo(x, y);
    for (let j = 0; j < 5; j++) { x += random() * 1.1; y += (random() - .5) * .8; cracks.lineTo(x, y); }
    if (i % 3 === 0) { cracks.moveTo(x, y); cracks.lineTo(x - .5, y - .65); }
  }
  for (let i = 0; i < 21; i++) blob(repairs, -69 + random() * 53, -17.3 + random() * 6.4, .25 + random() * .65);
  for (let i = 0; i < 13; i++) blob(holes, -68 + random() * 49, -17 + random() * 5.9, .16 + random() * .44);
  blob(wet, -46, -14.9, .47); blob(wet, -40.2, -12.7, .31);
  const ruts = new Path2D();
  for (const x of [-29.15, -26.85]) {
    ruts.moveTo(x, -10);
    for (let y = -10; y <= 72; y += .7) ruts.lineTo(x + Math.sin(y * .4) * .09, y);
  }
  const median = new Path2D();
  median.moveTo(-28.3, -7);
  for (let y = -7; y <= 72; y += .5) median.lineTo(-28.32 + Math.sin(y * .8) * .13, y);
  for (let y = 72; y >= -7; y -= .5) median.lineTo(-27.68 + Math.sin(y * 1.1) * .12, y);
  median.closePath();
  return {
    draw(c) {
      c.fillStyle = materials.grass; c.fillRect(-72, -72, 144, 144);
      // Thin dusty shoulders soften the boundary without making tile-shaped borders.
      for (const width of [.65,.4,.22]) { c.strokeStyle = '#92866526'; c.lineWidth = width; c.stroke(road); }
      c.fillStyle = materials.asphalt; c.fill(road);
      c.save(); c.clip(road);
      c.fillStyle = '#92836d24'; c.fillRect(-72, -19, 60, 10);
      c.fillStyle = '#494842'; c.globalAlpha = .45; c.fill(repairs); c.globalAlpha = 1;
      c.strokeStyle = '#aaa18b60'; c.lineWidth = .065; c.stroke(holes);
      c.fillStyle = materials.dirt; c.fill(holes);
      c.fillStyle = '#292d2ac0'; c.fill(holes);
      c.fillStyle = '#7b848080'; c.fill(wet);
      c.strokeStyle = '#aaa08a50'; c.lineWidth = .085; c.stroke(cracks);
      c.strokeStyle = '#292d2aaf'; c.lineWidth = .029; c.stroke(cracks);
      c.restore();
      for (const width of [.8,.5,.25]) { c.strokeStyle = '#b8a57a30'; c.lineWidth = width; c.stroke(dirt); }
      c.fillStyle = materials.dirt; c.fill(dirt);
      c.save(); c.clip(dirt);
      c.strokeStyle = '#6b5e4845'; c.lineWidth = .42; c.stroke(ruts);
      c.strokeStyle = '#c2ac8460'; c.lineWidth = .16; c.stroke(ruts);
      c.strokeStyle = materials.grass; c.globalAlpha = .17; c.lineWidth = .28; c.stroke(median);
      c.globalAlpha = .65; c.fillStyle = materials.grass; c.fill(median); c.restore();
      c.fillStyle = materials.paving;
      for (const h of houses) {
        c.fillRect(h.x - 17, h.y - 10, 34, 17);
        c.strokeStyle = '#c4c0a1'; c.lineWidth = .10;
        c.strokeRect(h.x - 17, h.y - 10, 34, 17);
      }
      c.strokeStyle = '#e2e0ce'; c.lineWidth = .11;
      c.setLineDash([2.4, 3.6]); c.beginPath(); c.moveTo(-10, -14); c.lineTo(72, -14); c.stroke();
      c.setLineDash([]); c.globalAlpha = .7; c.lineWidth = .09;
      c.beginPath(); c.moveTo(-10, -17.55); c.lineTo(72, -17.55); c.moveTo(-10, -10.45); c.lineTo(72, -10.45); c.stroke(); c.globalAlpha = 1;
    },
  };
}
