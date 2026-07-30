import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
    baseURL: 'http://localhost:2306/v3pz',
    timeout: 10000,
    headers: {
        "terminal": "admin"
    }
})

// 添加请求拦截器
http.interceptors.request.use(function (config) {
    // 在发送请求之前做些什么
    const token = localStorage.getItem('pz_token')
    // 不需要添加token的api
    const whiteUrl = ['/get/code', '/user/authentication', '/login']
    if (token && !whiteUrl.includes(config.url)) {
        config.headers['x-token'] = token
    }
    return config;
}, function (error) {
    // 对请求错误做些什么
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
            localStorage.removeItem('pz_token')
            localStorage.removeItem('pz_userInfo')
            localStorage.removeItem('pz_v3pz')
            ElMessage.error(message)
            window.location.href = window.location.origin
        } else {
            ElMessage.warning(message)
        }
    }
    return response;
}, function (error) {
    return Promise.reject(error);
});

export default http