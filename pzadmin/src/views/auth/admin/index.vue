<template>
  <div>
  <panel-head :route="route" />
    <el-table :data="tableData.list" style="width: 100%">
      <el-table-column prop="id" label="id" />
      <el-table-column prop="name" label="昵称" />
      <el-table-column prop="permissions_id" label="所属组别">
        <template #default="scope">
          {{ permissName(scope.row.permissions_id) }}
        </template>
      </el-table-column>
      <el-table-column prop="mobile" label="手机号"> </el-table-column>
      <el-table-column prop="active" label="状态">
        <template #default="scope">
          <el-tag :type="scope.row.active ? 'success' : 'danger'">{{
            scope.row.active ? "正常" : "失效"
          }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create-time" label="创建时间">
        <template #default="scope">
          <div class="flex-box">
            <el-icon><Clock /></el-icon>
            <span style="margin-left: 10px">{{ scope.row.create_time }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="primary" @click="open(scope.row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination-info" style="display:flex;justify-content:space-between;align-items:center;padding:10px">
      <span style="font-size:13px;color:#999">显示第 {{ (paginationData.pageNum-1)*paginationData.pageSize+1 }}-{{ Math.min(paginationData.pageNum*paginationData.pageSize, tableData.total) }} 条，共 {{ tableData.total }} 条</span>
      <el-pagination
        :current-page="paginationData.pageNum"
        :page-size="paginationData.pageSize"
        layout="prev, pager, next"
        :total="tableData.total"
        @size-change="v=>{paginationData.pageSize=v;getListData()}"
        @current-change="v=>{paginationData.pageNum=v;getListData()}"
      />
    </div>
    <el-dialog
      v-model="dialogFormVisable"
      :before-close="beforeClose"
      title="添加权限"
      width="500"
    >
      <el-form
        ref="formRef"
        label-width="100px"
        label-position="left"
        :model="form"
        :rules="rules"
      >
        <el-form-item label="手机号" prop="mobile">
          <el-input v-model="form.mobile" disabled></el-input>
        </el-form-item>
        <el-form-item label="昵称" prop="name">
          <el-input v-model="form.name"></el-input>
        </el-form-item>
        <el-form-item label="菜单权限" prop="permissions_id">
          <el-select
            v-model="form.permissions_id"
            placaholder="请选择菜单权限"
            style="width: 240px"
          >
            <el-option
              v-for="item in options"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            >
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div>
          <el-button type="primary" @click="confirm(formRef)">确认</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { authAdmin, menuSelectList, updateUser } from "../../../api";
import { ref, reactive, onMounted } from "vue";
import dayjs from "dayjs";
import {useRoute} from 'vue-router'

const route = useRoute()

const paginationData = reactive({
  pageNum: 1,
  pageSize: 10,
});

const tableData = reactive({
  list: [],
  total: 0,
});

onMounted(() => {
  getListData();
  menuSelectList().then(({ data }) => {
    // console.log(data.data);
    options.value = data.data;
  });
});

const getListData = () => {
  authAdmin(paginationData).then((data) => {
    // console.log(data.data);
    const { list, total } = data.data.data;
    list.forEach((item) => {
      item.create_time = dayjs(item.createTime).format("YYYY-MM-DD");
    });
    tableData.list = list;
    tableData.total = total;
  });
};

const rules = reactive({
  name: [
    {
      required: true,
      trigger: "blur",
      message: "请填写昵称",
    },
  ],
  permissions_id: [
    {
      required: true,
      trigger: "blur",
      message: "请选择菜单权限",
    },
  ],
});

const formRef = ref();
const form = reactive({
  mobile: "",
  name: "",
  premissions_id: "",
});
const confirm = async (formEl) => {
  if (!formEl) return;
  await formEl.validate((valid, fields) => {
    if (valid) {
      // console.log("success");
      const { name, permissions_id } = form;
      updateUser({ name, permissions_id }).then(({ data }) => {
        if (data.code === 10000) {
          console.log(data);
          dialogFormVisable.value = false;
          getListData();
        }
      });
    } else {
      console.log("error submit!", fields);
    }
  });
};

const options = ref([]);

const permissName = (id) => {
  const data = options.value.find((el) => el.id === id);
  return data ? data.name : "超级管理员";
};

const open = (rowData) => {
  // console.log(rowData);
  dialogFormVisable.value = true;
  Object.assign(form, {
    mobile: rowData.mobile,
    name: rowData.name,
    permissions_id: rowData.permissions_id,
  });
};

const handleSizeChange = (val) => {
  paginationData.pageSize = val;
  getListData();
};

const handleCurrentChange = (val) => {
  paginationData.pageNum = val;
  getListData();
};

const dialogFormVisable = ref(false);

const beforeClose = () => {
  dialogFormVisable.value = false;
};
</script>

<style lang="less" scoped>
.flex-box {
  display: flex;
  align-items: center;
}
</style>