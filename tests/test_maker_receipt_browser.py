"""Spec 160 J: a pick's receipt and the cap stop's one-press way to its plate."""
import pytest

pytest.importorskip('playwright.sync_api')
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401
from tests.test_stall_browser import MakerShelfHost, opened  # noqa: E402

pytestmark = pytest.mark.browser


def test_receipt_under_variants_and_cap_stop_opens_the_partys_plate(gui):
    pg, host, log = opened(gui, 'art', host=MakerShelfHost())
    try:
        pg.evaluate('''async () => {
          const {html} = await import('/static/js/html.js');
          const {render} = await import('preact');
          const {Tiles} = await import('/static/js/arena/picks.js');
          const {MakerStop} = await import('/static/js/arena/makerreceipt.js');
          const frame = await import('/static/js/frame/state.js');
          frame.closeInventory();
          const el = document.createElement('div'); el.id = 'receipt-test'; document.body.append(el);
          const cost = {amount:'0.12', currency:'USD', estimate:true}, cap = {amount:'1', currency:'USD'};
          render(html`<${Tiles} row=${{slug:'g', task:'k1', media:'text', variants:[{key:'A', name:'One', text:'A'}], maker:{word:'Picture maker', cost, cap}}} />
            <${MakerStop} stop=${{tool:'openai-images', party:'art', price:cost, cap, held:{amount:'0.96', currency:'USD', estimate:true}}} />`, el);
        }''')
        receipt = pg.locator('#receipt-test .pick-receipt').first
        assert receipt.inner_text() == 'Made by the Picture maker · about 0.12 USD of a 1 USD cap'
        assert pg.locator('#receipt-test .pick-tiles').evaluate('(e) => !!e.nextElementSibling?.classList.contains("pick-receipt")')
        assert pg.locator('#receipt-test .pick-receipt p').inner_text() == 'The next request costs about 0.12 USD; with about 0.96 USD already held, it would exceed the 1 USD cap.'
        pg.locator('#receipt-test button', has_text='Change the cap').click()
        plate = pg.locator('[data-stall="art"] [data-ware="openai-images"] .stall-ware__press')
        plate.wait_for(timeout=WAIT_MS)
        pg.wait_for_function('() => document.activeElement?.closest("[data-ware]")?.dataset.ware === "openai-images"', timeout=WAIT_MS)
        assert plate.get_attribute('aria-label') == 'Its makers: Picture maker'
    finally:
        pg.close()
    assert not log, '\n'.join(log)
