<template>
  <div>
    <panel-head :route="route" />
    <div class="form">
      <el-form inline="true" :model="searchForm">
        <el-form-item prop="out_trade_no">
          <el-input v-model="searchForm.out_trade_no" placeholder="订单号" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSubmit">查询</el-button>
        </el-form-item>
      </el-form>
    </div>
    <el-table :data="tableData.list">
      <el-table-column
        prop="out_trade_no"
        label="订单号"
        width="150"
        fiexd="left"
      ></el-table-column>
      <el-table-column prop="hospital_name" label="就诊医院"></el-table-column>
      <el-table-column prop="service_name" label="陪诊服务"></el-table-column>
      <el-table-column label="陪护师">
        <template #default="scope">
          <el-image
            style="width: 40px; height: 40px"
            :src="scope.row.companion.avatar"
          />
        </template>
      </el-table-column>
      <el-table-column label="陪护师手机号" width="120">
        <template #default="scope">
          {{ scope.row.companion.mobile }}
        </template>
      </el-table-column>
      <el-table-column prop="price" label="总价"></el-table-column>
      <el-table-column prop="paidPrice" label="已付"></el-table-column>
      <el-table-column label="下单时间">
        <template #default="scope">
          {{ dayjs(scope.row.order_start_time).format("YYYY-MM-DD") }}
        </template>
      </el-table-column>
      <el-table-column label="下单状态" width="120">
        <template #default="scope">
          <el-tag :type="statusMap(scope.row.order_state)">{{
            scope.row.trade_state
          }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="service_state" label="接单状态"></el-table-column>
      <el-table-column
        prop="tel"
        label="联系人手机号"
        width="120"
      ></el-table-column>
      <el-table-column label="操作" width="100" fiexd="right">
        <template #default="scope">
          <el-popconfirm
            v-if="scope.row.trade_state === '待服务'"
            title="是否确认完成?"
            :icon="InfoFilled"
            icon-color="#626AEF"
            confirm-button-text="是"
            cancel-button-text="否"
            @confirm="confirmEvent(scope.row.out_trade_no)"
          >
            <template #reference>
              <el-button type="primary" link>服务完成</el-button>
            </template>
          </el-popconfirm>
          <el-button v-else link disabled>暂无服务</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { Plus, InfoFilled, Delete } from "@element-plus/icons-vue";
import { useRoute } from "vue-router";
import { adminOrder, updateOrder } from "../../../api/index";
import dayjs from "dayjs";
import panelHead from "../../../components/panelHead.vue";
const route = useRoute();

const paginationData = reactive({
  pageNum: 1,
  pageSize: 10,
});

const searchForm = reactive({
  out_trade_no: "",
});

const tableData = reactive({
  list: [],
  total: 0,
});

onMounted(() => {
  getListData();
});

const statusMap = () => {
  const obj = {
    已取消: "info",
    待支付: "warning",
    已完成: "success",
  };
  return obj;
};

const getListData = (params = {}) => {
  adminOrder({ ...paginationData, ...params }).then((res) => {
    const { list, total } = res.data.data;
    tableData.list = list;
    tableData.total = total;
    console.log(res.data.data);
  });
};

const onSubmit = () => {
  console.log(searchForm);
  getListData(searchForm);
};

const handleSizeChange = (val) => {
  paginationData.pageSize = val;
  getListData();
};

const handleCurrentChange = (val) => {
  paginationData.pageNum = val;
  getListData();
};

const confirmEvent = (id) => {
  updateOrder({ id }).then((data) => {
    if (data.data.code === 10000) {
      getListData();
    }
  });
};
</script>

<style lang="less" scoped>
.form {
  display: flex;
  justify-content: flex-end;
  padding: 10px 0 10px 10px;
  background-color: #fff;
}
</style>