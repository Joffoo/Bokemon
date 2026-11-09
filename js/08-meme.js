// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        async function renderCanvasMeme(imageSource, punchline) {
          return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
              try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const w = img.naturalWidth || img.width || 600;
                const h = img.naturalHeight || img.height || 450;
                canvas.width = w;
                canvas.height = h;

                // 1. Draw original picture
                ctx.drawImage(img, 0, 0, w, h);

                // 2. Dynamic font size calculation (matching render_meme.py with 12-20 words elasticity)
                let fontSize = Math.max(22, Math.floor(w / 16));
                const minSize = Math.max(16, Math.floor(w / 40));
                const fontStack = '"Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Meiryo", sans-serif';

                ctx.font = `900 ${fontSize}px ${fontStack}`;
                let textW = ctx.measureText(punchline).width;

                while (textW > w * 0.85 && fontSize > minSize) {
                  fontSize -= 2;
                  ctx.font = `900 ${fontSize}px ${fontStack}`;
                  textW = ctx.measureText(punchline).width;
                }

                const textH = fontSize;
                // Position: bottom centered, 8% margin from bottom, strictly anchored with textBaseline 'bottom'
                ctx.textBaseline = 'bottom';
                const x = Math.floor((w - textW) / 2);
                const y = Math.floor(h - Math.floor(h * 0.08));

                // 3. Bottom translucent dark protective bar
                const barTop = Math.max(0, Math.floor(y - textH * 1.35));
                const gradient = ctx.createLinearGradient(0, barTop, 0, h);
                gradient.addColorStop(0, 'rgba(0, 0, 0, 0)');
                gradient.addColorStop(0.35, 'rgba(0, 0, 0, 0.55)');
                gradient.addColorStop(1, 'rgba(0, 0, 0, 0.82)');
                ctx.fillStyle = gradient;
                ctx.fillRect(0, barTop, w, h - barTop);

                // 4. Solid Black Heavy Stroke (scaled by font size)
                const strokeW = Math.max(4, Math.floor(fontSize / 7));
                ctx.lineJoin = 'round';
                ctx.miterLimit = 2;
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = strokeW * 2;
                ctx.strokeText(punchline, x, y);

                // 5. Pure White Variety Show Main Text
                ctx.fillStyle = '#FFFFFF';
                ctx.fillText(punchline, x, y);

                const dataUrl = canvas.toDataURL('image/png', 1.0);
                resolve(dataUrl);
              } catch (err) {
                reject(err);
              }
            };
            img.onerror = () => reject(new Error("Failed to load image for Canvas meme rendering"));
            img.src = imageSource;
          });
        }

        // Helper: Canvas rounded rectangle
        function drawRoundRect(ctx, x, y, width, height, radius) {
          ctx.beginPath();
          ctx.moveTo(x + radius, y);
          ctx.lineTo(x + width - radius, y);
          ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
          ctx.lineTo(x + width, y + height - radius);
          ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
          ctx.lineTo(x + radius, y + height);
          ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
          ctx.lineTo(x, y + radius);
          ctx.quadraticCurveTo(x, y, x + radius, y);
          ctx.closePath();
        }

        // Helper: Canvas multi-line text measurement
        function measureWrappedLines(ctx, text, maxWidth) {
          if (!text) return [];
          const chars = String(text).split('');
          const lines = [];
          let currentLine = '';
          for (let i = 0; i < chars.length; i++) {
            const testLine = currentLine + chars[i];
            if (ctx.measureText(testLine).width > maxWidth && currentLine.length > 0) {
              lines.push(currentLine);
              currentLine = chars[i];
            } else {
              currentLine = testLine;
            }
          }
          if (currentLine) lines.push(currentLine);
          return lines;
        }

        // Helper: Canvas multi-line text wrapper
        function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight) {
          if (!text) return y;
          const lines = measureWrappedLines(ctx, text, maxWidth);
          let curY = y;
          for (let i = 0; i < lines.length; i++) {
            ctx.fillText(lines[i], x, curY);
            curY += lineHeight;
          }
          return curY;
        }

        // Client-side HTML5 Canvas High-Fidelity Share Poster Card
