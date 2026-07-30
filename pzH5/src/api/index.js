import request from '../utils/request'

export default {
    login(data) {
        return request.post('/login', data)
    },
    index(params) {
        return request.get('/index/index', { params })
    },
    h5Companion() {
        return request.get('/h5/companion')
    },
    createOrder(data) {
        return request.post('/createOrder', data)
    },
    orderList(params) {
        return request.get('/order/list', { params })
    },
    orderDetail(params) {
        return request.get('/order/detail', { params })
    },
    // AI Agent
    agentChat(data) {
        return request.post('/agent/chat', data)
    },
    triageRecommend(data) {
        return request.post('/agent/triage/recommend', data)
    },
    visitPlan(data) {
        return request.post('/agent/visit-plan', data)
    },
    agentConversationList(params) {
        return request.get('/agent/conversation/list', { params })
    },
    agentConversationMessages(convId) {
        return request.get(`/agent/conversation/${convId}/messages`)
    },
    // 天气
    getWeather(params) {
        return request.get('/weather', { params })
    },
    // 客服评价
    submitFeedback(data) {
        return request.post('/agent/feedback', data)
    },
    // FAQ搜索
    searchFAQ(params) {
        return request.get('/agent/faq/search', { params })
    },
    // 城市列表
    getCities() {
        return request.get('/hospital/cities')
    }
}
