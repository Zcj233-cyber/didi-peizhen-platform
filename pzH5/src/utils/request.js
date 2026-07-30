import axios from 'axios'
import { showToast } from 'vant'

const http = axios.create({
    baseURL: 'http://localhost:2306/v3pz',
    timeout: 120000,  // AI接口调用DeepSeek较慢，设为120秒
    headers: {
        "terminal": "h5"
    }
})

// 添加请求拦截器
http.interceptors.request.use(function (config) {
    const token = localStorage.getItem('h5_token')
    const whiteUrl = ['/login']
    if (token && !whiteUrl.includes(config.url)) {
        config.headers['h-token'] = token
    }
    return config;
}, function (error) {
    return Promise.reject(error);
});

// 添加响应拦截器
http.interceptors.response.use(function (response) {
    const code = response.data.code
    const message = response.data.message || response.data.msg || '请求失败'
    // 后端成功码为 10000
    if (code !== 10000) {
        // token 相关错误 → 跳转登录页
        if (code === -2 || message.includes('token')) {
            localStorage.removeItem('h5_token')
            localStorage.removeItem('h5_userInfo')
            showToast({ type: 'fail', message })
            window.location.href = '#/login'
        } else {
            showToast({ type: 'fail', message })
        }
    }
    return response;
}, function (error) {
    return Promise.reject(error);
});

export default http