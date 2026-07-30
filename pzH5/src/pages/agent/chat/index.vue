<template>
  <div class="container">
    <van-nav-bar title="AI智能助手" left-arrow @click-left="goBack">
      <template #right>
        <van-icon name="clock-o" size="20" @click="showHistoryPanel = true" v-if="conversationId" />
      </template>
    </van-nav-bar>

    <!-- 快捷操作引导 -->
    <div class="quick-bar" v-if="messages.length <= 1 && !showFaq">
      <div class="quick-title">👋 有什么可以帮您？</div>
      <div class="quick-tags">
        <van-tag plain color="#409eff" @click="sendQuick('陪诊服务怎么收费的')">💰 服务价格</van-tag>
        <van-tag plain color="#07c160" @click="sendQuick('查看我的订单')">📋 我的订单</van-tag>
        <van-tag plain color="#ee6a55" @click="sendQuick('如何取消预约')">❌ 取消预约</van-tag>
        <van-tag plain color="#7232dd" @click="sendQuick('陪诊流程是什么')">📝 服务流程</van-tag>
        <van-tag plain color="#f57c00" @click="sendQuick('怎么改约')">📅 改约</van-tag>
        <van-tag plain color="#1989fa" @click="toggleFAQ">❓ 常见问题</van-tag>
      </div>
    </div>

    <!-- FAQ 面板 -->
    <div class="faq-panel" v-if="showFaq">
      <div class="faq-header">
        <span>常见问题</span>
        <van-icon name="cross" @click="showFaq = false" />
      </div>
      <div class="faq-list">
        <div v-for="faq in faqList" :key="faq.id" class="faq-item" @click="sendQuick(faq.question)">
          <div class="faq-q">{{ faq.question }}</div>
          <div class="faq-a">{{ faq.answer }}</div>
        </div>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-box" id="chatBox" ref="chatBoxRef">
      <div v-for="(msg, i) in messages" :key="i" :class="['msg-row', msg.role === 'user' ? 'msg-user' : 'msg-assistant']">
        <div class="msg-avatar" v-if="msg.role === 'assistant'">
          <van-image round width="32" height="32" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='50' fill='%23409eff'/%3E%3Ctext x='50' y='68' text-anchor='middle' font-size='45' fill='white'%3E🤖%3C/text%3E%3C/svg%3E" />
        </div>
        <div class="msg-body">
          <div class="msg-content">
            <div class="msg-text">{{ msg.content }}</div>
            <!-- 结构化卡片 -->
            <div v-if="msg.meta_data && msg.meta_data.travel_advice && msg.role === 'assistant'" class="msg-weather-card">
              <van-icon name="location-o" color="#f57c00" /> {{ msg.meta_data.travel_advice }}
            </div>
            <div v-if="msg.meta_data && msg.meta_data.faq_matched" class="msg-faq-badge">
              <van-tag plain size="small" type="success">来自知识库</van-tag>
            </div>
          </div>
          <div class="msg-footer">
            <span class="msg-time">{{ msg.time || '' }}</span>
            <span v-if="msg.role === 'assistant'" class="msg-actions">
              <van-icon name="like-o" size="14" :color="msg.rated === 1 ? '#07c160' : '#ccc'" @click="rateMessage(i, 1)" />
              <van-icon name="delete-o" size="14" :color="msg.rated === 2 ? '#ee6a55' : '#ccc'" @click="rateMessage(i, 2)" />
              <van-icon name="share-o" size="14" @click="copyText(msg.content)" />
            </span>
          </div>
        </div>
      </div>
      <!-- 加载中 -->
      <div v-if="loading" class="msg-row msg-assistant">
        <div class="msg-avatar">
          <van-image round width="32" height="32" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='50' fill='%23409eff'/%3E%3Ctext x='50' y='68' text-anchor='middle' font-size='45' fill='white'%3E🤖%3C/text%3E%3C/svg%3E" />
        </div>
        <div class="msg-body">
          <div class="msg-content">
            <span class="loading-dots"><van-icon name="underway" spin /> AI正在思考...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-bar">
      <van-field v-model="inputText" placeholder="请输入您的问题..." :border="false" autosize type="textarea"
        @keypress.enter="sendMessage" :disabled="loading" />
      <van-button round type="primary" @click="sendMessage" :disabled="!inputText.trim() || loading" size="small">
        <van-icon name="chat-o" />
      </van-button>
    </div>

    <!-- 历史会话抽屉 -->
    <van-popup v-model:show="showHistoryPanel" position="right" :style="{ width: '85%', height: '100%' }">
      <div class="history-panel">
        <van-nav-bar title="历史对话" left-arrow @click-left="showHistoryPanel = false" />
        <div class="history-list">
          <div v-for="conv in historyList" :key="conv.conversation_id" class="history-item" @click="loadHistory(conv)">
            <div class="history-title">{{ conv.title || '对话' }}</div>
            <div class="history-meta">{{ conv.agent_type }} · {{ conv.message_count }}条消息 · {{ conv.created_at }}</div>
          </div>
          <van-empty v-if="!historyList.length" description="暂无历史记录" />
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, nextTick, getCurrentInstance, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { showToast, showSuccessToast } from "vant";

const { proxy } = getCurrentInstance();
const router = useRouter();
const route = useRoute();

const messages = ref([]);
const inputText = ref("");
const loading = ref(false);
const conversationId = ref("");
const showFaq = ref(false);
const showHistoryPanel = ref(false);
const historyList = ref([]);
const faqList = ref([]);
const chatBoxRef = ref(null);

const goBack = () => router.go(-1);

const scrollToBottom = () => {
  nextTick(() => {
    const box = document.getElementById("chatBox");
    if (box) box.scrollTop = box.scrollHeight;
  });
};

const formatTime = () => {
  const now = new Date();
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
};

const sendMessage = async () => {
  const text = inputText.value.trim();
  if (!text || loading.value) return;
  inputText.value = "";
  showFaq.value = false;

  messages.value.push({ role: "user", content: text, time: formatTime() });
  scrollToBottom();
  loading.value = true;

  try {
    const { data } = await proxy.$api.agentChat({
      message: text,
      agent_type: "auto",
      conversation_id: conversationId.value,
    });
    if (data.code === 10000) {
      const d = data.data;
      conversationId.value = d.conversation_id;
      messages.value.push({
        role: "assistant",
        content: d.reply,
        meta_data: d.meta_data || {},
        time: formatTime(),
        rated: 0,
      });
    } else {
      messages.value.push({ role: "assistant", content: "抱歉，我暂时无法处理，请稍后再试。", time: formatTime() });
    }
  } catch (e) {
    messages.value.push({ role: "assistant", content: "网络异常，请检查网络后重试。", time: formatTime() });
  }
  loading.value = false;
  scrollToBottom();
};

const sendQuick = (text) => {
  inputText.value = text;
  sendMessage();
};

const copyText = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    showSuccessToast("已复制");
  });
};

const rateMessage = async (index, rating) => {
  const msg = messages.value[index];
  if (!msg || msg.rated) return;
  msg.rated = rating;
  try {
    await proxy.$api.submitFeedback({
      conversation_id: conversationId.value,
      rating: rating,
      feedback_text: rating === 2 ? "用户点踩" : "用户点赞",
    });
    showToast(rating === 1 ? "感谢您的好评" : "感谢您的反馈，我们会改进");
  } catch (e) { /* ignore */ }
};

const toggleFAQ = async () => {
  showFaq.value = !showFaq.value;
  if (showFaq.value && !faqList.value.length) {
    try {
      const { data } = await proxy.$api.searchFAQ({ keyword: "" });
      if (data.code === 10000) faqList.value = data.data;
    } catch (e) { /* ignore */ }
  }
};

const loadHistory = async (conv) => {
  showHistoryPanel.value = false;
  try {
    const { data } = await proxy.$api.agentConversationMessages(conv.conversation_id);
    if (data.code === 10000 && data.data.length) {
      messages.value = [];
      conversationId.value = conv.conversation_id;
      data.data.forEach(m => {
        if (m.role !== "system") {
          messages.value.push({
            role: m.role,
            content: m.content,
            meta_data: m.meta_data || {},
            time: m.created_at ? m.created_at.slice(11, 16) : "",
            rated: 0,
          });
        }
      });
      scrollToBottom();
      showToast("已加载历史对话");
    }
  } catch (e) { showToast("加载失败"); }
};

onMounted(async () => {
  // 欢迎消息
  messages.value.push({
    role: "assistant",
    content: "您好！我是AI智能助手 🎉\n\n我可以帮您：\n• 查询订单状态\n• 咨询服务价格与流程\n• 预约/改约/取消操作\n• 推荐医院和科室\n\n请问有什么可以帮您的？",
    meta_data: { agent_type: "customer_service" },
    time: formatTime(),
  });

  // 加载历史
  try {
    const { data } = await proxy.$api.agentConversationList({});
    if (data.code === 10000) historyList.value = data.data;
  } catch (e) { /* ignore */ }
});
</script>

<style lang="less" scoped>
.container { display: flex; flex-direction: column; height: 100vh; background: #f5f5f5; }

/* 快捷引导 */
.quick-bar { padding: 10px 12px 8px; background: #fff; border-bottom: 1px solid #eee; }
.quick-title { font-size: 14px; color: #333; margin-bottom: 8px; font-weight: bold; }
.quick-tags { display: flex; flex-wrap: wrap; gap: 8px; }

/* FAQ面板 */
.faq-panel { background: #fff; border-bottom: 1px solid #eee; max-height: 50vh; overflow-y: auto; }
.faq-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; font-weight: bold; border-bottom: 1px solid #f0f0f0; }
.faq-list { padding: 4px 0; }
.faq-item { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; }
.faq-q { font-size: 14px; font-weight: bold; color: #333; margin-bottom: 4px; }
.faq-a { font-size: 12px; color: #999; line-height: 1.4; }

/* 聊天区域 */
.chat-box { flex: 1; overflow-y: auto; padding: 12px; -webkit-overflow-scrolling: touch; }
.msg-row { margin-bottom: 16px; display: flex; gap: 8px; }
.msg-user { flex-direction: row-reverse; .msg-body { align-items: flex-end; } }
.msg-assistant { .msg-body { align-items: flex-start; } }
.msg-body { display: flex; flex-direction: column; max-width: 80%; }
.msg-content {
  padding: 10px 14px; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; font-size: 14px;
  .msg-user & { background: #409eff; color: #fff; border-radius: 12px 4px 12px 12px; }
  .msg-assistant & { background: #fff; color: #333; border-radius: 4px 12px 12px 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
}
.msg-footer { display: flex; align-items: center; gap: 8px; margin-top: 4px; padding: 0 4px; }
.msg-time { font-size: 11px; color: #bbb; }
.msg-actions { display: flex; gap: 10px; }
.msg-weather-card { margin-top: 8px; padding: 6px 10px; background: #fffbe6; border-radius: 6px; font-size: 12px; color: #795548; display: flex; align-items: center; gap: 4px; }
.msg-faq-badge { margin-top: 6px; }
.loading-dots { color: #999; font-size: 13px; }

/* 输入区 */
.input-bar { display: flex; align-items: flex-end; background: #fff; padding: 6px 8px; border-top: 1px solid #eee; gap: 6px; .van-field { flex: 1; background: #f5f5f5; border-radius: 20px; padding: 4px 12px; } }

/* 历史面板 */
.history-panel { height: 100%; display: flex; flex-direction: column; background: #fff; }
.history-list { flex: 1; overflow-y: auto; padding: 10px; }
.history-item { padding: 12px; border-bottom: 1px solid #f0f0f0; }
.history-title { font-size: 14px; font-weight: bold; color: #333; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-meta { font-size: 12px; color: #999; }
</style>
