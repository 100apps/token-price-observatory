# Token Atlas · 模型价格观察站

公开、无需 API Key 的静态模型价格计算器。默认输入与输出各 **100,000,000 token**，缓存命中率 **90%**；可切换到一百万。每天抓取公开价格，保留不可覆盖的历史快照与原始证据。

- 页面：https://100apps.github.io/token-price-observatory/
- 数据：[latest.json](data/latest.json)
- 快照索引：[history/index.json](data/history/index.json)
- 自动任务：[Daily prices and GitHub Pages](https://github.com/100apps/token-price-observatory/actions/workflows/daily.yml)

## 功能

1. 输入、输出、缓存命中率计算；平台/模型搜索、数据来源筛选、价格排序、按平台分组展开报价详情。
2. 相同模型 ID 的跨平台候选比价，保留地区、模式、上下文和服务等级差异；不宣称所有候选具备相同服务质量。
3. 逐报价的输入、缓存、输出历史折线和快照下载。默认最近 30 次，可选 90 次或全部；只展示真实采集历史。
4. 每行官方链接、数据来源类型、采集时间、旧数据状态、原始证据与抓取失败信息。
5. USD / CNY 显示，汇率由用户输入；默认 7.2 仅是估算假设。

## 来源调研与覆盖策略

自动探测的来源清单在 `scripts/collect.py` 的 `SOURCES` 中。**官方页面成功归档，不等于该平台所有价格均已结构化解析。** 页面显式区分官方直采、社区目录与仅归档；不能把社区目录当作已核验的厂商现价。

| 平台 | 每日读取来源 | 当前结构化方式 |
| --- | --- | --- |
| OpenRouter | 官方 `/api/v1/models` | 官方输入、输出、缓存 token 价及全量文本输出模型 |
| 阿里云百炼 | `help.aliyun.com/zh/model-studio/model-pricing` | 百炼官方价格表；按地区、上下文阶梯、思考/非思考模式拆行；不使用阿里云旧模型页代替百炼报价 |
| DeepSeek | 官方 `quick_start/pricing.md` | 官方忙时/闲时、输入缓存命中/未命中和输出价；保留官方 UTC 时段、周末和中国法定节假日条件 |
| OpenAI | 官方 API pricing | 官方文本价格表，区分 Standard、Batch、Fast 等服务等级；缓存写入价格保留详情 |
| Anthropic | Claude 官方 pricing | 官方文本和缓存读取表；上下文限制、缓存写入保留详情 |
| DeepInfra | 官方公开模型目录 API | 可用文本生成模型和 token 计费；美分/token 转美元/百万 token |
| 硅基流动 | 官方 pricing | 页面可见对话模型价格，分时段、上下文阶梯和缓存读取价；折叠未渲染的型号不猜价 |
| MiniMax | 官方 pay-as-you-go 文档 | 可无歧义解析的文本报价；同格原价/折扣并列的报价不猜测 |
| Google Gemini | 官方 pricing 文档 | 官网归档 + LiteLLM 社区目录；重定向或动态页面不冒充解析成功 |
| 月之暗面 Kimi | 官方模型推理价格文档 | 官网归档 + LiteLLM 社区目录 |
| 智谱 / Z.ai | 国内文档与 Z.ai pricing | 官网归档 + LiteLLM 社区目录；国内与国际站报价不可直接等同 |
| 火山方舟 | 官方模型价格文档 | 官网归档 + LiteLLM 社区目录 |
| 腾讯混元 | 官方计费文档 | 官网归档 + LiteLLM 社区目录 |
| Mistral、xAI | 官方价格/模型文档 | 官网归档 + LiteLLM 社区目录 |
| Together AI、Fireworks | 官方 pricing | 官网归档 + LiteLLM 社区目录 |
| AWS Bedrock、Azure OpenAI | 官方 pricing | 官网归档 + LiteLLM 社区目录；区域、吞吐套餐与附加条款保留详情 |

社区目录为 [BerriAI/LiteLLM](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)，每条保留目录链接及官方来源链接。官方同平台同模型已成功解析时优先使用官方数据。社区已经注明下线的条目不展示，但未注明下线不构成可用性保证。

**覆盖边界：** 这不是所有平台所有型号的全量已核验价格库；当前有部分官方直采及明确标识的社区补充。动态页面、登录墙、复杂促销和未识别结构会保留证据并标记未解析，不以硬编码旧价伪装实时价格。

## 计费口径

所有结构化单价都是原始币种的 **每百万 token**：

```text
(inputTokens × ((1 − hitRate) × inputPrice + hitRate × cacheReadPrice)
 + outputTokens × outputPrice) / 1,000,000
```

- 缓存价未知时按普通输入价估算，并显示提示；`0` 和未知值 `null` 严格区分。
- 三项输入只能估算 token 消耗成本。缓存写入、存储、工具、搜索、图片、音频、视频、税费、最低消费不在总额中，相关报价条件留在详情和官方证据。
- 累计用量不等于单次上下文。不会拿一亿累计 token 自动套进单次上下文的最高阶梯，用户应按实际单次请求选择对应报价行。
- 忙闲时段按官方表拆成独立报价，不按浏览器当前时钟替用户猜测使用分布。DeepSeek 的时区和节假日规则保留官方文字。
- 同模型候选仅以末段模型 ID 精确匹配，不合并版本别名。不同量化、地区、SLA、服务等级、供应商路由必须自行核对。
- 官方若改变页面结构，解析不足会告警；抓取失败保留上次成功值并标记 `stale`，不改变其原始成功观测时间。

## 每日工作流

GitHub Actions 在 **每天 02:23 UTC / 北京时间 10:23** 调度，也支持手动 `workflow_dispatch`。GitHub 定时任务可能延迟，公共仓库长期无活动可能暂停调度，不能保证分钟级时效。

流程：安装固定版本解析依赖 → 单元测试 → 并行抓取公开来源（超时重试） → 规范化并验证非负有限单价 → 保存证据与快照 → 原子更新 latest → 提交数据 → 上传静态文件并部署 Pages。推送代码只测试和部署，不重复采集。

```text
data/latest.json                         # 前端唯一当前价格入口
 data/history/<UTC timestamp>.json.gz     # 每次采集完整快照；早期 .json 也兼容
 data/history/index.json                  # 按新到旧的文件列表
 data/raw/<hash-prefix>/<sha256>.*.gz      # 原始字节 gzip，无变化不重复保存
```

原始证据 SHA-256 是解压后的字节摘要。下载 `.gz` 后可用 `gzip -dc file.json.gz` 或 Python `gzip.open` 读取。网页通过浏览器 `DecompressionStream` 读取压缩历史，需要较新的浏览器。快照不覆盖旧文件；代码解析升级可能改变字段/报价拆分，比较时须核对条件。

所有采集失败时不会覆盖已有 `latest.json`。部分失败在 Actions 中显示 warning，网站“数据来源”标记失败并保留原有报价。报价非结构化成功来源显示“已归档 · 未自动解析”。

## 本地运行与验证

Python 3.12+、Node.js 22+：

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/collect.py
python -m unittest discover -s tests -v
node --test tests/calc.test.mjs
python -m http.server 8000
```

打开 `http://localhost:8000`。没有构建步骤、模型调用费用或外部付费爬取服务。

## GitHub Pages 配置

在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。Actions 需要 `contents: write`、`pages: write`、`id-token: write`。首次启用后可在 Actions 页面手动运行工作流。组织若禁止工作流写仓库或部署，需要仓库管理员调整策略。

归档会随历史增长，gzip 与内容去重减少空间占用；长期使用仍需关注 GitHub 仓库及 Pages 配额，必要时迁移旧证据到独立对象存储，并保留快照链接。

## 扩展解析器

添加来源 → 写明确单位、币种和条件的解析器 → 添加独立价格样例测试 → 加入采集器解析列表。不要把未知缓存成本填成零，不要把旧路径返回的导航页当成新价格，不要把折扣系数当作绝对单价。为每条报价保留官方来源与观测时间。

代码使用 MIT 许可；原始厂商页面与报价数据的权利归各自所有者。


## 准确性校验与分享（v1.1）

- 默认只对**过去 48 小时内、抓取成功的官方直采报价**排名。社区目录、抓取失败回退和异常隔离报价，可在“全部报价”查看，默认不推荐。
- 校验币种、有限非负单价、重复 ID 冲突；报价数量下降超过 30% 时整批拒收。任一单价变化超过 50% 或由零变收费/反向变化时，仅隔离相应报价、保留旧观测时间，其他模型继续更新。候选原文仍按 SHA-256 存档。“数据来源”提供复核告警。
- 缺少缓存单价仍会显示保守估算，不能宣称是准确账单；工具、缓存写入、税费等依旧不包含在 token 估算里。
- 百炼报价 ID 改为由模型与计费条件生成，不随价格改变；章节层级重新解析，防止上一地区标题串入本行。早期历史保留原有 ID，不推断合并不同地区的旧记录。
- 官方抓取样例固定在 `tests/fixtures/`，以独立写定的金额检查美元/人民币、百万 token 换算、缓存和忙闲分档。`sources.json` 的 SHA-256 指向原始完整文档，fixture 可能只摘录其中表格并补充编码元信息。
- 异常是真调价还是页面结构改变，需要维护者点开官方文档复核；核对后可运行 `python scripts/collect.py --accept-source PROVIDER=SHA256`。只批准完全匹配该摘要的当前文档，不绕过字段/重复冲突校验；下次抓取自动恢复常规门槛。若文档摘要已变化，会拒绝批准。审核记录写入快照的 `sources.reviewed_sha256`。
- 参数变化自动以 `history.replaceState` 同步 URL。支持 input、output、cache（百分数）、currency、fx、平台、搜索、排序、数据可信度、当前视图和历史选择。点击“复制分享链接”，打开可恢复同一组参数。非法参数回退默认值；零用量与 0% 缓存有效。
- 分享的是**计算参数**，报价采用打开时的最新快照，故以后再打开可能得到不同费用；快照本身仍可从历史页面下载。

这些门槛能发现常见单位错误、结构变化和异常调价，但不能从数学上保证厂商页面或解析器永远正确。最终账单仍取决于所选区域、模式、服务等级及官方计费规则。
