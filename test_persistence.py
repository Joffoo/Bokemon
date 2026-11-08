import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

async def run_persistence_tests():
    html_path = os.path.abspath("e:/Projects/Bokeman/index.html")
    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    print(f"Testing Message Persistence on: {file_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        # 1. First Load
        await page.goto(file_url, wait_until="networkidle")
        print("[1] Initial page loaded.")
        assert len(console_errors) == 0, f"Console errors on load: {console_errors}"

        # 2. Check initial state
        initial_count = await page.evaluate("() => window.oogiriStudio.messages.value.length")
        assert initial_count == 1, f"Expected 1 initial message, got {initial_count}"
        print("[2] Initial welcome message confirmed.")

        # 3. Run Pipeline Demo to generate conversation
        await page.click('button:has-text("命题库")')
        await page.click('button:has-text("立即演示")')
        await page.wait_for_selector('text=全场总冠军金句', timeout=10000)

        champion_before = (await page.locator('h2.font-variety').first.text_content()).strip()
        count_before = await page.evaluate("() => window.oogiriStudio.messages.value.length")
        assert count_before >= 2, f"Expected at least 2 messages, got {count_before}"
        print(f"[3] Generated conversation with champion: '{champion_before}', message count: {count_before}")

        # 4. Verify localStorage has stored messages
        stored_raw = await page.evaluate("() => localStorage.getItem('oogiri_chat_messages')")
        assert stored_raw is not None, "oogiri_chat_messages not found in localStorage"
        assert champion_before in stored_raw, "Champion text not found in stored messages JSON"
        print("[4] Verified localStorage contains serialized chat messages.")

        # 5. RELOAD THE PAGE (Simulate user pressing F5 / refresh)
        print("[5] Reloading page (F5 / refresh)...")
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(500)
        assert len(console_errors) == 0, f"Console errors after reload: {console_errors}"

        # 6. Verify conversation is RESTORED after reload!
        count_after = await page.evaluate("() => window.oogiriStudio.messages.value.length")
        assert count_after == count_before, f"Expected {count_before} messages after reload, but got {count_after}!"
        
        champion_after = (await page.locator('h2.font-variety').first.text_content()).strip()
        assert champion_after == champion_before, f"Champion mismatch after reload: '{champion_after}' vs '{champion_before}'"
        print(f"[6] SUCCESS! Chat history successfully persisted across refresh: '{champion_after}' (count={count_after})")

        # 7. Check host message is also visible
        host_visible = await page.is_visible("text=史上首个 130 人组成的摇滚乐队解散，理由是什么？")
        assert host_visible, "Host question bubble not visible after reload"
        print("[7] Host question bubble verified after reload.")

        # 8. Test New Game Reset Persistence
        await page.click('button:has-text("新对局")')
        await page.wait_for_timeout(300)
        count_reset = await page.evaluate("() => window.oogiriStudio.messages.value.length")
        assert count_reset == 1, f"Expected 1 message after reset, got {count_reset}"

        # Reload after reset
        await page.reload(wait_until="networkidle")
        count_after_reset_reload = await page.evaluate("() => window.oogiriStudio.messages.value.length")
        assert count_after_reset_reload == 1, f"Expected 1 message after reload following reset, got {count_after_reset_reload}"
        print("[8] Verified '新对局' (New Game) reset correctly persists after reload.")

        print("\nALL MESSAGE PERSISTENCE VERIFICATIONS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(run_persistence_tests())
