<template>
  <view class="detail-container">
    <view class="detail-header">
      <view class="back-btn" @tap="goBack"></view>
    </view>
    <view class="tab-bar">
      <view
        v-for="(tab, idx) in tabs"
        :key="tab"
        :class="['tab-item', { active: activeTab === idx }]"
        @tap="activeTab = idx"
        >{{ tab }}</view
      >
    </view>
    <view v-if="activeTab === 0" class="overview-tab">
      <view v-for="(day, dayIdx) in itinerary" :key="dayIdx" class="day-card">
        <view class="day-title">
          第{{ dayIdx + 1 }}天 {{ day.date }} 天气：{{ day.weatherIcon }}
          {{ day.temperature }}
        </view>
        <view
          v-for="(event, eventIdx) in day.events"
          :key="eventIdx"
          class="event-row"
        >
          <view class="event-time">{{ event.time }}</view>
          <view class="event-location">{{ event.location }}</view>
          <view v-if="event.subtext" class="event-subtext">{{
            event.subtext
          }}</view>
          <image v-if="event.image" :src="event.image" class="event-image" />
        </view>
      </view>
      <view class="budget-card" v-if="budget">
        <view class="budget-title">预计资金花费</view>
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle
            v-for="(item, idx) in budget.chart"
            :key="item.name"
            :stroke="item.color"
            stroke-width="16"
            fill="none"
            :stroke-dasharray="getBudgetChartDasharray(idx, budget.chart)"
            :stroke-dashoffset="getBudgetChartOffset(idx, budget.chart)"
            cx="60"
            cy="60"
            r="50"
            transform="rotate(-90 60 60)"
          />
        </svg>
        <view class="legend-row" v-for="item in budget.chart" :key="item.name">
          <view class="legend-item" :style="{ color: item.color }"
            >{{ item.name }}：{{ item.value }}元</view
          >
        </view>
        <view class="legend-item" v-if="budget.其他"
          >其他：{{ budget.其他 }}元</view
        >
      </view>
      <view class="budget-card" v-if="timeChart && timeChart.length">
        <view class="budget-title">预计时间花费</view>
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle
            v-for="(item, idx) in timeChart"
            :key="item.name"
            :stroke="item.color"
            stroke-width="16"
            fill="none"
            :stroke-dasharray="getBudgetChartDasharray(idx, timeChart)"
            :stroke-dashoffset="getBudgetChartOffset(idx, timeChart)"
            cx="60"
            cy="60"
            r="50"
            transform="rotate(-90 60 60)"
          />
        </svg>
        <view class="legend-row" v-for="item in timeChart" :key="item.name">
          <view class="legend-item" :style="{ color: item.color }"
            >{{ item.name }}：{{ item.value }}分钟</view
          >
        </view>
      </view>
      <button class="edit-btn" @click="goEditRoute">修改路线</button>
    </view>
    <view v-else-if="activeTab === 1" class="detail-tab">
      <view class="day-switch">
        <view
          v-for="(day, idx) in itinerary"
          :key="idx"
          :class="['day-switch-item', { active: activeDayIndex === idx }]"
          @tap="activeDayIndex = idx"
          >第{{ idx + 1 }}天</view
        >
      </view>
      <view class="day-header">
        <view
          >第{{ activeDayIndex + 1 }}天 天气：{{
            itinerary[activeDayIndex]?.weatherIcon
          }}
          {{ itinerary[activeDayIndex]?.temperature }}</view
        >
        <view>
          {{ itinerary[activeDayIndex]?.events[0]?.location }} ->
          {{
            itinerary[activeDayIndex]?.events[
              itinerary[activeDayIndex]?.events.length - 1
            ]?.location
          }}
        </view>
      </view>
      <view class="timeline">
        <view
          v-for="(event, idx) in itinerary[activeDayIndex]?.events"
          :key="idx"
          class="timeline-event"
        >
          <view class="timeline-dot"></view>
          <view class="timeline-time">{{ event.time }}</view>
          <image :src="event.image" class="timeline-img" />
          <view class="timeline-location">{{ event.location }}</view>
        </view>
      </view>
      <view class="section-title">餐厅推荐</view>
      <scroll-view scroll-x class="restaurant-scroll">
        <view
          v-for="item in getRestaurantListForDay(activeDayIndex)"
          :key="item.name"
          class="restaurant-card"
        >
          <image :src="item.image" class="restaurant-img" />
          <view class="restaurant-name">{{ item.name }}</view>
          <view class="restaurant-info"
            >距离{{ item.distance }} <text class="nav-link">导航</text></view
          >
        </view>
      </scroll-view>
      <view class="section-title">小红书种草笔记</view>
      <view
        v-for="note in getNotesListForDay(activeDayIndex)"
        :key="note.title"
        class="note-card"
      >
        <image :src="note.image" class="note-img" />
        <view class="note-content">
          <view class="note-title">{{ note.title }}</view>
          <view class="note-text">{{ note.content }}</view>
          <view class="note-meta">
            <text>❤{{ note.likes }}</text>
            <text>💬{{ note.comments }}</text>
            <text>📁{{ note.collects }}</text>
          </view>
        </view>
      </view>
      <button class="edit-btn" @click="goEditRoute">修改路线</button>
    </view>
    <view v-else class="map-tab">
      <v-chart
        ref="echarts"
        :option="option"
        autoresize
        style="width: 100%; height: 400px"
        @click="onMapClick"
      />
      <uni-popup v-model="showPopup" type="bottom">
        <view class="popup-content">
          <text class="title">{{ currentPoint.name }}</text>
          <view class="img-list">
            <image
              v-for="(img, idx) in currentPoint.images"
              :key="idx"
              :src="img"
            />
          </view>
        </view>
      </uni-popup>
      <button class="edit-btn" @click="goEditRoute">修改路线</button>
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
      tabs: ["总览", "每日详情", "地图模式"],
      activeTab: 0,
      itinerary: [],
      budget: null,
      timeChart: [],
      activeDayIndex: 0,
      restaurantList: [
        {
          name: "海底捞春熙路店",
          image: "/static/images/food.jpg",
          distance: "23km",
        },
        {
          name: "海底捞IFS店",
          image: "/static/images/food.jpg",
          distance: "25km",
        },
      ],
      notesList: [
        {
          image: "/static/images/food.jpg",
          title: "成都city walk | IFS·春熙路·太古里·慢慢街",
          content:
            "成都春熙路一定要去，感受成都最热闹的商业街区...\nIFS大熊猫、太古里、春熙路、望平街、九眼桥都值得打卡",
          likes: 2727,
          comments: 155,
          collects: 44,
        },
        {
          image: "/static/images/food.jpg",
          title: "成都美食推荐",
          content:
            "火锅、串串、兔头、钵钵鸡、冒菜、甜水面...\n每一样都值得尝试！",
          likes: 1888,
          comments: 99,
          collects: 30,
        },
      ],
      showPopup: false,
      currentPoint: {},
      points: [
        {
          id: 1,
          name: "太古里IFS",
          coord: [104.080989, 30.657689],
          images: [
            "/static/images/ifs1.jpg",
            "/static/images/ifs2.jpg",
            "/static/images/ifs3.jpg",
            "/static/images/ifs4.jpg",
            "/static/images/ifs5.jpg",
            "/static/images/ifs6.jpg",
          ],
        },
        {
          id: 2,
          name: "春熙路",
          coord: [104.082321, 30.657378],
          images: ["/static/images/flower.jpg", "/static/images/food.jpg"],
        },
        // 可继续添加更多景点
      ],
      option: {},
    };
  },
  onLoad(options) {
    if (options.itinerary) {
      try {
        this.itinerary = JSON.parse(decodeURIComponent(options.itinerary));
      } catch (e) {
        // 解析失败可用默认值
      }
    }
    if (options.budget) {
      try {
        this.budget = JSON.parse(decodeURIComponent(options.budget));
      } catch (e) {}
    }
    this.timeChart = this.getTimeChartData();
  },
  mounted() {
    this.loadMap();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    goEditRoute() {
      const itineraryStr = encodeURIComponent(JSON.stringify(this.itinerary));
      uni.navigateTo({
        url: `/pages/editRoute/editRoute?itinerary=${itineraryStr}`,
      });
    },
    getBudgetChartDasharray(idx, chart) {
      const C = 2 * Math.PI * 50;
      const total = chart.reduce((sum, item) => sum + item.value, 0);
      const value = chart[idx].value;
      const length = (value / total) * C;
      return `${length} ${C - length}`;
    },
    getBudgetChartOffset(idx, chart) {
      const C = 2 * Math.PI * 50;
      const total = chart.reduce((sum, item) => sum + item.value, 0);
      let offset = 0;
      for (let i = 0; i < idx; i++) {
        offset += (chart[i].value / total) * C;
      }
      return -offset;
    },
    getTimeChartData() {
      // 遍历itinerary统计各类型事件的时长，假设event.type和event.duration（分钟）
      const typeMap = {};
      this.itinerary.forEach((day) => {
        (day.events || []).forEach((event) => {
          const type = event.type || "游玩";
          const duration = event.duration || 60; // 默认1小时
          if (!typeMap[type]) typeMap[type] = 0;
          typeMap[type] += duration;
        });
      });
      const colorList = ["#e6c36f", "#8fd3c7", "#5b8bee", "#6fc36f", "#f7a35c"];
      return Object.keys(typeMap).map((type, i) => ({
        name: type,
        value: typeMap[type],
        color: colorList[i % colorList.length],
      }));
    },
    getRestaurantListForDay(dayIdx) {
      // 可根据当天event地点动态生成，现用mock
      const day = this.itinerary[dayIdx];
      if (!day) return [];
      // 取当天第一个吃饭event或第一个event的location
      let loc = "";
      const eatEvent = (day.events || []).find((e) => e.type === "吃饭");
      if (eatEvent) loc = eatEvent.location;
      else if (day.events && day.events.length) loc = day.events[0].location;
      return [
        {
          name: loc + "·推荐餐厅A",
          image: "/static/images/food.jpg",
          distance: "1.2km",
        },
        {
          name: loc + "·推荐餐厅B",
          image: "/static/images/food.jpg",
          distance: "2.3km",
        },
      ];
    },
    getNotesListForDay(dayIdx) {
      // 可根据当天event地点动态生成，现用mock
      const day = this.itinerary[dayIdx];
      if (!day) return [];
      const loc = day.events && day.events.length ? day.events[0].location : "";
      return [
        {
          image: "/static/images/food.jpg",
          title: loc + "游玩体验",
          content: loc + "是本地热门打卡地，推荐大家慢慢逛、慢慢拍照！",
          likes: 1000 + dayIdx * 100,
          comments: 100 + dayIdx * 10,
          collects: 20 + dayIdx * 5,
        },
        {
          image: "/static/images/food.jpg",
          title: loc + "美食推荐",
          content: "附近有很多美食，火锅、串串、甜品都值得尝试！",
          likes: 800 + dayIdx * 80,
          comments: 80 + dayIdx * 8,
          collects: 15 + dayIdx * 3,
        },
      ];
    },
    async loadMap() {
      // 在线获取四川省geoJSON
      const res = await fetch(
        "https://geo.datav.aliyun.com/areas_v3/bound/510000_full.json"
      );
      const geoJson = await res.json();
      echarts.registerMap("sichuan", geoJson);
      this.option = {
        geo: {
          map: "sichuan",
          roam: true,
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
            data: this.points.map((p) => ({
              name: p.name,
              value: p.coord,
              id: p.id,
            })),
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
            data: this.getLineData(),
          },
        ],
      };
    },
    getLineData() {
      const arr = [];
      for (let i = 0; i < this.points.length - 1; i++) {
        arr.push({
          coords: [this.points[i].coord, this.points[i + 1].coord],
        });
      }
      return arr;
    },
    onMapClick(params) {
      if (
        params.componentType === "series" &&
        params.seriesType === "scatter"
      ) {
        const point = this.points.find((p) => p.name === params.name);
        if (point) {
          this.currentPoint = point;
          this.showPopup = true;
        }
      }
    },
  },
};
</script>

<style>
.detail-container {
  background: #fff;
  min-height: 100vh;
  padding-bottom: 4px;
}
.detail-header {
  display: flex;
  align-items: center;
  padding: 16px;
}
.back-btn {
  color: #673ab7;
  margin-right: 16px;
}
.title {
  font-weight: bold;
  font-size: 18px;
}
.tab-bar {
  display: flex;
  border-bottom: 1px solid #eee;
}
.tab-item {
  flex: 1;
  text-align: center;
  padding: 12px 0;
  color: #888;
}
.tab-item.active {
  color: #673ab7;
  border-bottom: 2px solid #673ab7;
  font-weight: bold;
}
.day-card {
  background: #f8f4e9;
  margin: 8px 16px 8px 16px;
  border-radius: 12px;
  padding: 12px;
}
.budget-card {
  background: #f8f4e9;
  margin: 8px 16px 8px 16px;
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}
.edit-btn {
  width: 90%;
  margin: 16px 5% 10px 5%;
  background: #673ab7;
  color: #fff;
  border-radius: 8px;
}
.event-row {
  display: flex;
  align-items: center;
  margin: 8px 0;
}
.event-time {
  min-width: 60px;
  color: #888;
  font-size: 13px;
  margin-right: 8px;
}
.event-location {
  font-size: 14px;
  color: #2c4a52;
  margin-right: 8px;
}
.event-subtext {
  font-size: 12px;
  color: #a88;
  margin-left: 4px;
}
.event-image {
  width: 40px;
  height: 30px;
  border-radius: 6px;
  margin-left: 8px;
  object-fit: cover;
}
.budget-title {
  font-weight: bold;
  margin-bottom: 8px;
}
.legend-row {
  display: flex;
  flex-wrap: wrap;
  margin: 4px 0;
}
.legend-item {
  flex: 1;
  font-size: 13px;
  margin-right: 8px;
}
.day-header {
  background: #f8f4e9;
  border-radius: 12px;
  margin: 8px 16px 8px 16px;
  padding: 12px;
  font-size: 15px;
}
.timeline {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  margin: 16px 0 12px 0;
  overflow-x: auto;
}
.timeline-event {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 16px;
  position: relative;
}
.timeline-dot {
  width: 10px;
  height: 10px;
  background: #673ab7;
  border-radius: 50%;
  margin-bottom: 4px;
}
.timeline-time {
  font-size: 13px;
  color: #888;
  margin-bottom: 4px;
}
.timeline-img {
  width: 48px;
  height: 36px;
  border-radius: 6px;
  object-fit: cover;
  margin-bottom: 4px;
}
.timeline-location {
  font-size: 13px;
  color: #2c4a52;
  text-align: center;
}
.section-title {
  font-weight: bold;
  margin: 18px 0 8px 16px;
  font-size: 15px;
}
.restaurant-scroll {
  display: flex;
  flex-direction: row;
  padding: 0 0 8px 16px;
}
.restaurant-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(60, 89, 107, 0.08);
  margin-right: 12px;
  width: 120px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.restaurant-img {
  width: 80px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
  margin-bottom: 6px;
}
.restaurant-name {
  font-size: 13px;
  color: #2c4a52;
  margin-bottom: 2px;
  text-align: center;
}
.restaurant-info {
  font-size: 12px;
  color: #888;
  text-align: center;
}
.nav-link {
  color: #673ab7;
  margin-left: 4px;
}
.note-card {
  display: flex;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(60, 89, 107, 0.08);
  margin: 12px 16px;
  padding: 8px;
}
.note-img {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
  margin-right: 10px;
}
.note-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.note-title {
  font-size: 14px;
  font-weight: bold;
  color: #2c4a52;
  margin-bottom: 2px;
}
.note-text {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}
.note-meta {
  font-size: 12px;
  color: #aaa;
  display: flex;
  gap: 12px;
}
.day-switch {
  display: flex;
  margin: 12px 0 0 16px;
}
.day-switch-item {
  padding: 6px 16px;
  border-radius: 16px;
  background: #f5f5f5;
  color: #888;
  margin-right: 8px;
  font-size: 14px;
  cursor: pointer;
}
.day-switch-item.active {
  background: #673ab7;
  color: #fff;
  font-weight: bold;
}
.map-tab {
  padding: 16px 0;
}
.popup-content {
  padding: 20px;
}
.img-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.img-list image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
}
</style>
