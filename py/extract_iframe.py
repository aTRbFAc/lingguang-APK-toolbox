import html
import os
import sys
from playwright.sync_api import sync_playwright
from py.config import load_config


def extract_nested_iframe_content(url, output_filename="extracted_content.html"):
    """
    提取嵌套 iframe 中内部 iframe 的 srcdoc 内容
    sandbox 只要包含 allow-scripts allow-same-origin 即算符合条件
    """
    try:
        print(f"[1/3] 正在启动 Playwright 浏览器引擎...")

        cfg = load_config()
        wait_ms = cfg["wait_time"] * 1000

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--allow-running-insecure-content'
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )

            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            print(f"[2/3] 正在访问网址: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=wait_ms)
            page.wait_for_timeout(wait_ms)

            print("[3/3] 开始查找嵌套 iframe 并提取 srcdoc 内容...")

            result = page.evaluate("""
                () => {
                    const hasWord = (attr, word) =>
                        attr && attr.split(/\\s+/).includes(word);

                    const matchIframe = (root) => {
                        return Array.from(root.querySelectorAll('iframe')).filter(f => {
                            const sb = f.getAttribute('sandbox');
                            return sb && hasWord(sb, 'allow-scripts') && hasWord(sb, 'allow-same-origin');
                        });
                    };

                    const allIframes = matchIframe(document);
                    console.log('[DEBUG] 外层 iframe 总数:', allIframes.length);

                    if (allIframes.length === 0) {
                        console.log('[DEBUG] ❌ 页面中没有找到任何符合条件的 iframe');
                        return {
                            success: false,
                            message: '未找到任何 sandbox 包含 allow-scripts allow-same-origin 的 iframe'
                        };
                    }

                    for (let i = 0; i < allIframes.length; i++) {
                        const iframe = allIframes[i];
                        console.log('[DEBUG] --------------------------');
                        console.log('[DEBUG] 正在处理第', i + 1, '个外层 iframe');
                        console.log('[DEBUG] iframe src:', iframe.src);
                        console.log('[DEBUG] iframe sandbox:', iframe.getAttribute('sandbox'));

                        let contentDoc = null;

                        try {
                            contentDoc = iframe.contentDocument || iframe.contentWindow?.document;
                            console.log('[DEBUG] ✅ 成功进入 iframe DOM');
                        } catch (e) {
                            console.log('[DEBUG] ❌ 无法进入 iframe DOM（跨域）:', e.message);
                        }

                        if (!contentDoc && iframe.srcdoc) {
                            console.log('[DEBUG] 尝试通过 srcdoc 解析 iframe 内容');
                            contentDoc = new DOMParser().parseFromString(iframe.srcdoc, 'text/html');
                        }

                        if (!contentDoc) {
                            console.log('[DEBUG] ❌ 无法获取 iframe 的 document，跳过');
                            continue;
                        }

                        const innerIframes = matchIframe(contentDoc);
                        console.log('[DEBUG] 内层 iframe 数量:', innerIframes.length);

                        if (innerIframes.length === 0) {
                            console.log('[DEBUG] ❌ 该 iframe 中未找到内层 iframe');
                            continue;
                        }

                        for (let j = 0; j < innerIframes.length; j++) {
                            const innerIframe = innerIframes[j];
                            console.log('[DEBUG] 检查第', j + 1, '个内层 iframe');
                            console.log('[DEBUG] 内层 iframe sandbox:', innerIframe.getAttribute('sandbox'));

                            const srcdoc = innerIframe.getAttribute('srcdoc');
                            if (srcdoc) {
                                console.log('[DEBUG] ✅ 成功提取 srcdoc');
                                return {
                                    success: true,
                                    content: srcdoc,
                                    source: 'inner_iframe_srcdoc'
                                };
                            } else {
                                console.log('[DEBUG] ❌ 该内层 iframe 没有 srcdoc');
                            }
                        }
                    }

                    console.log('[DEBUG] ❌ 所有 iframe 都检查完毕，未找到目标 srcdoc');
                    return {
                        success: false,
                        message: '未找到符合条件的嵌套 iframe'
                    };
                }
            """)

            if result and result.get('success'):
                content = result['content']
                print(f"✅ 找到内容! 来源: {result['source']}")

                final_content = (
                    html.unescape(content)
                    if '<' in content and '&' in content
                    else content
                )

                return final_content
            else:
                print(f"❌ {result.get('message', '未找到目标 iframe 或 srcdoc')}")
                return None

            browser.close()

    except Exception as e:
        print(f"发生严重错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None
