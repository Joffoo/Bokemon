BK.buildSetupTail = function () {
// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        // Load configuration from localStorage on mount
        onMounted(() => {
          // 挂载完成才显示：避免脚本加载期间浏览器先渲染出未编译的 {{ }} 模板（闪屏）
          document.getElementById('app')?.classList.remove('invisible');
          try {
            const saved = localStorage.getItem('oogiri_flow_config');
            if (saved) {
              const parsed = JSON.parse(saved);
              Object.assign(config, parsed);
              Object.assign(tempConfig, parsed);
            }
            const cachedModels = localStorage.getItem('oogiri_cached_models');
            if (cachedModels) {
              fetchedModels.value = JSON.parse(cachedModels);
            }
          } catch (e) {
            console.warn('Failed to load config from localStorage', e);
          }
          if (messages.value.length > 1) {
            scrollToBottom();
          }
        });

        // Toast Helper
        const exportedBundle = {
          chatContainer,
          inputText,
          selectedImage,
          isGeneratingAny,
          pipelineMode,
          showSettingsModal,
          showPresetsModal,
          showApiKey,
          testingApi,
          testStatus,
          testMessage,
          fetchingModels,
          fetchedModels,
          showModelDropdown,
          modelSearchQuery,
          recommendedModels,
          filteredFetchedModels,
          fetchAvailableModels,
          previewModal,
          toast,
          config,
          tempConfig,
          soundEnabled,
          providerPresets,
          messages,
          textPresets,
          imagePresets,
          showToast,
          copyPunchline,
          saveSettings,
          openSettingsModal,
          closeSettingsModal,
          purgeCredentials,
          selectProvider,
          testApiConnection,
          handleImageUpload,
          clearSelectedImage,
          selectPresetPrompt,
          selectImagePreset,
          openImagePreview,
          closeImagePreview,
          downloadMeme,
          runMockPreset,
          handleSend,
          getStatusBadgeClass,
          getStatusText,
          toggleSound,
          playStartSound,
          playChampionSound,
          exportMarkdownHistory,
          resetNewGame,
          crownManualVariant,
          rerollPunchline,
          cleanPunchline,
          cleanDirectReply,
          sharePosterModal,
          openSharePosterModal,
          downloadSharePoster,
          renderSharePoster,
          saveMessagesToStorage
        };

        // Expose to window for testing
        window.oogiriStudio = exportedBundle;

        return exportedBundle;

        };