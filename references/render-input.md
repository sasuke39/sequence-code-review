# 固定 HTML 生成入口

复制 `assets/review.example.json`，替换真实代码数据，执行：

```sh
python3 ~/.codex/skills/sequence-code-review/scripts/render_review.py review-data.json --output review.html
```

Python 标准库即可运行，无网络、无 CDN、无 Mermaid 安装依赖。HTML 内嵌固定 CSS、交互 JS 与 SVG，直接离线打开。示例路径是占位符，不能用于真实代码审查。

字段：
- title：侧栏标题。
- files：独立从 Git 采集的文件清单，id 唯一；path 为绝对路径，line 是业务跳转行，kind 是 original/added/updated/deleted，description 是文件用途，changed=false 表示仅作为原有上下文。
- chains：id、title、participants（唯一参与者名字，至少两个）、steps、files（额外支撑文件ID）。
- steps：from/to 引用参与者；kind 标记改动类型；method 是方法或操作名；description 是中文业务说明；file 引用文件ID；line 可选，默认文件业务改动行。condition 可选，显示业务分支条；async=true 使用虚线消息。

每步骤一个代码链接；两个不同方法拆两条步骤。支持自调用。复杂嵌套分支先拆成独立链路，当前渲染器的 condition 是分支说明条，不是嵌套 UML alt/end 语法。长方法名或很多参与者需要视觉检查后拆图，不通过缩小到不可读来掩盖问题。

默认适应宽度，图内拖动，文件列表折叠；顶部不显示宣传标题、事件流水、警告段落或操作说明。

生成器拒绝缺失业务说明、重复ID、非法文件引用及清单中有文件未映射的情况，并输出 review.coverage.json。该校验只核对输入数据，不能证明输入清单是全部 Git 改动；仍按 SKILL.md 独立核对 Git 快照及实际行号。删除文件请用独立删除说明与基线diff入口，目前 IDEA 文件跳转仅适用于存在的文件，不把示例渲染器当作完整的删除导航支持。

## 传入方式：JSON 文件路径，不传 HTML

1. 读取源码和 Git 清单，填写 UTF-8 编码的 `review-data.json`。只写合法 JSON，不包 Markdown 代码围栏，不写注释或尾逗号。
2. 第一个位置参数是该 JSON 文件路径；`--output` 是输出 HTML 文件路径。路径带空格时用引号。
3. 脚本同时生成同名 `.coverage.json`。退出码非0表示失败，修正输入后再运行，不交付旧 HTML 冒充新结果。

```bash
python3 "$HOME/.codex/skills/sequence-code-review/scripts/render_review.py" \
  "/absolute/path/review-data.json" \
  --output "/absolute/path/review.html"
```

不通过 stdin、命令行 JSON 字符串或脚本源码传业务数据。不修改 renderer、CSS 或 JS 来适配某次需求；输入无法表达的业务结构应明确说明，再扩展统一契约。

## 字段契约

根对象：

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| title | string | 是 | 侧栏及浏览器标题 |
| files | array<File> | 是 | 独立采集的文件清单；不要只列已经画到的文件 |
| chains | array<Chain> | 是 | 按展示顺序排列的业务链路 |

File：

| 字段 | 类型 | 必填/默认 | 含义 |
|---|---|---|---|
| id | string | 是 | 全包唯一，如 F001；多仓同名文件使用不同ID |
| path | string | 是 | 当前机器代码文件绝对路径，不是URL |
| line | integer | 是 | 从1开始，当前文件首个有业务意义的变更行；排除import等文件头改动，原有文件用相关定义行 |
| kind | string | 是 | original、added、updated、deleted 四选一 |
| description | string | 是 | 此文件在链路中的业务用途或改动说明 |
| changed | boolean | 否，true | 是否属于本次变更清单；原有上下文文件填false |

Chain：

| 字段 | 类型 | 必填/默认 | 含义 |
|---|---|---|---|
| id | string | 是 | 全包唯一，建议英文数字连字符，如 order-create |
| title | string | 是 | 该图业务名称，不必自己添加序号 |
| description | string | 是 | 链路的业务目的、触发动作、处理结果及此次改动作用，显示于图标题下方 |
| participants | array<string> | 是 | 从左到右的主体名称，至少两个且不重复 |
| steps | array<Step> | 是 | 从上到下排列的调用步骤 |
| files | array<string> | 否，空数组 | 额外支撑文件ID，如DTO、SQL、配置、测试；与步骤文件去重后生成本图文件区 |

Step：

| 字段 | 类型 | 必填/默认 | 含义 |
|---|---|---|---|
| from | string | 是 | 调用方，必须精确匹配participants中的名称 |
| to | string | 是 | 被调用方，可等于from表示自调用 |
| kind | string | 是 | original、added、updated、deleted 四选一 |
| method | string | 是 | 一个方法名或一个操作名称；禁止“A或B”共用一个入口 |
| description | string | 是 | 简洁中文说明该步骤的判断、处理、结果，不能只重复方法名 |
| file | string | 是 | files中的文件ID，作为本步骤点击目标 |
| line | integer | 否，使用File.line | 从1开始；原有方法定位定义行，更新方法可定位方法内改动行 |
| condition | string | 否，不显示 | 此步骤适用的类型/枚举/分支说明；不是可执行表达式 |
| async | boolean | 否，false | true画虚线消息；异步具体语义仍需description解释 |

`original/added/updated/deleted` 分别显示“原有/新增/更新/删除”。模型填写枚举英文值，不填写中文或自创值。

## 最小完整示例

```json
{
  "title": "订单创建需求审查",
  "files": [
    {
      "id": "F001",
      "path": "/workspace/order/src/OrderService.java",
      "line": 32,
      "kind": "updated",
      "description": "按订单类型计算数量并保存",
      "changed": true
    },
    {
      "id": "F002",
      "path": "/workspace/order/src/OrderDTO.java",
      "line": 18,
      "kind": "updated",
      "description": "新增数量字段，向下游传递计算结果",
      "changed": true
    }
  ],
  "chains": [
    {
      "id": "order-create",
      "title": "创建订单：分类计算并保存",
      "description": "接收订单创建消息并计算数量，保存后提供给交易下发；说明外部订单在原链路中的新增处理。",
      "participants": ["消息消费者", "订单服务"],
      "steps": [
        {
          "from": "消息消费者",
          "to": "订单服务",
          "kind": "updated",
          "method": "createOrder",
          "description": "根据订单实际SKU计算数量，校验通过后保存。",
          "file": "F001",
          "line": 40,
          "condition": "外部订单分支，实际类型需从源码核实",
          "async": false
        }
      ],
      "files": ["F002"]
    }
  ]
}
```

示例中，点击图上的createOrder跳到第40行；展开“本图全部文件”后，F001跳到业务改动行32，F002跳到18。模板中的路径、行号和业务均为示意，生成真实审查包时必须替换，不能照抄。


## 跳转元数据

填写line前必须读取 [navigation-lines.md](navigation-lines.md)。File可额外填写：
- firstChangedLine：Git hunk原始首改行，仅用于审计，不作为链接目标。
- navigationReason：为什么选择line，例如“第4行仅import，跳到第86行新增校验”。

生成器直接使用File.line或Step.line，不做语言语义解析。当前额外元数据保存在输入JSON中，不显示于页面；Git覆盖证明与跳转有效性仍应独立验证。

链路description必须由模型阅读源码后填写，不能由标题拼接或空泛描述。通常2～3句，说明谁在什么情况下触发、做了什么、结果给谁用，必要时说明适用类型及原逻辑影响。左侧目录按chains顺序自动编号，可收起为编号栏；无需模型传入HTML、序号或导航布局。
