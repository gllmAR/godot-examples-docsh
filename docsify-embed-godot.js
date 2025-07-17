// Docsify plugin for initializing demo iframes
(function() {
  'use strict';
  
  // Toggle fullscreen for iframe with mobile support
  function toggleFullscreen(iframe) {
    if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement) {
      // Exit fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
      }
    } else {
      // Enter fullscreen
      if (isMobileDevice()) {
        // Mobile: Use custom fullscreen
        handleMobileFullscreen(iframe);
      } else {
        // Desktop: Try native fullscreen on iframe first, fallback to container
        var container = iframe.closest('.demo-container');
        
        // Try iframe fullscreen first
        var fullscreenPromise = null;
        if (iframe.requestFullscreen) {
          fullscreenPromise = iframe.requestFullscreen();
        } else if (iframe.webkitRequestFullscreen) {
          fullscreenPromise = iframe.webkitRequestFullscreen();
        } else if (iframe.mozRequestFullScreen) {
          fullscreenPromise = iframe.mozRequestFullScreen();
        }
        
        // If iframe fullscreen fails, try container fullscreen
        if (fullscreenPromise) {
          fullscreenPromise.catch(() => {
            tryContainerFullscreen(container);
          });
        } else {
          tryContainerFullscreen(container);
        }
      }
    }
  }

  // Toggle true fullscreen (native browser fullscreen)
  function toggleTrueFullscreen(iframe) {
    if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement) {
      // Exit fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
      }
    } else {
      // Enter true fullscreen - try iframe first, then container
      var container = iframe.closest('.demo-container');
      
      var fullscreenPromise = null;
      if (iframe.requestFullscreen) {
        fullscreenPromise = iframe.requestFullscreen();
      } else if (iframe.webkitRequestFullscreen) {
        fullscreenPromise = iframe.webkitRequestFullscreen();
      } else if (iframe.mozRequestFullScreen) {
        fullscreenPromise = iframe.mozRequestFullScreen();
      }
      
      // If iframe fullscreen fails, try container fullscreen
      if (fullscreenPromise) {
        fullscreenPromise.catch(() => {
          tryContainerFullscreen(container);
        });
      } else {
        tryContainerFullscreen(container);
      }
    }
  }

  // Toggle expanded view (mobile-style fullscreen)
  function toggleExpandedView(iframe) {
    handleMobileFullscreen(iframe);
  }

  // Legacy fullscreen function - now delegates to appropriate method
  function toggleFullscreen(iframe) {
    if (isMobileDevice()) {
      toggleExpandedView(iframe);
    } else {
      toggleTrueFullscreen(iframe);
    }
  }

  function tryContainerFullscreen(container) {
    if (container.requestFullscreen) {
      container.requestFullscreen().catch(() => {
        console.warn('Fullscreen not supported, using mobile fallback');
        handleMobileFullscreen(container.querySelector('iframe'));
      });
    } else if (container.webkitRequestFullscreen) {
      container.webkitRequestFullscreen();
    } else if (container.mozRequestFullScreen) {
      container.mozRequestFullScreen();
    } else {
      // Fallback to mobile-style fullscreen
      console.warn('Fullscreen not supported, using mobile fallback');
      handleMobileFullscreen(container.querySelector('iframe'));
    }
  }

  function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
           ('ontouchstart' in window) || 
           (window.innerWidth <= 768);
  }

  function handleMobileFullscreen(iframe) {
    // Mobile fullscreen fallback
    var container = iframe.closest('.demo-container');
    
    if (container.classList.contains('mobile-fullscreen')) {
      // Exit mobile fullscreen
      exitMobileFullscreen(container);
    } else {
      // Enter mobile fullscreen
      enterMobileFullscreen(container);
    }
  }

  function enterMobileFullscreen(container) {
    container.classList.add('mobile-fullscreen');
    document.body.classList.add('mobile-fullscreen-active');
    
    // Lock scroll
    document.body.style.overflow = 'hidden';
    
    // Try to hide address bar on mobile
    if (window.screen && window.screen.orientation) {
      // Modern mobile browsers
      setTimeout(() => {
        window.scrollTo(0, 1);
      }, 100);
    }
    
    // Update all buttons
    updateFullscreenButtons(container);
  }

  function exitMobileFullscreen(container) {
    container.classList.remove('mobile-fullscreen');
    document.body.classList.remove('mobile-fullscreen-active');
    
    // Restore scroll
    document.body.style.overflow = '';
    
    // Update all buttons
    updateFullscreenButtons(container);
  }

  // Update button text for all fullscreen buttons
  function updateFullscreenButtons(container) {
    var isNativeFullscreen = document.fullscreenElement || 
                            document.webkitFullscreenElement || 
                            document.mozFullScreenElement;
    var isMobileFullscreen = container && container.classList.contains('mobile-fullscreen');
    
    // Update true fullscreen button
    var trueFullscreenBtn = container.querySelector('.btn-true-fullscreen');
    if (trueFullscreenBtn) {
      trueFullscreenBtn.textContent = isNativeFullscreen ? '⛶' : '⛶';
      trueFullscreenBtn.title = isNativeFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen (Native)';
    }
    
    // Update expanded view button - icon changes based on state
    var expandedBtn = container.querySelector('.btn-expanded');
    if (expandedBtn) {
      if (isMobileFullscreen) {
        expandedBtn.textContent = '⇲';  // Contract/minimize icon
        expandedBtn.title = 'Exit Expanded View';
      } else {
        expandedBtn.textContent = '⇱';  // Expand icon
        expandedBtn.title = 'Expanded View';
      }
    }
    
    // Update legacy fullscreen button (if exists)
    var fullscreenBtn = container.querySelector('.btn-fullscreen');
    if (fullscreenBtn) {
      var isFullscreen = isNativeFullscreen || isMobileFullscreen;
      fullscreenBtn.textContent = isFullscreen ? '⛶' : '⛶';
      fullscreenBtn.title = isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen';
    }
  }
  
  // Simple demo controls setup with mobile enhancements
  function setupDemoControls(iframeId, fullscreenBtnId, popoutBtnId, demoUrl, sceneName) {
    var iframe = document.getElementById(iframeId);
    var fullscreenBtn = document.getElementById(fullscreenBtnId);
    var popoutBtn = document.getElementById(popoutBtnId);
    
    // Get additional buttons
    var trueFullscreenBtn = document.getElementById(fullscreenBtnId.replace('fullscreen', 'true-fullscreen'));
    var expandedBtn = document.getElementById(fullscreenBtnId.replace('fullscreen', 'expanded'));
    
    if (!iframe || !popoutBtn) return;
    
    var container = iframe.closest('.demo-container');
    
    // True fullscreen functionality (desktop native)
    if (trueFullscreenBtn) {
      trueFullscreenBtn.addEventListener('click', function() {
        toggleTrueFullscreen(iframe);
      });
    }
    
    // Expanded view functionality (mobile-style)
    if (expandedBtn) {
      expandedBtn.addEventListener('click', function() {
        toggleExpandedView(iframe);
      });
    }
    
    // Legacy fullscreen functionality
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', function() {
        toggleFullscreen(iframe);
      });
    }
    
    // Pop-out functionality with mobile adjustments
    popoutBtn.addEventListener('click', function() {
      if (isMobileDevice()) {
        window.open(demoUrl, '_blank');
      } else {
        window.open(demoUrl, `demo-${sceneName}`, 'width=1000,height=800,scrollbars=yes,resizable=yes');
      }
    });
    
    // Listen for fullscreen changes (all vendors)
    document.addEventListener('fullscreenchange', function() {
      updateFullscreenButtons(container);
    });
    document.addEventListener('webkitfullscreenchange', function() {
      updateFullscreenButtons(container);
    });
    document.addEventListener('mozfullscreenchange', function() {
      updateFullscreenButtons(container);
    });
    
    // Listen for escape key to exit mobile fullscreen
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        if (container && container.classList.contains('mobile-fullscreen')) {
          exitMobileFullscreen(container);
        }
      }
    });
    
    // Add touch gesture support for mobile fullscreen
    if (isMobileDevice()) {
      addMobileTouchSupport(iframe);
    }
  }

  function addMobileTouchSupport(iframe) {
    var doubleTapTimeout;
    var lastTap = 0;
    
    iframe.addEventListener('touchend', function(e) {
      var currentTime = new Date().getTime();
      var tapLength = currentTime - lastTap;
      
      if (tapLength < 500 && tapLength > 0) {
        // Double tap detected
        e.preventDefault();
        toggleFullscreen(iframe);
      }
      
      lastTap = currentTime;
    });
  }

  // State management
  const processedMarkers = new Set();

  // Extract current path from window location
  function getCurrentScenePath() {
    var currentHash = window.location.hash.substring(1);
    console.log('🔍 getCurrentScenePath - hash:', currentHash);
    
    if (!currentHash) {
      console.warn('No hash found in URL');
      return null;
    }
    
    // Remove .md extension if present
    currentHash = currentHash.replace(/\.md$/, '');
    
    // Remove leading slash if present
    if (currentHash.startsWith('/')) {
      currentHash = currentHash.substring(1);
    }
    
    // Remove trailing slash if present
    if (currentHash.endsWith('/')) {
      currentHash = currentHash.substring(0, currentHash.length - 1);
    }
    
    // Strategy 1: Look for original docsify-godot-embed patterns like:
    // gdEmbed/scenes/category/scene_name/README
    // scenes/category/scene_name/README  
    // gdEmbed/scenes/category/scene_name
    // scenes/category/scene_name
    var originalPathMatch = currentHash.match(/(?:gdEmbed\/)?scenes\/([^\/]+)\/([^\/]+)(?:\/(?:README|index)?)?$/);
    
    if (originalPathMatch) {
      var category = originalPathMatch[1];
      var sceneName = originalPathMatch[2];
      var scenePath = category + '/' + sceneName;
      console.log('✅ Extracted original format scene path:', scenePath);
      return scenePath;
    }
    
    // Strategy 2: Look for general project structures like:
    // godot-demo-projects/2d/bullet_shower
    // godot-examples/category/project_name
    // any-repo/category/project_name
    var generalPathMatch = currentHash.match(/([^\/]+)\/([^\/]+)\/([^\/]+)(?:\/(?:README|index)?)?$/);
    
    if (generalPathMatch) {
      var repo = generalPathMatch[1];
      var category = generalPathMatch[2];
      var projectName = generalPathMatch[3];
      
      // For general structures, we'll use category/project_name as the scene path
      var scenePath = category + '/' + projectName;
      console.log('✅ Extracted general format scene path:', scenePath);
      return scenePath;
    }
    
    // Strategy 3: Fallback for simpler structures - use the last two path segments
    var pathSegments = currentHash.split('/').filter(segment => segment && segment !== 'README' && segment !== 'index');
    
    if (pathSegments.length >= 2) {
      var scenePath = pathSegments.slice(-2).join('/');
      console.log('✅ Extracted fallback scene path:', scenePath);
      return scenePath;
    }
    
    console.warn('Could not extract scene path from hash:', currentHash);
    return null;
  }

  function initializeDemoEmbeds() {
    // Find all embed markers
    var embedMarkers = document.evaluate(
      '//comment()[contains(., "embed-")]',
      document,
      null,
      XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE,
      null
    );
    
    if (embedMarkers.snapshotLength === 0) {
      return;
    }
    
    // Get base URL
    var baseUrl = window.location.href.split('#')[0].replace(/\/index\.html$/, '/');
    if (!baseUrl.endsWith('/')) baseUrl += '/';
    
    // Process each marker
    for (let i = 0; i < embedMarkers.snapshotLength; i++) {
      processEmbed(embedMarkers.snapshotItem(i), baseUrl);
    }
  }

  function processEmbed(marker, baseUrl) {
    var markerText = marker.textContent.trim();
    
    var markerId = markerText + '_' + Date.now();
    
    // Skip if already processed
    if (processedMarkers.has(markerId)) {
      return;
    }
    processedMarkers.add(markerId);
    
    // Check if container already exists
    const nextSibling = marker.nextSibling;
    if (nextSibling && nextSibling.classList && nextSibling.classList.contains('demo-container')) {
      return;
    }
    console.log('🎮 Processing embed marker:', markerText);
    
    // Handle the new {$PATH} syntax: <!-- embed-{$PATH} -->
    if (markerText === 'embed-{$PATH}') {
      console.log('🎯 Processing {$PATH} embed');
      
      var scenePath = getCurrentScenePath();
      if (!scenePath) {
        console.error('❌ Could not determine scene path for {$PATH}');
        insertErrorMessage(marker, 'Could not determine scene path from current location');
        return;
      }
      
      var sceneName = scenePath.split('/').pop();
      
      // Determine the demo path based on repository structure
      var currentHash = window.location.hash.substring(1);
      var demoPath;
      
      console.log('🔍 Current hash for path determination:', currentHash);
      
      // Strategy 1: gdEmbed structure - check if path contains gdEmbed or scenes
      if (currentHash.includes('gdEmbed') || currentHash.includes('/scenes/')) {
        demoPath = `godot-demo-extended/gdEmbed/exports/web/?scene=${encodeURIComponent(scenePath)}`;
        console.log('📍 Using gdEmbed strategy');
      } 
      // Strategy 2: Individual project structure (like godot-demo-projects)
      else {
        // For individual projects, construct path to the current project's exports
        // Remove leading slash and trailing slash/README
        var cleanHash = currentHash.replace(/^\//, '').replace(/\/(README)?$/, '');
        demoPath = `${cleanHash}/exports/web/`;
        console.log('📍 Using individual project strategy');
      }
      
      var fullDemoUrl = baseUrl + demoPath;
      
      console.log('✅ {$PATH} resolved to:', scenePath);
      console.log('🔗 Demo URL:', fullDemoUrl);
      console.log('🔗 Full demo path construction:', {
        baseUrl: baseUrl,
        currentHash: currentHash,
        cleanHash: currentHash.replace(/^\//, '').replace(/\/(README)?$/, ''),
        demoPath: demoPath,
        fullDemoUrl: fullDemoUrl
      });
      
      createEmbedContainer(marker, fullDemoUrl, sceneName, scenePath, true);
      return;
    }
    
    // Parse other marker formats - support the {project_path} format
    var embedMatch = markerText.match(/embed-\{([^}]+)\}/);
    if (embedMatch) {
      var projectPath = embedMatch[1];
      console.log('🎯 Processing project path embed:', projectPath);
      
      var pathParts = projectPath.split('/');
      var sceneName = pathParts[pathParts.length - 1];
      
      // For project path format, construct direct path to exports
      var demoPath = `${projectPath}/exports/web/`;
      var fullDemoUrl = baseUrl + demoPath;
      
      console.log('✅ Project path resolved to:', projectPath);
      console.log('🔗 Demo URL:', fullDemoUrl);
      
      createEmbedContainer(marker, fullDemoUrl, sceneName, projectPath, true);
      return;
    }
    
    // Legacy support for other formats
    var legacyMatch = markerText.match(/embed-([a-zA-Z0-9_-]+)(?:\s*:\s*(.+))?/);
    if (!legacyMatch) {
      console.warn('Invalid embed format:', markerText);
      insertErrorMessage(marker, `Invalid embed format: ${markerText}`);
      return;
    }
    
    var projectName = legacyMatch[1];
    var embedPath = legacyMatch[2];
    
    var sceneName, fullScenePath, demoPath;
    
    if (!embedPath) {
      // Simple embed format: <!-- embed-projectName -->
      sceneName = `${projectName} Project`;
      fullScenePath = '';
      demoPath = `${projectName}/exports/web/`;
    } else {
      // Full embed format with specific scene path
      embedPath = embedPath.trim();
      
      // Handle path expansion for {$PATH} substitution
      if (embedPath.startsWith('{$PATH}/')) {
        var currentScenePath = getCurrentScenePath();
        if (!currentScenePath) {
          console.warn('Could not determine current path for {$PATH} expansion');
          insertErrorMessage(marker, 'Could not determine current path for {$PATH} expansion');
          return;
        }
        
        embedPath = embedPath.replace('{$PATH}', 'scenes/' + currentScenePath);
      }
      
      var pathParts = embedPath.split('/');
      
      if (pathParts.length < 4) {
        console.warn('Invalid embed path format:', embedPath);
        return;
      }
      
      var category = pathParts[1];
      var sceneFolder = pathParts[2];
      sceneName = pathParts[3];
      
      var scenePath = `${category}/${sceneFolder}`;
      demoPath = `${projectName}/exports/web/?scene=${encodeURIComponent(scenePath)}`;
    }
    
    // Build demo URL
    var fullDemoUrl = baseUrl + demoPath;
    
    createEmbedContainer(marker, fullDemoUrl, sceneName, embedPath || projectName, !embedPath);
  }

  // Helper function to insert error messages
  function insertErrorMessage(marker, message) {
    var errorDiv = document.createElement('div');
    errorDiv.className = 'embed-error';
    errorDiv.style.cssText = 'background: #fee; border: 1px solid #fcc; border-radius: 4px; padding: 12px; margin: 16px 0; color: #c33;';
    errorDiv.innerHTML = `⚠️ Embed Error: ${message}`;
    marker.parentNode.insertBefore(errorDiv, marker.nextSibling);
  }

  // Helper function to create embed container
  function createEmbedContainer(marker, fullDemoUrl, sceneName, embedPath, isProjectEmbed) {
    // Create container
    var container = document.createElement('div');
    container.className = 'demo-container';
    
    if (isProjectEmbed) {
      container.classList.add('demo-project-embed');
    }
    
    var iframeId = `demo-iframe-${sceneName.replace(/\s+/g, '-')}-${Date.now()}`;
    var fullscreenBtnId = `fullscreen-btn-${sceneName.replace(/\s+/g, '-')}-${Date.now()}`;
    var trueFullscreenBtnId = `true-fullscreen-btn-${sceneName.replace(/\s+/g, '-')}-${Date.now()}`;
    var expandedBtnId = `expanded-btn-${sceneName.replace(/\s+/g, '-')}-${Date.now()}`;
    var popoutBtnId = `popout-btn-${sceneName.replace(/\s+/g, '-')}-${Date.now()}`;

    var headerTitle = `🎮 Interactive Demo: ${sceneName}`;
    var instructions = 'Interactive demo';

    // Create control buttons based on device type
    var controlButtons = '';
    if (isMobileDevice()) {
      // Mobile: Show expanded view and pop-out
      controlButtons = `
        <button id="${expandedBtnId}" class="btn-expanded" title="Expanded View">⇱</button>
        <button id="${popoutBtnId}" class="btn-popout" title="Open in New Tab">↗</button>
      `;
    } else {
      // Desktop: Show all three options in order [expand][fullscreen][pop out]
      controlButtons = `
        <button id="${expandedBtnId}" class="btn-expanded" title="Expanded View">⇱</button>
        <button id="${trueFullscreenBtnId}" class="btn-true-fullscreen" title="Enter Fullscreen (Native)">⛶</button>
        <button id="${popoutBtnId}" class="btn-popout" title="Open in New Window">↗</button>
      `;
    }

    container.innerHTML = `
      <div class="demo-header">
        <h3>${headerTitle}</h3>
        <div class="demo-controls">
          ${controlButtons}
        </div>
      </div>
      <div class="iframe-wrapper">
        <iframe 
          id="${iframeId}" 
          src="${fullDemoUrl}"
          width="800" 
          height="600" 
          frameborder="0"
          allowfullscreen="true">
          <p>Your browser does not support iframes. <a href="${fullDemoUrl}" target="_blank">Open demo in new tab</a></p>
        </iframe>
      </div>
      <p class="demo-instructions">${instructions}</p>
    `;
    
    // Insert container after marker
    marker.parentNode.insertBefore(container, marker.nextSibling);
    
    // Setup controls
    setTimeout(() => {
      setupDemoControls(iframeId, fullscreenBtnId, popoutBtnId, fullDemoUrl, sceneName);
    }, 100);
  }
  
  // Plugin initialization
  function initializePlugin() {
    // Clear processed markers on route change
    processedMarkers.clear();
    
    // Initialize embeds after DOM is ready
    setTimeout(initializeDemoEmbeds, 100);
  }
  
  // Register Docsify plugin
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function(hook) {
    hook.doneEach(initializePlugin);
  });
  
  // Monitor hash changes for SPA navigation
  window.addEventListener('hashchange', () => {
    setTimeout(initializePlugin, 200);
  });
  
  console.log('🎮 Demo embed plugin loaded');
})();
