<template>
  <div class="config-page">
    <panel-head :route="route" />

    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-title">📚 FAQ知识库</span>
        <el-tag size="small">{{ faqTotal }} 条</el-tag>
      </div>
      <el-button type="primary" :icon="Plus" @click="openFaqDialog(null)">新增FAQ</el-button>
    </div>

    <el-table :data="faqList" stripe>
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="question" label="问题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="answer" label="答案" min-width="280" show-overflow-tooltip>
        <template #default="scope">
          <span class="faq-answer">{{ scope.row.answer }}</span>
        </template>
      </el-table-column>
      <el-table-column label="分类" width="100">
        <template #default="scope">
          <el-tag :type="categoryType(scope.row.category)" size="small" effect="plain">
            {{ categoryLabel(scope.row.category) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="scope">
          <el-switch v-model="scope.row.enabled" :active-value="1" :inactive-value="0"
            @change="toggleFaq(scope.row)" size="small" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" align="center">
        <template #default="scope">
          <el-button size="small" type="primary" link @click="openFaqDialog(scope.row)">
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
          <el-popconfirm title="确认删除？" @confirm="deleteFaq(scope.row)">
            <template #reference>
              <el-button size="small" type="danger" link>
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <div class="page-wrap">
      <el-pagination
        :current-page="faqPage.pageNum" :page-size="faqPage.pageSize"
        layout="total, prev, pager, next" :total="faqTotal"
        @current-change="v=>{faqPage.pageNum=v;loadFaq()}"
      />
    </div>

    <el-dialog v-model="faqDialog" :title="editingFaq ? '编辑FAQ' : '新增FAQ'" width="650">
      <el-form :model="faqForm" label-width="70px">
        <el-form-item label="问题">
          <el-input v-model="faqForm.question" placeholder="用户常问的问题" />
        </el-form-item>
        <el-form-item label="答案">
          <el-input v-model="faqForm.answer" type="textarea" :rows="5" placeholder="标准回答内容" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="分类">
              <el-select v-model="faqForm.category" style="width:100%">
                <el-option label="服务" value="service" />
                <el-option label="价格" value="price" />
                <el-option label="流程" value="process" />
                <el-option label="订单" value="order" />
                <el-option label="通用" value="general" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关键词">
              <el-input v-model="faqForm.keywords" placeholder="逗号分隔" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="faqDialog=false">取消</el-button>
        <el-button type="primary" @click="saveFaq">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useRoute } from "vue-router";
import { agentFaqList, agentFaqCreate, agentFaqUpdate, agentFaqDelete } from "../../../api";
import { ElMessage } from "element-plus";
import { Plus, Edit, Delete } from "@element-plus/icons-vue";

const route = useRoute();
const faqList = ref([]);
const faqTotal = ref(0);
const faqPage = reactive({ pageNum:1, pageSize:10 });
const faqDialog = ref(false);
const editingFaq = ref(null);
const faqForm = reactive({ question:"", answer:"", category:"general", keywords:"" });

const categoryType = (c) => ({ service:"success", price:"warning", process:"info", order:"danger" }[c]||"");
const categoryLabel = (c) => ({ service:"服务", price:"价格", process:"流程", order:"订单" }[c]||c);

onMounted(() => loadFaq());

const loadFaq = () => {
  agentFaqList(faqPage).then(({ data }) => {
    if (data.code === 10000) {
      faqList.value = data.data.list||[];
      faqTotal.value = data.data.total||0;
    }
  }).catch(() => {});
};

const openFaqDialog = (row) => {
  editingFaq.value = row;
  faqForm.question = row?.question || "";
  faqForm.answer = row?.answer || "";
  faqForm.category = row?.category || "general";
  faqForm.keywords = row?.keywords || "";
  faqDialog.value = true;
};

const saveFaq = () => {
  if (!faqForm.question || !faqForm.answer) { ElMessage.warning("请填写问题和答案"); return; }
  const action = editingFaq.value
    ? agentFaqUpdate({ id:editingFaq.value.id, ...faqForm })
    : agentFaqCreate(faqForm);
  action.then(({ data }) => {
    if (data.code === 10000) { ElMessage.success("保存成功"); faqDialog.value=false; loadFaq(); }
  }).catch(() => {});
};

const toggleFaq = (row) => {
  agentFaqUpdate({ id:row.id, enabled:row.enabled }).then(({ data }) => {
    if (data.code === 10000) ElMessage.success(row.enabled?"已启用":"已禁用");
  }).catch(() => {});
};

const deleteFaq = (row) => {
  agentFaqDelete({ id:row.id }).then(({ data }) => {
    if (data.code === 10000) { ElMessage.success("已删除"); loadFaq(); }
  }).catch(() => {});
};
</script>

<style lang="less" scoped>
.config-page { padding:0 0 20px; }
.toolbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.toolbar-left { display:flex; align-items:center; gap:8px; }
.toolbar-title { font-size:15px; font-weight:600; }
.faq-answer { display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; color:#666; }
.page-wrap { margin-top:15px; display:flex; justify-content:flex-end; }
</style>
