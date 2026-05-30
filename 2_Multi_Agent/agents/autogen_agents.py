"""
AutoGen智能体模块
基于AutoGen框架实现多智能体客服系统
"""
import autogen
import json
import time
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from rich import box
from core.logger import setup_logger
from config.settings import settings
from tools.api_client import api_client
import asyncio

logger = setup_logger(__name__)
console = Console()


class InteractiveAgentDisplay:
    """智能体交互显示包装器"""
    
    def __init__(self, agent_name: str, agent_type: str):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.start_time = None
        self.task_count = 0
        
    def log_interaction(self, message: str, level: str = "info", task_id: str = None):
        """记录智能体交互过程"""
        timestamp = time.strftime("%H:%M:%S")
        
        # 创建交互消息
        if level == "start":
            self.start_time = time.time()
            self.task_count += 1
            panel_content = f"🤖 [bold blue]{self.agent_name}[/bold blue] 开始执行任务"
            border_style = "bright_blue"
            # 添加详细的开始日志
            logger.info(f"🚀 Agent [{self.agent_name}] 开始执行任务 #{self.task_count} - {message}")
        elif level == "thinking":
            panel_content = f"🧠 [bold yellow]{self.agent_name}[/bold yellow] 正在思考: {message}"
            border_style = "bright_yellow"
            logger.info(f"🧠 Agent [{self.agent_name}] 思考中: {message}")
        elif level == "action":
            panel_content = f"🛠️  [bold green]{self.agent_name}[/bold green] 执行操作: {message}"
            border_style = "bright_green"
            logger.info(f"🛠️ Agent [{self.agent_name}] 执行操作: {message}")
        elif level == "result":
            elapsed = time.time() - self.start_time if self.start_time else 0
            panel_content = f"✅ [bold green]{self.agent_name}[/bold green] 任务完成 (耗时: {elapsed:.2f}s)\n{message}"
            border_style = "bright_green"
            # 添加详细的完成日志
            logger.info(f"✅ Agent [{self.agent_name}] 任务完成 - 耗时: {elapsed:.2f}s")
            logger.info(f"📋 Agent [{self.agent_name}] 任务结果: {message}")
        elif level == "error":
            panel_content = f"❌ [bold red]{self.agent_name}[/bold red] 错误: {message}"
            border_style = "bright_red"
            logger.error(f"❌ Agent [{self.agent_name}] 执行错误: {message}")
        else:
            panel_content = f"💬 {self.agent_name}: {message}"
            border_style = "white"
            logger.info(f"💬 Agent [{self.agent_name}]: {message}")
        
        # 显示交互面板
        panel = Panel(
            panel_content,
            title=f"[bold]{self.agent_name}[/bold]",
            subtitle=f"⏰ {timestamp} | 📋 任务 #{self.task_count}",
            border_style=border_style,
            box=box.ROUNDED,
            expand=False
        )
        
        console.print(panel)


# 自定义消息处理函数
def create_agent_message_handler(agent_name: str, display: InteractiveAgentDisplay):
    """创建agent消息处理函数"""
    def handle_message(sender, message, request_reply=False):
        """处理agent消息"""
        if sender.name != agent_name:  # 只处理发送给当前agent的消息
            # 显示接收到的消息
            display.log_interaction(f"接收到来自 {sender.name} 的消息", level="start")
            console.print(f"[bold cyan]📨 {agent_name} 接收消息:[/bold cyan]")
            console.print(Panel(message.get("content", ""), border_style="cyan", box=box.SIMPLE))
            
        return False, None  # 不拦截消息，继续正常处理
    
    return handle_message


def create_agent_reply_handler(agent_name: str, display: InteractiveAgentDisplay):
    """创建agent回复处理函数"""
    def handle_reply(sender, message, recipient, silent):
        """处理agent回复"""
        # 处理不同类型的消息
        content = ""
        if isinstance(message, str):
            content = message
        elif isinstance(message, dict) and message.get("content"):
            content = message.get("content", "")
        
        if content:
            # 显示agent正在生成回复
            display.log_interaction(f"正在生成回复给 {recipient.name}", level="thinking")
            
            # 显示回复内容
            console.print(f"[bold green]📤 {agent_name} 发送回复:[/bold green]")
            console.print(Panel(content, border_style="green", box=box.SIMPLE))
            
            display.log_interaction(f"已发送回复给 {recipient.name}", level="result")
            
        return message  # 返回原始消息，不修改
    
    return handle_reply


# 工具函数定义
def extract_order_id_from_message(message: str) -> str:
    """
    从消息中提取订单ID
    
    Args:
        message: 用户消息内容
        
    Returns:
        str: 提取到的订单ID，如果没有找到则返回默认值ORD001
    """
    import re
    # 使用正则表达式匹配订单ID模式 (ORD + 数字)
    pattern = r'ORD\d+'
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        order_id = match.group().upper()
        logger.info(f"🔍 从消息中提取到订单ID: {order_id}")
        return order_id
    else:
        logger.warning(f"⚠️ 未能从消息中提取订单ID，使用默认值: ORD001")
        return "ORD001"

async def get_order_info_async(order_id: str) -> str:
    """异步获取订单信息的工具函数"""
    display = InteractiveAgentDisplay("订单查询工具", "tool")
    
    # 如果没有提供order_id，使用默认值
    if not order_id:
        order_id = "ORD001"  # 默认值
    
    display.log_interaction(f"开始查询订单: {order_id}", level="start")
    
    try:
        order_info = await api_client.get_order_status(order_id)
        
        # 检查是否有错误
        if "error" in order_info:
            error_msg = f"很抱歉，订单 {order_id} 不存在。请检查订单号是否正确，或联系客服获取帮助。"
            display.log_interaction(f"订单不存在: {order_id}", level="error")
            logger.warning(f"❌ 订单不存在: {order_id}")
            return error_msg
        
        result = f"""订单查询结果：
            订单ID: {order_info.get('order_id', 'N/A')}
            订单状态: {order_info.get('status', 'N/A')}
            客户姓名: {order_info.get('customer_name', 'N/A')}
            订单金额: ¥{order_info.get('total_amount', 0)}
            商品列表: {', '.join(order_info.get('items', []))}
            收货地址: {order_info.get('shipping_address', 'N/A')}
            创建时间: {order_info.get('created_at', 'N/A')}
            更新时间: {order_info.get('updated_at', 'N/A')}"""
        
        # 添加详细的订单结果日志
        logger.info(f"📦 订单查询成功 - 订单ID: {order_info.get('order_id')}")
        logger.info(f"📊 订单详情 - 状态: {order_info.get('status')}, 金额: ¥{order_info.get('total_amount', 0)}")
        logger.info(f"👤 客户信息 - 姓名: {order_info.get('customer_name')}, 地址: {order_info.get('shipping_address')}")
        logger.info(f"🛍️ 商品列表: {', '.join(order_info.get('items', []))}")
        
        display.log_interaction(f"订单查询成功: {order_id}", level="result")
        return result
        
    except Exception as e:
        error_msg = f"订单查询系统暂时不可用，请稍后重试或联系客服。错误信息: {str(e)}"
        display.log_interaction(error_msg, level="error")
        logger.error(f"❌ 订单查询异常: {order_id} -> {str(e)}")
        return error_msg

def get_order_info(order_id: str) -> str:
    """获取订单信息的工具函数（同步包装器）"""
    try:
        # 尝试获取当前运行的事件循环
        loop = asyncio.get_running_loop()
        # 如果已经在事件循环中，使用 run_in_executor
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, get_order_info_async(order_id))
            return future.result()
    except RuntimeError:
        # 如果没有运行的事件循环，直接运行
        return asyncio.run(get_order_info_async(order_id))


def get_logistics_info(order_id: str) -> str:
    """获取物流信息的工具函数"""
    display = InteractiveAgentDisplay("物流查询工具", "tool")
    display.log_interaction(f"开始查询物流: {order_id}", level="start")

    try:
        # 在同步环境中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logistics_info = loop.run_until_complete(api_client.get_logistics_info(order_id))

            # 检查是否有错误
            if "error" in logistics_info:
                error_msg = f"很抱歉，订单 {order_id} 的物流信息不存在。可能是订单尚未发货或订单号不正确，请联系客服获取帮助。"
                display.log_interaction(f"物流信息不存在: {order_id}", level="error")
                logger.warning(f"❌ 物流信息不存在: {order_id}")
                return error_msg

            # 格式化物流轨迹
            tracking_history = ""
            if logistics_info.get('tracking_history'):
                tracking_history = "\n物流轨迹:\n"
                for record in logistics_info['tracking_history']:
                    tracking_history += f"  {record.get('time', 'N/A')} - {record.get('location', 'N/A')}: {record.get('status', 'N/A')}\n"

            result = f"""物流查询结果：
                物流单号: {logistics_info.get('tracking_number', '暂未分配')}
                物流状态: {logistics_info.get('status', 'N/A')}
                当前位置: {logistics_info.get('current_location', 'N/A')}
                承运商: {logistics_info.get('carrier', 'N/A')}
                预计送达: {logistics_info.get('estimated_delivery', '未确定')}{tracking_history}"""

            # 添加详细的物流结果日志
            logger.info(f"🚚 物流查询成功 - 订单ID: {order_id}")
            logger.info(f"📋 物流详情 - 单号: {logistics_info.get('tracking_number')}, 状态: {logistics_info.get('status')}")
            logger.info(f"📍 位置信息 - 当前位置: {logistics_info.get('current_location')}, 承运商: {logistics_info.get('carrier')}")
            logger.info(f"⏰ 预计送达: {logistics_info.get('estimated_delivery', '未确定')}")

            display.log_interaction(f"物流查询成功: {order_id}", level="result")
            return result

        finally:
            loop.close()

    except Exception as e:
        error_msg = f"物流查询系统暂时不可用，请稍后重试或联系客服。错误信息: {str(e)}"
        display.log_interaction(error_msg, level="error")
        logger.error(f"❌ 物流查询异常: {order_id} -> {str(e)}")
        return error_msg



def create_autogen_agents():
    """创建AutoGen智能体"""
    logger.info("创建AutoGen智能体")
    console.print("\n[bold cyan]🚀 正在初始化AutoGen智能体团队...[/bold cyan]\n")
    
    # 配置LLM
    config_list = [
        {
            "model": settings.AUTOGEN_MODEL,
            "api_key": settings.AUTOGEN_API_KEY or settings.OPENAI_API_KEY,
            "base_url": settings.AUTOGEN_BASE_URL,
        }
    ]
    
    llm_config = {
        "config_list": config_list,
        "temperature": settings.AUTOGEN_TEMPERATURE,
        "timeout": settings.AUTOGEN_TIMEOUT,
    }
    
    # 创建交互显示包装器
    interactive_displays = {
        "customer_service": InteractiveAgentDisplay("客服接待员", "customer_service"),
        "order_query": InteractiveAgentDisplay("订单查询专员", "order_query"),
        "logistics": InteractiveAgentDisplay("物流跟踪专员", "logistics"),
        "summary": InteractiveAgentDisplay("客服主管", "summary"),
    }
    
    # # 创建用户代理
    # user_proxy = autogen.UserProxyAgent(
    #     name="客户",
    #     human_input_mode=settings.AUTOGEN_HUMAN_INPUT_MODE,
    #     max_consecutive_auto_reply=settings.AUTOGEN_MAX_CONSECUTIVE_AUTO_REPLY,
    #     is_termination_msg=lambda x: x.get("content", "") and ("问题已解决" in x.get("content", "") or "TERMINATE" in x.get("content", "")),
    #     code_execution_config={"work_dir": "temp", "use_docker": False},
    # )

    # 创建用户代理（客户）
    user_proxy = autogen.UserProxyAgent(
        name="客户",
        system_message="""你是一个真实的电商客户，有以下特征：
                1. 你会提出关于订单、物流、售后等问题
                2. 你会追问细节，比如"为什么还没发货？"、"什么时候能到？"
                3. 如果问题没解决，你会继续追问
                4. 问题解决后，你会表示感谢并结束对话
                5. 说话风格自然、口语化，像普通人一样

                当前问题已得到满意解答时，请在回复中包含"问题已解决"或"谢谢，没问题了"来表示结束。""",
        human_input_mode="NEVER",  # 不等待人工输入，让 AI 模拟客户
        max_consecutive_auto_reply=10,
        llm_config=llm_config,  # 添加 LLM 配置，让客户能够生成回复
        is_termination_msg=lambda x: x.get("content", "") and (
                    "问题已解决" in x.get("content", "") or "谢谢" in x.get("content", "")),
        code_execution_config={"work_dir": "temp", "use_docker": False},
    )
    
    # 客服接待智能体
    customer_service_agent = autogen.AssistantAgent(
        name="客服接待员",
        system_message="""你是一名专业的电商客服接待员。你的职责是：
            1. 友好接待客户，了解客户问题
            2. 对问题进行初步分类（订单查询、退换货、物流问题、产品咨询等）
            3. 收集必要的订单信息（订单号、客户信息等）
            4. 将问题转交给相应的专业团队处理

            请用简洁明了的语言与客户沟通。当客户提到具体订单号时，请直接转交给订单查询专员处理。
            如果问题涉及多个方面，请协调相关专员共同解决。

            回复格式：简洁专业，直接回答客户问题。""",
                    llm_config=llm_config,
                )
    
    # 订单查询智能体
    order_query_agent = autogen.AssistantAgent(
        name="订单查询专员",
        system_message="""你是订单查询专员，负责处理所有订单相关的查询。你的职责包括：
            1. 从客户查询中提取订单号（格式如ORD001、ORD002等）
            2. 使用get_order_info工具函数查询订单详细信息
            3. 解释订单状态和处理进度
            4. 提供预计发货和到货时间
            5. 识别需要其他部门协助的问题

            重要：当客户提供订单号时，你必须：
            1. 从查询文本中提取订单ID（如ORD002）
            2. 调用get_order_info函数，传入提取到的订单ID
            3. 根据查询结果向客户提供详细信息
            
            如果无法从查询中提取到订单ID，请使用默认值ORD001。
            
            示例：
            客户问："我的订单ORD002为什么还没发货？"
            你应该调用：get_order_info("ORD002")
            然后根据返回结果回答客户问题。

            回复格式：提供详细的订单信息，包括状态、商品、金额等关键信息。""",
        llm_config=llm_config,
    )
    
    # 物流跟踪智能体
    logistics_agent = autogen.AssistantAgent(
        name="物流跟踪专员",
        system_message="""你是物流跟踪专员，专门处理配送和物流相关问题。你的职责包括：
            1. 查询包裹物流状态和位置
            2. 提供准确的配送时间预估
            3. 处理配送异常和延误问题
            4. 协调配送地址修改

            当需要查询物流信息时，请使用 get_logistics_info 函数。
            请提供实时、准确的物流信息，并主动提醒客户注意事项。

            回复格式：提供详细的物流状态，包括当前位置、预计到达时间等。""",
                    llm_config=llm_config,
                )
                
    # 结果汇总智能体
    summary_agent = autogen.AssistantAgent(
        name="客服主管",
        system_message="""你是一名资深的客服主管，拥有多年的客户服务经验。
            你擅长整合来自不同部门的信息，为客户提供全面、准确、友好的回复。
            你总是站在客户的角度思考问题，能够用通俗易懂的语言解释复杂的情况，
            并在必要时提供解决方案和建议。

            你的职责是：
            1. 汇总订单和物流信息
            2. 生成完整的问题解答
            3. 确保客户得到满意的答复

            回复格式：友好、专业、完整，确保客户理解所有相关信息。""",
                    llm_config=llm_config,
                )
    
    # 为每个agent添加消息处理器
    customer_service_agent.register_hook("process_message_before_send", 
                                        create_agent_reply_handler("客服接待员", interactive_displays["customer_service"]))
    order_query_agent.register_hook("process_message_before_send", 
                                   create_agent_reply_handler("订单查询专员", interactive_displays["order_query"]))
    logistics_agent.register_hook("process_message_before_send", 
                                create_agent_reply_handler("物流跟踪专员", interactive_displays["logistics"]))
    summary_agent.register_hook("process_message_before_send", 
                              create_agent_reply_handler("客服主管", interactive_displays["summary"]))
    
    # 注册工具函数
    autogen.register_function(
        get_order_info,
        caller=order_query_agent,
        executor=user_proxy,
        description="根据订单号获取订单详细信息"
    )
    
    autogen.register_function(
        get_logistics_info,
        caller=logistics_agent,
        executor=user_proxy,
        description="根据订单号获取物流跟踪信息"
    )
    
    console.print("[bold green]✅ AutoGen智能体团队创建完成！[/bold green]\n")
    
    return {
        "user_proxy": user_proxy,
        "customer_service_agent": customer_service_agent,
        "order_query_agent": order_query_agent,
        "logistics_agent": logistics_agent,
        "summary_agent": summary_agent,
        "interactive_displays": interactive_displays,
        "llm_config": llm_config
    }


def create_group_chat(agents_dict):
    """创建群组聊天"""
    agents = [
        agents_dict["customer_service_agent"],
        agents_dict["order_query_agent"],
        agents_dict["logistics_agent"],
        agents_dict["summary_agent"],
        agents_dict["user_proxy"]
    ]
    
    groupchat = autogen.GroupChat(
        agents=agents,
        messages=[],
        max_round=settings.AUTOGEN_MAX_ROUNDS,
        speaker_selection_method="auto"
    )
    
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=agents_dict["llm_config"])
    
    return manager