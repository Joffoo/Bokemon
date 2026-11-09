// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        function findHostMessage(playerMsg) {
          const idx = messages.value.findIndex(m => m.id === playerMsg.id);
          if (idx <= 0) return null;
          for (let i = idx - 1; i >= 0; i--) {
            if (messages.value[i].role === 'host') return messages.value[i];
          }
          return null;
        }

        // Manual Variant Crowning (Reversal Mechanism)
        async function crownManualVariant(msg, variantText, variantType) {
          if (!variantText) return;
          const cleaned = cleanPunchline(variantText);
          if (!cleaned) return;
          if (msg.champion === cleaned) {
            showToast(`当前主金句已是【${variantType}】`);
            return;
          }

          msg.champion = cleaned;
          // Re-render meme if picture question
          const hostMsg = findHostMessage(msg);
          const imgUrl = (hostMsg && hostMsg.imageDataUrl) || msg.imageDataUrl;
          if (imgUrl) {
            try {
              const memeUrl = await renderCanvasMeme(imgUrl, cleaned);
              msg.memeDataUrl = memeUrl;
            } catch (e) {
              console.error('Failed to re-render meme on manual crown', e);
            }
          }

          playChampionSound();
          showToast(`已将【${variantType}】平反加冕为全场总冠军！👑`);
        }

        // Re-roll Punchline reusing Stage 0 Telemetry
        function handleImageUpload(e) {
          const file = e.target.files && e.target.files[0];
          if (!file) return;

          const reader = new FileReader();
          reader.onload = (evt) => {
            const rawDataUrl = evt.target.result;
            const img = new Image();
            img.onload = () => {
              try {
                const maxDim = 1280;
                let w = img.naturalWidth || img.width || 600;
                let h = img.naturalHeight || img.height || 450;
                if (w > maxDim || h > maxDim) {
                  if (w > h) {
                    h = Math.round((h * maxDim) / w);
                    w = maxDim;
                  } else {
                    w = Math.round((w * maxDim) / h);
                    h = maxDim;
                  }
                }
                const canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, w, h);
                const compressedUrl = canvas.toDataURL('image/jpeg', 0.85);
                selectedImage.value = {
                  file: file,
                  name: file.name,
                  dataUrl: compressedUrl
                };
              } catch (err) {
                selectedImage.value = {
                  file: file,
                  name: file.name,
                  dataUrl: rawDataUrl
                };
              }
            };
            img.onerror = () => {
              selectedImage.value = {
                file: file,
                name: file.name,
                dataUrl: rawDataUrl
              };
            };
            img.src = rawDataUrl;
          };
          reader.readAsDataURL(file);
          e.target.value = '';
        }

        function clearSelectedImage() {
          selectedImage.value = null;
        }

        // Select Presets
        function selectPresetPrompt(item) {
          inputText.value = item.prompt || item.title;
          showPresetsModal.value = false;
        }

        function selectImagePreset(item) {
          selectedImage.value = {
            name: item.title,
            dataUrl: item.dataUrl
          };
          inputText.value = item.prompt || item.title;
          showPresetsModal.value = false;
        }

        // Fullscreen Image Preview
        function openImagePreview(url, title = '预览') {
          previewModal.url = url;
          previewModal.title = title;
          previewModal.visible = true;
        }

        function closeImagePreview() {
          previewModal.visible = false;
        }

        // Download Meme as PNG
        function downloadMeme(dataUrl) {
          if (!dataUrl) return;
          const a = document.createElement('a');
          const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
          a.download = `oogiri_meme_${timestamp}.png`;
          a.href = dataUrl;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          showToast('已开始下载压字 PNG');
        }

        // Auto-scroll chat container to bottom
