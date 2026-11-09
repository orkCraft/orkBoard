from tests.browser_kit import gui, WAIT_MS
from tests.test_stall_browser import StallHost

OUT = "/tmp/claude-0/-home-user-orkBoard/c68e1c18-1be6-55bb-a2ff-b93ce3e1a5aa/scratchpad/"


def test_x(gui):
    server, browser = gui
    host = StallHost()
    ctx = browser.new_context(viewport={"width": 1366, "height": 768})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".hand-card").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT + "a5.png")
    print(errs)
    print(pg.locator(".hand-end .place-box, .hand-die__box").evaluate_all("els => els.map((e) => { const b = e.getBoundingClientRect(); return [e.className, b.x, b.y, b.width, b.height]; })"))
    pg.locator("[data-book]").click()
    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT + "a5b.png")
    print(errs)
