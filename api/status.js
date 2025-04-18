// api/status.js
import { kv } from '@vercel/kv'; // 这个库会自动使用 Vercel 注入的环境变量连接 KV

// --- 你自己定义的安全令牌 ---
// *** 这里是你需要修改的第一个地方 ***
// 将 'YOUR_SECRET_TOKEN_HERE' 替换成一个 *你自己设定* 的复杂密码串。
// 这个密码是你之后从摄像头程序发送请求时需要提供的凭证。
const SECRET_TOKEN = 'hibo2352'; 
// ----------------------------

const STATUS_KEY = 'office_status'; // 在 KV 存储中使用的键名

export default async function handler(request, response) {
  // --- CORS 配置 ---
  // *** 这里是你需要修改的第二个地方 ***
  // 将 'https://only4john.github.io' 替换成你实际的 GitHub Pages URL!
  // (看起来你的用户名是 only4john，所以这个 URL 应该是正确的，但请确认)
  const allowedOrigin = 'https://only4john.github.io'; 
  response.setHeader('Access-Control-Allow-Origin', allowedOrigin);
  response.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  response.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization'); 
  // ------------------

  // 处理 CORS 预检请求
  if (request.method === 'OPTIONS') {
    return response.status(200).end();
  }

  // --- 处理 GET 请求 (获取当前状态) ---
  if (request.method === 'GET') {
    try {
      const currentStatus = await kv.get(STATUS_KEY); 
      const statusToSend = currentStatus || 'out'; 
      return response.status(200).json({ status: statusToSend });
    } catch (error) {
      console.error('Error getting status from KV:', error);
      return response.status(500).json({ error: 'Failed to retrieve status' });
    }
  }

  // --- 处理 POST 请求 (更新状态) ---
  if (request.method === 'POST') {
    try {
      // 1. 验证安全令牌 (比较请求中提供的令牌和你上面设定的 SECRET_TOKEN)
      let providedToken = null;
      const authHeader = request.headers['authorization'];
      if (authHeader && authHeader.startsWith('Bearer ')) {
        providedToken = authHeader.substring(7); 
      } else if (request.body && request.body.token) {
        providedToken = request.body.token; 
      }
      
      if (providedToken !== SECRET_TOKEN) {
        return response.status(401).json({ error: 'Unauthorized: Invalid token' });
      }

      // 2. 获取并验证状态值
      const { status } = request.body; 
      if (status === 'in' || status === 'out') {
        await kv.set(STATUS_KEY, status); 
        return response.status(200).json({ message: 'Status updated successfully', status: status });
      } else {
        return response.status(400).json({ error: 'Invalid status value. Use "in" or "out".' });
      }
    } catch (error) {
      console.error('Error updating status:', error);
      return response.status(500).json({ error: 'Failed to update status' });
    }
  }

  // --- 处理不支持的 HTTP 方法 ---
  response.setHeader('Allow', ['GET', 'POST', 'OPTIONS']); 
  return response.status(405).end(`Method ${request.method} Not Allowed`);
}