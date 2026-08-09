import request from "../utils/request";

export const getCode = (data) => {
    return request.post("/get/code", data);
}

export const userAuthentication = (data) => {
    return request.post("/user/authentication", data)
}

export const login = (data) => {
    return request.post("/login", data)
}

export const authAdmin = (params) => {
    return request.get("/auth/admin", { params })
}

export const userGetMenu = () => {
    return request.get("/user/getmenu")
}

export const userSetMenu = (data) => {
    return request.post("/user/setmenu", data)
}

export const menuList = (params) => {
    return request.get("/menu/list", { params })
}

export const menuSelectList = () => {
    return request.get("/menu/selectlist")
}

export const menuPermissions = () => {
    return request.get("/menu/permissions")
}

export const updateUser = (data) => {
    return request.post("/update/user", data)
}

export const photoList = () => {
    return request.get("/photo/list")
}

export const companion = (data) => {
    return request.post("/companion",data)
}

export const companionList = (params) => {
    return request.get("/companion/list", { params })
}

export const deleteCompanion = (data) => {
    return request.post("/delete/companion", data)
}

export const adminOrder = (params) => {
    return request.get("/admin/order", { params })
}

export const updateOrder = (data) => {
    return request.post("/update/order", data)
}

// ==================== AI Agent ====================

export const agentOverview = () => {
    return request.get("/agent/admin/overview")
}

export const agentBusinessStats = () => {
    return request.get("/agent/admin/business/stats")
}

export const agentFaqList = (params) => {
    return request.get("/agent/admin/faq/list", { params })
}

export const agentFaqCreate = (data) => {
    return request.post("/agent/admin/faq/create", data)
}

export const agentFaqUpdate = (data) => {
    return request.post("/agent/admin/faq/update", data)
}

export const agentFaqDelete = (data) => {
    return request.post("/agent/admin/faq/delete", data)
}

export const agentAdminChat = (data) => {
    return request.post("/agent/chat", data)
}

// ==================== Admin 智能运营中心 ====================

export const adminDashboard = () => {
    return request.get("/agent/admin/dashboard")
}
