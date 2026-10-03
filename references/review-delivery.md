# 快照、覆盖与导航实现要点

## Git 清单

每仓使用固定的已核实基线 SHA。下面是信息源，不把 `master` 当作默认需求基线：

```sh
git rev-parse HEAD
git status --porcelain=v1 -z
git diff --name-status -z --find-renames BASE HEAD
git diff --name-status -z --find-renames HEAD
git diff --cached --name-status -z --find-renames
git ls-files --others --exclude-standard -z
git diff --no-ext-diff --unified=0 BASE -- path/to/file
```

通过 Python subprocess 参数数组执行并解析 NUL 分隔的名字，支持空格、中文、重命名；不用 shell 拼接用户路径。最终状态以工作区相对基线的净变化为主，同时单列已提交但暂存区/工作区又反向覆盖的情况。用 diff hunk 的新文件 `+start,count` 记录原始首变更行（firstChangedLine），再按 navigation-lines.md 选择业务跳转行；count=0 的删除 hunk 定位邻近有效行并明确是删除，不伪造新增行。完全删除文件跳基线 diff，不链接不存在的本地文件。

生成快照指纹：基线与 HEAD SHA、diff 字节、未跟踪文件路径及内容摘要；二进制和子模块记录各自类型和摘要/提交。不能仅比较 HEAD，因为工作区可变。不要把凭据文件内容写入审查页面。

多仓键用 `(repoId, relativePath)`，禁止只按文件名去重。重命名保存 oldPath/newPath。

建议交付文件：`review.html`、`inventory.json`、`mapping.json`、`coverage.json`、图源目录。输出放用户指定目录；本地预览如需忽略按用户要求处理，不擅改仓库配置。

## 映射验证

每个文件至少一条可见图节点或图内支持文件入口，不能仅在页尾清单里挂链接就算“图上覆盖”。

集合核对：
- expected = Git 净变更与显式记录的暂存特殊项
- mapped = 有真实渲染节点和可点击入口的文件
- missing = expected - mapped - explicit_exclusions
- dangling = mapped - expected（原有上下文文件单独分类，不当悬空）

排除理由公开展示；有排除项时用“范围内覆盖X/X，另排除Y项”，不说“所有Git改动100%覆盖”。映射覆盖和人工已读数量分别显示。

## IDEA 链接

可尝试当前机器已注册的 IDEA 协议，例如：

```text
idea://open?file=<URL编码后的绝对文件路径>&line=<1-based行号>
```

不同 IDEA 版本、Toolbox 和浏览器可能不支持同一协议，应先验证实际打开效果；不要自动安装插件、更改 IDE 设置或建立未鉴权文件执行服务。备用入口提供可复制绝对路径、行号和本地文件链接。

每个链接的目标路径与行号来自同一份 mapping.json。覆盖入口定位首个业务变更行；方法步骤可定位具体定义或方法内改动行并注明区别。重新改代码后必须重新选择并校验业务跳转行。

## 业务步骤例子

```text
【原有】consumeCreateOrder
接收创建消息，按 OrderTypeEnum 分派订单类型。

alt 达人外部订单（实际枚举值从源码填写）
  【更新】calculateQuantity
  使用订单实际 SKU 的价格计算数量，失败时阻止下发并告警。
else 其他订单
  【原有】buildOrder
  沿用原字段来源；说明这一分支实际涵盖哪些类型。
end

【更新SQL】saveOrder → Mapper.xml:首变更行
保存新增数量与单价字段。
【更新DTO】OrderDTO.java:首变更行
向原交易组装链路传递新增字段。
```

这是结构示例，不能直接当作任意项目的真实业务事实。实际图应标清谁调用谁、事务边界与下游行为。
