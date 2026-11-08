import asyncio
from playwright.async_api import async_playwright
import base64

async def test_perfect():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 900, 'height': 900})
        await page.goto('file:///e:/Projects/Bokeman/index.html')
        
        # Run demo
        await page.click('button:has-text("命题库")')
        await page.click('button:has-text("立即演示")')
        await page.wait_for_selector('text=全场总冠军金句', timeout=10000)
        
        data_url = await page.evaluate('''async () => {
            const hostEl = Array.from(document.querySelectorAll('.bubble-tail-left')).map(b => b.closest('.flex.items-start')).pop();
            const playerEl = Array.from(document.querySelectorAll('.bubble-tail-right')).map(b => b.closest('.flex.items-start.justify-end')).pop();
            
            const wrapper = document.createElement('div');
            wrapper.style.width = '600px';
            wrapper.style.backgroundColor = '#EDEDED';
            wrapper.style.padding = '24px 20px';
            wrapper.style.position = 'fixed';
            wrapper.style.top = '0';
            wrapper.style.left = '0';
            wrapper.style.zIndex = '-9999';
            wrapper.style.pointerEvents = 'none';
            wrapper.style.fontFamily = '"Microsoft YaHei", -apple-system, sans-serif';
            wrapper.className = 'space-y-4';
            
            const hostClone = hostEl.cloneNode(true);
            const playerClone = playerEl.cloneNode(true);
            
            // Fix 1: Hide interactive buttons inside green bubble for the share card
            const btnsBar = playerClone.querySelector('.border-t.border-emerald-600\\\\/15') || playerClone.querySelector('.border-t');
            if (btnsBar) {
                // Keep only a clean footer or remove interactive buttons
                btnsBar.innerHTML = '<span class="text-[10px] text-emerald-800 font-medium">Bokemon · 决选金句</span><span class="text-[10px] text-emerald-800">全场总冠军</span>';
                btnsBar.className = 'mt-2 text-[10px] text-emerald-800 flex items-center justify-between pt-1.5 border-t border-emerald-600/20';
            }
            
            // Fix 2: Remove font-mono from badge to avoid Chinese font mismatch
            playerClone.querySelectorAll('.font-mono').forEach(el => {
                el.classList.remove('font-mono');
                el.style.fontFamily = '"Microsoft YaHei", -apple-system, sans-serif';
                el.style.lineHeight = '1.4';
            });
            
            wrapper.appendChild(hostClone);
            wrapper.appendChild(playerClone);
            document.body.appendChild(wrapper);
            
            const canvas = await html2canvas(wrapper, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#EDEDED',
                logging: false,
                scrollX: 0,
                scrollY: 0,
                windowWidth: 1200
            });
            
            document.body.removeChild(wrapper);
            return canvas.toDataURL('image/png');
        }''')
        
        with open('e:/Projects/Bokeman/perfect_share_test.png', 'wb') as f:
            f.write(base64.b64decode(data_url.split(',')[1]))
        print('[OK] Saved perfect_share_test.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_perfect())
