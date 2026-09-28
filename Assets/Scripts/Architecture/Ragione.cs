using System.Collections.Generic;
using UnityEngine;

namespace Padova.Architecture
{
    /// <summary>
    /// Palazzo della Ragione, modelled in 3D on its surveyed outline.
    /// Footprint, hall/loggia/shop depths and eaves: DBT units (see CityPlan.ragione.sources).
    /// Ridge: OSM height 35 m. Bay rhythm and storey proportions (shop arcade, trachyte arches,
    /// balustraded loggia, banded hall wall, merlons, lead hull with hooded dormers) follow the 2017
    /// Descouens photograph used as a drawing reference; nothing from the photo is projected as texture.
    /// </summary>
    public sealed class RagioneBuilder
    {
        readonly MeshSink s;
        readonly FacadeBuilder fb;
        readonly RagioneFrame r;
        readonly Vector3 C, A, Nn;
        readonly float g;
        public readonly List<(Vector3 centre, Vector3 size, Quaternion rotation)> Colliders = new List<(Vector3, Vector3, Quaternion)>();
        readonly List<Vector2> pts = new List<Vector2>(32);

        public RagioneBuilder(MeshSink sink, RagioneFrame frame)
        {
            s = sink; r = frame;
            fb = new FacadeBuilder(sink);
            C = new Vector3(r.cx, 0, r.cz);
            A = new Vector3(r.ax, 0, r.az).normalized;
            Nn = new Vector3(-A.z, 0, A.x);
            g = r.ground;
        }

        Vector2 W(float sAlong, float t) { var p = C + A * sAlong + Nn * t; return new Vector2(p.x, p.z); }
        Vector3 P(float sAlong, float y, float t) => C + A * sAlong + Nn * t + Vector3.up * y;
        Quaternion Rot => Quaternion.LookRotation(Nn, Vector3.up);

        UnitStyle Style(Slot wall, bool round = true, float spacing = 3.4f) => new UnitStyle
        {
            Wall = wall, RoundColumns = round, ColumnSpacing = spacing, ArcadeArch = Arch.Round, Rng = new System.Random(1219)
        };

        public void Build()
        {
            float h0 = r.hall[0], h1 = r.hall[1], t0 = r.hall[2], t1 = r.hall[3];
            float loggiaFloor = g + 9.8f, hallEave = r.hallEave, loggiaEave = r.loggiaEave;
            Hall(h0, h1, t0, t1, loggiaFloor, hallEave, loggiaEave);
            Roof(h0, h1, t0, t1, hallEave);
            Loggia(+1, r.northLoggia, t1, loggiaFloor, loggiaEave);
            Loggia(-1, r.southLoggia, t0, loggiaFloor, loggiaEave);
            Shops(+1, r.northShops, r.northLoggia[3], r.northGap);
            Shops(-1, r.southShops, r.southLoggia[2], r.southGap);
            float tn = r.northLoggia[3], ts = r.southLoggia[2];
            Colliders.Add((P((h0 + h1) / 2, (g + hallEave) / 2, (tn + ts) / 2), new Vector3(h1 - h0, hallEave - g + 1, tn - ts), Rot));
        }

        // ------------------------------------------------------------------ hall
        void Hall(float h0, float h1, float t0, float t1, float loggiaFloor, float eave, float loggiaEave)
        {
            fb.Style = Style(Slot.Masonry);
            // Long sides: visible above the loggia floor (behind the loggia) and above the loggia roof.
            foreach (int side in new[] { +1, -1 })
            {
                var f = side > 0 ? new Frame(W(h1, t1), W(h0, t1)) : new Frame(W(h0, t0), W(h1, t0));
                var rows = new List<FacadeBuilder.Row>
                {
                    ArchRow(f.L, 7.2f, 1.7f, loggiaFloor, loggiaFloor + 2.7f),
                    ArchRow(f.L, 4.3f, 1.05f, g + 19.4f, g + 20.7f)
                };
                fb.WallWithRowsLocal(Slot.Masonry, f, loggiaFloor - 0.2f, eave, rows);
                foreach (var o in rows[0].Ops) { fb.Reveal(Slot.Masonry, f, o, 0, -0.5f, false); fb.Panel(Slot.Dark, f, o, -0.5f); fb.Surround(Slot.Stone, f, o, 0.16f, 0.04f); }
                foreach (var o in rows[1].Ops) { fb.Reveal(Slot.Masonry, f, o, 0, -0.45f, true); fb.Panel(Slot.Glass, f, o, -0.45f); fb.Surround(Slot.Stone, f, o, 0.14f, 0.04f); }
                for (float u = 7.2f; u < f.L - 3; u += 14.4f) fb.Rect(Slot.Stone, f, u - 0.2f, loggiaEave, u + 0.2f, eave - 0.5f, 0.05f);
                Crown(f, eave);
            }
            // Short (east/west) ends: full height, a ground passage arch and two rows of windows.
            foreach (int side in new[] { +1, -1 })
            {
                var f = side > 0 ? new Frame(W(h1, t0), W(h1, t1)) : new Frame(W(h0, t1), W(h0, t0));
                var ground = new FacadeBuilder.Row { Yb = g, Ops = new List<Opening>() };
                float w = 4.4f, c = f.L / 2;
                ground.Ops.Add(new Opening { U0 = c - w / 2, U1 = c + w / 2, Yb = g, Ys = g + 4.4f, Yt = g + 4.4f + w / 2, Arch = Arch.Round });
                ground.Yt = g + 4.4f + w / 2;
                var mid = ArchRow(f.L, f.L / 3, 1.6f, g + 11.5f, g + 14.6f);
                var top = ArchRow(f.L, f.L / 5, 1.05f, g + 19.4f, g + 20.7f);
                var rows = new List<FacadeBuilder.Row> { ground, mid, top };
                fb.WallWithRowsLocal(Slot.Masonry, f, g - 0.4f, eave, rows);
                foreach (var o in ground.Ops) { fb.Reveal(Slot.GreyStone, f, o, 0, -1.2f, false); fb.Panel(Slot.Dark, f, o, -1.2f); fb.Surround(Slot.Stone, f, o, 0.4f, 0.05f); }
                foreach (var o in mid.Ops) { fb.Reveal(Slot.Masonry, f, o, 0, -0.5f, true); fb.Panel(Slot.Glass, f, o, -0.5f); fb.Surround(Slot.Stone, f, o, 0.18f, 0.04f); }
                foreach (var o in top.Ops) { fb.Reveal(Slot.Masonry, f, o, 0, -0.45f, true); fb.Panel(Slot.Glass, f, o, -0.45f); fb.Surround(Slot.Stone, f, o, 0.14f, 0.04f); }
                fb.Block(Slot.GreyStone, f, -0.05f, f.L + 0.05f, g - 0.4f, g + 0.6f, 0, 0.05f, false);
                Crown(f, eave);
            }
            // Corner pinnacles.
            foreach (var (sa, ta) in new[] { (h0, t0), (h1, t0), (h1, t1), (h0, t1) })
            {
                var c = P(sa, eave + 1.1f, ta);
                s.Box(Slot.Stone, c, A * 0.55f, Vector3.up * 1.1f, Nn * 0.55f);
                Pyramid(Slot.Stone, P(sa, eave + 2.2f, ta), 0.62f, 1.5f);
            }
        }

        FacadeBuilder.Row ArchRow(float L, float spacing, float w, float yb, float ys)
        {
            int n = Mathf.Max(1, Mathf.FloorToInt(L / spacing));
            float bay = L / n;
            var row = new FacadeBuilder.Row { Yb = yb, Ops = new List<Opening>(n), Yt = ys + w / 2 };
            for (int i = 0; i < n; i++)
            {
                float c = (i + 0.5f) * bay;
                row.Ops.Add(new Opening { U0 = c - w / 2, U1 = c + w / 2, Yb = yb, Ys = ys, Yt = ys + w / 2, Arch = Arch.Round });
            }
            return row;
        }

        /// <summary>Stone cornice, merlons (the white crenellation along the eaves).</summary>
        void Crown(in Frame f, float eave)
        {
            fb.Block(Slot.Stone, f, -0.3f, f.L + 0.3f, eave - 0.75f, eave - 0.45f, 0, 0.22f);
            fb.Block(Slot.Stone, f, -0.4f, f.L + 0.4f, eave - 0.45f, eave, 0, 0.36f);
            for (float u = 0.6f; u < f.L - 0.4f; u += 1.15f)
            {
                var c = f.P(u, eave + 0.38f, 0.16f);
                s.Box(Slot.Stone, c, f.E * 0.19f, Vector3.up * 0.38f, f.N * 0.12f);
                Pyramid(Slot.Stone, f.P(u, eave + 0.76f, 0.16f), 0.19f, 0.34f, f.E, f.N * 0.63f);
            }
        }

        void Pyramid(Slot slot, Vector3 baseCentre, float half, float height) => Pyramid(slot, baseCentre, half, height, A, Nn);

        void Pyramid(Slot slot, Vector3 baseCentre, float half, float height, Vector3 ax, Vector3 az)
        {
            var apex = baseCentre + Vector3.up * height;
            var e1 = ax.normalized * half; var e2 = az.normalized * half * az.magnitude;
            var c = new[] { baseCentre - e1 - e2, baseCentre + e1 - e2, baseCentre + e1 + e2, baseCentre - e1 + e2 };
            for (int k = 0; k < 4; k++)
            {
                var a = c[k]; var b = c[(k + 1) % 4];
                var n = Vector3.Cross(b - a, apex - a).normalized;
                if (Vector3.Dot(n, (a + b) / 2 - baseCentre) < 0) n = -n;
                s.Tri(slot, a, b, apex, n, new Vector2(0, 0), new Vector2(1, 0), new Vector2(0.5f, 1));
            }
        }

        // ------------------------------------------------------------------ hull roof
        void Roof(float h0, float h1, float t0, float t1, float eave)
        {
            float hl = (h1 - h0) / 2, hw = (t1 - t0) / 2, sc = (h0 + h1) / 2, tc = (t0 + t1) / 2;
            float rise = r.ridge - eave, end = 11f;
            const int ns = 110, nt = 44;
            var p = new Vector3[ns + 1, nt + 1];
            var uv = new Vector2[ns + 1, nt + 1];
            for (int i = 0; i <= ns; i++)
            {
                float a = Mathf.Lerp(-1, 1, i / (float)ns);
                float sl = Mathf.Sign(a) * (1 - Mathf.Pow(1 - Mathf.Abs(a), 1.6f)) * hl;
                for (int j = 0; j <= nt; j++)
                {
                    float b = Mathf.Lerp(-1, 1, j / (float)nt);
                    float tl = Mathf.Sin(b * Mathf.PI / 2) * hw;
                    float y = eave - 0.05f + rise * Hull(sl, tl, hl, hw, end);
                    p[i, j] = P(sc + sl, y, tc + tl);
                    uv[i, j] = new Vector2(sl, tl);
                }
            }
            // Arc-length V so the lead seams keep their spacing on the steep flanks.
            for (int i = 0; i <= ns; i++)
            {
                float acc = 0;
                uv[i, 0] = new Vector2(uv[i, 0].x, 0);
                for (int j = 1; j <= nt; j++) { acc += (p[i, j] - p[i, j - 1]).magnitude; uv[i, j] = new Vector2(uv[i, j].x, acc); }
            }
            s.Grid(Slot.Lead, p, uv, true);
            // Seven hooded dormers per flank, as in the photograph.
            foreach (int side in new[] { +1, -1 })
                for (int k = 0; k < 7; k++)
                {
                    float sl = Mathf.Lerp(-hl * 0.74f, hl * 0.74f, k / 6f);
                    float tl = side * hw * 0.6f;
                    float y = eave - 0.05f + rise * Hull(sl, tl, hl, hw, end);
                    Dormer(sc + sl, tc + tl, y, side);
                }
        }

        static float Hull(float sl, float tl, float hl, float hw, float end)
        {
            float nt = Mathf.Abs(tl) / hw;
            float ns = Mathf.Max(0, Mathf.Abs(sl) - (hl - end)) / end;
            float m = Mathf.Pow(Mathf.Pow(nt, 6) + Mathf.Pow(ns, 6), 1f / 6);
            m = Mathf.Clamp01(m);
            return Mathf.Pow(1 - Mathf.Pow(m, 2.3f), 0.6f);
        }

        void Dormer(float sa, float ta, float y, int side)
        {
            var out_ = Nn * side;
            var front = P(sa, y, ta) + out_ * 0.1f;
            float w = 0.8f, h = 1.2f, depth = 2.4f;
            // Cheeks and window.
            var f = new Frame(new Vector2((front - A * w).x, (front - A * w).z), new Vector2((front + A * w).x, (front + A * w).z));
            if (Vector3.Dot(f.N, out_) < 0) f = new Frame(new Vector2((front + A * w).x, (front + A * w).z), new Vector2((front - A * w).x, (front - A * w).z));
            fb.Rect(Slot.Lead, f, 0, y - 0.6f, 2 * w, y + h, 0);
            var o = new Opening { U0 = w - 0.42f, U1 = w + 0.42f, Yb = y - 0.1f, Ys = y + h - 0.45f, Yt = y + h - 0.03f, Arch = Arch.Round };
            fb.Panel(Slot.Dark, f, o, 0.01f);
            fb.Surround(Slot.Stone, f, o, 0.08f, 0.03f);
            s.Box(Slot.Lead, front - out_ * (depth / 2) + Vector3.up * (-0.6f + (h + 0.6f) / 2) + A * w, out_ * (depth / 2), Vector3.up * ((h + 0.6f) / 2), A * 0.04f);
            s.Box(Slot.Lead, front - out_ * (depth / 2) + Vector3.up * (-0.6f + (h + 0.6f) / 2) - A * w, out_ * (depth / 2), Vector3.up * ((h + 0.6f) / 2), A * 0.04f);
            // Semicircular hood.
            const int n = 10;
            var p = new Vector3[n + 1, 2];
            var uv = new Vector2[n + 1, 2];
            for (int k = 0; k <= n; k++)
            {
                float a = Mathf.PI * k / n;
                var rim = A * (Mathf.Cos(a) * (w + 0.08f)) + Vector3.up * (Mathf.Sin(a) * (w + 0.08f));
                p[k, 0] = front + out_ * 0.15f + Vector3.up * (h - w) + rim;
                p[k, 1] = front - out_ * depth + Vector3.up * (h - w) + rim;
                uv[k, 0] = new Vector2(a * w, 0); uv[k, 1] = new Vector2(a * w, depth);
            }
            s.Grid(Slot.Lead, p, uv, side > 0);
        }

        // ------------------------------------------------------------------ loggias
        void Loggia(int side, float[] ext, float hallT, float floorY, float eave)
        {
            float ls0 = ext[0], ls1 = ext[1];
            float outT = side > 0 ? ext[3] : ext[2];
            var f = side > 0 ? new Frame(W(ls1, outT), W(ls0, outT)) : new Frame(W(ls0, outT), W(ls1, outT));
            float depth = Mathf.Abs(outT - hallT);
            float L = f.L;
            // Trachyte base with the great ground-floor arches and oculi.
            fb.Style = Style(Slot.GreyStone);
            int nBig = Mathf.Max(1, Mathf.RoundToInt(L / 5.6f));
            float bigBay = L / nBig, span = bigBay - 1.35f;
            float spring = g + 5.0f, apex = spring + span / 2;
            var row = new FacadeBuilder.Row { Yb = g, Yt = apex, Ops = new List<Opening>(nBig) };
            for (int i = 0; i < nBig; i++)
            {
                float c = (i + 0.5f) * bigBay;
                row.Ops.Add(new Opening { U0 = c - span / 2, U1 = c + span / 2, Yb = g, Ys = spring, Yt = apex, Arch = Arch.Round });
            }
            fb.WallWithRowsLocal(Slot.GreyStone, f, g - 0.4f, floorY, new List<FacadeBuilder.Row> { row });
            foreach (var o in row.Ops)
            {
                fb.Reveal(Slot.GreyStone, f, o, 0, -0.9f, false);
                fb.Panel(Slot.ShopGlass, f, o, -0.9f, false);
                var arch = o; arch.Yb = o.Ys;
                fb.Panel(Slot.Dark, f, arch, -0.88f, true, o.Ys);
                fb.Rect(Slot.Iron, f, o.U0, o.Ys - 0.12f, o.U1, o.Ys, -0.86f);
                fb.Surround(Slot.Stone, f, o, 0.22f, 0.03f);
            }
            for (int i = 1; i < nBig; i++) Oculus(f, i * bigBay, apex + (floorY - apex) * 0.45f, 0.42f);
            // Floor, balustrade, columns, arches.
            float colTop = g + 13.4f;
            s.Quad(Slot.Stone, f.P(0, floorY, 0), f.P(L, floorY, 0), f.P(L, floorY, -depth), f.P(0, floorY, -depth), Vector3.up,
                new Vector2(0, 0), new Vector2(L, 0), new Vector2(L, depth), new Vector2(0, depth));
            fb.Block(Slot.Stone, f, 0, L, floorY - 0.25f, floorY + 0.12f, -0.1f, 0.12f);
            s.Quad(Slot.Balustrade, f.P(0, floorY + 0.12f, -0.2f), f.P(L, floorY + 0.12f, -0.2f), f.P(L, floorY + 1.02f, -0.2f), f.P(0, floorY + 1.02f, -0.2f), f.N,
                new Vector2(0, 0), new Vector2(L / 1.2f, 0), new Vector2(L / 1.2f, 1), new Vector2(0, 1));
            fb.Block(Slot.Stone, f, 0, L, floorY + 1.02f, floorY + 1.14f, -0.33f, -0.07f);
            fb.Style = Style(Slot.Plaster1, true, 3.6f);
            // Upper loggia: spandrels up to the frieze, then cornice and lean-to roof.
            float frieze = g + 15.7f;
            int n = Mathf.Max(1, Mathf.RoundToInt(L / 3.6f));
            float bay = L / n, span2 = bay - 0.46f;
            float spring2 = colTop;
            var arches = new FacadeBuilder.Row { Yb = spring2, Yt = spring2 + span2 / 2, Ops = new List<Opening>(n) };
            for (int i = 0; i < n; i++)
            {
                float c = (i + 0.5f) * bay;
                arches.Ops.Add(new Opening { U0 = c - span2 / 2, U1 = c + span2 / 2, Yb = spring2, Ys = spring2, Yt = spring2 + span2 / 2, Arch = Arch.Round });
            }
            float frontTop = Mathf.Max(frieze, arches.Yt + 0.2f);
            fb.WallWithRowsBand(f, spring2, frontTop, arches, 0, false);
            fb.WallWithRowsBand(f, spring2, frontTop, arches, -0.6f, true);
            foreach (var o in arches.Ops)
            {
                fb.ArchSoffit(f, o, 0, -0.6f);
                fb.Surround(Slot.Stone, f, o, 0.16f, 0.03f);
            }
            for (int i = 0; i <= n; i++)
            {
                float uc = Mathf.Clamp(i * bay, 0.25f, L - 0.25f);
                var foot = f.P(uc, floorY, -0.3f);
                s.Box(Slot.Stone, foot + Vector3.up * 0.2f, f.E * 0.26f, Vector3.up * 0.2f, f.N * 0.26f);
                s.Cylinder(Slot.Stone, foot + Vector3.up * 0.4f, 0.17f, spring2 - floorY - 0.72f, 12, 0.9f);
                s.Box(Slot.Stone, f.P(uc, spring2 - 0.16f, -0.3f), f.E * 0.3f, Vector3.up * 0.16f, f.N * 0.3f, true);
            }
            // Frieze of small hanging arches (archetti pensili) in stone above a cream band.
            fb.Rect(Slot.Plaster1, f, 0, frontTop, L, eave - 0.55f, 0);
            for (float u = 0.4f; u < L - 0.4f; u += 0.8f)
            {
                var o = new Opening { U0 = u - 0.28f, U1 = u + 0.28f, Yb = eave - 1.35f, Ys = eave - 1.1f, Yt = eave - 0.82f, Arch = Arch.Round };
                fb.Surround(Slot.Stone, f, o, 0.07f, 0.03f);
            }
            fb.Block(Slot.Stone, f, -0.2f, L + 0.2f, eave - 0.55f, eave - 0.3f, 0, 0.25f);
            fb.Block(Slot.Stone, f, -0.3f, L + 0.3f, eave - 0.3f, eave, 0, 0.42f);
            // Ceiling and roof.
            s.Quad(Slot.Wood, f.P(0, frontTop - 0.1f, -0.6f), f.P(L, frontTop - 0.1f, -0.6f), f.P(L, frontTop - 0.1f, -depth), f.P(0, frontTop - 0.1f, -depth), Vector3.down,
                new Vector2(0, 0), new Vector2(L, 0), new Vector2(L, depth), new Vector2(0, depth));
            var roofN = (f.N * 0.2f + Vector3.up).normalized;
            s.Quad(Slot.Lead, f.P(-0.3f, eave, 0.42f), f.P(L + 0.3f, eave, 0.42f), f.P(L + 0.3f, eave + 1.3f, -depth), f.P(-0.3f, eave + 1.3f, -depth), roofN,
                new Vector2(0, 0), new Vector2(L, 0), new Vector2(L, depth), new Vector2(0, depth));
            // Loggia ends.
            foreach (int end in new[] { 0, 1 })
            {
                float se = end == 0 ? ls0 : ls1;
                var fe = end == 0
                    ? (side > 0 ? new Frame(W(se, outT), W(se, hallT)) : new Frame(W(se, hallT), W(se, outT)))
                    : (side > 0 ? new Frame(W(se, hallT), W(se, outT)) : new Frame(W(se, outT), W(se, hallT)));
                var er = ArchRow(fe.L, fe.L, Mathf.Min(2.2f, fe.L - 1.4f), floorY, floorY + 2.8f);
                fb.WallWithRowsLocal(Slot.Masonry, fe, g - 0.4f, eave + 1.3f, new List<FacadeBuilder.Row> { er });
                foreach (var o in er.Ops) { fb.Reveal(Slot.Masonry, fe, o, 0, -0.5f, true); fb.Panel(Slot.Dark, fe, o, -0.5f); }
            }
        }

        void Oculus(in Frame f, float u, float y, float radius)
        {
            const int n = 16;
            for (int k = 0; k < n; k++)
            {
                float a0 = k * Mathf.PI * 2 / n, a1 = (k + 1) * Mathf.PI * 2 / n;
                var p0 = new Vector2(u + Mathf.Cos(a0) * radius, y + Mathf.Sin(a0) * radius);
                var p1 = new Vector2(u + Mathf.Cos(a1) * radius, y + Mathf.Sin(a1) * radius);
                var q0 = new Vector2(u + Mathf.Cos(a0) * (radius + 0.14f), y + Mathf.Sin(a0) * (radius + 0.14f));
                var q1 = new Vector2(u + Mathf.Cos(a1) * (radius + 0.14f), y + Mathf.Sin(a1) * (radius + 0.14f));
                s.Tri(Slot.Dark, f.P(u, y, 0.005f), f.P(p0.x, p0.y, 0.005f), f.P(p1.x, p1.y, 0.005f), f.N, Vector2.zero, Vector2.zero, Vector2.zero);
                s.Quad(Slot.Stone, f.P(p0.x, p0.y, 0.03f), f.P(p1.x, p1.y, 0.03f), f.P(q1.x, q1.y, 0.03f), f.P(q0.x, q0.y, 0.03f), f.N, p0, p1, q1, q0);
            }
        }

        // ------------------------------------------------------------------ shop arcades
        void Shops(int side, float[] ext, float backT, float gap)
        {
            float ss0 = ext[0], ss1 = ext[1];
            float frontT = side > 0 ? ext[3] : ext[2];
            float depth = Mathf.Abs(frontT - backT);
            var f = side > 0 ? new Frame(W(ss1, frontT), W(ss0, frontT)) : new Frame(W(ss0, frontT), W(ss1, frontT));
            float L = f.L;
            float eave = r.shopEave, under = g + 4.9f;
            float gapU = side > 0 ? ss1 - gap : gap - ss0;
            float pw = 5.4f, pu0 = gapU - pw / 2, pu1 = gapU + pw / 2;
            fb.Style = Style(Slot.Plaster1, true, 3.15f);
            foreach (var (a, b) in new[] { (0f, pu0), (pu1, L) })
            {
                if (b - a < 2) continue;
                var part = new Frame(new Vector2(f.P(a, 0, 0).x, f.P(a, 0, 0).z), new Vector2(f.P(b, 0, 0).x, f.P(b, 0, 0).z));
                fb.Arcade(part, g, under, false);
                foreach (var col in fb.Columns) Colliders.Add((col.center, col.size, Quaternion.LookRotation(f.N)));
                fb.Columns.Clear();
                fb.Rect(Slot.Plaster1, part, 0, under, part.L, eave - 0.35f, 0);
                fb.Block(Slot.Stone, part, -0.1f, part.L + 0.1f, eave - 0.35f, eave, 0, 0.28f);
                // Ceiling, stone floor and lead lean-to roof.
                s.Quad(Slot.Ceiling, part.P(0, under, -0.55f), part.P(part.L, under, -0.55f), part.P(part.L, under, -depth), part.P(0, under, -depth), Vector3.down,
                    new Vector2(0, 0), new Vector2(part.L, 0), new Vector2(part.L, depth), new Vector2(0, depth));
                s.Quad(Slot.PorticoFloor, part.P(0, g + 0.14f, 0), part.P(part.L, g + 0.14f, 0), part.P(part.L, g + 0.14f, -depth), part.P(0, g + 0.14f, -depth), Vector3.up,
                    new Vector2(0, 0), new Vector2(part.L, 0), new Vector2(part.L, depth), new Vector2(0, depth));
                fb.Rect(Slot.Stone, part, 0, g - 0.2f, part.L, g + 0.14f, 0.01f);
                var roofN = (part.N * 0.3f + Vector3.up).normalized;
                s.Quad(Slot.Lead, part.P(-0.1f, eave, 0.3f), part.P(part.L + 0.1f, eave, 0.3f), part.P(part.L + 0.1f, eave + 0.9f, -depth), part.P(-0.1f, eave + 0.9f, -depth), roofN,
                    new Vector2(0, 0), new Vector2(part.L, 0), new Vector2(part.L, depth), new Vector2(0, depth));
            }
            Pavilion(f, pu0, pu1, depth, eave);
            // Open arched ends.
            foreach (int end in new[] { 0, 1 })
            {
                float se = end == 0 ? ss0 : ss1;
                Frame fe;
                if (end == 0) fe = side > 0 ? new Frame(W(se, frontT), W(se, backT)) : new Frame(W(se, backT), W(se, frontT));
                else fe = side > 0 ? new Frame(W(se, backT), W(se, frontT)) : new Frame(W(se, frontT), W(se, backT));
                fb.Arcade(fe, g, under, false);
                foreach (var col in fb.Columns) Colliders.Add((col.center, col.size, Quaternion.LookRotation(f.N)));
                fb.Columns.Clear();
                fb.Rect(Slot.Plaster1, fe, 0, under, fe.L, eave + 0.4f, 0);
            }
        }

        void Pavilion(in Frame f, float u0, float u1, float depth, float eave)
        {
            // Central gabled entrance pavilion of the shop arcade.
            float top = g + 9.4f, apex = top + 1.6f, proud = 0.35f;
            float w = u1 - u0;
            var pf = new Frame(new Vector2(f.P(u0, 0, proud).x, f.P(u0, 0, proud).z), new Vector2(f.P(u1, 0, proud).x, f.P(u1, 0, proud).z));
            var door = new Opening { U0 = w / 2 - 1.6f, U1 = w / 2 + 1.6f, Yb = g, Ys = g + 4.3f, Yt = g + 5.9f, Arch = Arch.Round };
            var row = new FacadeBuilder.Row { Yb = g, Yt = door.Yt, Ops = new List<Opening> { door } };
            fb.WallWithRowsLocal(Slot.Plaster1, pf, g - 0.3f, top, new List<FacadeBuilder.Row> { row });
            fb.Reveal(Slot.Plaster1, pf, door, 0, -(depth + proud), false);
            fb.Panel(Slot.Dark, pf, door, -(depth + proud) + 0.02f);
            fb.Surround(Slot.Stone, pf, door, 0.3f, 0.05f);
            var tondo = new Opening { U0 = w / 2 - 0.5f, U1 = w / 2 + 0.5f, Yb = g + 7.2f, Ys = g + 7.9f, Yt = g + 8.4f, Arch = Arch.Round };
            fb.Surround(Slot.Stone, pf, tondo, 0.12f, 0.04f);
            fb.Block(Slot.Stone, pf, -0.15f, w + 0.15f, top - 0.3f, top, 0, 0.3f);
            // Pediment.
            s.Tri(Slot.Plaster1, pf.P(0, top, 0), pf.P(w, top, 0), pf.P(w / 2, apex, 0), pf.N, new Vector2(0, top), new Vector2(w, top), new Vector2(w / 2, apex));
            var ridgeBack = pf.P(w / 2, apex, -(depth + proud));
            foreach (int k in new[] { 0, 1 })
            {
                float ue = k == 0 ? 0 : w;
                var a = pf.P(ue, top, 0.1f); var b = pf.P(w / 2, apex + 0.05f, 0.1f);
                var c = pf.P(w / 2, apex + 0.05f, -(depth + proud)); var d = pf.P(ue, top, -(depth + proud));
                var n = Vector3.Cross(b - a, d - a).normalized; if (n.y < 0) n = -n;
                s.Quad(Slot.Lead, a, b, c, d, n, new Vector2(0, 0), new Vector2(1, 0), new Vector2(1, 1), new Vector2(0, 1));
            }
            // Side cheeks.
            foreach (int k in new[] { 0, 1 })
            {
                float ue = k == 0 ? 0 : w;
                var n = k == 0 ? -pf.E : pf.E;
                s.Quad(Slot.Plaster1, pf.P(ue, g - 0.3f, 0), pf.P(ue, g - 0.3f, -(depth + proud)), pf.P(ue, top, -(depth + proud)), pf.P(ue, top, 0), n,
                    new Vector2(0, 0), new Vector2(depth, 0), new Vector2(depth, top), new Vector2(0, top));
            }
            Colliders.Add((pf.P(0.2f, (g + top) / 2, -(depth + proud) / 2), new Vector3(0.4f, top - g, depth + proud), Quaternion.LookRotation(pf.N)));
            Colliders.Add((pf.P(w - 0.2f, (g + top) / 2, -(depth + proud) / 2), new Vector3(0.4f, top - g, depth + proud), Quaternion.LookRotation(pf.N)));
        }
    }
}
