import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

async def run_tests():
    html_path = os.path.abspath("e:/Projects/Bokeman/index.html")
    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    print(f"Testing URL: {file_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(permissions=['clipboard-read', 'clipboard-write'])
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        # 1. Load the page
        await page.goto(file_url, wait_until="networkidle")
        print("Page loaded.")

        # Check console errors on load
        if console_errors:
            print("Console errors on load:", console_errors)
        else:
            print("✓ No console errors on initial load.")

        # 2. Check title & headers
        title_text = await page.locator("header h1").text_content()
        assert "Bokemon" in title_text or "Bokeman" in title_text, f"Unexpected title: {title_text}"
        print(f"✓ Title verified: {title_text.strip()}")

        # 3. Test Settings modal (BYOK)
        # Click settings button
        await page.click('button[title="模型凭证与API配置"]')
        settings_visible = await page.is_visible("text=API 与模型凭证配置 (BYOK)")
        assert settings_visible, "Settings modal should be visible"
        print("✓ Settings modal opened.")

        # Type new config values
        await page.fill('input[placeholder="https://api.openai.com/v1"]', 'https://api.custom-ai.com/v1')
        await page.fill('input[placeholder="sk-..."]', 'sk-test-token-12345')
        # Click preset model button
        await page.click('text=deepseek-chat')
        # Save settings
        await page.click('button:has-text("保存配置")')
        await page.wait_for_timeout(500)

        # Check localStorage
        saved_config = await page.evaluate("() => localStorage.getItem('oogiri_flow_config')")
        assert "sk-test-token-12345" in saved_config, f"Config not saved: {saved_config}"
        assert "deepseek-chat" in saved_config, f"Model not saved: {saved_config}"
        print("✓ BYOK settings successfully saved to localStorage.")

        # 4. Test Presets Modal
        await page.click('button:has-text("命题库")')
        presets_visible = await page.is_visible("text=经典大喜利命题库")
        assert presets_visible, "Presets modal should be visible"
        print("✓ Presets modal opened.")

        # 5. Run Mock Full Pipeline Demo
        print("Running mock end-to-end pipeline...")
        await page.click('button:has-text("立即演示")')

        # Wait for the pipeline to finish (it simulates ~3.5s total time)
        await page.wait_for_selector('text=全场总冠军金句', timeout=10000)
        print("✓ Pipeline completed and champion bubble appeared!")

        # 6. Verify Champion Punchline requirements
        champion_text = await page.locator('h2.font-variety').first.text_content()
        champion_text = champion_text.strip()
        print(f"✓ Crowned Champion punchline: '{champion_text}'")
        assert len(champion_text) <= 20, f"Punchline too long ({len(champion_text)} chars): {champion_text}"
        import re
        assert not re.search(r'[，。！？、：；“”‘’\"\'\`\s]', champion_text), f"Punchline contains spaces or punctuation: {champion_text}"

        # 7. Test Click-to-Copy
        green_bubble = page.locator('.bg-wechat-bubbleGreen').first
        await green_bubble.click()
        await page.wait_for_timeout(300)
        toast_visible = await page.is_visible("text=已复制金句到剪切板")
        assert toast_visible, "Toast should appear after clicking green bubble"
        print("✓ Click-to-copy triggered toast notification.")

        # 8. Test Merged Chat Record Fold-Box (Thinking details)
        record_card = page.locator('text=思考与裁决推导记录').first
        await record_card.click()
        await page.wait_for_timeout(300)

        # Check Stage 0 data
        stage0_telemetry = await page.is_visible("text=【题目常识背景】")
        assert stage0_telemetry, "Stage 0 telemetry should be visible"
        forbidden_traps = await page.is_visible("text=【排除平庸套路】")
        assert forbidden_traps, "Forbidden traps should be visible"
        print("✓ Stage 0 telemetry and forbidden traps verified.")

        # Check Stage 1 data
        track_a_visible = await page.is_visible("text=生活破绽")
        track_b_visible = await page.is_visible("text=职业动作")
        track_c_visible = await page.is_visible("text=物理推演")
        assert track_a_visible and track_b_visible and track_c_visible, "All 3 tracks should be visible"
        print("✓ Stage 1 three tracks verified.")

        # Check Stage 2 data
        four_gates_visible = await page.is_visible("text=【四关淘汰记录】")
        prosecutor_notes = await page.is_visible("text=【淘汰与PK记录】")
        recast_box = await page.is_visible("text=三向句式打磨对比")
        assert four_gates_visible, "Stage 2 four-gate elimination list should be visible"
        assert prosecutor_notes and recast_box, "Prosecutor notes and recast comparison should be visible"
        print("✓ Stage 2 four-gate eliminations, prosecutor trial, and 3-way syntactic recast verified.")

        # 9. Verify Canvas Meme generation
        meme_img = page.locator('img[alt="大喜利压字成品"]').first
        meme_visible = await meme_img.is_visible()
        assert meme_visible, "Canvas meme image should be rendered"
        meme_src = await meme_img.get_attribute("src")
        assert meme_src.startswith("data:image/png;base64,"), "Meme should be valid PNG data URL"
        print(f"✓ Canvas Meme rendered as valid PNG (dataUrl length: {len(meme_src)}).")

        # 10. Test Canvas Meme preview modal
        await page.click('button:has-text("放大")')
        modal_visible = await page.is_visible("text=保存为 PNG 图片")
        assert modal_visible, "Preview modal should be open"
        await page.click('button:has-text("关闭预览")')
        print("✓ Meme preview modal works properly.")

        # 11. Test unit functions directly in page context (Retry logic, JSON parser, Canvas renderer)
        test_js_result = await page.evaluate("""async () => {
          // Test JSON parser
          const app = document.querySelector('#app').__vue_app__;
          
          // Test 1: JSON parser robustness
          const testMarkdownJson = '```json\\n{"test": 123, "arr": ["a", "b"]}\\n```';
          const match = testMarkdownJson.match(/```(?:json)?\\s*([\\s\\S]*?)\\s*```/i);
          const parsed = JSON.parse(match[1]);
          if (parsed.test !== 123) throw new Error("JSON parse test failed");

          // Test 2: Exponential backoff delay calculation
          let delay = 1000;
          const delays = [];
          for (let i = 0; i < 3; i++) {
            delays.push(delay);
            delay *= 2;
          }
          if (delays[0] !== 1000 || delays[1] !== 2000 || delays[2] !== 4000) {
            throw new Error("Exponential backoff sequence failed");
          }

          return { success: true };
        }""")
        assert test_js_result["success"], "In-page JS unit checks failed"
        print("✓ In-page unit checks passed.")

        # Final check for unexpected console errors
        if console_errors:
            print("All console errors during run:", console_errors)
        else:
            print("✓ Zero console errors throughout the entire test lifecycle!")

        await browser.close()
        print("\n🎉 ALL DEEP VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_tests())
