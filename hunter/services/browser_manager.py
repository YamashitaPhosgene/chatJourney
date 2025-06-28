import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, BrowserContext, Page
from ..config.settings import HunterConfig

logger = logging.getLogger(__name__)

class BrowserManager:
    """浏览器管理器，负责浏览器的生命周期管理"""
    
    def __init__(self):
        self.browser_context: Optional[BrowserContext] = None
        self.main_page: Optional[Page] = None
        self.is_logged_in: bool = False
        self._lock = asyncio.Lock()
        self._playwright = None
        
        # 确保目录存在
        HunterConfig.ensure_directories()
    
    async def initialize(self) -> bool:
        """初始化浏览器"""
        async with self._lock:
            try:
                if self.browser_context is None:
                    logger.info("正在初始化浏览器...")
                    
                    # 启动 Playwright
                    self._playwright = await async_playwright().start()
                    
                    # 启动浏览器
                    self.browser_context = await self._playwright.chromium.launch_persistent_context(
                        user_data_dir=str(HunterConfig.BROWSER_DATA_DIR),
                        headless=HunterConfig.BROWSER_HEADLESS,
                        viewport=HunterConfig.BROWSER_VIEWPORT,
                        timeout=HunterConfig.BROWSER_TIMEOUT
                    )
                    
                    # 获取主页面
                    if self.browser_context.pages:
                        self.main_page = self.browser_context.pages[0]
                    else:
                        self.main_page = await self.browser_context.new_page()
                    
                    # 设置页面超时
                    self.main_page.set_default_timeout(HunterConfig.BROWSER_TIMEOUT)
                    
                    logger.info("浏览器初始化完成")
                    return True
                else:
                    logger.info("浏览器已初始化")
                    return True
                    
            except Exception as e:
                logger.error(f"浏览器初始化失败: {e}")
                return False
    
    async def ensure_login(self) -> bool:
        """确保登录状态"""
        if self.is_logged_in:
            return True
        
        if not self.main_page:
            logger.error("浏览器未初始化")
            return False
        
        try:
            # 访问小红书首页
            await self.main_page.goto(HunterConfig.XIAOHONGSHU_BASE_URL, timeout=HunterConfig.BROWSER_TIMEOUT)
            await asyncio.sleep(3)
            
            # 检查是否已登录
            login_elements = await self.main_page.query_selector_all('text="登录"')
            if not login_elements:
                self.is_logged_in = True
                logger.info("已检测到登录状态")
                return True
            else:
                logger.info("需要登录，请手动完成登录操作")
                return False
                
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    async def login(self) -> str:
        """登录小红书账号"""
        if self.is_logged_in:
            return "已登录小红书账号"
        
        if not self.main_page:
            return "浏览器初始化失败，请重试"
        
        try:
            # 访问小红书首页
            await self.main_page.goto(HunterConfig.XIAOHONGSHU_BASE_URL, timeout=HunterConfig.BROWSER_TIMEOUT)
            await asyncio.sleep(3)
            
            # 查找登录按钮并点击
            login_elements = await self.main_page.query_selector_all('text="登录"')
            if login_elements:
                await login_elements[0].click()
                
                # 等待用户手动登录
                max_wait_time = HunterConfig.XIAOHONGSHU_LOGIN_TIMEOUT
                wait_interval = 5
                waited_time = 0
                
                while waited_time < max_wait_time:
                    # 检查是否已登录成功
                    still_login = await self.main_page.query_selector_all('text="登录"')
                    if not still_login:
                        self.is_logged_in = True
                        await asyncio.sleep(2)
                        logger.info("登录成功")
                        return "登录成功！"
                    
                    # 继续等待
                    await asyncio.sleep(wait_interval)
                    waited_time += wait_interval
                
                return "登录等待超时。请重试或手动登录后再使用其他功能。"
            else:
                self.is_logged_in = True
                return "已登录小红书账号"
                
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return f"登录失败: {str(e)}"
    
    async def search_notes(self, keywords: str, limit: int = 5) -> str:
        """搜索笔记"""
        if not await self.ensure_login():
            return "请先登录小红书账号"
        
        if not self.main_page:
            return "浏览器初始化失败，请重试"
        
        try:
            # 构建搜索URL并访问
            search_url = f"{HunterConfig.XIAOHONGSHU_BASE_URL}/search_result?keyword={keywords}"
            await self.main_page.goto(search_url, timeout=HunterConfig.BROWSER_TIMEOUT)
            await asyncio.sleep(HunterConfig.SEARCH_WAIT_TIME)
            
            # 等待页面完全加载
            await asyncio.sleep(HunterConfig.SEARCH_WAIT_TIME)
            
            # 获取帖子卡片
            post_cards = await self.main_page.query_selector_all('section.note-item')
            if not post_cards:
                post_cards = await self.main_page.query_selector_all('div[data-v-a264b01a]')
            
            post_links = []
            post_titles = []
            
            for card in post_cards:
                try:
                    # 获取链接
                    link_element = await card.query_selector('a[href*="/search_result/"]')
                    if not link_element:
                        continue
                    
                    href = await link_element.get_attribute('href')
                    if href and '/search_result/' in href:
                        # 构建完整URL
                        if href.startswith('/'):
                            full_url = f"{HunterConfig.XIAOHONGSHU_BASE_URL}{href}"
                        else:
                            full_url = href
                            
                        post_links.append(full_url)
                        
                        # 获取标题
                        title = "未知标题"
                        title_element = await card.query_selector('div.footer a.title span')
                        if title_element:
                            title_text = await title_element.text_content()
                            if title_text:
                                title = title_text.strip()
                        
                        post_titles.append(title)
                except Exception as e:
                    logger.error(f"处理帖子卡片时出错: {e}")
                    continue
            
            # 去重并限制数量
            unique_posts = []
            seen_urls = set()
            for url, title in zip(post_links, post_titles):
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_posts.append({"url": url, "title": title})
            
            unique_posts = unique_posts[:limit]
            
            # 格式化返回结果
            if unique_posts:
                result = "搜索结果：\n\n"
                for i, post in enumerate(unique_posts, 1):
                    result += f"{i}. {post['title']}\n   链接: {post['url']}\n\n"
                return result
            else:
                return f"未找到与\"{keywords}\"相关的笔记"
                
        except Exception as e:
            logger.error(f"搜索笔记时出错: {e}")
            return f"搜索笔记时出错: {str(e)}"
    
    async def get_note_content(self, url: str) -> str:
        """获取笔记内容"""
        if not await self.ensure_login():
            return "请先登录小红书账号"
        
        if not self.main_page:
            return "浏览器初始化失败，请重试"
        
        try:
            # 验证URL
            if not url or not url.strip():
                return "URL不能为空"
            
            # 处理URL
            try:
            processed_url = self._process_url(url)
            except ValueError as e:
                return f"URL格式错误: {str(e)}"
            
            logger.info(f"访问URL: {processed_url}")
            
            # 访问帖子链接
            await self.main_page.goto(processed_url, timeout=HunterConfig.BROWSER_TIMEOUT)
            await asyncio.sleep(10)
            
            # 检查错误页面
            error_page = await self.main_page.evaluate('''
                () => {
                    const errorTexts = [
                        "当前笔记暂时无法浏览",
                        "内容不存在",
                        "页面不存在",
                        "内容已被删除"
                    ];
                    
                    for (const text of errorTexts) {
                        if (document.body.innerText.includes(text)) {
                            return { isError: true, errorText: text };
                        }
                    }
                    return { isError: false };
                }
            ''')
            
            if error_page.get("isError", False):
                return f"无法获取笔记内容: {error_page.get('errorText', '未知错误')}"
            
            # 滚动页面加载内容
            await self.main_page.evaluate('''
                () => {
                    window.scrollTo(0, document.body.scrollHeight);
                    setTimeout(() => { 
                        window.scrollTo(0, document.body.scrollHeight / 2); 
                    }, 1000);
                    setTimeout(() => { 
                        window.scrollTo(0, 0); 
                    }, 2000);
                }
            ''')
            await asyncio.sleep(3)
            
            # 获取内容
            post_content = {}
            
            # 获取标题
            title_element = await self.main_page.query_selector('#detail-title')
            if title_element:
                title = await title_element.text_content()
                post_content["标题"] = title.strip() if title else "未知标题"
            else:
                post_content["标题"] = "未知标题"
            
            # 获取作者
            author_element = await self.main_page.query_selector('span.username')
            if author_element:
                author = await author_element.text_content()
                post_content["作者"] = author.strip() if author else "未知作者"
            else:
                post_content["作者"] = "未知作者"
            
            # 获取发布时间
            time_element = await self.main_page.query_selector('span.date')
            if time_element:
                time_text = await time_element.text_content()
                post_content["发布时间"] = time_text.strip() if time_text else "未知"
            else:
                post_content["发布时间"] = "未知"
            
            # 获取点赞数
            likes = 0
            try:
                # 尝试多种点赞数选择器
                likes_selectors = [
                    'span.like-count',
                    'div.like-count',
                    'span[data-v-*]',  # 动态属性选择器
                    'div[class*="like"]',
                    'span[class*="like"]',
                    'div[class*="count"]',
                    'span[class*="count"]'
                ]
                
                for selector in likes_selectors:
                    try:
                        likes_element = await self.main_page.query_selector(selector)
                        if likes_element:
                            likes_text = await likes_element.text_content()
                            if likes_text:
                                # 提取数字
                                import re
                                likes_match = re.search(r'(\d+)', likes_text)
                                if likes_match:
                                    likes = int(likes_match.group(1))
                                    logger.info(f"找到点赞数: {likes}")
                                    break
                    except Exception as e:
                        logger.debug(f"尝试选择器 {selector} 失败: {e}")
                        continue
                
                # 如果上面的方法都失败了，尝试使用JavaScript
                if likes == 0:
                    likes = await self.main_page.evaluate('''
                        () => {
                            // 尝试多种可能的点赞数选择器
                            const selectors = [
                                'span.like-count',
                                'div.like-count',
                                '[class*="like"]',
                                '[class*="count"]',
                                'span[data-v-*]'
                            ];
                            
                            for (const selector of selectors) {
                                const elements = document.querySelectorAll(selector);
                                for (const el of elements) {
                                    const text = el.textContent.trim();
                                    if (text && /\\d+/.test(text)) {
                                        const match = text.match(/(\\d+)/);
                                        if (match) {
                                            return parseInt(match[1]);
                                        }
                                    }
                                }
                            }
                            
                            // 尝试查找包含"赞"字的元素
                            const likeElements = document.querySelectorAll('*');
                            for (const el of likeElements) {
                                const text = el.textContent.trim();
                                if (text && text.includes('赞') && /\\d+/.test(text)) {
                                    const match = text.match(/(\\d+)/);
                                    if (match) {
                                        return parseInt(match[1]);
                                    }
                                }
                            }
                            
                            return 0;
                        }
                    ''')
                    
            except Exception as e:
                logger.error(f"获取点赞数失败: {e}")
                likes = 0
            
            post_content["点赞数"] = likes
            
            # 获取内容
            content_element = await self.main_page.query_selector('#detail-desc .note-text')
            if content_element:
                content_text = await content_element.text_content()
                post_content["内容"] = content_text.strip() if content_text else "未能获取内容"
            else:
                post_content["内容"] = "未能获取内容"
            
            # 格式化返回结果
            result = f"标题: {post_content['标题']}\n"
            result += f"作者: {post_content['作者']}\n"
            result += f"发布时间: {post_content['发布时间']}\n"
            result += f"点赞数: {post_content['点赞数']}\n"
            result += f"链接: {url}\n\n"
            result += f"内容:\n{post_content['内容']}"
            
            return result
            
        except Exception as e:
            logger.error(f"获取笔记内容时出错: {e}")
            return f"获取笔记内容时出错: {str(e)}"
    
    async def get_note_comments(self, url: str) -> str:
        """获取笔记评论"""
        if not await self.ensure_login():
            return "请先登录小红书账号"
        
        if not self.main_page:
            return "浏览器初始化失败，请重试"
        
        try:
            # 验证URL
            if not url or not url.strip():
                return "URL不能为空"
            
            # 处理URL
            try:
                processed_url = self._process_url(url)
            except ValueError as e:
                return f"URL格式错误: {str(e)}"
            
            logger.info(f"访问评论URL: {processed_url}")
            
            # 访问帖子链接
            await self.main_page.goto(processed_url, timeout=HunterConfig.BROWSER_TIMEOUT)
            await asyncio.sleep(5)
            
            # 检查错误页面
            error_page = await self.main_page.evaluate('''
                () => {
                    const errorTexts = [
                        "当前笔记暂时无法浏览",
                        "内容不存在",
                        "页面不存在",
                        "内容已被删除"
                    ];
                    
                    for (const text of errorTexts) {
                        if (document.body.innerText.includes(text)) {
                            return { isError: true, errorText: text };
                        }
                    }
                    return { isError: false };
                }
            ''')
            
            if error_page.get("isError", False):
                return f"无法获取笔记评论: {error_page.get('errorText', '未知错误')}"
            
            # 滚动到评论区
            comment_section_locators = []
            try:
                comment_section_locators = [
                    self.main_page.get_by_text("条评论", exact=False),
                    self.main_page.get_by_text("评论", exact=False),
                    self.main_page.locator("text=评论").first
                ]
            except Exception as e:
                logger.error(f"创建评论区定位器时出错: {str(e)}")
            
            for locator in comment_section_locators:
                try:
                    if locator and await locator.count() > 0:
                        await locator.scroll_into_view_if_needed(timeout=5000)
                        await asyncio.sleep(2)
                        break
                except Exception as e:
                    logger.error(f"滚动到评论区时出错: {str(e)}")
                    continue
            
            # 滚动页面以加载更多评论
            for i in range(8):
                try:
                    await self.main_page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(1)
                    
                    # 尝试点击"查看更多评论"按钮
                    more_comment_selectors = [
                        "text=查看更多评论",
                        "text=展开更多评论",
                        "text=加载更多",
                        "text=查看全部"
                    ]
                    
                    for selector in more_comment_selectors:
                        try:
                            more_btn = self.main_page.locator(selector).first
                            if more_btn and await more_btn.count() > 0 and await more_btn.is_visible():
                                await more_btn.click()
                                await asyncio.sleep(2)
                        except Exception as e:
                            logger.error(f"点击查看更多按钮时出错: {str(e)}")
                            continue
                except Exception as e:
                    logger.error(f"滚动页面加载更多评论时出错: {str(e)}")
                    pass
            
            # 获取评论
            comments = []
            
            # 使用特定评论选择器
            comment_selectors = [
                "div.comment-item", 
                "div.commentItem",
                "div.comment-content",
                "div.comment-wrapper",
                "section.comment",
                "div.feed-comment"
            ]
            
            for selector in comment_selectors:
                try:
                    comment_elements = self.main_page.locator(selector)
                    if comment_elements:
                        count = await comment_elements.count()
                        if count > 0:
                            for i in range(count):
                                try:
                                    comment_element = comment_elements.nth(i)
                                    if not comment_element:
                                        continue
                                    
                                    # 提取评论者名称
                                    username = "未知用户"
                                    username_selectors = ["span.user-name", "a.name", "div.username", "span.nickname", "a.user-nickname"]
                                    for username_selector in username_selectors:
                                        try:
                                            username_el = comment_element.locator(username_selector).first
                                            if username_el and await username_el.count() > 0:
                                                username_text = await username_el.text_content()
                                                if username_text:
                                                    username = username_text.strip()
                                                    break
                                        except Exception as e:
                                            logger.error(f"获取用户名出错: {str(e)}")
                                            continue
                                    
                                    # 如果没有找到，尝试通过用户链接查找
                                    if username == "未知用户":
                                        try:
                                            user_link = comment_element.locator('a[href*="/user/profile/"]').first
                                            if user_link and await user_link.count() > 0:
                                                username_text = await user_link.text_content()
                                                if username_text:
                                                    username = username_text.strip()
                                        except Exception as e:
                                            logger.error(f"通过用户链接获取用户名出错: {str(e)}")
                                    
                                    # 提取评论内容
                                    content = "未知内容"
                                    content_selectors = ["div.content", "p.content", "div.text", "span.content", "div.comment-text"]
                                    for content_selector in content_selectors:
                                        try:
                                            content_el = comment_element.locator(content_selector).first
                                            if content_el and await content_el.count() > 0:
                                                content_text = await content_el.text_content()
                                                if content_text:
                                                    content = content_text.strip()
                                                    break
                                        except Exception as e:
                                            logger.error(f"获取评论内容出错: {str(e)}")
                                            continue
                                    
                                    # 如果没有找到内容，可能内容就在评论元素本身
                                    if content == "未知内容":
                                        try:
                                            full_text = await comment_element.text_content()
                                            if full_text:
                                                if username != "未知用户" and username in full_text:
                                                    content = full_text.replace(username, "").strip()
                                                else:
                                                    content = full_text.strip()
                                        except Exception as e:
                                            logger.error(f"获取评论全文出错: {str(e)}")
                                    
                                    # 提取评论时间
                                    time_location = "未知时间"
                                    time_selectors = ["span.time", "div.time", "span.date", "div.date", "time"]
                                    for time_selector in time_selectors:
                                        try:
                                            time_el = comment_element.locator(time_selector).first
                                            if time_el and await time_el.count() > 0:
                                                time_text = await time_el.text_content()
                                                if time_text:
                                                    time_location = time_text.strip()
                                                    break
                                        except Exception as e:
                                            logger.error(f"获取评论时间出错: {str(e)}")
                                            continue
                                    
                                    # 如果内容有足够长度且找到用户名，添加评论
                                    if username != "未知用户" and content != "未知内容" and len(content) > 2:
                                        comments.append({
                                            "用户名": username,
                                            "内容": content,
                                            "时间": time_location
                                        })
                                except Exception as e:
                                    logger.error(f"处理单个评论出错: {str(e)}")
                                    continue
                            
                            # 如果找到了评论，就不继续尝试其他选择器了
                            if comments:
                                break
                except Exception as e:
                    logger.error(f"处理评论选择器出错: {str(e)}")
                    continue
            
            # 如果没有找到评论，尝试使用其他方法
            if not comments:
                # 获取所有用户名元素
                username_elements = self.main_page.locator('a[href*="/user/profile/"]')
                username_count = await username_elements.count()
                
                if username_count > 0:
                    for i in range(username_count):
                        try:
                            username_element = username_elements.nth(i)
                            username = await username_element.text_content()
                            
                            # 尝试获取评论内容
                            content = await self.main_page.evaluate('''
                                (usernameElement) => {
                                    const parent = usernameElement.parentElement;
                                    if (!parent) return null;
                                    
                                    // 尝试获取同级的下一个元素
                                    let sibling = usernameElement.nextElementSibling;
                                    while (sibling) {
                                        const text = sibling.textContent.trim();
                                        if (text) return text;
                                        sibling = sibling.nextElementSibling;
                                    }
                                    
                                    // 尝试获取父元素的文本，并过滤掉用户名
                                    const allText = parent.textContent.trim();
                                    if (allText && allText.includes(usernameElement.textContent.trim())) {
                                        return allText.replace(usernameElement.textContent.trim(), '').trim();
                                    }
                                    
                                    return null;
                                }
                            ''', username_element)
                            
                            if username and content:
                                comments.append({
                                    "用户名": username.strip(),
                                    "内容": content.strip(),
                                    "时间": "未知时间"
                                })
                        except Exception:
                            continue
            
            # 格式化返回结果
            if comments:
                result = f"共获取到 {len(comments)} 条评论：\n\n"
                for i, comment in enumerate(comments, 1):
                    result += f"{i}. {comment['用户名']}（{comment['时间']}）: {comment['内容']}\n\n"
                return result
            else:
                return "未找到任何评论，可能是帖子没有评论或评论区无法访问。"
        
        except Exception as e:
            logger.error(f"获取评论时出错: {e}")
            return f"获取评论时出错: {str(e)}"
    
    def _process_url(self, url: str) -> str:
        """处理URL，确保格式正确"""
        if not url or not url.strip():
            raise ValueError("URL不能为空")
        
        processed_url = url.strip()
        
        # HunterAPI返回的URL已经是完整格式，直接返回
        if processed_url.startswith('https://www.xiaohongshu.com'):
            return processed_url
        
        # 如果是相对路径，添加基础URL
        if processed_url.startswith('/'):
            return f"{HunterConfig.XIAOHONGSHU_BASE_URL}{processed_url}"
        
        # 其他情况，尝试添加https前缀
        if not processed_url.startswith('http'):
            processed_url = 'https://' + processed_url
        
        return processed_url
    
    async def shutdown(self):
        """关闭浏览器"""
        async with self._lock:
            try:
                if self.browser_context:
                    await self.browser_context.close()
                    self.browser_context = None
                    self.main_page = None
                
                if self._playwright:
                    await self._playwright.stop()
                    self._playwright = None
                
                self.is_logged_in = False
                logger.info("浏览器已关闭")
                
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {e}")
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self.browser_context is not None and self.main_page is not None 