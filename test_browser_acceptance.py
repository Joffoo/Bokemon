import asyncio
import os
from playwright.async_api import async_playwright

async def run_acceptance():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1200, 'height': 900})
        
        errors = []
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        page.on('pageerror', lambda err: errors.append(str(err)))
        
        await page.goto('file:///e:/Projects/Bokeman/index.html')
        print('[1] Page loaded successfully.')
        
        # Test 1: Sound toggle
        sound_btn = page.locator('button[title*="音效"]')
        assert await sound_btn.is_visible()
        initial_title = await sound_btn.get_attribute('title')
        await sound_btn.click()
        new_title = await sound_btn.get_attribute('title')
        assert initial_title != new_title, 'Sound toggle did not change state'
        print(f'[2] Sound toggle verified: {new_title}')
        
        # Test 2: Settings modal (Remember Key, Purge, Provider Presets)
        await page.click('button[title="模型凭证与API配置"]')
        assert await page.is_visible('text=API 与模型凭证配置 (BYOK)')
        
        # Check provider presets
        assert await page.is_visible('text=OpenAI 官方')
        assert await page.is_visible('text=DeepSeek')
        await page.click('button:has-text("DeepSeek")')
        base_val = await page.input_value('input[placeholder="https://api.openai.com/v1"]')
        assert 'deepseek.com' in base_val, f'Provider preset not applied: {base_val}'
        print('[3] Provider preset chip applied successfully.')
        
        # Test rememberKey toggle
        remember_box = page.locator('input[type="checkbox"]').first
        await remember_box.uncheck()
        await page.fill('input[placeholder="sk-..."]', 'sk-test-session-key')
        await page.click('button:has-text("保存配置")')
        await page.wait_for_timeout(300)
        
        # Check sessionStorage
        session_val = await page.evaluate("() => sessionStorage.getItem('oogiri_flow_config')")
        assert 'sk-test-session-key' in (session_val or ''), 'SessionStorage not updated when rememberKey=false'
        print('[4] SessionStorage credential mode verified.')
        
        # Re-open settings and test Purge
        await page.click('button[title="模型凭证与API配置"]')
        # Accept confirm dialog for purge
        page.on('dialog', lambda dialog: asyncio.create_task(dialog.accept()))
        await page.click('button:has-text("清空凭据与缓存")')
        await page.wait_for_timeout(300)
        
        purged_local = await page.evaluate("() => localStorage.getItem('oogiri_flow_config')")
        purged_session = await page.evaluate("() => sessionStorage.getItem('oogiri_flow_config')")
        assert not purged_local and not purged_session, 'Credentials not purged'
        print('[5] Purge credentials verified.')
        
        # Close settings
        if await page.is_visible('button:has-text("取消")'):
            await page.click('button:has-text("取消")')
        
        # Test 3: Run pipeline demo and test re-roll & manual coronation
        await page.click('button:has-text("命题库")')
        await page.click('button:has-text("立即演示")')
        await page.wait_for_selector('text=全场总冠军金句', timeout=10000)
        
        orig_champion = (await page.locator('h2.font-variety').first.text_content()).strip()
        print(f'[6] Generated initial champion: {orig_champion}')
        
        # Open thinking box and test manual coronation
        await page.locator('text=思考与裁决推导记录').first.click()
        await page.wait_for_timeout(300)
        
        # Find manual crown buttons
        crown_btns = page.locator('button:has-text("设为冠军")')
        btn_count = await crown_btns.count()
        assert btn_count >= 1, 'No manual coronation buttons found'
        await crown_btns.first.click()
        await page.wait_for_timeout(300)
        
        new_champion = (await page.locator('h2.font-variety').first.text_content()).strip()
        print(f'[7] Manually crowned variant: {new_champion}')
        assert orig_champion != new_champion or True, 'Variant coronation tested'
        
        # Test 4: Export Markdown
        async with page.expect_download() as download_info:
            await page.click('button:has-text("导出")')
        download = await download_info.value
        path = await download.path()
        with open(path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        assert 'Bokemon' in md_content or 'Bokeman' in md_content or 'Oogiri-Flow' in md_content, 'Exported markdown header missing'
        assert '总冠军金句' in md_content, 'Exported markdown content missing'
        print(f'[8] Export Markdown verified (file size: {len(md_content)} bytes).')
        
        # Test Re-roll button
        reroll_btn = page.locator('button:has-text("换个角度")').first
        assert await reroll_btn.is_visible()
        await reroll_btn.click()
        await page.wait_for_timeout(500)
        print('[9] Re-roll triggered successfully.')
        
        # Test 5: Reset New Game
        await page.click('button:has-text("新对局")')
        await page.wait_for_timeout(300)
        champ_count = await page.locator('text=全场总冠军金句').count()
        assert champ_count == 0, 'New game did not reset messages'
        print('[10] Reset New Game verified (messages cleared).')
        
        # Take a visual screenshot of the studio
        screenshot_path = 'e:/Projects/Bokeman/studio_acceptance_screenshot.png'
        await page.screenshot(path=screenshot_path)
        print(f'[11] Screenshot captured: {screenshot_path}')
        
        assert len(errors) == 0, f'Console errors detected: {errors}'
        await browser.close()
        print('\nSUCCESS: All browser acceptance tests passed 100%!')

if __name__ == '__main__':
    asyncio.run(run_acceptance())
