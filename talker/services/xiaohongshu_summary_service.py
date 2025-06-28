#!/usr/bin/env python
# encoding: utf-8

import asyncio
import logging
import json
import re
from typing import Dict, Any, List, Optional
from hunter.api.hunter_api import api as hunter_api
from .chat_service import ChatService

logger = logging.getLogger(__name__)

class XiaohongshuSummaryService:
    """小红书内容总结服务"""
    
    def __init__(self):
        self.chat_service = ChatService()
        logger.info("XiaohongshuSummaryService 已初始化")
    
    async def search_and_summarize(self, keyword: str, limit: int = 5, summary_type: str = "general") -> Dict[str, Any]:
        """搜索关键词并总结小红书内容
        
        Args:
            keyword: 搜索关键词
            limit: 搜索笔记数量限制
            summary_type: 总结类型 ("general", "food", "travel", "shopping", "beauty")
            
        Returns:
            总结结果
        """
        try:
            # 1. 检查HunterAPI状态
            status = hunter_api.get_status()
            if not status["success"]:
                return {"success": False, "error": "HunterAPI状态检查失败"}
            
            # 2. 搜索笔记
            print(f"开始搜索关键词: {keyword}")
            search_result = await hunter_api.search_notes(keyword, limit)
            print(f"搜索结果: {search_result}")
            
            if not search_result["success"]:
                return search_result
            notes_data = search_result["data"]
            print(f"notes_data类型: {type(notes_data)}")
            print(f"notes_data内容: {json.dumps(notes_data)}")
            
            # 兼容字符串和列表
            if isinstance(notes_data, str):
                print("notes_data是字符串，开始解析...")
                notes = self._parse_search_result_string(notes_data)
                print(f"解析后的notes: {json.dumps(notes)}")
            elif isinstance(notes_data, list):
                print("notes_data是列表")
                notes = notes_data
            else:
                print(f"notes_data是其他类型: {type(notes_data)}")
                notes = []
            if not notes:
                return {
                    "success": True, 
                    "data": {
                        "keyword": keyword,
                        "summary": "未找到相关笔记，无法生成总结",
                        "notes_count": 0,
                        "notes": []
                    }
                }
            
            # 3. 获取笔记详细内容和评论（只信任hunter_api返回结构，不做任何字符串解析）
            logger.info(f"开始获取 {len(notes)} 条笔记的详细内容")
            notes_with_content = []
            for i, note in enumerate(notes):
                logger.info(f"处理第 {i+1} 条笔记: {json.dumps(note)}")
                try:
                    # 检查URL
                    note_url = note.get("url", "")
                    logger.info(f"笔记URL: '{note_url}' (长度: {len(note_url)})")
                    
                    if not note_url:
                        logger.warning(f"第 {i+1} 条笔记URL为空，跳过")
                        continue
                    
                    # 直接调用hunter_api获取内容
                    content_result = await hunter_api.get_note_content(note_url)
                    comments_result = await hunter_api.get_note_comments(note_url)
                    
                    logger.info(f"内容结果: {content_result}")
                    logger.info(f"评论结果: {comments_result}")
                    
                    note_data = {
                        "title": note.get("title", ""),
                        "author": note.get("author", ""),
                        "likes": note.get("likes", 0),
                        "content": "",
                        "comments": []
                    }
                    if content_result["success"]:
                        content_data = content_result["data"]
                        # 只信任hunter_api返回的结构
                        if isinstance(content_data, dict):
                            note_data["content"] = content_data.get("text") or content_data.get("内容") or str(content_data)
                        else:
                            note_data["content"] = str(content_data)
                        
                        # 从content中解析结构化信息
                        parsed_info = self._parse_note_content_for_info(note_data["content"])
                        note_data.update(parsed_info)
                    else:
                        note_data["content"] = "获取内容失败"
                    
                    # 解析评论数据
                    if comments_result["success"]:
                        comments_data = comments_result["data"]
                        if isinstance(comments_data, str):
                            # 解析字符串格式的评论
                            parsed_comments = self._parse_comments_string(comments_data)
                            note_data["comments"] = parsed_comments
                        elif isinstance(comments_data, list):
                            note_data["comments"] = comments_data[:10]  # 限制评论数量
                        else:
                            note_data["comments"] = []
                    else:
                        note_data["comments"] = []
                    
                    notes_with_content.append(note_data)
                except Exception as e:
                    logger.warning(f"获取笔记 {note.get('url', '')} 内容失败: {e}")
                    continue
            # 4. 生成总结
            logger.info(f"开始生成总结，共 {len(notes_with_content)} 条有效笔记")
            summary = await self._generate_summary(keyword, notes_with_content, summary_type)
            return {
                "success": True,
                "data": {
                    "keyword": keyword,
                    "summary": summary,
                    "notes_count": len(notes_with_content),
                    "notes": notes_with_content
                }
            }
        except Exception as e:
            logger.error(f"搜索总结异常: {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return {
                "success": False, 
                "error": str(e),
                "data": {
                    "keyword": keyword,
                    "summary": f"总结生成失败: {str(e)}",
                    "notes_count": 0,
                    "notes": []
                }
            }
    
    def _parse_search_result_string(self, result_string: str) -> List[Dict[str, Any]]:
        """解析字符串格式的搜索结果
        
        Args:
            result_string: 搜索结果字符串
            
        Returns:
            解析后的笔记列表
        """
        try:
            print(f"开始解析搜索结果字符串: {result_string[:200]}...")
            notes = []
            lines = result_string.strip().split('\n')
            
            current_note = {}
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                print(f"解析第 {line_num+1} 行: '{line}'")
                # 匹配笔记条目 (1. 标题)
                if line[0].isdigit() and '. ' in line:
                    if current_note:
                        print(f"添加笔记: {current_note}")
                        notes.append(current_note)
                    title = line.split('. ', 1)[1] if '. ' in line else line
                    current_note = {
                        "title": title,
                        "author": "未知作者",
                        "likes": 0,
                        "url": "",
                        "content": ""
                    }
                    print(f"创建新笔记，标题: {title}")
                # 宽松匹配链接行
                elif '链接:' in line:
                    url = line.split('链接:', 1)[-1].strip()
                    if current_note:
                        current_note["url"] = url
                        print(f"设置笔记URL: {url}")
            # 添加最后一个笔记
            if current_note:
                print(f"添加最后一个笔记: {current_note}")
                notes.append(current_note)
            print(f"解析完成，共 {len(notes)} 条笔记")
            return notes
        except Exception as e:
            print(f"解析搜索结果字符串失败: {e}")
            return []
    
    def _parse_note_content_string(self, content_string: str) -> Dict[str, Any]:
        """解析字符串格式的笔记内容
        
        Args:
            content_string: 笔记内容字符串
            
        Returns:
            解析后的笔记数据
        """
        try:
            parsed_data = {
                "title": "未知标题",
                "author": "未知作者",
                "content": "",
                "publish_time": "未知",
                "likes": 0
            }
            
            lines = content_string.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 匹配标题
                if line.startswith('标题: '):
                    parsed_data["title"] = line.replace('标题: ', '').strip()
                
                # 匹配作者
                elif line.startswith('作者: '):
                    parsed_data["author"] = line.replace('作者: ', '').strip()
                
                # 匹配发布时间
                elif line.startswith('发布时间: '):
                    parsed_data["publish_time"] = line.replace('发布时间: ', '').strip()
                
                # 匹配点赞数
                elif line.startswith('点赞数: '):
                    likes_text = line.replace('点赞数: ', '').strip()
                    try:
                        parsed_data["likes"] = int(likes_text)
                    except ValueError:
                        parsed_data["likes"] = 0
                
                # 匹配内容部分
                elif line == '内容:':
                    current_section = 'content'
                elif current_section == 'content':
                    if parsed_data["content"]:
                        parsed_data["content"] += "\n" + line
                    else:
                        parsed_data["content"] = line
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"解析笔记内容字符串失败: {e}")
            return {
                "title": "解析失败",
                "author": "未知作者",
                "content": content_string,
                "publish_time": "未知",
                "likes": 0
            }
    
    def _parse_comments_string(self, comments_string: str) -> List[Dict[str, Any]]:
        """解析字符串格式的评论数据
        
        Args:
            comments_string: 评论数据字符串
            
        Returns:
            解析后的评论列表
        """
        try:
            comments = []
            lines = comments_string.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 匹配评论格式：数字. 用户名（时间）: 内容
                import re
                comment_pattern = r'^(\d+)\.\s*([^（]+)（([^）]+)）:\s*(.+)$'
                match = re.match(comment_pattern, line)
                
                if match:
                    comment = {
                        "author": match.group(2).strip(),
                        "time": match.group(3).strip(),
                        "content": match.group(4).strip()
                    }
                    comments.append(comment)
                else:
                    # 尝试其他格式
                    # 格式：用户名（时间）: 内容
                    alt_pattern = r'^([^（]+)（([^）]+)）:\s*(.+)$'
                    alt_match = re.match(alt_pattern, line)
                    
                    if alt_match:
                        comment = {
                            "author": alt_match.group(1).strip(),
                            "time": alt_match.group(2).strip(),
                            "content": alt_match.group(3).strip()
                        }
                        comments.append(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"解析评论字符串失败: {e}")
            return []
    
    async def _generate_summary(self, keyword: str, notes: List[Dict], summary_type: str) -> str:
        """生成内容总结
        
        Args:
            keyword: 搜索关键词
            notes: 笔记列表
            summary_type: 总结类型
            
        Returns:
            总结文本
        """
        try:
            print(f"开始生成总结，关键词: {keyword}, 类型: {summary_type}, 笔记数量: {len(notes)}")
            
            # 构建提示词
            if len(notes) == 1:
                # 单条笔记总结
                note = notes[0]
                prompt = f"""请对以下小红书笔记内容进行{summary_type}总结：

笔记信息：
- 标题：{note.get('title', '未知')}
- 作者：{note.get('author', '未知')}
- 发布时间：{note.get('publish_time', '未知')}
- 点赞数：{note.get('likes', 0)}
- IP地址：{note.get('ip', '未知')}
- 标签：{', '.join(note.get('tags', []))}
- 链接：{note.get('url', '未知')}

笔记内容：
{note.get('content', '无内容')}

{f"评论内容：\n{note.get('comments', '')}" if note.get('comments') else ""}

请根据以上信息，生成一个{summary_type}的总结。总结应该：
1. 突出笔记的核心观点和主要内容
2. 分析笔记的受欢迎程度（基于点赞数）
3. 总结用户反馈和评论要点
4. 提供有价值的见解和建议

总结要求：
- 语言简洁明了
- 结构清晰
- 重点突出
- 实用性强

请开始总结："""
            else:
                # 多条笔记总结
                notes_text = ""
                for i, note in enumerate(notes, 1):
                    notes_text += f"\n=== 笔记 {i} ===\n"
                    notes_text += f"标题：{note.get('title', '未知')}\n"
                    notes_text += f"作者：{note.get('author', '未知')}\n"
                    notes_text += f"发布时间：{note.get('publish_time', '未知')}\n"
                    notes_text += f"点赞数：{note.get('likes', 0)}\n"
                    notes_text += f"IP地址：{note.get('ip', '未知')}\n"
                    notes_text += f"标签：{', '.join(note.get('tags', []))}\n"
                    notes_text += f"链接：{note.get('url', '未知')}\n"
                    notes_text += f"内容：{note.get('content', '无内容')}\n"
                    if note.get('comments'):
                        notes_text += f"评论：{note.get('comments')}\n"
                
                prompt = f"""请对以下{len(notes)}条小红书笔记内容进行{summary_type}总结：

搜索关键词：{keyword}

笔记列表：
{notes_text}

请根据以上信息，生成一个{summary_type}的总结。总结应该：
1. 分析所有笔记的共同主题和核心观点
2. 对比不同笔记的受欢迎程度（基于点赞数）
3. 总结用户反馈和评论要点
4. 提供有价值的见解和建议

总结要求：
- 语言简洁明了
- 结构清晰
- 重点突出
- 实用性强

请开始总结："""
            
            # 调用聊天服务生成总结
            print("开始调用ChatService...")
            response = self.chat_service.process_chat(
                message=prompt,
                temperature=0.7,
                max_tokens=2048
            )
            print(f"ChatService响应类型: {type(response)}")
            print(f"ChatService响应: {response}")
            
            if isinstance(response, dict) and response.get("error"):
                print(f"生成总结失败: {response.get('message', '未知错误')}")
                return f"总结生成失败: {response.get('message', '未知错误')}"
            
            # 提取响应内容
            if hasattr(response, 'json'):
                result = response.json()
                print(f"JSON响应: {result}")
                return result.get("content", "总结生成失败")
            elif isinstance(response, dict):
                print(f"字典响应: {response}")
                # 处理VivoGPT的响应结构
                if response.get("code") == 0 and "data" in response:
                    data = response["data"]
                    if isinstance(data, dict) and "content" in data:
                        return data["content"]
                    else:
                        return str(data)
                elif "content" in response:
                    return response["content"]
                else:
                    return str(response)
            else:
                print(f"其他类型响应: {response}")
                return str(response)
                
        except Exception as e:
            print(f"生成总结异常: {e}")
            import traceback
            print(f"异常堆栈: {traceback.format_exc()}")
            return f"总结生成失败: {str(e)}"
    
    def _build_summary_prompt(self, keyword: str, notes: List[Dict], summary_type: str) -> str:
        """构建总结提示词
        
        Args:
            keyword: 搜索关键词
            notes: 笔记列表
            summary_type: 总结类型
            
        Returns:
            提示词
        """
        print(f"开始构建提示词，关键词: {keyword}, 类型: {summary_type}, 笔记数量: {len(notes)}")
        
        # 根据总结类型选择不同的提示词模板
        if summary_type == "food":
            template = self._get_food_summary_template()
        elif summary_type == "travel":
            template = self._get_travel_summary_template()
        elif summary_type == "shopping":
            template = self._get_shopping_summary_template()
        elif summary_type == "beauty":
            template = self._get_beauty_summary_template()
        else:
            template = self._get_general_summary_template()
        
        print(f"选择的模板长度: {len(template)}")
        
        # 构建笔记内容文本
        notes_text = ""
        for i, note in enumerate(notes, 1):
            print(f"处理第 {i} 条笔记: {json.dumps(note, ensure_ascii=False)}")
            notes_text += f"\n\n=== 笔记 {i} ===\n"
            notes_text += f"标题: {note.get('title', '无标题')}\n"
            notes_text += f"作者: {note.get('author', '匿名')}\n"
            notes_text += f"发布时间: {note.get('publish_time', '未知')}\n"
            notes_text += f"IP地址: {note.get('ip', '未知')}\n"
            notes_text += f"点赞数: {note.get('likes', 0)}\n"
            
            # 添加标签信息
            tags = note.get('tags', [])
            if tags:
                notes_text += f"标签: {', '.join(tags)}\n"
            
            notes_text += f"内容: {note.get('content', '')}\n"
            
            comments = note.get('comments', [])
            if comments:
                notes_text += f"评论 ({len(comments)} 条):\n"
                for j, comment in enumerate(comments[:5], 1):  # 只显示前5条评论
                    notes_text += f"  {j}. {comment.get('content', '')} (by {comment.get('author', '匿名')} at {comment.get('time', '未知时间')})\n"
        
        print(f"拼接后的notes_text长度: {len(notes_text)}")
        print(f"拼接后的notes_text前500字符: {notes_text[:500]}...")
        print(f"拼接后的notes_text后500字符: {notes_text[-500:] if len(notes_text) > 500 else notes_text}...")
        
        final_prompt = template.format(keyword=keyword, notes_content=notes_text)
        print(f"最终提示词长度: {len(final_prompt)}")
        print(f"最终提示词前200字符: {final_prompt[:200]}...")
        
        return final_prompt
    
    def _get_general_summary_template(self) -> str:
        """获取通用总结模板"""
        return """你是一个专业的内容分析师，请基于以下小红书笔记内容，为关键词"{keyword}"生成一份详细的分析总结。

要求：
1. 分析用户关注点和热门话题
2. 总结主要观点和评价
3. 识别优缺点和争议点
4. 提供实用的建议和洞察
5. 使用中文回复，语言要专业、客观、易懂

笔记内容：
{notes_content}

请生成一份结构化的总结报告。"""

    def _get_food_summary_template(self) -> str:
        """获取美食总结模板"""
        return """你是一个专业的美食评论家，请基于以下小红书笔记内容，为关键词"{keyword}"生成一份详细的美食分析总结。

要求：
1. 分析推荐度最高的餐厅/美食
2. 总结口味特点和价格区间
3. 识别热门菜品和避雷建议
4. 提供用餐建议（时间、人数、预算等）
5. 总结用户整体评价和情感倾向

笔记内容：
{notes_content}

请生成一份专业的美食推荐总结。"""

    def _get_travel_summary_template(self) -> str:
        """获取旅行总结模板"""
        return """你是一个专业的旅行规划师，请基于以下小红书笔记内容，为关键词"{keyword}"生成一份详细的旅行攻略总结。

要求：
1. 分析最佳游玩时间和季节
2. 总结必去景点和推荐路线
3. 识别住宿和交通建议
4. 提供预算参考和消费水平
5. 总结用户体验和注意事项

笔记内容：
{notes_content}

请生成一份实用的旅行攻略总结。"""

    def _get_shopping_summary_template(self) -> str:
        """获取购物总结模板"""
        return """你是一个专业的购物顾问，请基于以下小红书笔记内容，为关键词"{keyword}"生成一份详细的购物分析总结。

要求：
1. 分析推荐度最高的商品/品牌
2. 总结价格区间和性价比
3. 识别购买渠道和优惠信息
4. 提供购买建议和注意事项
5. 总结用户满意度评价

笔记内容：
{notes_content}

请生成一份实用的购物指南总结。"""

    def _get_beauty_summary_template(self) -> str:
        """获取美妆总结模板"""
        return """你是一个专业的美妆顾问，请基于以下小红书笔记内容，为关键词"{keyword}"生成一份详细的美妆分析总结。

要求：
1. 分析推荐度最高的产品/品牌
2. 总结适用肤质和使用效果
3. 识别价格区间和购买渠道
4. 提供使用建议和注意事项
5. 总结用户真实体验评价

笔记内容：
{notes_content}

请生成一份专业的美妆推荐总结。"""

    def _parse_note_content_for_info(self, content: str) -> Dict[str, Any]:
        """从笔记内容中解析结构化信息
        
        Args:
            content: 笔记内容字符串
            
        Returns:
            解析后的结构化信息
        """
        try:
            parsed_info = {}
            
            # 解析标题
            title_match = re.search(r'标题: (.+)', content)
            if title_match:
                parsed_info["title"] = title_match.group(1).strip()
            
            # 解析作者
            author_match = re.search(r'作者: (.+)', content)
            if author_match:
                parsed_info["author"] = author_match.group(1).strip()
            
            # 解析发布时间
            publish_time_match = re.search(r'发布时间: (.+)', content)
            if publish_time_match:
                parsed_info["publish_time"] = publish_time_match.group(1).strip()
            
            # 解析IP地址
            ip_match = re.search(r'IP地址: (.+)', content)
            if ip_match:
                parsed_info["ip"] = ip_match.group(1).strip()
            
            # 解析点赞数
            likes_match = re.search(r'点赞数: (\d+)', content)
            if likes_match:
                parsed_info["likes"] = int(likes_match.group(1))
            else:
                parsed_info["likes"] = 0
            
            # 解析标签
            tag_match = re.findall(r'#([^#\s]+)', content)
            if tag_match:
                parsed_info["tags"] = [tag.strip() for tag in tag_match]
            
            return parsed_info
            
        except Exception as e:
            logger.error(f"解析笔记内容结构化信息失败: {e}")
            return {}

# 创建全局实例
summary_service = XiaohongshuSummaryService() 