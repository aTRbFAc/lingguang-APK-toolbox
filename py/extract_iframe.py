import html
import os
import sys
from playwright.sync_api import sync_playwright
from py.config import load_config

def extract_nested_iframe_content(url, output_filename="extracted_content.html"):
    """
    提取嵌套iframe中内部iframe的srcdoc内容：
    1. 查找具有sandbox="allow-scripts allow-same-origin"的iframe
    2. 在这个iframe内部查找另一个具有相同sandbox属性的iframe
    3. 保存内部iframe的srcdoc内容
    """
    try:
        print(f"[1/3] 正在启动 Playwright 浏览器引擎...")

        cfg = load_config()
        wait_ms = cfg["wait_time"] * 1000  # 使用设置中的等待时间

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

            print("等待页面完全渲染...")
            page.wait_for_timeout(wait_ms)

            print("[3/3] 开始查找嵌套的iframe并提取srcdoc内容...")

            result = page.evaluate("""
                () => {
                    const allIframes = document.querySelectorAll(
                        'iframe[sandbox="allow-scripts allow-same-origin"]'
                    );

                    for(const iframe of allIframes) {
                        console.log('找到外层iframe，尝试访问内容...');

                        let contentDoc = null;

                        try {
                            if(iframe.contentDocument) {
                                contentDoc = iframe.contentDocument;
                            } else if(iframe.contentWindow && iframe.contentWindow.document) {
                                contentDoc = iframe.contentWindow.document;
                            }
                        } catch(e) {
                            console.log('直接访问失败:', e.message);
                        }

                        if(!contentDoc && iframe.srcdoc) {
                            const parser = new DOMParser();
                            contentDoc = parser.parseFromString(iframe.srcdoc, 'text/html');
                        }

                        if(contentDoc) {
                            console.log('成功访问iframe内容文档');

                            const innerIframes = contentDoc.querySelectorAll(
                                'iframe[sandbox="allow-scripts allow-same-origin"]'
                            );

                            for(const innerIframe of innerIframes) {
                                console.log('找到内层符合条件的iframe');

                                const srcdoc = innerIframe.getAttribute('srcdoc');

                                if(srcdoc) {
                                    console.log('成功提取srcdoc内容');
                                    return {
                                        success: true,
                                        content: srcdoc,
                                        source: 'inner_iframe_srcdoc'
                                    };
                                }
                            }
                        }
                    }

                    return {
                        success: false,
                        content: null,
                        message: '未找到符合条件的嵌套iframe'
                    };
                }
            """)

            if result['success']:
                content = result['content']
                print(f"找到内容! 来源: {result['source']}")

                final_content = (
                    html.unescape(content)
                    if '<' in content and '&' in content
                    else content
                )

                return final_content
            else:
                print(f"{result['message']}")
                return None

            browser.close()

    except Exception as e:
        print(f"发生严重错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None
