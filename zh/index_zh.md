---
layout: default_zh
title: 费  腾
---

## 费&ensp;&ensp;腾&ensp;&ensp;FEI Teng [<img src='..\img\icon.jpg' style=' float:right; width:150px;height: px' id='profile-photo'/>](https://scholar.google.com/citations?user=yDkjL1UAAAAJ&hl=en) (<span id="status-indicator" style="font-size: 16px;">&#x25CF;</span> <span id="status-message" style="font-size: 16px;">正在查询状态...</span>)

博士， 武汉大学 资源与环境科学学院，副教授，博导   
研究方向： 城市地理大数据，生态遥感应用，地理信息科学相关  
Email: feiteng[at]whu.edu.cn  

---

## 专业兴趣: 
城市地理大数据，生态遥感应用，地理信息科学，基于位置的服务（LBS），林业遥感，高光谱遥感，自然资源管理，健康地理学，人类情绪景观，城市听觉环境 


## 受教育经历：

Twente University, the Netherlands, PhD  

武汉大学，资源与环境科学学院，博士  

ITC，the Netherlands, MSc 科学硕士  

武汉大学，遥感信息工程学院，学士  

## 研究工作经历：

2013/01 - 今，&ensp;&ensp;&ensp;&ensp;&ensp;
武汉大学，资源与环境科学学院，副教授  

2019/09 - 2020/09，伊利诺伊大学厄巴纳香槟分校（UIUC），访问学者  

2011/01 - 2013/01，武汉大学，资源与环境科学学院，讲师  

2010/07 - 2012/06，武汉大学，资源与环境科学学院，博士后研究  

## 讲授课程：

- 遥感概论
- 遥感实习
- 新生讨论课
- 地理信息科学进展
- 资源环境遥感（硕）

---

硕士研究生招生方向：地图学与地理信息科学  测绘工程

<script>
  // 使用 DOMContentLoaded 确保 HTML 元素加载完毕后再执行脚本
  document.addEventListener('DOMContentLoaded', function() {

    // --- 配置 ---
    // 您确认可用的 Vercel API 地址
    const statusApiUrl = 'https://only4john-github-io.vercel.app/api/status';
    // 获取页面上用于显示状态的元素
    const statusIndicatorElement = document.getElementById('status-indicator'); // 小圆点元素
    const statusMessageElement = document.getElementById('status-message');   // 状态文字元素
    // --- 结束配置 ---

    // 检查元素是否存在，避免在没有这些元素的页面上执行时出错
    if (!statusIndicatorElement || !statusMessageElement) {
      // 如果当前页面没有状态显示元素，就不执行后续操作
      // console.warn('此页面未找到状态显示元素。');
      return;
    }

    // 使用 fetch API 从您的 Vercel API 获取状态
    fetch(statusApiUrl)
      .then(response => {
        // 检查网络请求是否成功 (例如 200 OK)
        if (!response.ok) {
          throw new Error('网络响应错误: ' + response.status + ' ' + response.statusText);
        }
        // 解析返回的 JSON 数据，例如 {"status":"in"}
        return response.json();
      })
      .then(data => {
        // --- 根据 API 返回的状态 更新显示 ---
        let displayMessage = '状态未知';  // 默认文字
        let displayColor = 'gray';      // 默认颜色 (灰色)

        if (data && data.status) {
          // 根据 API 返回的 status 值设置不同的文字和颜色
          switch (data.status.toLowerCase()) { // 转小写以防大小写问题
            case 'in':
              displayMessage = '我在办公室里';
              displayColor = 'green';
              break;
            case 'out': // 假设您 API 会返回 'out'
              displayMessage = '我不在办公室';
              displayColor = 'red';
              break;
            // 您可以根据需要添加更多状态判断
            // case 'meeting':
            //   displayMessage = '会议中';
            //   displayColor = 'orange';
            //   break;
            default:
              // 如果 status 不是 'in' 或 'out'，显示原始状态
              displayMessage = `状态: ${data.status}`;
              displayColor = 'orange'; // 用橙色表示其他状态
          }
        }
        // --- 结束状态更新逻辑 ---

        // 将获取到的状态更新到页面上的 HTML 元素
        statusMessageElement.textContent = displayMessage;
        statusIndicatorElement.style.color = displayColor;
      })
      .catch(error => {
        // 如果在 fetch 或处理过程中发生任何错误
        console.error('获取或处理状态时出错:', error);
        // 在页面上显示错误信息
        statusMessageElement.textContent = '无法获取状态';
        statusIndicatorElement.style.color = 'gray'; // 出错时显示灰色
      });
  });
</script>