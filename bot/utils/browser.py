from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
from bot.models import KongUser

#   ------------------------------add_init_script


def browser_init_script() -> str:
    return """
        Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
        Object.defineProperty(document, 'hidden', { get: () => false });
        document.addEventListener('visibilitychange', e => e.stopImmediatePropagation(), true);

        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {} };
    """


def speed_init_script() -> str:
    return """
    (() => {
        const originalClearInterval = window.clearInterval;
        const originalClearTimeout = window.clearTimeout;
        const originalSetInterval = window.setInterval;
        const originalSetTimeout = window.setTimeout;
        const originalPerformanceNow = window.performance.now.bind(window.performance);
        const originalDateNow = Date.now;
        const originalRAF = window.requestAnimationFrame;

        let cfg = {
            speed: 1,
            interval: true,
            timeout: true,
            performanceNow: true,
            dateNow: true,
            raf: true,
        };
        
        window.__nativePerfNow = originalPerformanceNow;
        window.__setSpeed = (multiplier) => {
            const validateSpeed = (s) => (s > 0 ? s : 1);

            cfg.speed = validateSpeed(multiplier);
            reloadTimers();
        };
        window.__getSpeed = () => cfg.speed;

        // --- setInterval ---
        let timers = [];
        const reloadTimers = () => {
            const newTimers = [];
            timers.forEach((timer) => {
                originalClearInterval(timer.id);
                if (timer.customTimerId) originalClearInterval(timer.customTimerId);
                if (!timer.finished) {
                    const newId = originalSetInterval(
                        timer.handler,
                        cfg.interval ? timer.timeout / cfg.speed : timer.timeout,
                        ...timer.args
                    );
                    timer.customTimerId = newId;
                    newTimers.push(timer);
                }
            });
            timers = newTimers;
        };

        window.clearInterval = (id) => {
            originalClearInterval(id);
            timers.forEach((t) => {
                if (t.id == id) {
                    t.finished = true;
                    if (t.customTimerId) originalClearInterval(t.customTimerId);
                }
            });
        };

        window.clearTimeout = (id) => {
            originalClearTimeout(id);
        };

        window.setInterval = (handler, timeout, ...args) => {
            if (!timeout) timeout = 0;
            const id = originalSetInterval(
                handler,
                cfg.interval ? timeout / cfg.speed : timeout,
                ...args
            );
            timers.push({ id, handler, timeout, args, finished: false, customTimerId: null });
            return id;
        };

        window.setTimeout = (handler, timeout, ...args) => {
            if (!timeout) timeout = 0;
            return originalSetTimeout(
                handler,
                cfg.timeout ? timeout / cfg.speed : timeout,
                ...args
            );
        };

        // --- performance.now ---
        (() => {
            let value = null;
            let prev = null;
            window.performance.now = () => {
                const real = originalPerformanceNow();
                if (value !== null) {
                    value += (real - prev) * (cfg.performanceNow ? cfg.speed : 1);
                } else {
                    value = real;
                }
                prev = real;
                return Math.floor(value);
            };
        })();

        // --- Date.now ---
        (() => {
            let value = null;
            let prev = null;
            Date.now = () => {
                const real = originalDateNow();
                if (value !== null) {
                    value += (real - prev) * (cfg.dateNow ? cfg.speed : 1);
                } else {
                    value = real;
                }
                prev = real;
                return Math.floor(value);
            };
        })();

        // --- requestAnimationFrame ---
        window.requestAnimationFrame = (callback) => {
            return originalRAF((timestamp) => {
                if (cfg.raf) {
                    callback(window.performance.now());
                } else {
                    callback(timestamp);
                }
            });
        };
    })();
    """


def preserve_drawing_buffer_script() -> str:
    return """
        (() => {
            const origGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, attrs) {
                if (type === 'webgl' || type === 'webgl2') {
                    attrs = attrs || {};
                    attrs.preserveDrawingBuffer = true;
                }
                return origGetContext.call(this, type, attrs);
            };
        })();
    """


#   ------------------------------evaluate
def speed_apply_script(multiplier: float) -> str:
    return f"""
    (() => {{
        window.__setSpeed({multiplier})
    }})();
    """


def inject_fps_counter_script() -> str:
    return """
        (() => {
            if (document.getElementById('__fps_overlay')) return;

            const nativeNow = window.__nativePerfNow || window.performance.now.bind(window.performance);

            const overlay = document.createElement('div');
            overlay.id = '__fps_overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 8px;
                left: 8px;
                background: rgba(0,0,0,0.6);
                color: #00ff88;
                font: bold 12px monospace;
                padding: 3px 7px;
                border-radius: 4px;
                z-index: 99999;
                pointer-events: none;
                user-select: none;
            `;
            overlay.textContent = 'FPS: --';
            document.body.appendChild(overlay);

            let frames = 0;
            let lastTime = nativeNow();

            const origRAF = window.requestAnimationFrame;
            const tick = () => {
                frames++;
                const now = nativeNow();
                const elapsed = now - lastTime;
                if (elapsed >= 500) {
                    const fps = (frames / elapsed * 1000).toFixed(0);
                    overlay.textContent = `FPS: ${fps}`;
                    frames = 0;
                    lastTime = now;
                }
                origRAF(tick);
            };
            origRAF(tick);
        })();
    """


def inject_speed_display_script() -> str:
    return """
        (() => {
            if (document.getElementById('__speed_overlay')) return;

            const overlay = document.createElement('div');
            overlay.id = '__speed_overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 30px;
                left: 8px;
                background: rgba(0,0,0,0.6);
                color: #ffaa00;
                font: bold 12px monospace;
                padding: 3px 7px;
                border-radius: 4px;
                z-index: 99999;
                pointer-events: none;
                user-select: none;
            `;
            overlay.textContent = 'Speed: 1.0x';
            document.body.appendChild(overlay);

            const updateSpeed = () => {
                const speed = window.__getSpeed ? window.__getSpeed() : 1;
                overlay.textContent = `Speed: ${speed.toFixed(1)}x`;
            };

            updateSpeed();
            setInterval(updateSpeed, 100);
        })();
    """


def inject_task_display_script(task_name: str) -> str:
    return f"""
        (() => {{
            const overlayId = '__task_overlay';
            let overlay = document.getElementById(overlayId);
            if (!overlay) {{
                overlay = document.createElement('div');
                overlay.id = overlayId;
                overlay.style.cssText = `
                    position: fixed;
                    top: 52px;   /* below the speed overlay (if used) */
                    left: 8px;
                    background: rgba(0,0,0,0.6);
                    color: #00ccff;
                    font: bold 12px monospace;
                    padding: 3px 7px;
                    border-radius: 4px;
                    z-index: 99999;
                    pointer-events: none;
                    user-select: none;
                `;
                document.body.appendChild(overlay);
            }}
            overlay.textContent = 'Task: {task_name}';
        }})();
    """

#   ------------------------------functions


async def get_uid_token() -> KongUser:
    url = "https://www.kongregate.com/en/games/juppiomenz/bit-heroes"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel="chromium", headless=False)
        page = await browser.new_page()

        async with page.expect_response(
            lambda response: "kongregate_user_id=" in response.url,
            timeout=0
        ) as response_info:
            await page.goto(url)

        response = await response_info.value
        params = parse_qs(urlparse(response.url).query)

        uid = params.get("kongregate_user_id", [None])[0]
        token = params.get("kongregate_game_auth_token", [None])[0]

        if not uid or not token:
            raise ValueError("uid or token not found")

        await browser.close()
        return KongUser(uid, token)


def to_keyboard_key(key: str, keyboard_map: dict[str, str]) -> str:
    if key in keyboard_map:
        return keyboard_map[key]
    raise ValueError(f"Key {key} not found in keyboard mapping")
