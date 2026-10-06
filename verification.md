# 签到修复验证

## 故障依据

- 2026-10-05：[Actions 37261390652](https://github.com/zzdccww/Rainyun-Qiandao/actions/runs/37261390652)。
- 2026-10-06：[Actions 37415170629](https://github.com/zzdccww/Rainyun-Qiandao/actions/runs/37415170629)。
- 两次运行均安装 ddddocr 1.5.6，检测到 3～5 个候选框；SIFT 最低匹配率为 0.0000 或 0.0400，五次重试后签到失败，最终统计均为 `签到 0/1`。
- 策略选择原来只判断结果对象是否存在，导致低分 SIFT 结果阻断模板策略。调度入口在业务失败后仍返回 0，因此 Actions 显示成功。

## 改动与兼容性

- 根据 [PyPI 官方发布页](https://pypi.org/project/ddddocr/)，固定使用 ddddocr 1.6.1，保持 Python 3.11 和 CPU 推理。
- OCR 与检测实例按新版 API 明确区分，移除旧版本初始化回退及 Pillow 全局兼容补丁。
- 每个匹配策略先校验三个唯一坐标和有限、达标的匹配率，再决定是否命中；不合格结果继续尝试下一策略。
- 常量图返回零模板匹配率，避免 OpenCV 将无有效特征的图片视为完美匹配。
- Linux 使用 headless OpenCV，Windows/macOS 使用标准 OpenCV，避免两个包覆盖同一 `cv2` 模块。
- 签到失败或续费检查结果标记失败时，完成通知后返回 1；已经签到和未配置 API Key 的续费跳过不算失败。
- Actions 的失败日志步骤读取宿主机挂载路径，避免误读只存在于容器内的 `/logs`。

## 验证结果

- Python 源码编译：通过。
- Workflow YAML、四段 shell、内嵌配置生成 Python 和入口 shell 语法：通过。
- `python -m unittest discover -s tests -v`：19 项测试全部通过，包含实际 OCR/检测模型推理、合成小图匹配、无效策略切换和调度通知/退出码验证。
- `uv pip check --python .venv/Scripts/python.exe`：27 个已安装依赖兼容。
- Linux Python 3.11 依赖解析：通过；ddddocr 1.6.1、OpenCV headless 4.12.0.88、NumPy 2.2.6 和 ONNX Runtime 1.30.0 可共同解析。

## 发布与验证边界

本地 Docker 引擎不可用；容器构建已在下述 GitHub Actions 运行中通过。本地测试没有登录真实账号、执行续费或发送通知；经用户批准后的线上验证使用现有账号和配置。合成图片只能验证策略切换和模型 API，无法证明当前线上验证码必然识别成功。

2026-10-06 已将修复提交 `a5776e417b21f0dd0f7121dffddbe52330556df9` 推送到 main，并手动触发 [Actions 37486870893](https://github.com/zzdccww/Rainyun-Qiandao/actions/runs/37486870893)。本次容器确认安装 ddddocr 1.6.1，任务与 workflow 均成功。北京时间 23:23 的业务日志确认：

- 今日已签到（每日签到模块显示“已完成”），跳过签到流程。
- 签到 `1/1`，续费检查 `1/1`。
- Telegram 推送成功。

本次属于“已签到”路径，未执行线上验证码识别；下一次尚未签到的定时运行才可验证真实验证码效果。验收时需同时查看 Actions 状态和业务日志，最终统计应为 `签到 1/1`；仅构建成功不能视作签到成功。无需变更 Secrets 或迁移数据，workflow 会重新构建镜像。

如需回滚，撤销本次修复提交并重新构建镜像。恢复旧调度入口会再次出现业务失败但 Actions 显示成功的行为。
