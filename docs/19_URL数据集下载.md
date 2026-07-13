# URL 下载数据集汇总

> 基于 YouTube URL 的视频数据集，通过 yt-dlp 批量下载。
> 最后更新：2026-07-13

---

## 一、已提取 URL 的数据集

### Action100M (Meta, 2026)

| 维度 | 详情 |
|------|------|
| 总 URL 数 | 60,000（preview 10%，全量 147M） |
| 已下载 | 24 videos（450MB） |
| 格式 | 360p MP4（format 18） |
| 来源 | `facebook/action100m-preview` on HuggingFace |
| URL 文件 | `dataset/url_datasets/youtube_urls_full.txt` |
| 下载命令 | `yt-dlp --cookies cookies_netscape.txt --js-runtimes deno --remote-components ejs:github -a youtube_urls_full.txt` |

### InternVid (上海 AI Lab, 2024)

| 维度 | 详情 |
|------|------|
| 规模 | 10M 视频 URL（FLT 子集） |
| 状态 | 需申请访问权限（gated repo） |
| 来源 | `OpenGVLab/InternVid-10M-FLT` on HuggingFace |
| 备注 | 已申请，等待审批 |

---

## 二、YouTube URL 下载方案

### 可工作配置

```bash
yt-dlp \
  --cookies /path/to/cookies_netscape.txt \
  --js-runtimes deno \
  --remote-components ejs:github \
  --download-archive downloaded.txt \
  --format "18/best[height<=720]" \
  --output "videos/%(id)s.%(ext)s" \
  --concurrent-fragments 2 \
  --sleep-interval 2 --max-sleep-interval 8 \
  --no-playlist \
  -a youtube_urls.txt
```

### Cookies 格式转换

```python
import json
with open('www.youtube.com_YYYY-MM-DD.json') as f:
    data = json.load(f)
with open('cookies_netscape.txt', 'w') as f:
    f.write('# Netscape HTTP Cookie File\n')
    for c in data['cookies']:
        f.write(f"{c['domain']}\tTRUE\t{c['path']}\tTRUE\t{int(c['expirationDate'])}\t{c['name']}\t{c['value']}\n")
```

### 注意事项

1. **Cookies 过期**：每 1-2 小时需从浏览器重新导出 JSON → 转换为 Netscape 格式
2. **限流**：每次限流 1 小时后恢复，建议 sleep 间隔 ≥ 2s
3. **断点续传**：`--download-archive` 自动跳过已下载视频
4. **视频可用性**：部分旧视频已删除/私有，会自动跳过

---

## 三、其他 URL 数据集（待处理）

| 数据集 | 规模 | URL 数量 | 状态 |
|--------|------|---------|------|
| Panda-70M | 70M clips | YouTube URLs | 未提取（HF 404） |
| HD-VILA-100M | 100M clips | YouTube URLs | 未提取（HF 404） |
| WebVid-10M | 10M clips | YouTube URLs | 未提取（HF 404） |
| InternVid | 10M | YouTube URLs | 需授权 |
| MiraData | 长片段 | YouTube URLs | 未提取 |
| CelebV-HQ | 高质量人脸 | YouTube URLs | 需法务审核 |

---

## 四、下载进度

| 日期 | Cookies | 下载 | 累计 |
|------|---------|------|------|
| 07-13 | 第1次 | 24 videos (450MB) | 24 |
