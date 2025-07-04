<template>
  <view class="edit-route-container">
    <!-- 顶部地图 -->
    <view class="map-section">
      <v-chart
        ref="echarts"
        :option="option"
        autoresize
        style="width: 100%; height: 260px"
      />
    </view>
    <!-- 标题 -->
    <view class="route-title">{{ routeTitle }}</view>
    <!-- 行程编辑区 -->
    <view class="days-section">
      <view v-for="(day, dayIdx) in days" :key="dayIdx" class="day-block">
        <view class="day-title">第{{ dayIdx + 1 }}天：</view>
        <view class="point-names-row">
          <text
            v-for="(point, idx) in day.points"
            :key="idx"
            class="point-name-row-item"
          >
            {{ point.name
            }}<span v-if="idx !== day.points.length - 1"> / </span>
          </text>
        </view>
        <view class="divider"></view>
        <!-- 横向时间轴（节点在一条横线上，节点下方展示内容） -->
        <scroll-view scroll-x class="timeline-horizontal">
          <view class="timeline-h-row">
            <view
              v-for="(point, idx) in day.points"
              :key="idx"
              class="timeline-h-node"
            >
              <view class="timeline-h-time">{{ point.time }}</view>
              <view class="timeline-h-dot"></view>
              <view
                class="timeline-h-line"
                v-if="idx !== day.points.length - 1"
              ></view>
              <image :src="point.image" class="timeline-h-img" />
              <button
                class="timeline-h-btn"
                @click="onChangeImage(dayIdx, idx)"
              >
                更换 ✎
              </button>
              <button
                class="timeline-h-del"
                @click="onDeletePoint(dayIdx, idx)"
              >
                ×
              </button>
            </view>
          </view>
        </scroll-view>
        <button class="add-btn" @click="onAddPoint(dayIdx)">+ 添加地点</button>
      </view>
    </view>
    <!-- 底部操作栏 -->
    <view class="bottom-bar">
      <button @click="onBack">后退</button>
      <button @click="onForward">前进</button>
      <button @click="onAdjustPlace">调整地点</button>
      <button @click="onAdjustTime">调整时间</button>
      <button class="save-btn" @click="onSave">保存</button>
    </view>
    <!-- 在底部操作栏上方插入弹窗和遮罩 -->
    <view
      v-if="showAdjustPopup"
      class="adjust-popup-mask"
      @click="showAdjustPopup = false"
    ></view>
    <view v-if="showAdjustPopup" class="adjust-popup">
      <view class="adjust-popup-btn" @click="handleAdjust('smart')"
        >智能调整</view
      >
      <view class="adjust-popup-btn" @click="handleAdjust('manual')"
        >手动调整</view
      >
      <view class="adjust-popup-btn" @click="showAdjustPopup = false"
        >取消</view
      >
    </view>
    <!-- 地点选择弹窗 -->
    <view v-if="showPlaceSelector" class="place-selector-modal">
      <view class="place-selector-content">
        <view class="place-selector-title">
          第{{ editPoint && editPoint.dayIdx + 1 }}天 ·
          {{ editPoint && editPoint.point && editPoint.point.time }}
        </view>
        <view style="margin: 10px 0 6px 0">已定地点：</view>
        <view class="place-selected">
          <image
            :src="editPoint && editPoint.point && editPoint.point.image"
            class="place-selected-img"
          />
          <view class="place-selected-name">{{
            editPoint && editPoint.point && editPoint.point.name
          }}</view>
        </view>
        <view class="place-tabs">
          <view
            v-for="(tab, idx) in placeTabs"
            :key="tab"
            :class="['place-tab', { active: activePlaceTab === idx }]"
            @tap="onSwitchPlaceTab(idx)"
            >{{ tab }}</view
          >
        </view>
        <view class="place-candidates">
          <view
            v-for="place in placeCandidates[activePlaceTab]"
            :key="place.name"
            class="place-card"
            @tap="onSelectPlace(place)"
          >
            <image :src="place.image" class="place-card-img" />
            <view class="place-card-name">{{ place.name }}</view>
          </view>
        </view>
        <view class="place-selector-close" @tap="onClosePlaceSelector"
          >关闭</view
        >
      </view>
    </view>
    <!-- 智能调整弹窗 -->
    <view v-if="showSmartAdjust" class="smart-adjust-modal">
      <view class="smart-adjust-content">
        <view class="smart-title">智能调整</view>
        <view class="smart-desc">选择酒店后，AI将自动为您调整攻略</view>
        <view
          v-for="(hotels, dayIdx) in smartHotelOptions"
          :key="dayIdx"
          class="smart-group"
        >
          <view class="smart-group-title"
            >选择第{{ dayIdx + 1 }}天入住酒店（AI推荐）：</view
          >
          <view class="smart-hotel-list">
            <view
              v-for="(hotel, hotelIdx) in hotels"
              :key="hotelIdx"
              class="smart-hotel-card"
              :class="{ selected: smartHotelSelected[dayIdx] === hotelIdx }"
              @tap="selectSmartHotel(dayIdx, hotelIdx)"
            >
              <image :src="hotel.image" class="smart-hotel-img" />
              <view class="smart-hotel-name">{{ hotel.name }}</view>
              <view
                class="smart-radio"
                v-if="smartHotelSelected[dayIdx] === hotelIdx"
              ></view>
            </view>
          </view>
        </view>
        <button class="smart-save-btn" @tap="saveSmartAdjust">保存</button>
      </view>
    </view>
    <!-- 统一调整弹窗 -->
    <view v-if="showEditDialog" class="manual-adjust-modal">
      <view class="manual-adjust-content">
        <view class="manual-title">{{ routeTitle }}</view>
        <view
          v-for="(day, dayIdx) in editDialogDays"
          :key="dayIdx"
          class="manual-day"
        >
          <view class="manual-day-title">第{{ dayIdx + 1 }}天:</view>
          <view class="manual-points-row">
            <view
              v-for="(point, idx) in day.points"
              :key="idx"
              class="manual-point-card"
              draggable="true"
              @dragstart="startDrag(dayIdx, idx)"
              @dragover.prevent="onDragOver(dayIdx, idx)"
              @drop.prevent="endDrag"
              :class="{
                dragging: dragInfo.dayIdx === dayIdx && dragInfo.from === idx,
              }"
            >
              <input
                v-if="editDialogType === 'manual'"
                v-model="point.name"
                class="manual-point-input"
                placeholder="名称"
              />
              <input
                v-else
                :value="point.name"
                class="manual-point-input"
                readonly
              />
              <input
                v-if="editDialogType === 'time'"
                v-model="point.time"
                class="manual-time-input"
                placeholder="时间"
              />
              <input
                v-else
                :value="point.time"
                class="manual-time-input"
                readonly
              />
              <image :src="point.image" class="manual-point-img" />
              <view class="manual-drag-tip">按住拖动</view>
              <view
                class="manual-del-btn"
                @click="deleteManualPoint(dayIdx, idx)"
                >×</view
              >
            </view>
          </view>
          <button class="manual-add-btn" @click="addManualPoint(dayIdx)">
            + 添加地点
          </button>
        </view>
        <view class="manual-btn-row">
          <button class="manual-save-btn" @tap="saveEditDialog">完成</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import * as echarts from "echarts";
import VChart from "vue-echarts";

export default {
  components: { "v-chart": VChart },
  data() {
    return {
      routeTitle: "成都3天2晚旅游攻略-路线",
      days: [
        {
          points: [
            {
              name: "春熙路",
              time: "8:00",
              image: "/static/images/ifs1.jpg",
            },
            {
              name: "景点名称xxx",
              time: "9:00",
              image: "/static/images/ifs1.jpg",
            },
          ],
        },
        {
          points: [
            {
              name: "地点名称xxx",
              time: "时间点",
              image: "/static/images/ifs1.jpg",
            },
          ],
        },
        {
          points: [
            {
              name: "地点名称xxx",
              time: "时间点",
              image: "/static/images/ifs1.jpg",
            },
          ],
        },
      ],
      option: {},
      showAdjustPopup: false,
      showPlaceSelector: false,
      editPoint: null, // {dayIdx, pointIdx, point}
      placeTabs: ["相似主体", "更高性价比", "更少人流"],
      activePlaceTab: 0,
      placeCandidates: [
        [
          { name: "成都太古里IFS", image: "/static/images/ifs1.jpg" },
          { name: "地点名称xxxxxx", image: "/static/images/ifs1.jpg" },
        ],
        [{ name: "高性价比A", image: "/static/images/ifs1.jpg" }],
        [{ name: "人流少A", image: "/static/images/ifs1.jpg" }],
      ],
      showSmartAdjust: false,
      smartHotelOptions: [], // 每天的酒店候选
      smartHotelSelected: [], // 每天选中的酒店下标
      showEditDialog: false,
      editDialogType: "", // 'manual' or 'time'
      editDialogDays: [],
      dragInfo: { dayIdx: null, from: null, to: null },
    };
  },
  onLoad(options) {
    if (options && options.itinerary) {
      try {
        const itinerary = JSON.parse(decodeURIComponent(options.itinerary));
        this.days = itinerary.map((day) => ({
          points: (day.events || []).map((event) => ({
            name: event.location,
            time: event.time,
            image: event.image,
          })),
        }));
      } catch (e) {
        // 解析失败则保留默认静态数据
      }
    }
  },
  mounted() {
    this.loadMap();
  },
  methods: {
    loadMap() {
      fetch("https://geo.datav.aliyun.com/areas_v3/bound/510000_full.json")
        .then((res) => res.json())
        .then((geoJson) => {
          echarts.registerMap("sichuan", geoJson);
          this.option = {
            geo: {
              map: "sichuan",
              roam: false,
              label: { show: true },
              itemStyle: {
                areaColor: "#4da3ff",
                borderColor: "#fff",
              },
            },
            series: [
              {
                type: "scatter",
                coordinateSystem: "geo",
                data: [
                  { name: "太古里IFS", value: [104.080989, 30.657689] },
                  { name: "春熙路", value: [104.082321, 30.657378] },
                  // ...可根据days自动生成
                ],
                symbolSize: 16,
                label: {
                  show: true,
                  formatter: "{b}",
                  color: "#222",
                  backgroundColor: "#fff",
                  borderRadius: 4,
                  padding: [2, 6],
                },
                itemStyle: {
                  color: "#d0021b",
                },
              },
              {
                type: "lines",
                coordinateSystem: "geo",
                zlevel: 2,
                effect: {
                  show: true,
                  period: 6,
                  trailLength: 0.1,
                  color: "#fff",
                  symbolSize: 4,
                },
                lineStyle: {
                  color: "#d0021b",
                  width: 2,
                  opacity: 0.6,
                  curveness: 0.2,
                },
                data: [
                  {
                    coords: [
                      [104.080989, 30.657689],
                      [104.082321, 30.657378],
                    ],
                  },
                  // ...可根据days自动生成
                ],
              },
            ],
          };
        });
    },
    onChangeImage(dayIdx, idx) {
      this.editPoint = {
        dayIdx,
        pointIdx: idx,
        point: this.days[dayIdx].points[idx],
      };
      this.showPlaceSelector = true;
      this.activePlaceTab = 0;
      // 可根据实际地点动态生成 placeTabs 和 placeCandidates
    },
    onDeletePoint(dayIdx, idx) {
      this.days[dayIdx].points.splice(idx, 1);
    },
    onAddPoint(dayIdx) {
      this.days[dayIdx].points.push({
        name: "新地点",
        time: "时间点",
        image: "/static/images/ifs1.jpg",
      });
    },
    onBack() {},
    onForward() {},
    onAdjustPlace() {
      this.showAdjustPopup = true;
    },
    handleAdjust(type) {
      this.showAdjustPopup = false;
      if (type === "smart") {
        // 构造智能调整弹窗数据
        this.smartHotelOptions = this.days.map((day) => [
          { name: "酒店名称xxxxx", image: "/static/images/flower.jpg" },
          { name: "酒店名称xxxxx", image: "/static/images/flower.jpg" },
        ]);
        this.smartHotelSelected = this.days.map(() => 0); // 默认每组选第一个
        this.showSmartAdjust = true;
      } else if (type === "manual") {
        this.editDialogType = "manual";
        this.editDialogDays = JSON.parse(JSON.stringify(this.days));
        this.showEditDialog = true;
      }
    },
    onAdjustTime() {
      this.editDialogType = "time";
      this.editDialogDays = JSON.parse(JSON.stringify(this.days));
      this.showEditDialog = true;
    },
    onSave() {
      uni.showToast({ title: "保存成功", icon: "success" });
    },
    onSelectPlace(place) {
      const { dayIdx, pointIdx } = this.editPoint;
      this.days[dayIdx].points[pointIdx].name = place.name;
      this.days[dayIdx].points[pointIdx].image = place.image;
      this.showPlaceSelector = false;
      this.editPoint = null;
    },
    onSwitchPlaceTab(idx) {
      this.activePlaceTab = idx;
    },
    onClosePlaceSelector() {
      this.showPlaceSelector = false;
      this.editPoint = null;
    },
    selectSmartHotel(dayIdx, hotelIdx) {
      this.smartHotelSelected.splice(dayIdx, 1, hotelIdx);
    },
    saveSmartAdjust() {
      // 将选择同步到 days
      this.days.forEach((day, dayIdx) => {
        const hotel =
          this.smartHotelOptions[dayIdx][this.smartHotelSelected[dayIdx]];
        // 假设每个 day 的第一个点为酒店
        if (day.points && day.points.length > 0) {
          day.points[0].name = hotel.name;
          day.points[0].image = hotel.image;
        }
      });
      this.showSmartAdjust = false;
      uni.showToast({ title: "已保存智能调整", icon: "success" });
    },
    startDrag(dayIdx, idx) {
      this.dragInfo = { dayIdx, from: idx, to: idx };
    },
    onDragOver(dayIdx, idx) {
      if (this.dragInfo.dayIdx === dayIdx) {
        this.dragInfo.to = idx;
      }
    },
    endDrag() {
      const { dayIdx, from, to } = this.dragInfo;
      if (from !== null && to !== null && from !== to) {
        const arr = this.editDialogDays[dayIdx].points;
        const moved = arr.splice(from, 1)[0];
        arr.splice(to, 0, moved);
      }
      this.dragInfo = { dayIdx: null, from: null, to: null };
    },
    deleteManualPoint(dayIdx, idx) {
      this.editDialogDays[dayIdx].points.splice(idx, 1);
    },
    addManualPoint(dayIdx) {
      this.editDialogDays[dayIdx].points.push({
        name: "",
        time: "",
        image: "",
      });
    },
    saveEditDialog() {
      this.days = JSON.parse(JSON.stringify(this.editDialogDays));
      this.showEditDialog = false;
      uni.showToast({ title: "已保存", icon: "success" });
    },
  },
};
</script>

<style scoped>
.edit-route-container {
  background: #fafbfc;
  min-height: 100vh;
  padding-bottom: 100px;
}
.map-section {
  width: 100%;
  margin: 24px 0 10px 0;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.07);
  padding: 18px 0 10px 0;
  max-width: 520px;
  margin-left: auto;
  margin-right: auto;
}
.route-title {
  font-size: 22px;
  font-weight: 700;
  text-align: center;
  margin: 18px 0 8px 0;
  letter-spacing: 1px;
  color: #222;
}
.days-section {
  padding: 0 16px;
  padding-bottom: 80px;
  max-width: 520px;
  margin: 0 auto;
}
.day-block {
  margin-bottom: 28px;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #f2f2f2;
  padding: 18px 16px 14px 16px;
}
.day-title {
  font-size: 17px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #3d1fff;
}
.point-names-row {
  display: flex;
  flex-wrap: wrap;
  font-size: 15px;
  color: #444;
  margin-bottom: 4px;
}
.point-name-row-item {
  margin-right: 2px;
}
.divider {
  height: 1.5px;
  background: linear-gradient(90deg, #3d1fff22 0%, #673ab722 100%);
  opacity: 0.5;
  margin-bottom: 8px;
  border-radius: 2px;
}
.timeline-horizontal {
  overflow-x: auto;
  padding: 24px 0 16px 0;
  white-space: nowrap;
}
.timeline-h-row {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
}
.timeline-h-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 100px;
  margin-right: 40px;
  position: relative;
}
.timeline-h-time {
  font-size: 15px;
  font-weight: bold;
  color: #3d1fff;
  margin-bottom: 4px;
  letter-spacing: 1px;
}
.timeline-h-dot {
  width: 14px;
  height: 14px;
  background: linear-gradient(135deg, #3d1fff 60%, #b39ddb 100%);
  border-radius: 50%;
  margin-bottom: 8px;
  z-index: 2;
  box-shadow: 0 2px 8px #3d1fff33;
}
.timeline-h-line {
  position: absolute;
  top: 20px;
  left: 100%;
  width: 40px;
  height: 2px;
  background: #b39ddb44;
  z-index: 1;
  border-radius: 2px;
}
.timeline-h-img {
  width: 64px;
  height: 64px;
  border-radius: 10px;
  object-fit: cover;
  margin-bottom: 4px;
  box-shadow: 0 2px 8px #eee;
}
.timeline-h-btn {
  font-size: 13px;
  color: #3d1fff;
  background: #f5f7ff;
  border: none;
  border-radius: 8px;
  padding: 4px 14px;
  margin-bottom: 2px;
  margin-top: 2px;
  transition: background 0.2s, color 0.2s;
}
.timeline-h-btn:active {
  background: #e6eaff;
  color: #222;
}
.timeline-h-del {
  position: absolute;
  top: 26px;
  right: 0;
  background: #fff;
  color: #d0021b;
  border: 1px solid #eee;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 14px;
  line-height: 18px;
  padding: 0;
  z-index: 2;
  box-shadow: 0 2px 8px #eee;
}
.add-btn {
  font-size: 14px;
  color: #3d1fff;
  background: none;
  border: none;
  margin-top: 4px;
  border-radius: 8px;
  padding: 4px 10px;
  transition: background 0.2s, color 0.2s;
}
.add-btn:active {
  background: #f5f7ff;
  color: #222;
}
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: rgba(247, 247, 250, 0.92);
  padding: 18px 0 14px 0;
  box-shadow: 0 -4px 24px #eaeaff44;
  border-top: 1.5px solid #ececf2;
  z-index: 100;
  backdrop-filter: blur(10px);
  gap: 18px;
  min-height: 68px;
}
.save-btn {
  background: linear-gradient(90deg, #3d1fff 60%, #6a5bff 100%);
  color: #fff;
  border-radius: 22px;
  padding: 12px 38px;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 2px 12px #3d1fff33;
  border: none;
  transition: background 0.2s, box-shadow 0.2s;
  letter-spacing: 1px;
}
.save-btn:active {
  background: linear-gradient(90deg, #2a0fcf 60%, #3d1fff 100%);
  box-shadow: 0 1px 4px #3d1fff22;
}
.bottom-bar button {
  background: #fff;
  color: #3d1fff;
  border-radius: 18px;
  padding: 10px 28px;
  font-size: 16px;
  margin: 0 2px;
  border: 2px solid #e0e3ff;
  box-shadow: none;
  font-weight: 500;
  transition: border 0.2s, color 0.2s, background 0.2s;
  letter-spacing: 0.5px;
}
.bottom-bar button:active {
  background: #f5f7ff;
  color: #3d1fff;
  border: 2px solid #3d1fff;
}
.adjust-popup-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.1);
  z-index: 1000;
}
.adjust-popup {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 70px; /* 适当调整距离 */
  margin: 0 auto;
  width: 320px;
  max-width: 92vw;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 22px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  overflow: visible;
  backdrop-filter: blur(12px);
  border: 1.5px solid rgba(180, 180, 200, 0.13);
}
.adjust-popup-btn {
  padding: 18px 0 16px 0;
  text-align: center;
  font-size: 19px;
  color: #222;
  background: transparent;
  transition: background 0.2s, color 0.2s;
  cursor: pointer;
  user-select: none;
  font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}
.adjust-popup-btn:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}
.adjust-popup-btn:active {
  background: #f3f6ff;
  color: #3d1fff;
}
.adjust-popup-btn:last-child {
  border-bottom: none;
  margin-top: 8px;
  color: #888;
  font-size: 18px;
  background: #f7f7fa;
  border-radius: 0 0 22px 22px;
}
.adjust-popup-btn:last-child:active {
  background: #ececf2;
  color: #d0021b;
}
.place-selector-modal {
  position: fixed;
  left: 0;
  top: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.25);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.place-selector-content {
  background: #fff;
  border-radius: 18px;
  padding: 24px 16px 18px 16px;
  width: 90vw;
  max-width: 320px;
  box-shadow: 0 4px 24px rgba(60, 89, 107, 0.12);
  position: relative;
  border: 1px solid #e0e0e0;
}
.place-selector-title {
  text-align: center;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}
.place-selected {
  display: flex;
  align-items: center;
  background: #f8f4e9;
  border-radius: 12px;
  padding: 8px 12px;
  margin-bottom: 12px;
}
.place-selected-img {
  width: 56px;
  height: 42px;
  border-radius: 8px;
  margin-right: 12px;
  object-fit: cover;
}
.place-selected-name {
  font-size: 15px;
  color: #2c4a52;
}
.place-tabs {
  display: flex;
  margin-bottom: 10px;
  border-bottom: 2px solid #eee;
}
.place-tab {
  flex: 1;
  text-align: center;
  font-size: 15px;
  color: #888;
  padding: 8px 0 6px 0;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}
.place-tab.active {
  color: #673ab7;
  font-weight: bold;
  border-bottom: 2px solid #673ab7;
}
.place-candidates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 18px;
}
.place-card {
  background: #f8f4e9;
  border-radius: 12px;
  padding: 8px 6px 6px 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(60, 89, 107, 0.06);
  transition: box-shadow 0.2s;
}
.place-card:active {
  box-shadow: 0 4px 16px rgba(60, 89, 107, 0.12);
}
.place-card-img {
  width: 80px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
  margin-bottom: 6px;
}
.place-card-name {
  font-size: 14px;
  color: #2c4a52;
}
.place-selector-close {
  text-align: center;
  color: #888;
  font-size: 15px;
  margin-top: 4px;
  padding: 6px 0;
  cursor: pointer;
}
.smart-adjust-modal {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.18);
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.smart-adjust-content {
  background: #fff;
  border-radius: 18px;
  padding: 18px 12px 12px 12px;
  width: 94vw;
  max-width: 400px;
  box-shadow: 0 4px 24px rgba(60, 89, 107, 0.12);
  border: 1px solid #e0e0e0;
}
.smart-title {
  text-align: center;
  font-size: 19px;
  font-weight: bold;
  margin-bottom: 2px;
}
.smart-desc {
  text-align: center;
  color: #a88;
  font-size: 13px;
  margin-bottom: 10px;
}
.smart-group {
  margin-bottom: 12px;
}
.smart-group-title {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 6px;
}
.smart-hotel-list {
  display: flex;
  gap: 10px;
  margin-bottom: 4px;
}
.smart-hotel-card {
  background: #f8f4e9;
  border-radius: 10px;
  padding: 6px 4px 4px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(60, 89, 107, 0.06);
  border: 2px solid transparent;
  position: relative;
  width: 110px;
}
.smart-hotel-card.selected {
  border: 2px solid #673ab7;
}
.smart-hotel-img {
  width: 100px;
  height: 70px;
  border-radius: 8px;
  object-fit: cover;
  margin-bottom: 4px;
}
.smart-hotel-name {
  font-size: 13px;
  color: #2c4a52;
  text-align: center;
}
.smart-radio {
  position: absolute;
  top: 6px;
  right: 8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #673ab7;
  background: #fff;
}
.smart-save-btn {
  width: 100%;
  margin-top: 10px;
  background: #673ab7;
  color: #fff;
  border-radius: 10px;
  font-size: 17px;
  font-weight: 600;
  padding: 12px 0;
}
.manual-adjust-modal {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.12);
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.manual-adjust-content {
  background: #fff;
  border-radius: 18px;
  padding: 18px 12px 12px 12px;
  width: 96vw;
  max-width: 480px;
  box-shadow: 0 4px 24px rgba(60, 89, 107, 0.12);
  border: 1px solid #e0e0e0;
  max-height: 90vh;
  overflow-y: auto;
}
.manual-title {
  text-align: center;
  font-size: 19px;
  font-weight: bold;
  margin-bottom: 10px;
}
.manual-day-title {
  font-size: 16px;
  font-weight: 600;
  margin: 10px 0 4px 0;
}
.manual-points-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}
.manual-point-card {
  background: #f8f4e9;
  border-radius: 10px;
  padding: 8px 6px 6px 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 110px;
  position: relative;
  border: 2px solid transparent;
  transition: border 0.2s;
}
.manual-point-card.dragging {
  border: 2px dashed #673ab7;
  opacity: 0.7;
}
.manual-point-input,
.manual-time-input {
  width: 90px;
  margin-bottom: 4px;
  border: 1px solid #ececf2;
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 13px;
  text-align: center;
}
.manual-point-img {
  width: 80px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
  margin-bottom: 4px;
}
.manual-drag-tip {
  font-size: 12px;
  color: #aaa;
  margin-bottom: 2px;
}
.manual-del-btn {
  position: absolute;
  top: 26px;
  right: 6px;
  color: #d0021b;
  font-size: 18px;
  cursor: pointer;
  background: #fff;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  text-align: center;
  line-height: 18px;
  border: 1px solid #eee;
}
.manual-add-btn {
  background: #f5f7ff;
  color: #3d1fff;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 14px;
  border: none;
  margin-top: 4px;
}
.manual-btn-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}
.manual-save-btn {
  background: #673ab7;
  color: #fff;
  border-radius: 10px;
  font-size: 17px;
  font-weight: 600;
  padding: 10px 32px;
}
</style>
