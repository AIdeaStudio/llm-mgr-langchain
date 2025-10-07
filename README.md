# 通用大模型管理器

这是一个功能强大且灵活的大模型（LLM）服务管理器，使用 Python 编写，并基于 SQLAlchemy 和 LangChain。它旨在为开发者提供一个统一的后端，以管理不同来源、不同平台的大模型服务，并轻松集成到各种应用中。

该管理器设计的核心是**模式化**和**多租户支持**，使其能够适应从个人开发、私有化部署到多用户 SaaS 平台的多种应用场景。

## ✨ 核心特性

*   **三种使用模式**：内置支持三种主流使用场景，只需修改一个配置即可切换。
    1.  **无用户/全局单用户模式**：适用于开发者、私有系统或调试，所有请求共享一套由环境变量配置的系统模型。
    2.  **多用户固定平台模式**：管理员定义一组高质量的“系统平台”，用户不能添加自己的平台，但可以使用自己的 API Key，从而节省管理员的成本。
    3.  **多用户自定义平台模式**：提供最大自由度，用户可以自由添加、管理自己的私有平台和模型。
*   **系统与用户平台分离**：明确区分管理员定义的“系统平台”和用户自己创建的“私有平台”，便于管理和权限控制。
*   **灵活的 API Key 管理**：拥有完善的 API Key 解析逻辑。对于系统平台，优先使用用户提供的 Key，若用户未提供，则可选择性地自动回退到服务器端配置的 Key。
*   **数据库持久化**：使用 SQLAlchemy 和 SQLite（可轻松更换为其他数据库）持久化存储所有平台、模型和用户配置，确保数据安全和状态一致。
*   **动态 LLM 实例**：通过 `get_user_llm` 方法，可根据用户 ID 动态生成一个配置好的 `langchain_openai.ChatOpenAI` 实例，无缝集成到 LangChain 生态。
*   **完善的 CRUD 操作**：提供完整的接口用于添加、删除、重命名和显隐控制平台与模型。
*   **配置自动修复**：当用户的模型选择因平台更新而失效时，系统会自动为其切换到第一个可用的默认模型，保证服务的连续性。
*   **远程模型探测**：内置 `probe_platform_models` 功能，可以探测一个符合 OpenAI API 规范的端点，并返回其可用的模型列表，方便用户快速添加。

## 🚀 快速开始

### 1. 环境准备

**安装依赖库：**

```bash
pip install langchain-openai sqlalchemy requests
```

**设置环境变量：**

在项目根目录下创建一个 `.env` 文件（或直接在操作系统中设置），用于存放系统平台的 API Key。这些 Key 将作为系统默认或在用户未提供 Key 时的备用选择。

```env
# .env

# 魔搭 ModelScope
MODELSCOPE_API_KEY="your_modelscope_api_key_here"

# 阿里云百炼
ALIYUN_API_KEY="your_aliyun_api_key_here"

# OpenRouter
OPENROUTER_API_KEY="your_openrouter_api_key_here"

# 自定义 Gemini 代理
GEMINIX_API_KEY="your_gemini_api_key_here"
```

*注意：代码会自动加载这些环境变量。*

### 2. 配置管理器

在代码的顶部，您可以根据需求修改核心配置：

```python
# 当 user_id = '-1' 时，代表系统运行于无用户/全局单用户模式
SYSTEM_USER_ID = "-1"

# 如果为True，则当用户无apikey时，将尝试自动获取服务器apikey密钥
# ⚠️如果不想给用户免费提供apikey，请保持此项为False
LLM_AUTO_KEY = True 

# 如果为True，则所有用户均使用系统平台配置，不能创建自己的平台和模型（模式 2）
# 如果为False，则用户可以自由拓展自己的平台（模式 3）
USE_SYS_LLM_CONFIG = True 

# 系统内置平台模型模板
# 您可以在这里修改、添加或删除默认的系统平台
DEFAULT_PLATFORM_CONFIGS: Dict[str, Any] = {
    "魔搭ModelScope": {
        "base_url": "https://api-inference.modelscope.cn/v1/",
        "api_key": MODELSCOPE_API_KEY,
        "models": {
            # ... models
        },
    },
    # ... other platforms
}
```

### 3. 初始化

在您的应用启动时，务必调用初始化函数。它会完成以下工作：
1.  根据 `DEFAULT_PLATFORM_CONFIGS` 同步系统平台和模型到数据库。
2.  确保系统用户 (`SYSTEM_USER_ID`) 拥有默认配置。

```python
from your_module import init_default_llm, LLM_Manager

# 在应用启动时执行
init_default_llm()
```

## 📖 使用示例 (API)

`AIManager` 类提供了一个名为 `LLM_Manager` 的全局单例，您可以直接导入并使用。

### 获取 LLM 实例

这是最常用的功能。根据用户 ID 获取一个为他配置好的 LangChain LLM 实例。

```python
from your_module import LLM_Manager

# 获取特定用户的LLM实例（例如 user-001）
# 管理器会自动处理该用户的平台、模型和API Key选择
try:
    llm = LLM_Manager.get_user_llm(user_id="user-001")
  
    # 直接使用
    response = llm.invoke("你好，请介绍一下你自己。")
    for chunk in response:
        print(chunk.content, end="")

except ValueError as e:
    print(f"获取LLM失败: {e}") # 例如，API Key未设置

# 在全局单用户模式下，不传递 user_id 或使用 SYSTEM_USER_ID
# llm_sys = LLM_Manager.get_user_llm() 
```

### 获取用户可选的模型列表

为前端提供渲染所需的模型列表，包含了平台信息。

```python
# 获取 user-001 可见的所有模型（包括系统平台和他的私有平台）
all_models = LLM_Manager.get_platform_models(user_id="user-001")

for model_info in all_models:
    if not model_info["platform_hide"]: # 过滤掉用户隐藏的平台
        print(
            f"平台: {model_info['platform_name']} "
            f"(ID: {model_info['platform_id']}), "
            f"模型: {model_info['display_name']} "
            f"(ID: {model_info['model_id']}), "
            f"API Key是否已设置: {model_info['api_key_set']}"
        )
```

### 管理用户配置

```python
user_id = "user-002"

# 1. 保存用户的模型选择
# 假设用户在前端选择了平台ID为2，模型ID为5
LLM_Manager.save_user_selection(user_id=user_id, platform_id=2, model_id=5)

# 2. 更新平台的 API Key
# 如果是系统平台，则为该用户单独存储Key；如果是私有平台，则直接更新。
LLM_Manager.update_platform_config(user_id=user_id, platform_id=1, api_key="sk-xxxxxx")

# 3. 切换平台的可见性
# 隐藏平台ID为3的平台
LLM_Manager.toggle_platform_visibility(user_id=user_id, platform_id=3, hide=True)
```

### 管理自定义平台 (仅在 `USE_SYS_LLM_CONFIG = False` 时有效)

```python
user_id = "user-003"
try:
    # 1. 添加一个私有平台
    new_platform = LLM_Manager.add_platform(
        user_id=user_id,
        name="我的专属平台",
        base_url="https://api.example.com/v1",
        api_key="my-private-key"
    )
    platform_id = new_platform.id
    print(f"平台 '{new_platform.name}' 添加成功，ID: {platform_id}")

    # 2. 为新平台添加模型
    new_model = LLM_Manager.add_model(
        user_id=user_id,
        platform_id=platform_id,
        model_name="custom-model-v1",
        display_name="自定义模型V1"
    )
    print(f"模型 '{new_model.display_name}' 添加成功")

    # 3. 删除模型
    # LLM_Manager.delete_model(user_id=user_id, model_id=new_model.id)

    # 4. 删除平台（会级联删除其下所有模型）
    # LLM_Manager.delete_platform(user_id=user_id, platform_id=platform_id)

except ValueError as e:
    print(f"操作失败: {e}")
```

### 探测远程平台

在用户添加自定义平台前，可以提供一个探测功能，帮助用户发现可用模型。

```python
try:
    available_models = LLM_Manager.probe_platform_models(
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-or-v1-xxxxxxxx"
    )
    if available_models:
        print("发现以下模型:")
        for model in available_models:
            print(f"- {model['id']}")
except (PermissionError, RuntimeError) as e:
    print(f"探测失败: {e}")

```

## 🏛️ 架构与设计

### 数据库模型

管理器使用 SQLAlchemy ORM 定义了以下数据表：

*   `llm_platforms`: 存储平台信息，通过 `is_sys` 字段区分系统平台和用户私有平台。
*   `llm_platform_models`: 存储模型信息，并与平台表关联。
*   `llm_sys_platform_keys`: **核心设计之一**。当用户为**系统平台**提供自己的 API Key 时，记录会存储在这张表中，实现了用户 Key 与系统平台的解耦。
*   `user_ai_configs`: 存储每个用户的当前模型选择（`selected_platform_id` 和 `selected_model_id`）。

### 核心逻辑

*   **`AIManager` 类**: 作为所有操作的中心控制器，管理数据库会话、缓存和业务逻辑。
*   **配置同步 (`_sync_default_platforms`)**: 应用启动时，将代码中定义的 `DEFAULT_PLATFORM_CONFIGS` 与数据库同步，确保系统平台的权威性。
*   **API Key 解析 (`_get_effective_api_key`)**: 这是一个统一的内部方法，根据平台类型（系统/私有）和用户 ID，按照预设的优先级（用户自定义 Key > 系统环境变量 Key）返回最终有效的 API Key。
*   **选择解析与修复 (`_resolve_user_choice`)**: 在获取 LLM 实例时，此方法会验证用户当前的选择是否有效（如平台、模型是否存在，是否有权限等）。如果配置失效，它会自动触发回退机制，为用户选择一个可用的系统模型，并更新其配置。

---
