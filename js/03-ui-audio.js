// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        function showToast(msg, duration = 2000) {
          if (toast.timer) clearTimeout(toast.timer);
          toast.message = msg;
          toast.visible = true;
          toast.timer = setTimeout(() => {
            toast.visible = false;
          }, duration);
        }

        // Copy Punchline to Clipboard
        async function copyPunchline(text) {
          if (!text) return;
          try {
            if (navigator.clipboard && window.isSecureContext) {
              await navigator.clipboard.writeText(text);
            } else {
              throw new Error('Fallback to execCommand');
            }
          } catch (err) {
            try {
              const ta = document.createElement('textarea');
              ta.value = text;
              ta.style.position = 'fixed';
              ta.style.opacity = '0';
              ta.style.left = '-9999px';
              document.body.appendChild(ta);
              ta.focus();
              ta.select();
              const successful = document.execCommand('copy');
              document.body.removeChild(ta);
              if (!successful) throw new Error('execCommand copy failed');
            } catch (e2) {
              showToast('复制失败，请长按文本复制');
              return;
            }
          }
          showToast('已复制金句到剪切板 ✓');
        }

        // Shared AudioContext (lazy init + resume)
        function getAudioContext() {
          try {
            if (!audioCtx) {
              const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
              if (AudioCtxClass) {
                audioCtx = new AudioCtxClass();
              }
            }
            if (audioCtx && audioCtx.state === 'suspended') {
              audioCtx.resume().catch(() => {});
            }
            return audioCtx;
          } catch (e) {
            return null;
          }
        }

        function toggleSound() {
          soundEnabled.value = !soundEnabled.value;
          try {
            localStorage.setItem('oogiri_sound_enabled', String(soundEnabled.value));
          } catch (e) {}
          showToast(soundEnabled.value ? '🔔 音效已开启' : '🔕 音效已静音');
        }

        // Japanese Taiko / Wooden Clapper synth sound on prompt initiation
        function playStartSound() {
          if (!soundEnabled.value) return;
          const ctx = getAudioContext();
          if (!ctx) return;
          try {
            const now = ctx.currentTime;
            // Taiko bass body
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(170, now);
            osc.frequency.exponentialRampToValueAtTime(45, now + 0.35);

            gain.gain.setValueAtTime(0.7, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.35);

            // Wood clapper snap attack
            const snapOsc = ctx.createOscillator();
            const snapGain = ctx.createGain();
            snapOsc.type = 'triangle';
            snapOsc.frequency.setValueAtTime(520, now);
            snapOsc.frequency.exponentialRampToValueAtTime(120, now + 0.08);

            snapGain.gain.setValueAtTime(0.4, now);
            snapGain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

            snapOsc.connect(snapGain);
            snapGain.connect(ctx.destination);
            snapOsc.start(now);
            snapOsc.stop(now + 0.08);
          } catch (e) {}
        }

        // Champion gavel knock & celebratory chime arpeggio
        function playChampionSound() {
          if (!soundEnabled.value) return;
          const ctx = getAudioContext();
          if (!ctx) return;
          try {
            const now = ctx.currentTime;
            // Gavel knock (short woody tap)
            const knockOsc = ctx.createOscillator();
            const knockGain = ctx.createGain();
            knockOsc.type = 'triangle';
            knockOsc.frequency.setValueAtTime(650, now);
            knockOsc.frequency.exponentialRampToValueAtTime(90, now + 0.12);

            knockGain.gain.setValueAtTime(0.8, now);
            knockGain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

            knockOsc.connect(knockGain);
            knockGain.connect(ctx.destination);
            knockOsc.start(now);
            knockOsc.stop(now + 0.12);

            // Chime celebratory fanfare (G5, C6, E6, G6)
            const notes = [784, 1046.5, 1318.5, 1568];
            notes.forEach((freq, idx) => {
              const t = now + 0.08 + idx * 0.07;
              const chimeOsc = ctx.createOscillator();
              const chimeGain = ctx.createGain();
              chimeOsc.type = 'sine';
              chimeOsc.frequency.setValueAtTime(freq, t);

              chimeGain.gain.setValueAtTime(0.25, t);
              chimeGain.gain.exponentialRampToValueAtTime(0.001, t + 0.45);

              chimeOsc.connect(chimeGain);
              chimeGain.connect(ctx.destination);
              chimeOsc.start(t);
              chimeOsc.stop(t + 0.45);
            });
          } catch (e) {}
        }

        // ==========================================
        // RESET NEW GAME
        // ==========================================
        function resetNewGame() {
          isGeneratingAny.value = false;
          messages.value = [
            {
              id: 1,
              time: '刚刚',
              showTime: true,
              role: 'host',
              text: '欢迎来到 Bokemon！请在下方输入文字命题，或点击 📎 按钮上传图片命题。',
              imageDataUrl: null
            }
          ];
          saveMessagesToStorage();
          inputText.value = '';
          selectedImage.value = null;
          showToast('已重置对局，新一轮大喜利已就绪');
        }

        // Auto-scroll chat container to bottom
        function scrollToBottom() {
          nextTick(() => {
            if (chatContainer.value) {
              chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
            }
          });
        }
