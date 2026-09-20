#!/usr/bin/env python3
"""Labradorite Drift — neon asteroids arcade for ElbowOS."""
import argparse, math, os, random, subprocess, sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "LABRADORITE DRIFT"
HANDLE = "x.com/ElbowOS"
PAL = {
    "bg0": (4, 6, 22),
    "bg1": (10, 18, 48),
    "teal": (48, 230, 210),
    "ice": (210, 255, 250),
    "gold": (255, 206, 64),
    "amber": (255, 150, 40),
    "mag": (255, 70, 170),
    "violet": (140, 90, 255),
    "rock": (90, 130, 210),
    "dim": (90, 110, 160),
}
PLAY = pygame.Rect(40, 180, W - 80, H - 280)


def ang(a):
    return math.cos(a), math.sin(a)


class Ship:
    def __init__(self):
        self.x, self.y = W * 0.5, H * 0.55
        self.a = -math.pi / 2
        self.vx = self.vy = 0.0
        self.cool = 0
        self.alive = True

    def nose(self, r=28):
        c, s = ang(self.a)
        return self.x + c * r, self.y + s * r


class Rock:
    def __init__(self, x, y, r, vx, vy, kind=0):
        self.x, self.y, self.r = x, y, r
        self.vx, self.vy = vx, vy
        self.spin = random.uniform(-0.06, 0.06)
        self.phi = random.random() * 6.28
        self.kind = kind
        self.verts = [
            (math.cos(i / 7 * 6.28) * random.uniform(0.72, 1.08),
             math.sin(i / 7 * 6.28) * random.uniform(0.72, 1.08))
            for i in range(7)
        ]


class Game:
    def __init__(self, auto=False):
        self.auto = auto
        self.t = self.score = self.hits = self.lives = 0
        self.flash = 0
        self.ship = Ship()
        self.rocks, self.shots, self.sparks, self.gems = [], [], [], []
        self.stars = [(random.randrange(W), random.randrange(H), random.randint(1, 3),
                       random.choice((PAL["teal"], PAL["violet"], PAL["ice"], PAL["gold"])))
                      for _ in range(70)]
        self.lives = 3
        for _ in range(7):
            self._spawn_rock(large=True)

    def _spawn_rock(self, large=True, x=None, y=None):
        r = random.randint(54, 86) if large else random.randint(22, 38)
        if x is None:
            side = random.choice(("l", "r", "t", "b"))
            if side == "l":
                x, y = PLAY.left - 10, random.uniform(PLAY.top, PLAY.bottom)
            elif side == "r":
                x, y = PLAY.right + 10, random.uniform(PLAY.top, PLAY.bottom)
            elif side == "t":
                x, y = random.uniform(PLAY.left, PLAY.right), PLAY.top - 10
            else:
                x, y = random.uniform(PLAY.left, PLAY.right), PLAY.bottom + 10
        spd = random.uniform(1.6, 3.4) if large else random.uniform(2.2, 4.6)
        a = random.random() * 6.28
        self.rocks.append(Rock(x, y, r, math.cos(a) * spd, math.sin(a) * spd, 0 if large else 1))

    def _burst(self, x, y, col, n=16):
        for _ in range(n):
            a = random.random() * 6.28
            s = random.uniform(1.5, 8.0)
            self.sparks.append([x, y, math.cos(a) * s, math.sin(a) * s, 18, col])

    def _shoot(self):
        s = self.ship
        if s.cool > 0 or not s.alive:
            return
        c, si = ang(s.a)
        nx, ny = s.nose(26)
        self.shots.append([nx, ny, c * 18, si * 18, 34])
        s.cool = 7

    def autoplay(self):
        s = self.ship
        if not self.rocks:
            return
        tgt = min(self.rocks, key=lambda r: (r.x - s.x) ** 2 + (r.y - s.y) ** 2)
        want = math.atan2(tgt.y - s.y, tgt.x - s.x)
        diff = (want - s.a + math.pi) % (2 * math.pi) - math.pi
        s.a += max(-0.16, min(0.16, diff))
        dist = math.hypot(tgt.x - s.x, tgt.y - s.y)
        if abs(diff) < 0.22:
            self._shoot()
        if dist < 160 or (s.x - PLAY.centerx) ** 2 + (s.y - PLAY.centery) ** 2 > 280 ** 2:
            c, si = ang(s.a + (math.pi if dist < 160 else 0))
            s.vx += c * 0.35
            s.vy += si * 0.35
        if self.t % 40 == 0:
            s.vx += math.cos(s.a) * 0.28
            s.vy += math.sin(s.a) * 0.28

    def _wrap(self, o):
        if o.x < PLAY.left - 40:
            o.x = PLAY.right + 20
        if o.x > PLAY.right + 40:
            o.x = PLAY.left - 20
        if o.y < PLAY.top - 40:
            o.y = PLAY.bottom + 20
        if o.y > PLAY.bottom + 40:
            o.y = PLAY.top - 20

    def _reset_ship(self):
        self.ship = Ship()
        self.flash = 10

    def step(self, keys=None):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        s = self.ship
        s.cool = max(0, s.cool - 1)
        if self.auto:
            self.autoplay()
        elif keys is not None and s.alive:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                s.a -= 0.14
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                s.a += 0.14
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                c, si = ang(s.a)
                s.vx += c * 0.42
                s.vy += si * 0.42
            if keys[pygame.K_SPACE]:
                self._shoot()
        if s.alive:
            s.vx *= 0.99
            s.vy *= 0.99
            s.x += s.vx
            s.y += s.vy
            self._wrap(s)
        keep_s = []
        for sh in self.shots:
            sh[0] += sh[2]
            sh[1] += sh[3]
            sh[4] -= 1
            if sh[4] > 0 and PLAY.inflate(30, 30).collidepoint(sh[0], sh[1]):
                keep_s.append(sh)
        self.shots = keep_s
        born = []
        stay = []
        for rk in self.rocks:
            rk.x += rk.vx
            rk.y += rk.vy
            rk.phi += rk.spin
            self._wrap(rk)
            hit = None
            for sh in self.shots:
                if (sh[0] - rk.x) ** 2 + (sh[1] - rk.y) ** 2 < (rk.r + 6) ** 2:
                    hit = sh
                    break
            if hit:
                self.shots.remove(hit)
                self.hits += 1
                self.score += 40 if rk.kind == 0 else 20
                self._burst(rk.x, rk.y, PAL["gold"] if rk.kind == 0 else PAL["teal"], 20)
                if rk.kind == 0:
                    for _ in range(2):
                        a = random.random() * 6.28
                        spd = random.uniform(2.0, 4.2)
                        born.append(Rock(rk.x, rk.y, random.randint(22, 36),
                                         math.cos(a) * spd, math.sin(a) * spd, 1))
                    if random.random() < 0.45:
                        self.gems.append([rk.x, rk.y, random.uniform(-1, 1), random.uniform(-1, 1), 90])
                continue
            if s.alive and (s.x - rk.x) ** 2 + (s.y - rk.y) ** 2 < (rk.r + 16) ** 2:
                s.alive = False
                self.lives = max(0, self.lives - 1)
                self._burst(s.x, s.y, PAL["mag"], 28)
                self.flash = 9
            stay.append(rk)
        self.rocks = stay + born
        if len(self.rocks) < 5 and self.t % 20 == 0:
            self._spawn_rock(large=True)
        if not s.alive and self.t % 28 == 0:
            self._reset_ship()
        gkeep = []
        for g in self.gems:
            g[0] += g[2]
            g[1] += g[3]
            g[4] -= 1
            if s.alive and (s.x - g[0]) ** 2 + (s.y - g[1]) ** 2 < 32 ** 2:
                self.score += 75
                self._burst(g[0], g[1], PAL["violet"], 12)
                continue
            if g[4] > 0:
                gkeep.append(g)
        self.gems = gkeep
        sk = []
        for sp in self.sparks:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[4] -= 1
            if sp[4] > 0:
                sk.append(sp)
        self.sparks = sk

    def _poly(self, surf, rock):
        pts = []
        ca, sa = math.cos(rock.phi), math.sin(rock.phi)
        for vx, vy in rock.verts:
            x = rock.x + (vx * ca - vy * sa) * rock.r
            y = rock.y + (vx * sa + vy * ca) * rock.r
            pts.append((x, y))
        col = PAL["rock"] if rock.kind == 0 else PAL["violet"]
        pygame.draw.polygon(surf, col, pts, 0)
        pygame.draw.polygon(surf, PAL["ice"] if rock.kind else PAL["teal"], pts, 3)

    def draw(self, surf, font, small, mid):
        for y in range(0, H, 8):
            k = y / H
            pygame.draw.rect(surf, (int(4 + 8 * k), int(6 + 16 * k), int(22 + 30 * k)), (0, y, W, 8))
        for i, (x, y, r, col) in enumerate(self.stars):
            yy = (y + int(self.t * 0.4 + i * 0.3)) % H
            pygame.draw.circle(surf, col, (x, yy), r)
        pygame.draw.rect(surf, PAL["bg1"], PLAY, 0, 18)
        pygame.draw.rect(surf, PAL["teal"], PLAY, 3, 18)
        for rk in self.rocks:
            self._poly(surf, rk)
        for g in self.gems:
            pygame.draw.circle(surf, PAL["mag"], (int(g[0]), int(g[1])), 10)
            pygame.draw.circle(surf, PAL["ice"], (int(g[0]), int(g[1])), 4)
        for sh in self.shots:
            pygame.draw.circle(surf, PAL["gold"], (int(sh[0]), int(sh[1])), 5)
            pygame.draw.circle(surf, PAL["ice"], (int(sh[0]), int(sh[1])), 2)
        s = self.ship
        if s.alive:
            c, si = ang(s.a)
            p1 = (s.x + c * 28, s.y + si * 28)
            p2 = (s.x + math.cos(s.a + 2.5) * 20, s.y + math.sin(s.a + 2.5) * 20)
            p3 = (s.x - c * 10, s.y - si * 10)
            p4 = (s.x + math.cos(s.a - 2.5) * 20, s.y + math.sin(s.a - 2.5) * 20)
            pygame.draw.polygon(surf, PAL["teal"], [p1, p2, p3, p4])
            pygame.draw.polygon(surf, PAL["gold"], [p1, p2, p3, p4], 3)
            pygame.draw.circle(surf, PAL["ice"], (int(s.x), int(s.y)), 5)
            if self.t % 4 < 2 and (abs(s.vx) + abs(s.vy)) > 0.4:
                pygame.draw.circle(surf, PAL["amber"], (int(s.x - c * 18), int(s.y - si * 18)), 7)
        for sp in self.sparks:
            pygame.draw.circle(surf, sp[5], (int(sp[0]), int(sp[1])), max(2, sp[4] // 4))
        if self.flash:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 70, 170, 10 * self.flash))
            surf.blit(veil, (0, 0))
        banner = pygame.Surface((W, 150), pygame.SRCALPHA)
        banner.fill((4, 6, 22, 230))
        surf.blit(banner, (0, 0))
        surf.blit(font.render(TITLE, True, PAL["teal"]), (40, 18))
        surf.blit(small.render(HANDLE, True, PAL["gold"]), (40, 88))
        sc = font.render(f"{self.score:05d}", True, PAL["gold"])
        surf.blit(sc, (W - 48 - sc.get_width(), 18))
        meta = small.render(f"SPLITS {self.hits}   HULL {self.lives}", True, PAL["ice"])
        surf.blit(meta, (W - 48 - meta.get_width(), 90))
        hint = "A/D aim   W thrust   SPACE fire" if not self.auto else "AUTO DRIFT"
        foot = small.render(hint, True, PAL["dim"])
        surf.blit(foot, foot.get_rect(center=(W * 0.5, H - 48)))


def record(path):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.font.init()
    surf = pygame.Surface((W, H))
    font = pygame.font.SysFont("DejaVu Sans", 54, bold=True)
    mid = pygame.font.SysFont("DejaVu Sans", 44, bold=True)
    small = pygame.font.SysFont("DejaVu Sans", 32, bold=True)
    g = Game(auto=True)
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    frames = FPS * 15
    try:
        for _ in range(frames):
            g.step()
            g.draw(surf, font, small, mid)
            proc.stdin.write(pygame.image.tostring(surf, "RGB"))
        proc.stdin.close()
        err = proc.stderr.read()
        rc = proc.wait(timeout=60)
    except Exception:
        proc.kill()
        raise
    if rc != 0:
        raise RuntimeError(err.decode("utf-8", "ignore")[-800:])
    print("wrote", path)


def play():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("DejaVu Sans", 54, bold=True)
    mid = pygame.font.SysFont("DejaVu Sans", 44, bold=True)
    small = pygame.font.SysFont("DejaVu Sans", 32, bold=True)
    g = Game(auto=False)
    run = True
    while run:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                run = False
        g.step(pygame.key.get_pressed())
        g.draw(screen, font, small, mid)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--record", action="store_true")
    p.add_argument("--play", action="store_true")
    p.add_argument("--out", default="/home/workdir/artifacts/labradorite_drift_ElbowOS.mp4")
    a = p.parse_args()
    if a.record or not a.play:
        record(a.out)
        if a.play:
            play()
    else:
        play()


if __name__ == "__main__":
    main()
