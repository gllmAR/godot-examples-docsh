# Pause Demo


    <div class="game-embed">
        <div class="embed-container" style="position: relative; width: 100%; max-width: 800px; margin: 20px auto;">
            <iframe 
                src="godot-demo-projects/misc/pause/exports/web/index.html" 
                width="800" 
                height="600"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 600px; border: 2px solid #478cbf; border-radius: 8px;">
            </iframe>
            <div class="embed-controls" style="text-align: center; margin-top: 10px;">
                <button onclick="toggleFullscreen()" class="control-btn">⛶ Fullscreen</button>
                <button onclick="reloadGame()" class="control-btn">🔄 Reload</button>
                <a href="godot-demo-projects/misc/pause/exports/web/index.html" target="_blank" class="control-btn">🔗 Open in New Tab</a>
            </div>
        </div>
    </div>
    
    <style>
        .game-embed {
            margin: 20px 0;
            text-align: center;
        }
        .embed-container {
            background: #f0f0f0;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .control-btn {
            background: #478cbf;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
        }
        .control-btn:hover {
            background: #3a7ca8;
        }
        @media (max-width: 768px) {
            .embed-container {
                padding: 10px;
            }
            .embed-container iframe {
                height: 400px;
            }
        }
    </style>
    
    <script>
        function toggleFullscreen() {
            const iframe = document.querySelector('.game-embed iframe');
            if (iframe.requestFullscreen) {
                iframe.requestFullscreen();
            } else if (iframe.webkitRequestFullscreen) {
                iframe.webkitRequestFullscreen();
            } else if (iframe.msRequestFullscreen) {
                iframe.msRequestFullscreen();
            }
        }
        
        function reloadGame() {
            const iframe = document.querySelector('.game-embed iframe');
            iframe.src = iframe.src;
        }
    </script>
    


A demo showing how a game made in Godot can be paused.

Language: GDScript

Renderer: Compatibility

Check out this demo on the asset library: https://godotengine.org/asset-library/asset/2790

## Screenshots

![Screenshot](screenshots/pause.png)
