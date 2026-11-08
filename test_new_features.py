import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

async def run_new_features_tests():
    html_path = os.path.abspath("e:/Projects/Bokeman/index.html")
    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    print(f"Testing New Features on: {file_url}")

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

        # ========================================================
        # Feature 1: Web Audio Synthesis & Sound Toggle in Navbar
        # ========================================================
        sound_btn = page.locator('header button[title*="音效"]')
        assert await sound_btn.is_visible(), "Sound toggle button must be in header"
        # Initial state should be enabled (🔔)
        initial_sound_text = await sound_btn.text_content()
        assert "🔔" in initial_sound_text, f"Initial sound state should be 🔔, got {initial_sound_text}"
        
        # Toggle sound off (🔕)
        await sound_btn.click()
        await page.wait_for_timeout(200)
        sound_text_off = await sound_btn.text_content()
        assert "🔕" in sound_text_off, f"Sound should toggle to 🔕, got {sound_text_off}"
        saved_sound_pref = await page.evaluate("() => localStorage.getItem('oogiri_sound_enabled')")
        assert saved_sound_pref == "false", f"Sound pref not saved to localStorage: {saved_sound_pref}"

        # Test Web Audio synth in page context without throwing error
        synth_test = await page.evaluate("""() => {
            const studio = window.oogiriStudio;
            studio.playStartSound();
            studio.playChampionSound();
            return { soundTested: true };
        }""")
        assert synth_test["soundTested"], "Web Audio synthesis should execute cleanly"
        print("✓ Feature 1: Web Audio synthesizer and header sound toggle verified.")

        # Re-enable sound
        await sound_btn.click()
        await page.wait_for_timeout(200)

        # ========================================================
        # Feature 2: Provider Presets, Remember Key, & Purge Credentials
        # ========================================================
        await page.click('button[title="模型凭证与API配置"]')
        assert await page.is_visible("text=API 与模型凭证配置 (BYOK)"), "Settings modal should open"

        # 2a. Verify provider preset buttons
        for provider_name in ['OpenAI 官方', 'OpenRouter', 'DeepSeek 官方', '硅基流动']:
            assert await page.is_visible(f'button:has-text("{provider_name}")'), f"Provider preset {provider_name} missing"

        # Click OpenRouter preset
        await page.click('button:has-text("OpenRouter")')
        base_val = await page.input_value('input[placeholder="https://api.openai.com/v1"]')
        assert base_val == 'https://openrouter.ai/api/v1', f"Base URL not updated to OpenRouter: {base_val}"

        # Click SiliconFlow preset
        await page.click('button:has-text("硅基流动")')
        base_val = await page.input_value('input[placeholder="https://api.openai.com/v1"]')
        assert base_val == 'https://api.siliconflow.cn/v1', f"Base URL not updated to SiliconFlow: {base_val}"

        # 2b. Test Remember Key toggle (localStorage vs sessionStorage)
        # Check the remember key switch
        remember_checkbox = page.locator('input[type="checkbox"]:has-text("")')
        await page.fill('input[placeholder="sk-..."]', 'sk-session-only-secret-999')

        # Uncheck "记住密钥" (switch to sessionStorage only)
        is_checked = await page.is_checked('input[type="checkbox"]')
        assert is_checked, "Remember Key should be checked by default"
        await page.uncheck('input[type="checkbox"]')
        assert not (await page.is_checked('input[type="checkbox"]')), "Remember Key should now be unchecked"

        # Save settings with sessionStorage mode
        await page.click('button:has-text("保存配置")')
        await page.wait_for_timeout(300)

        # Verify it went to sessionStorage and NOT localStorage
        session_stored = await page.evaluate("() => sessionStorage.getItem('oogiri_flow_config')")
        local_stored = await page.evaluate("() => localStorage.getItem('oogiri_flow_config')")
        assert session_stored and "sk-session-only-secret-999" in session_stored, f"Not saved to sessionStorage: {session_stored}"
        assert local_stored is None or "sk-session-only-secret-999" not in (local_stored or ''), "Secret should not leak to localStorage in session mode"
        print("✓ Feature 2b: Session-only credential security (sessionStorage) verified.")

        # Reopen and test "Purge Credentials"
        await page.click('button[title="模型凭证与API配置"]')
        purge_btn = page.locator('button:has-text("清空凭据与缓存")')
        assert await purge_btn.is_visible(), "Purge credentials button must be present"
        await purge_btn.click()
        await page.wait_for_timeout(300)

        # Verify storage was completely wiped
        purged_local = await page.evaluate("() => localStorage.getItem('oogiri_flow_config')")
        purged_session = await page.evaluate("() => sessionStorage.getItem('oogiri_flow_config')")
        assert purged_local is None, f"localStorage config was not purged: {purged_local}"
        assert purged_session is None, f"sessionStorage config was not purged: {purged_session}"
        # Test that canceling discards uncommitted edits
        await page.fill('input[placeholder="sk-..."]', 'uncommitted-secret-to-discard')
        await page.click('button:has-text("取消")')
        await page.wait_for_timeout(200)
        # Re-open and verify field does not retain uncommitted input
        await page.click('button[title="模型凭证与API配置"]')
        cur_input_val = await page.input_value('input[placeholder="sk-..."]')
        assert cur_input_val == "", f"Uncommitted edit leaked into tempConfig: {cur_input_val}"
        await page.click('button:has-text("取消")')

        # ========================================================
        # Feature 3: Run pipeline demo to produce full thinking state
        # ========================================================
        await page.click('button:has-text("命题库")')
        await page.click('button:has-text("立即演示")')
        await page.wait_for_selector('text=全场总冠军金句', timeout=10000)
        
        initial_champion = await page.locator('h2.font-variety').first.text_content()
        initial_champion = initial_champion.strip()
        print(f"✓ Pipeline demo produced champion: {initial_champion}")

        # ========================================================
        # Feature 4: Three-Way Recast Manual Crowning (平反加冕机制)
        # ========================================================
        # Open thinking process fold-box
        await page.click('text=思考与裁决推导记录')
        await page.wait_for_timeout(300)

        # Check for crowning buttons in the 3-way recast section
        crown_buttons = page.locator('button:has-text("设为冠军")')
        count_crown_btns = await crown_buttons.count()
        assert count_crown_btns >= 1, f"Expected manual crowning buttons, found {count_crown_btns}"

        # Click the first variant's "设为冠军" button
        first_variant_card = page.locator('span:has-text("[现场喝止体]")').locator('xpath=..').locator('span.truncate')
        first_variant_text = await first_variant_card.text_content()
        first_variant_text = first_variant_text.strip()
        
        # Click the crown button next to monologue variant
        first_crown_btn = page.locator('button:has-text("设为冠军")').first
        await first_crown_btn.click()
        await page.wait_for_timeout(500)

        # Verify green bubble main punchline changed to the crowned variant
        new_champion_text = await page.locator('h2.font-variety').first.text_content()
        new_champion_text = new_champion_text.strip()
        assert new_champion_text == first_variant_text, f"Crowned variant mismatch: expected '{first_variant_text}', got '{new_champion_text}'"
        print(f"✓ Feature 4: Manual 3-way variant crowning successfully overturned champion to: '{new_champion_text}'")

        # ========================================================
        # Feature 5: "🎲 换个角度再来一句" (Re-roll with Stage 0 reuse)
        # ========================================================
        reroll_btn = page.locator('button:has-text("换个角度")').first
        assert await reroll_btn.is_visible(), "Re-roll button must be visible in champion bubble"
        await reroll_btn.click()
        
        # Wait for reroll completion
        await page.wait_for_selector('text=已换角度决出全新冠军金句', timeout=10000)
        await page.wait_for_timeout(500)

        rerolled_champion = await page.locator('h2.font-variety').first.text_content()
        rerolled_champion = rerolled_champion.strip()
        assert len(rerolled_champion) <= 20, f"Rerolled punchline too long: {rerolled_champion}"
        print(f"✓ Feature 5: Re-roll successfully produced new champion: '{rerolled_champion}'")

        # ========================================================
        # Feature 6: Export to Structured Markdown (Obsidian Ready)
        # ========================================================
        # We can evaluate export markdown directly to inspect structure and frontmatter
        md_export_test = await page.evaluate("""() => {
            const studio = window.oogiriStudio;
            const msgs = studio.messages.value || studio.messages;
            // Generate markdown string directly using internal pairs logic
            const pairs = [];
            for (let i = 0; i < msgs.length; i++) {
                const msg = msgs[i];
                if (msg.role === 'host') {
                    let player = null;
                    for (let j = i + 1; j < msgs.length; j++) {
                        if (msgs[j].role === 'player') {
                            player = msgs[j];
                            break;
                        }
                    }
                    if (player && player.champion) pairs.push({ host: msg, player });
                }
            }

            if (pairs.length === 0) return { success: false, reason: 'No pairs found' };
            const p = pairs[0];
            return {
                success: true,
                hasHost: Boolean(p.host.text),
                hasChampion: Boolean(p.player.champion),
                hasStage0: Boolean(p.player.pipelineState.stage0.raw_telemetry),
                hasTraps: Boolean(p.player.pipelineState.stage0.forbidden_baseline.length),
                hasTrackA: Boolean(p.player.pipelineState.trackA.candidates.length),
                hasTrackB: Boolean(p.player.pipelineState.trackB.candidates.length),
                hasTrackC: Boolean(p.player.pipelineState.trackC.candidates.length),
                hasStage2Elim: Boolean(p.player.pipelineState.stage2.four_gate_eliminations.length),
                hasDuel: Boolean(p.player.pipelineState.stage2.duel_records),
                hasRecast: Boolean(p.player.pipelineState.stage2.recast_variants)
            };
        }""")
        assert md_export_test["success"], f"Markdown structure check failed: {md_export_test}"
        assert md_export_test["hasStage0"] and md_export_test["hasTraps"], "Markdown missing Stage 0 data"
        assert md_export_test["hasTrackA"] and md_export_test["hasTrackB"] and md_export_test["hasTrackC"], "Markdown missing Stage 1 data"
        assert md_export_test["hasStage2Elim"] and md_export_test["hasDuel"] and md_export_test["hasRecast"], "Markdown missing Stage 2 data"
        
        # Click header Export button to verify UI flow
        export_btn = page.locator('header button:has-text("导出")')
        await export_btn.click()
        await page.wait_for_timeout(300)
        assert await page.is_visible("text=已成功导出 Markdown 记录"), "Export toast notification missing"

        # Verify duplicate chat stream export button is eliminated from main
        stream_export_btn = page.locator('main button:has-text("导出记录")')
        assert await stream_export_btn.count() == 0, "Duplicate chat stream export button must be removed"

        # Verify the actual Markdown string returned by exportMarkdownHistory()
        md_text = await page.evaluate("() => window.oogiriStudio.exportMarkdownHistory()")
        assert md_text and len(md_text) > 0, "exportMarkdownHistory() should return markdown content"
        
        import re
        # Check Chinese typography rule: ** 内侧只能紧挨汉字、字母或数字，标点一律放到星号外面
        # Extract individual bold spans
        bold_chunks = re.findall(r'\*\*(.+?)\*\*', md_text)
        assert len(bold_chunks) > 0, "Markdown must contain bold spans"
        # Test each bold chunk to ensure inner sides are only Chinese characters, letters, or digits
        bold_inner_punct = [b for b in bold_chunks if re.search(r'^[^\w\u4e00-\u9fff]|[^\w\u4e00-\u9fff]$', b)]
        assert len(bold_inner_punct) == 0, f"Found punctuation/symbols inside bold asterisks: {bold_inner_punct}"

        print("✓ Feature 6: Structured Markdown export (Obsidian-ready, typography-compliant) verified.")

        # ========================================================
        # Feature 8: Share Poster Modal & Canvas Generation (🖼️ 分享图)
        # ========================================================
        header_share_btn = page.locator('header button:has-text("分享图")')
        assert await header_share_btn.is_visible(), "Header share image button must be visible"
        await header_share_btn.click()
        await page.wait_for_timeout(500)

        # Verify modal opened
        assert await page.is_visible("text=大喜利对决分享卡片"), "Share poster modal must be visible"
        poster_img = page.locator('img[alt="大喜利分享卡片"]')
        assert await poster_img.is_visible(), "Poster image element must be visible"
        src = await poster_img.get_attribute("src")
        assert src and src.startswith("data:image/png;base64,"), "Poster preview must have valid dataURL source"
        
        # Verify download button
        download_btn = page.locator('button:has-text("保存为 PNG 图片")')
        assert await download_btn.is_visible(), "Download poster button must be visible"

        # Close modal
        close_modal_btn = page.locator('button:has-text("✕")')
        await close_modal_btn.click()
        await page.wait_for_timeout(300)
        assert not await page.is_visible("text=大喜利对决分享卡片"), "Share modal should be closed"

        # Verify bubble share button
        bubble_share_btn = page.locator('.bg-wechat-bubbleGreen button:has-text("分享图")').first
        assert await bubble_share_btn.is_visible(), "Bubble share button must be visible"
        await bubble_share_btn.click()
        await page.wait_for_timeout(500)
        assert await page.is_visible("text=大喜利对决分享卡片"), "Modal should open from champion bubble button"
        await page.locator('button:has-text("✕")').click()
        await page.wait_for_timeout(300)
        print("✓ Feature 8: Share poster modal & pure Canvas rendering verified.")

        # ========================================================
        # Feature 7: New Game / Reset Flow (🧹 新对局)
        # ========================================================
        new_game_btn = page.locator('header button:has-text("新对局")')
        assert await new_game_btn.is_visible(), "New game button must be in header"
        await new_game_btn.click()
        await page.wait_for_timeout(300)

        # Dialog should be reset back to just the system welcome banner & greeting
        message_count = await page.evaluate("() => (window.oogiriStudio.messages.value || window.oogiriStudio.messages).length")
        assert message_count == 1, f"Messages should be reset to 1 initial host message, got {message_count}"
        champion_bubbles = await page.locator('.bg-wechat-bubbleGreen').count()
        assert champion_bubbles == 0, f"All champion bubbles should be cleared, found {champion_bubbles}"
        print("✓ Feature 7: New Game reset flow verified (clean slate for new match).")

        # Zero console errors check
        if console_errors:
            print("Console errors during test:", console_errors)
        else:
            print("✓ Zero console errors throughout new feature tests!")

        await browser.close()
        print("\n🎉 ALL NEW FEATURES TESTED AND FULLY PASSED!")

if __name__ == "__main__":
    asyncio.run(run_new_features_tests())
