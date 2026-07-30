<template>
  <div>
    <panel-head :route="route" />
    <div class="toolbar">
      <el-form inline="true" :model="searchForm">
        <el-form-item label="订单号">
          <el-input v-model="searchForm.out_trade_no" placeholder="订单号" clearable @clear="onSubmit" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.trade_state" placeholder="全部状态" clearable @change="onSubmit" style="width:130px">
            <el-option label="待支付" value="待支付" />
            <el-option label="待服务" value="待服务" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSubmit">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
      <div class="toolbar-info">
        <el-tag type="info" effect="plain">共 {{ tableData.total }} 条记录</el-tag>
      </div>
    </div>
    <el-table :data="tableData.list" stripe>
      <el-table-column prop="out_trade_no" label="订单号" width="170" fiexd="left" />
      <el-table-column prop="hospital_name" label="就诊医院" min-width="180" />
      <el-table-column prop="service_name" label="陪诊服务" width="120" />
      <el-table-column label="陪护师" width="70">
        <template #default="scope">
          <el-image style="width:36px;height:36px;border-radius:50%" :src="scope.row.companion.avatar" v-if="scope.row.companion?.avatar" />
          <span v-else style="color:#ccc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="陪护师手机号" width="120">
        <template #default="scope">
          {{ scope.row.companion?.mobile || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="price" label="总价" width="80" />
      <el-table-column prop="paidPrice" label="已付" width="80" />
      <el-table-column label="下单时间" width="120">
        <template #default="scope">
          {{ dayjs(scope.row.order_start_time).format("YYYY-MM-DD") }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="statusTag(scope.row.trade_state)">{{ scope.row.trade_state }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tel" label="联系人手机" width="120" />
      <el-table-column label="操作" width="110" fiexd="right">
        <template #default="scope">
          <el-popconfirm
            v-if="scope.row.trade_state === '待服务'"
            title="确认服务完成？"
            :icon="InfoFilled"
            icon-color="#626AEF"
            @confirm="confirmEvent(scope.row.out_trade_no)"
          >
            <template #reference>
              <el-button type="primary" link size="small">服务完成</el-button>
            </template>
          </el-popconfirm>
          <el-tag v-else type="info" effect="plain" size="small">已处理</el-tag>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination-wrap">
      <span class="page-summary">显示第 {{ startRow }}-{{ endRow }} 条，共 {{ tableData.total }} 条</span>
      <el-pagination
        :current-page="paginationData.pageNum"
        :page-size="paginationData.pageSize"
        layout="prev, pager, next"
        :total="tableData.total"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { InfoFilled } from "@element-plus/icons-vue";
import { useRoute } from "vue-router";
import { adminOrder, updateOrder } from "../../../api/index";
import dayjs from "dayjs";
import { ElMessage } from "element-plus";

const route = useRoute();

const paginationData = reactive({ pageNum: 1, pageSize: 10 });
const searchForm = reactive({ out_trade_no: "", trade_state: "" });
const tableData = reactive({ list: [], total: 0 });

const startRow = computed(() => (paginationData.pageNum - 1) * paginationData.pageSize + 1);
const endRow = computed(() => Math.min(paginationData.pageNum * paginationData.pageSize, tableData.total));

const statusTag = (s) => ({ "待支付":"warning", "待服务":"primary", "已完成":"success", "已取消":"info" }[s] || "info");

onMounted(() => getListData());

const getListData = () => {
  adminOrder({ ...paginationData, ...searchForm }).then((res) => {
    const d = res.data;
    if (d.code === 10000) {
      tableData.list = d.data.list || [];
      tableData.total = d.data.total || 0;
    }
  });
};

const onSubmit = () => { paginationData.pageNum = 1; getListData(); };
const resetSearch = () => { searchForm.out_trade_no = ""; searchForm.trade_state = ""; onSubmit(); };
const handleCurrentChange = (val) => { paginationData.pageNum = val; getListData(); };

const confirmEvent = (id) => {
  updateOrder({ id }).then(({ data }) => {
    if (data.code === 10000) { ElMessage.success("操作成功"); getListData(); }
  });
};
</script>

<style lang="less" scoped>
.toolbar {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
  padding: 8px 10px; background: #fff;
}
.toolbar-info { white-space: nowrap; }
.pagination-wrap {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 10px; background: #fff;
  .page-summary { font-size: 13px; color: #999; }
}
</style>
