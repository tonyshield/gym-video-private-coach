# Gym Video Private Coach · 私人健身视频教练

把一组普通健身房训练视频变成有证据、能执行的反馈：**这组怎样、先改什么、下一组怎么试、下次如何复查**。

面向普通成年健身者，首版中文。覆盖深蹲、髋铰链/硬拉、卧推/俯卧撑、肩推、划船、下拉/引体、腿举等基础器械、单腿及基础核心。器械、自重、哑铃和杠铃都可用，不要求练三大项。

## 第一版包含什么

- 可安装的中文 Skill，按组和重复复盘，给出原片时间证据。
- 对应动作的观察清单、可调整口令、拍摄建议和判断边界。
- 下一组/下次安排和条件允许时的历史比较。
- 本地抽帧辅助工具，不上传原片，不依赖姿态模型。
- 开源用 MIT 许可证、贡献说明与人工行为验收用例。

这是由具备视觉能力的助手执行的 Skill，不是独立训练 App。自动计数、姿态识别和自动标注视频不属于首版脚本功能；助手可按可用工具制作证据媒体，做不了会说明。尚未用真实健身视频验证教练效果。

## 安装

仓库内 [`skills/gym-video-private-coach-zh`](skills/gym-video-private-coach-zh) 是完整 Skill，可复制到支持 `SKILL.md` 的工具中。不同工具的发现路径与视频能力需分别确认。

Codex 本地目录的安装示例（在仓库根目录运行）：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/gym-video-private-coach-zh "${CODEX_HOME:-$HOME/.codex}/skills/"
```

若已有同名 Skill，先检查其内容，不直接覆盖。此仓库是开发源；复制安装后，仓库修改不会自动同步到安装副本。让客户端重新加载技能列表后使用。未自动修改任何已安装 Skill。

## 使用

上传训练视频或给出本地视频路径，例如：

> 请用 $gym-video-private-coach-zh 看这组高位下拉。我练了两个月，最关心后半组为什么越来越晃。重量标的是第 5 档，每周练两次，目前没有疼痛。先给我最值得改的一点和下一组怎么试。

其他请求：

- “看这组杯式深蹲，帮我找一个可保留的重复和一个需要调整的重复，附时间点。”
- “这是上周和这周的划船，器械相同但重量变了，哪些能比较？”
- “画面看不清的话告诉我怎么补拍，别猜关节角度。”

不必先填完整问卷。关键缺口会补问；看不清、重量不明和疼痛未确认会明确标注。

## 本地视频工具

助手能直接看视频时无需额外依赖。要运行抽帧脚本，需 Python 3.10+ 和 FFmpeg/ffprobe，无第三方 Python 包：

```bash
python3 skills/gym-video-private-coach-zh/scripts/sample_video.py \
  '/path/to/training.mov' --out '/path/to/private-review/overview' --every 2
```

输出目录必须是新目录；默认最多 48 帧，超限明确报错。输出为图像与时间清单，不是动作分析结果。用法及时间精度限制见 [视频工作流](skills/gym-video-private-coach-zh/references/video-workflow.md)。

## 结构与质量检查

```text
skills/gym-video-private-coach-zh/
  SKILL.md
  agents/openai.yaml
  references/
    exercise-checks.md
    programming.md
    video-workflow.md
    report-format.md
    sources.md
  scripts/sample_video.py
evals/scenarios.md
```

修改后检查本地链接、Skill 前置信息及脚本帮助。运行 `python3 -m unittest discover -s tests -v` 可用合成视频检查抽帧、时间范围、非法输入与不覆盖原片。教练行为按 [验收场景](evals/scenarios.md) 人工验证；格式检查不等于临床或教练有效性验证。

## 数据与适用边界

原片与健康信息默认留本地。真实训练素材、生成帧和私人报告不能随代码提交或公开；忽略规则只是辅助。需要上传或公开时另行授权。

本项目提供一般训练教育反馈，不诊断或提供康复处方。运动中锐痛、麻木、明显肿胀等需停止相关动作并求助专业人员；胸痛、晕厥或严重异常呼吸困难需立即寻求当地急救。无法从视频证明“绝对安全”。

## 参考与许可

受 [zakezhang/tennis-video-private-coach](https://github.com/zakezhang/tennis-video-private-coach/tree/main/skills/tennis-video-private-coach-zh) 的证据复盘流程启发，按健身场景重新编写。训练原则参考 [ACSM 2026 官方概要](https://acsm.org/resistance-training-guidelines-update-2026/)，详细出处与未核实范围见 [来源](skills/gym-video-private-coach-zh/references/sources.md)。

[MIT License](LICENSE)。当前为本地开发版本，尚未配置远程仓库或发布。
