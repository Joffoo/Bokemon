// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        function exportMarkdownHistory() {
          const pairs = [];
          for (let i = 0; i < messages.value.length; i++) {
            const msg = messages.value[i];
            if (msg.role === 'host') {
              let player = null;
              for (let j = i + 1; j < messages.value.length; j++) {
                if (messages.value[j].role === 'player') {
                  player = messages.value[j];
                  break;
                }
                if (messages.value[j].role === 'host') break;
              }
              if (player && player.champion) {
                pairs.push({ host: msg, player });
              }
            }
          }

          if (pairs.length === 0) {
            showToast('当前暂无可导出的对局记录');
            return;
          }

          const now = new Date();
          const pad = (n) => String(n).padStart(2, '0');
          const timeStr = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
          const fileTime = `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;

          let md = `# 🏆 日式大喜利流水线对战记录 (Bokemon Records)\n\n`;
          md += `> **导出时间**：${timeStr}\n`;
          md += `> **平台引擎**：Bokemon (日式大喜利流水线)\n`;
          md += `> **对战总局数**：共 ${pairs.length} 局\n\n`;
          md += `---\n\n`;

          pairs.forEach((pair, idx) => {
            const h = pair.host;
            const p = pair.player;
            const s0 = p.pipelineState?.stage0 || {};
            const s1 = p.pipelineState || {};
            const s2 = p.pipelineState?.stage2 || {};

            md += `## 题号 #${idx + 1}：${h.text || '看图命题'}\n\n`;
            if (h.imageDataUrl) {
              md += `- **命题类型**：看图大喜利 (附图命题)\n`;
            } else {
              md += `- **命题类型**：文字大喜利命题\n`;
            }
            md += `- **对局时间**：${h.time || p.time || '未知'}\n`;
            md += `- **全场总冠军金句**：**${p.champion}** (${p.champion.length}字 · 零标点)\n`;
            if (s2.crowning_reason) {
              md += `- **加冕判词**：${s2.crowning_reason}\n`;
            }
            md += `\n`;

            // Stage 0
            md += `### 🎯 Stage 0 · 常识地基切片与预筛\n\n`;
            md += `- 【**Raw Telemetry 纯物理底料**】：\n  ${s0.raw_telemetry || '无'}\n\n`;
            if (s0.forbidden_baseline && s0.forbidden_baseline.length) {
              md += `- 【**封死平庸三阱**】：\n`;
              s0.forbidden_baseline.forEach(f => {
                md += `  - ${f}\n`;
              });
              md += `\n`;
            }
            if (s0.secular_domains && s0.secular_domains.length) {
              md += `- 【**预选世俗域**】：${s0.secular_domains.join('、')}\n\n`;
            }

            // Stage 1
            md += `### 🚀 Stage 1 · 三轨一次发散候选池\n\n`;
            // Track A
            md += `#### A轨 · 体面破绽 (庄重地基+琐碎错位)\n`;
            if (s1.trackA?.candidates && s1.trackA.candidates.length) {
              s1.trackA.candidates.forEach((c, ci) => {
                md += `${ci + 1}. ${c}\n`;
              });
            } else {
              md += `(暂无候选)\n`;
            }
            md += `\n`;

            // Track B
            md += `#### B轨 · 异业动作清单 (前提级误解+行业肌肉记忆)\n`;
            if (s1.trackB?.candidates && s1.trackB.candidates.length) {
              s1.trackB.candidates.forEach(c => {
                const cat = c.category || c.name || '异业动作';
                const pun = c.punchline || c.line || '';
                const cleanCat = String(cat).replace(/[\[\]【】]/g, '').trim();
                md += `- [**${cleanCat}**]：${pun}\n`;
              });
            } else {
              md += `(暂无候选)\n`;
            }
            md += `\n`;

            // Track C
            md += `#### C轨 · 物理死磕 (单参数物理极限推演)\n`;
            if (s1.trackC?.candidates && s1.trackC.candidates.length) {
              s1.trackC.candidates.forEach((c, ci) => {
                md += `${ci + 1}. ${c}\n`;
              });
            } else {
              md += `(暂无候选)\n`;
            }
            md += `\n`;

            // Stage 2
            md += `### ⚔️ Stage 2 · 公诉人客观审判与代数重铸\n\n`;
            if (s2.four_gate_eliminations && s2.four_gate_eliminations.length) {
              md += `#### 四道客观检视淘汰清单\n`;
              s2.four_gate_eliminations.forEach(elim => {
                md += `- ${elim}\n`;
              });
              md += `\n`;
            }

            if (s2.duel_records || s2.pk_interrogation) {
              md += `#### 公诉人质询死斗记录\n\`\`\`\n${s2.duel_records || s2.pk_interrogation}\n\`\`\`\n\n`;
            }

            if (s2.track_champions) {
              md += `#### 轨道冠军与初稿决选\n`;
              if (s2.track_champions.trackA) md += `- **A轨冠军**：${s2.track_champions.trackA}\n`;
              if (s2.track_champions.trackB) md += `- **B轨冠军**：${s2.track_champions.trackB}\n`;
              if (s2.track_champions.trackC) md += `- **C轨冠军**：${s2.track_champions.trackC}\n`;
              if (s2.initial_champion) md += `- **总冠军初稿**：${s2.initial_champion}\n`;
              md += `\n`;
            }

            if (s2.recast_variants) {
              md += `#### 三向代数句法重铸对决\n`;
              if (s2.recast_variants.monologue) md += `- [**现场喝止独白体**]：${s2.recast_variants.monologue}\n`;
              if (s2.recast_variants.quantified) md += `- [**量化规矩折算体**]：${s2.recast_variants.quantified}\n`;
              if (s2.recast_variants.cold_sketch) md += `- [**冷面白描单动作体**]：${s2.recast_variants.cold_sketch}\n`;
              md += `\n`;
            }

            md += `---\n\n`;
          });

          try {
            const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `oogiri_records_${fileTime}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast('已成功导出 Markdown 记录 ✓');
            return md;
          } catch (e) {
            console.error('Export error:', e);
            showToast('导出失败：' + e.message);
            return md;
          }
        }

        // ==========================================
        // RESET NEW GAME
        // ==========================================
