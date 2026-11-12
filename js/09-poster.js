// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        async function renderSharePoster(pair) {
          const hMsg = pair.host;
          const pMsg = pair.player;
          const champion = pMsg.champion || '大喜利总冠军金句';

          // Primary: Native Browser Screenshot Engine (modern-screenshot via SVG foreignObject)
          if (window.modernScreenshot?.domToPng || typeof window.html2canvas === 'function') {
            try {
              const hostEl = document.getElementById('msg-' + hMsg.id) || 
                             Array.from(document.querySelectorAll('.bubble-tail-left')).map(b => b.closest('.flex.items-start')).pop();
              const playerEl = document.getElementById('msg-' + pMsg.id) || 
                               Array.from(document.querySelectorAll('.bubble-tail-right')).map(b => b.closest('.flex.items-start.justify-end')).pop();

              if (hostEl && playerEl) {
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

                // Add time tag
                if (hMsg.time || pMsg.time) {
                  const timeDiv = document.createElement('div');
                  timeDiv.className = 'flex justify-center my-1';
                  timeDiv.innerHTML = `<span class="text-[10px] text-gray-500 bg-[#DEDEDE] px-2 py-0.5 rounded font-sans">${hMsg.time || pMsg.time}</span>`;
                  wrapper.appendChild(timeDiv);
                }

                const hostClone = hostEl.cloneNode(true);
                const playerClone = playerEl.cloneNode(true);

                // Hide interactive web buttons (换个角度 / 分享图) inside the exported share card
                const btnsBar = playerClone.querySelector('.border-t');
                if (btnsBar) {
                  btnsBar.innerHTML = '<span class="text-[10px] text-emerald-800 font-medium">Bokemon · 决选金句</span><span class="text-[10px] text-emerald-800">全场总冠军</span>';
                  btnsBar.className = 'mt-2 text-[10px] text-emerald-800 flex items-center justify-between pt-1.5 border-t border-emerald-600/20';
                }

                wrapper.appendChild(hostClone);
                wrapper.appendChild(playerClone);
                document.body.appendChild(wrapper);

                let dataUrl = null;
                if (window.modernScreenshot?.domToPng) {
                  dataUrl = await window.modernScreenshot.domToPng(wrapper, {
                    scale: 2,
                    backgroundColor: '#EDEDED'
                  });
                } else {
                  const domCanvas = await window.html2canvas(wrapper, {
                    scale: 2,
                    useCORS: true,
                    backgroundColor: '#EDEDED',
                    logging: false,
                    scrollX: 0,
                    scrollY: 0,
                    windowWidth: 1200
                  });
                  dataUrl = domCanvas.toDataURL('image/png', 1.0);
                }

                document.body.removeChild(wrapper);
                if (dataUrl) return dataUrl;
              }
            } catch (e) {
              console.warn('DOM screenshot capture fallback to standard canvas', e);
            }
          }
          const promptText = hMsg.text || '大喜利命题';
          const s0 = pMsg.pipelineState?.stage0 || {};
          const telemetry = s0.raw_telemetry || '常识地基纯物理底料';
          const crowningReason = pMsg.pipelineState?.stage2?.crowning_reason || '单点错位极致反转，生活当下秒懂。';

          // Preload host image if exists
          let hostImg = null;
          if (hMsg.imageDataUrl) {
            try {
              hostImg = await new Promise((resolve) => {
                const img = new Image();
                img.crossOrigin = 'anonymous';
                img.onload = () => resolve(img);
                img.onerror = () => resolve(null);
                img.src = hMsg.imageDataUrl;
              });
            } catch (e) {
              hostImg = null;
            }
          }

          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          const width = 720;
          const pad = 28;
          const cardW = width - pad * 2;
          const hasImg = Boolean(hostImg);

          // Pre-measure section heights for dynamic layout (eliminates dead gray space)
          const headerH = 130;

          // Question box height
          ctx.font = 'bold 16px "Microsoft YaHei", sans-serif';
          const qLines = measureWrappedLines(ctx, promptText, cardW - 36);
          const qTextH = qLines.length * 24;
          const qBoxH = Math.max(88, 14 + 18 + qTextH + 16);

          // Image height
          const imgH = hasImg ? 200 : 0;

          // Champion bubble height
          const champH = 180;

          // Ground telemetry & Crowning reason box height
          ctx.font = '12px "Microsoft YaHei", sans-serif';
          const tLines = measureWrappedLines(ctx, telemetry, cardW - 36);
          const tH = tLines.length * 18;
          const cLines = measureWrappedLines(ctx, crowningReason, cardW - 36);
          const cH = cLines.length * 18;
          const infoH = 16 + 18 + tH + 14 + 1 + 14 + 18 + cH + 16;

          // Watermark footer height
          const footerH = 48;

          // Exact dynamic canvas height
          const totalH = pad + headerH + 16 + qBoxH + (hasImg ? (imgH + 16) : 0) + 16 + champH + 16 + infoH + 20 + footerH + pad;
          canvas.width = width;
          canvas.height = totalH;

          // 1. Overall Background (Light modern Japanese neutral)
          ctx.fillStyle = '#EAEAEA';
          ctx.fillRect(0, 0, width, totalH);

          // 2. Header Slate Banner (Japanese variety show broadcast style)
          ctx.save();
          ctx.fillStyle = '#1E242B';
          drawRoundRect(ctx, pad, pad, cardW, headerH, 16);
          ctx.fill();

          // Japanese circular seal "大喜利 一本"
          ctx.fillStyle = '#E02020';
          ctx.beginPath();
          ctx.arc(cardW + pad - 48, pad + 65, 30, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = '#FFFFFF';
          ctx.lineWidth = 2;
          ctx.stroke();

          ctx.fillStyle = '#FFFFFF';
          ctx.font = 'bold 14px "Microsoft YaHei", sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('大喜利', cardW + pad - 48, pad + 56);
          ctx.font = '900 11px sans-serif';
          ctx.fillText('一本', cardW + pad - 48, pad + 74);

          // Studio Title & Badges
          ctx.textAlign = 'left';
          ctx.fillStyle = '#FFFFFF';
          ctx.font = '900 24px "Microsoft YaHei", sans-serif';
          ctx.fillText('Bokemon', pad + 24, pad + 50);

          ctx.fillStyle = '#F5A623';
          ctx.font = 'bold 13px "Microsoft YaHei", sans-serif';
          ctx.fillText('日式大喜利流水线 · 巅峰对决出题', pad + 24, pad + 82);

          ctx.fillStyle = '#9CA3AF';
          ctx.font = '10px sans-serif';
          ctx.fillText('DUEL MEME POSTER · 拒绝AI文言文 · 说清才能脆', pad + 24, pad + 104);
          ctx.restore();

          let curY = pad + headerH + 16;

          // 3. Question (Host) Box (WeChat Host Bubble Style)
          ctx.save();
          ctx.fillStyle = '#FFFFFF';
          ctx.strokeStyle = '#DCDCDC';
          ctx.lineWidth = 1.5;
          drawRoundRect(ctx, pad, curY, cardW, qBoxH, 14);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#4B5563';
          ctx.font = 'bold 12px "Microsoft YaHei", sans-serif';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'top';
          ctx.fillText('🎙️ 大喜利主持命题', pad + 18, curY + 14);

          ctx.fillStyle = '#111827';
          ctx.font = 'bold 16px "Microsoft YaHei", sans-serif';
          drawWrappedText(ctx, promptText, pad + 18, curY + 36, cardW - 36, 24);
          ctx.restore();

          curY += qBoxH + 16;

          // If Host attached image, draw image preview
          if (hostImg) {
            ctx.save();
            drawRoundRect(ctx, pad, curY, cardW, imgH, 12);
            ctx.clip();
            ctx.drawImage(hostImg, pad, curY, cardW, imgH);
            ctx.restore();
            curY += imgH + 16;
          }

          // 4. Crowned Champion Hero Bubble (WeChat Bubble Green + Variety Text)
          ctx.save();
          ctx.fillStyle = '#95EC69';
          ctx.strokeStyle = '#85DC59';
          ctx.lineWidth = 2;
          drawRoundRect(ctx, pad, curY, cardW, champH, 18);
          ctx.fill();
          ctx.stroke();

          // Green bubble header pill
          ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
          drawRoundRect(ctx, pad + 18, curY + 14, 190, 26, 6);
          ctx.fill();

          ctx.fillStyle = '#065F46';
          ctx.font = 'bold 12px "Microsoft YaHei", sans-serif';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'middle';
          ctx.fillText(`🏆 全场总冠军金句 (${champion.length}字)`, pad + 28, curY + 27);

          // Hero Punchline text with robust font fitting loop (guaranteed zero overflow)
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          let champFontSize = 32;
          const minChampFontSize = 18;
          ctx.font = `900 ${champFontSize}px "Microsoft YaHei", "PingFang SC", sans-serif`;
          let champTextW = ctx.measureText(champion).width;
          while (champTextW > cardW - 60 && champFontSize > minChampFontSize) {
            champFontSize -= 1;
            ctx.font = `900 ${champFontSize}px "Microsoft YaHei", "PingFang SC", sans-serif`;
            champTextW = ctx.measureText(champion).width;
          }

          // Stroke outline
          ctx.strokeStyle = '#000000';
          ctx.lineWidth = 4;
          ctx.lineJoin = 'round';
          ctx.strokeText(champion, width / 2, curY + 90);

          // Main white text
          ctx.fillStyle = '#FFFFFF';
          ctx.fillText(champion, width / 2, curY + 90);

          // Sub-bar
          ctx.fillStyle = 'rgba(6, 95, 70, 0.85)';
          ctx.font = 'bold 11px sans-serif';
          ctx.fillText('全场裁决总冠军 · 零标点大白话', width / 2, curY + 148);
          ctx.restore();

          curY += champH + 16;

          // 5. Stage 0 Ground Telemetry & Crowning Reason Card (Adaptive height)
          ctx.save();
          ctx.fillStyle = '#FFFFFF';
          ctx.strokeStyle = '#DCDCDC';
          ctx.lineWidth = 1.5;
          drawRoundRect(ctx, pad, curY, cardW, infoH, 14);
          ctx.fill();
          ctx.stroke();

          // Section 1: 70% 常识地基切片
          ctx.fillStyle = '#1D4ED8';
          ctx.font = 'bold 12px "Microsoft YaHei", sans-serif';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'top';
          ctx.fillText('🎯 常识地基切片 (Ground Telemetry)', pad + 18, curY + 16);

          ctx.fillStyle = '#374151';
          ctx.font = '12px "Microsoft YaHei", sans-serif';
          drawWrappedText(ctx, telemetry, pad + 18, curY + 38, cardW - 36, 18);

          // Dynamic separator
          const sepY = curY + 38 + tH + 12;
          ctx.strokeStyle = '#F3F4F6';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(pad + 18, sepY);
          ctx.lineTo(pad + cardW - 18, sepY);
          ctx.stroke();

          // Section 2: 加冕判词
          const reasonTitleY = sepY + 14;
          ctx.fillStyle = '#B45309';
          ctx.font = 'bold 12px "Microsoft YaHei", sans-serif';
          ctx.fillText('⚖️ 公诉人加冕判词 (Crowning Reason)', pad + 18, reasonTitleY);

          ctx.fillStyle = '#4B5563';
          ctx.font = '12px "Microsoft YaHei", sans-serif';
          drawWrappedText(ctx, crowningReason, pad + 18, reasonTitleY + 20, cardW - 36, 18);
          ctx.restore();

          curY += infoH + 20;

          // 6. Watermark Footer
          ctx.save();
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';

          ctx.fillStyle = '#7F7F7F';
          ctx.font = 'bold 12px "Microsoft YaHei", sans-serif';
          ctx.fillText('ボケて (Bokete) · 日式大喜利流水线制作', width / 2, curY);

          ctx.font = '10px sans-serif';
          ctx.fillStyle = '#A0AEC0';
          const nowStr = new Date().toLocaleDateString('zh-CN');
          ctx.fillText(`生成日期: ${nowStr} · Bokemon`, width / 2, curY + 20);
          ctx.restore();

          return canvas.toDataURL('image/png', 1.0);
        }

        async function openSharePosterModal(targetMsg = null) {
          let pair = null;
          if (targetMsg && targetMsg.role === 'player') {
            const pIdx = messages.value.findIndex(m => m.id === targetMsg.id);
            for (let i = pIdx - 1; i >= 0; i--) {
              if (messages.value[i].role === 'host') {
                pair = { host: messages.value[i], player: targetMsg };
                break;
              }
            }
          }
          if (!pair) {
            for (let i = messages.value.length - 1; i >= 0; i--) {
              const p = messages.value[i];
              if (p.role === 'player' && p.champion) {
                for (let j = i - 1; j >= 0; j--) {
                  if (messages.value[j].role === 'host') {
                    pair = { host: messages.value[j], player: p };
                    break;
                  }
                }
                if (pair) break;
              }
            }
          }

          if (!pair) {
            showToast('当前暂无可分享的对局，请先出题或体验演示');
            return;
          }

          try {
            const dataUrl = await renderSharePoster(pair);
            sharePosterModal.url = dataUrl;
            sharePosterModal.title = `大喜利对决分享 · ${pair.player.champion}`;
            sharePosterModal.visible = true;
            showToast('已生成大喜利对决分享图！');
          } catch (err) {
            console.error('Share poster error', err);
            showToast('生成分享图失败：' + (err.message || '未知异常'));
          }
        }

        function downloadSharePoster() {
          if (!sharePosterModal.url) return;
          const link = document.createElement('a');
          link.href = sharePosterModal.url;
          const time = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
          link.download = `oogiri_share_${time}.png`;
          link.click();
        }

        // SUBAGENT CONCURRENCY STATUS HELPERS
        function getStatusBadgeClass(status) {
          switch (status) {
            case 'running': return 'text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded font-mono font-medium animate-pulse-subtle';
            case 'done': return 'text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-mono font-bold';
            case 'failed': return 'text-red-700 bg-red-50 px-1.5 py-0.5 rounded font-mono';
            default: return 'text-gray-400 font-mono';
          }
        }

        function getStatusText(track) {
          if (track.status === 'running') {
            return track.retries > 0 ? `重试第${track.retries}次` : '执行中...';
          }
          if (track.status === 'done') return '✓ 完成';
          if (track.status === 'failed') return '✕ 已跳过';
          return '等待';
        }
