<template>
  <view class="container">
    <!-- 自定义导航栏 -->
    <view class="custom-nav" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-content">
        <view class="left-area">
          <view class="menu-icon" @tap="toggleSidebar">
            <image src="/static/icons/menu.png" mode="aspectFit"></image>
          </view>
        </view>
        <view class="center-area">
          <view class="title" @click="goToHome">
            <image
              src="/static/icons/logo.png"
              mode="aspectFit"
              class="logo-icon"
            ></image>
            <text>ChatJourney</text>
          </view>
        </view>
        <view class="right-area">
          <view class="stream-toggle" @click="toggleStreamMode">
            <text :class="{ 'active': isStreamMode }">{{ isStreamMode ? '流式' : '同步' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 侧边栏 -->
    <view class="sidebar" :class="{ 'sidebar-show': showSidebar }">
      <view class="sidebar-content">
        <!-- 用户信息 -->
        <view class="user-info">
          <view class="avatar">
            <image src="/static/icons/avatar.png" mode="aspectFit"></image>
          </view>
          <view class="user-name">小王先生</view>
          <view class="user-actions">
            <view class="search-icon">
              <image src="/static/icons/search.png" mode="aspectFit"></image>
            </view>
            <view class="settings-icon">
              <image src="/static/icons/settings.png" mode="aspectFit"></image>
            </view>
          </view>
        </view>

        <!-- 新对话按钮 -->
        <view class="new-chat">
          <button class="new-chat-btn" @tap="createNewChatFromSidebar">
            + 新建对话
          </button>
        </view>

        <!-- 对话列表 -->
        <view class="chat-list">
          <view class="chat-list-title">历史对话</view>
          <view
            class="chat-item"
            v-for="chat in chatList"
            :key="chat.id"
            @tap="switchToChat(chat)"
          >
            <text class="chat-item-title">{{ chat.title }}</text>
            <text class="chat-item-time">{{ chat.lastTime }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 遮罩层 -->
    <view class="mask" v-if="showSidebar" @tap="toggleSidebar"></view>

    <view class="content" :style="{ paddingTop: contentPaddingTop + 'px' }">
      <!-- 背景图片 -->
      <view class="banner">
        <image src="/static/images/banner.jpg" mode="aspectFill"></image>
      </view>

      <!-- 欢迎区域 -->
      <view class="welcome-card" v-if="showWelcome">
        <view class="welcome-title">Hi~我的AI旅游小助手</view>
        <view class="welcome-subtitle"
          >你贴心的小导游，可以为您推荐好吃的、好玩的、便宜的旅游打卡地哦~</view
        >

        <!-- 快捷选项按钮组 -->
        <view class="quick-options">
          <view
            class="option-item"
            @click="
              autoSendMessage(
                '我想去成都玩3天，预算3000元，帮我出一套旅游攻略',
                true
              )
            "
            >我想去成都玩3天，预算3000元，帮我出一套旅游攻略</view
          >
          <view class="option-grid">
            <view
              class="option-btn"
              @click="autoSendMessage('我想超性价比的旅游', true)"
              >我想超性价比的旅游</view
            >
            <view
              class="option-btn"
              @click="autoSendMessage('我预算有限', true)"
              >我预算有限</view
            >
            <view
              class="option-btn"
              @click="autoSendMessage('时间别太赶', true)"
              >时间别太赶</view
            >
            <view
              class="option-btn"
              @click="autoSendMessage('我想少走路', true)"
              >我想少走路</view
            >
            <view
              class="option-btn"
              @click="autoSendMessage('距离近的周边游', true)"
              >距离近的周边游</view
            >
            <view
              class="option-btn"
              @click="autoSendMessage('引导问题xx', true)"
              >引导问题xx</view
            >
          </view>
        </view>
      </view>

      <!-- 对话背景 -->
      <view class="chat-background" v-if="!showWelcome">
        <view class="chat-container">
          <!-- 添加对话标题 -->
          <view class="chat-title" v-if="currentChatTitle">
            <text>{{ currentChatTitle }}</text>
          </view>
          <scroll-view
            scroll-y
            class="message-list"
            :scroll-top="scrollTop"
            @scrolltoupper="loadMoreMessages"
          >
            <view
              v-for="(message, index) in messages"
              :key="index"
              class="message-item"
              :class="message.type"
            >
              <template v-if="message.type === 'status'">
                <view class="message-content status-content">
                  <template v-if="message.content.includes('生成中')">
                    <image
                      class="status-icon loading-spin"
                      src="/static/icons/loading.svg"
                      mode="aspectFit"
                    />
                    <text>生成中，请稍等...</text>
                    <button class="cancel-btn" @click="cancelGeneration">
                      取消生成
                    </button>
                  </template>
                  <template v-else-if="message.content.includes('取消')">
                    <image
                      class="status-icon"
                      src="/static/icons/cancel.svg"
                      mode="aspectFit"
                    />
                    <text>已取消生成</text>
                  </template>
                  <template v-else-if="message.content.includes('完成')">
                    <image
                      class="status-icon"
                      src="/static/icons/success.svg"
                      mode="aspectFit"
                    />
                    <text>已完成生成</text>
                  </template>
                  <template v-else>
                    <image
                      class="status-icon loading-spin"
                      src="/static/icons/loading.svg"
                      mode="aspectFit"
                    />
                    <text>{{ message.content }}</text>
                  </template>
                </view>
              </template>
              <template v-else>
                <view class="message-content">
                  <text>{{ message.content }}</text>
                  <view class="message-footer">
                  <text class="message-time">{{ message.time }}</text>
                    <view v-if="message.isStreaming" class="streaming-indicator">
                      <text class="streaming-dot"></text>
                      <text class="streaming-text">生成中...</text>
                      <button class="cancel-stream-btn" @click="cancelStreamGeneration">取消</button>
                    </view>
                  </view>
                </view>
              </template>
            </view>
          </scroll-view>
        </view>
        <!-- 新增提示词区域 -->
        <view class="suggestion-bar" v-if="!showWelcome && suggestions.length">
          <view class="suggestion-title">你还可以这样说</view>
          <scroll-view scroll-x class="suggestion-list">
            <view
              class="suggestion-btn"
              v-for="(item, idx) in suggestions"
              :key="idx"
              @tap="autoSendMessage(item)"
            >
              {{ item }}
            </view>
          </scroll-view>
        </view>
      </view>

      <!-- 底部占位 -->
      <view class="bottom-space"></view>
    </view>

    <!-- 底部输入提示 -->
    <view class="input-hint">
      <view class="input-box">
        <input
          type="text"
          v-model="inputMessage"
          placeholder="何必自己做攻略，直接问我吧~"
          @confirm="sendMessage"
          class="message-input"
        />
        <image
          v-if="!awaitingReply && !initializing"
          src="/static/icons/send.png"
          mode="aspectFit"
          class="send-icon"
          @click="sendMessage"
        ></image>
        <image
          v-else
          src="/static/icons/loading.svg"
          mode="aspectFit"
          class="send-icon loading-spin"
        ></image>
      </view>
    </view>

    <!-- 灵感拼图悬浮按钮 -->
    <view
      class="jigsaw-fab"
      v-if="
        !showWelcome &&
        (jigsawType === 'location' ||
          jigsawType === 'budget' ||
          (jigsawType === 'itinerary' && itinerary.length))
      "
      @tap="toggleJigsaw"
    >
      <image src="/static/icons/star.png" mode="aspectFit"></image>
    </view>

    <!-- 灵感拼图侧边栏 -->
    <view class="jigsaw-sidebar" :class="{ 'jigsaw-sidebar-show': showJigsaw }">
      <view class="jigsaw-content">
        <view class="jigsaw-header">
          <view class="jigsaw-title">灵感拼图</view>
          <view class="jigsaw-subtitle">
            <template v-if="jigsawType === 'location'">猜你想去</template>
            <template v-else-if="jigsawType === 'budget'">预算分配</template>
            <template v-else>预览攻略</template>
          </view>
        </view>
        <scroll-view
          class="timeline-container"
          scroll-y
          :style="{ height: '100%' }"
        >
          <template v-if="jigsawType === 'location'">
            <view
              v-for="(item, idx) in locationJigsawData"
              :key="idx"
              style="margin-bottom: 18px"
            >
              <view
                style="
                  display: flex;
                  background: #fff;
                  border-radius: 16px;
                  box-shadow: 0 2px 8px rgba(60, 89, 107, 0.08);
                  padding: 10px 14px;
                  align-items: center;
                "
              >
                <image
                  :src="item.image"
                  style="
                    width: 70px;
                    height: 50px;
                    border-radius: 10px;
                    object-fit: cover;
                    margin-right: 12px;
                  "
                />
                <view style="flex: 1">
                  <view
                    style="
                      font-weight: bold;
                      font-size: 15px;
                      color: #2c4a52;
                      margin-bottom: 2px;
                    "
                    >{{ item.title }}</view
                  >
                  <view style="font-size: 13px; color: #888; margin-bottom: 2px"
                    >评分：{{ item.score }}分</view
                  >
                  <view
                    style="
                      display: flex;
                      align-items: center;
                      font-size: 12px;
                      color: #888;
                    "
                  >
                    <view style="margin-right: 10px">{{ item.traffic }}</view>
                    <view>{{ item.weather }}</view>
                  </view>
                </view>
              </view>
            </view>
          </template>
          <template v-else-if="jigsawType === 'budget'">
            <view
              style="
                background: #fcf6e8;
                border-radius: 16px;
                box-shadow: 0 2px 8px rgba(60, 89, 107, 0.08);
                padding: 18px;
                margin-bottom: 18px;
              "
            >
              <view
                style="
                  font-weight: bold;
                  font-size: 15px;
                  color: #2c4a52;
                  margin-bottom: 10px;
                "
                >预算分配</view
              >
              <view
                v-for="item in budgetJigsawData.chart"
                :key="item.name"
                style="margin-bottom: 12px"
              >
                <view style="display: flex; align-items: center">
                  <view style="width: 60px; color: #2c4a52; font-size: 14px">{{
                    item.name
                  }}</view>
                  <input
                    type="number"
                    v-model.number="budgetJigsawData[item.name]"
                    style="
                      flex: 1;
                      margin: 0 8px;
                      border: 1px solid #ddd;
                      border-radius: 8px;
                      padding: 0 12px;
                      font-size: 14px;
                      color: #2c4a52;
                      background: #fff;
                      height: 36px;
                    "
                    min="0"
                    max="10000"
                  />
                  <view style="color: #888; font-size: 13px">元</view>
                </view>
              </view>
              <view style="margin-top: 18px">
                <view
                  style="
                    font-weight: bold;
                    font-size: 15px;
                    color: #2c4a52;
                    margin-bottom: 10px;
                  "
                  >预算分布图</view
                >
                <svg width="120" height="120" viewBox="0 0 120 120">
                  <circle
                    v-for="(item, idx) in budgetJigsawData.chart"
                    :key="idx"
                    :stroke="item.color"
                    stroke-width="16"
                    fill="none"
                    :stroke-dasharray="getBudgetChartDasharray(idx)"
                    :stroke-dashoffset="getBudgetChartOffset(idx)"
                    cx="60"
                    cy="60"
                    r="50"
                    transform="rotate(-90 60 60)"
                  />
                </svg>
                <view style="margin-left: 16px">
                  <view
                    v-for="(item, idx) in budgetJigsawData.chart"
                    :key="idx"
                    style="
                      font-size: 13px;
                      color: #2c4a52;
                      margin-bottom: 4px;
                      display: flex;
                      align-items: center;
                    "
                  >
                    <view
                      :style="{
                        width: '12px',
                        height: '12px',
                        background: item.color,
                        borderRadius: '6px',
                        display: 'inline-block',
                        marginRight: '6px',
                      }"
                    ></view>
                    {{ item.name }}：{{ item.value }}元
                  </view>
                </view>
              </view>
            </view>
          </template>
          <template v-else>
            <!-- 行程预览（纵向timeline） -->
            <view class="timeline">
              <view v-for="(day, dayIdx) in itinerary" :key="day.date">
                <view class="timeline-day">
                  <text class="date">{{ day.date }}</text>
                  <text class="weather"
                    >{{ day.weatherIcon }} {{ day.temperature }}</text
                  >
                </view>
                <view class="timeline-events">
                  <view
                    class="event-item"
                    v-for="(event, eventIdx) in day.events"
                    :key="eventIdx"
                  >
                    <view class="event-time">
                      <view class="time-main">{{
                        formatTime(event.time).main
                      }}</view>
                      <view
                        class="time-range"
                        v-if="formatTime(event.time).range"
                        >{{ formatTime(event.time).range }}</view
                      >
                      <text class="time-sub" v-if="event.subtext">{{
                        event.subtext
                      }}</text>
                    </view>
                    <view class="event-line-content">
                      <view class="event-dot"></view>
                      <view
                        class="event-line"
                        v-if="eventIdx < day.events.length - 1"
                      ></view>
                      <view
                        class="event-image-card"
                        @tap="onEditEvent(dayIdx, eventIdx, event)"
                      >
                        <image
                          :src="event.image"
                          mode="aspectFill"
                          class="event-image"
                          :lazy-load="true"
                          @error="event.image = '/static/images/default.jpg'"
                        />
                        <view class="location-overlay">{{
                          event.location
                        }}</view>
                      </view>
                      <view class="travel-info" v-if="event.travel">
                        <view class="travel-line"></view>
                        <text
                          >{{ event.travel.duration }}
                          {{ event.travel.method }}</text
                        >
                        <view class="travel-arrow">↓</view>
                      </view>
                    </view>
                  </view>
                </view>
              </view>
            </view>
            <!-- 按钮放到scroll-view内部timeline后面 -->
            <view class="jigsaw-action-btns">
              <template v-if="!isSimpleEditMode">
                <view class="jigsaw-btn" @tap="onViewDetail">
                  <image
                    src="/static/icons/success.svg"
                    mode="aspectFit"
                    class="jigsaw-btn-icon"
                  />
                  <text>查看详情</text>
                </view>
                <view class="jigsaw-btn" @tap="onSimpleEdit">
                  <image
                    src="/static/icons/settings.png"
                    mode="aspectFit"
                    class="jigsaw-btn-icon"
                  />
                  <text>简单修改</text>
                </view>
              </template>
              <template v-else>
                <view class="jigsaw-btn" style="width: 100%" @tap="onSaveRoute">
                  <image
                    src="/static/icons/star.png"
                    mode="aspectFit"
                    class="jigsaw-btn-icon"
                  />
                  <text>保存路线</text>
                </view>
              </template>
            </view>
            <view style="height: 32px"></view>
            <!-- 地点选择弹窗 -->
            <view
              v-if="showPlaceSelector && editEvent && editEvent.event"
              class="place-selector-modal"
            >
              <view class="place-selector-content">
                <view class="place-selector-title">
                  第{{ editEvent && editEvent.dayIndex + 1 }}天 ·
                  {{ editEvent && editEvent.event && editEvent.event.time }}
                </view>
                <view style="margin: 10px 0 6px 0">已定地点：</view>
                <view class="place-selected">
                  <image
                    :src="editEvent && editEvent.event && editEvent.event.image"
                    class="place-selected-img"
                  />
                  <view class="place-selected-name">{{
                    editEvent && editEvent.event && editEvent.event.location
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
          </template>
        </scroll-view>
      </view>
    </view>

    <!-- 遮罩层 -->
    <view class="mask" v-if="showJigsaw" @tap="toggleJigsaw"></view>
  </view>
</template>

<script>
import { request, requestStream, requestStreamFallback } from "@/utils/request.js";

export default {
  data() {
    return {
      statusBarHeight: 0,
      contentPaddingTop: 0,
      navContentHeight: 52,
      showSidebar: false,
      showWelcome: true,
      inputMessage: "",
      messages: [],
      currentChatTitle: "",
      chatList: [],
      currentChatId: null,
      suggestions: [
        "我需要换个目的地",
        "我需要再调整一下预算",
        "帮我推荐亲子游",
        "帮我推荐美食路线",
        "帮我推荐避暑胜地",
      ],
      lastMessageId: "",
      showJigsaw: false,
      itinerary: [],
      isGenerating: false,
      jigsawType: "location", // 'location' | 'budget' | 'itinerary'
      locationJigsawData: [
        {
          title: "成都三元油菜花田",
          score: 4.8,
          traffic: "地铁出行",
          weather: "☀️ 32/39℃",
          image: "/static/images/flower.jpg",
        },
        {
          title: "云南罗平油菜花田",
          score: 4.8,
          traffic: "飞机出行",
          weather: "☀️ 32/39℃",
          image: "/static/images/flower.jpg",
        },
        {
          title: "云南罗平油菜花田",
          score: 4.8,
          traffic: "高铁出行",
          weather: "☀️ 32/39℃",
          image: "/static/images/flower.jpg",
        },
      ],
      budgetJigsawData: {
        住宿: 3400,
        餐饮: 3400,
        娱乐: 3400,
        total: 10200,
        chart: [
          { name: "住宿", value: 3400, color: "#e6c36f" },
          { name: "餐饮", value: 3400, color: "#8fd3c7" },
          { name: "娱乐", value: 3400, color: "#f7a35c" },
        ],
      },
      isSimpleEditMode: false,
      showPlaceSelector: false,
      editEvent: null, // {dayIndex, eventIndex, event}
      placeTabs: ["相似主体", "更高性价比", "更少人流"],
      activePlaceTab: 0,
      placeCandidates: [
        [
          { name: "当地YYY饭店", image: "/static/images/food.jpg" },
          { name: "当地YYY饭店", image: "/static/images/food.jpg" },
          { name: "当地YYY饭店", image: "/static/images/food.jpg" },
          { name: "当地YYY饭店", image: "/static/images/food.jpg" },
        ],
        [
          { name: "高性价比饭店A", image: "/static/images/food.jpg" },
          { name: "高性价比饭店B", image: "/static/images/food.jpg" },
        ],
        [
          { name: "人流少饭店A", image: "/static/images/food.jpg" },
          { name: "人流少饭店B", image: "/static/images/food.jpg" },
        ],
      ],
      sessionId: null, // 后端会话ID
      scrollTop: 0,
      _creatingSession: null,
      initializing: false,
      queuedMessage: "",
      awaitingReply: false,
      // 流式处理相关
      isStreamMode: true, // 是否启用流式模式
      streamingMessageIndex: -1, // 正在流式输出的消息索引
      streamingContent: "", // 流式输出的累积内容
      streamController: null, // 流式请求控制器
    };
  },
  onLoad() {
    const systemInfo = uni.getSystemInfoSync();
    this.statusBarHeight = systemInfo.statusBarHeight;
    this.contentPaddingTop = this.statusBarHeight + this.navContentHeight;
  },
  watch: {
    "budgetJigsawData.住宿"(newVal) {
      this.syncChartAndTotal("住宿", newVal);
    },
    "budgetJigsawData.餐饮"(newVal) {
      this.syncChartAndTotal("餐饮", newVal);
    },
    "budgetJigsawData.娱乐"(newVal) {
      this.syncChartAndTotal("娱乐", newVal);
    },
  },
  methods: {
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
    },
    createNewChatFromSidebar() {
      this.toggleSidebar();
      this.goToHome();
    },
    goToHome() {
      this._resetFlags();
      this.showWelcome = true;
    },
    startNewChat() {
      this._resetFlags();
      this.showWelcome = false;
    },
    autoSendMessage(content, isNewChat = false) {
      if (isNewChat) {
        this.startNewChat();
        setTimeout(() => {
          this.inputMessage = content;
          this.sendMessage();
        }, 100);
      } else {
        this.inputMessage = content;
        this.sendMessage();
      }
    },
    saveChatToHistory() {
      if (this.messages.length > 0) {
        const chatId = this.currentChatId || Date.now().toString();
        const chatData = {
          id: chatId,
          title: this.currentChatTitle,
          messages: [...this.messages],
          lastTime: new Date().toLocaleString(),
          itinerary: JSON.parse(JSON.stringify(this.itinerary)),
          budget: JSON.parse(JSON.stringify(this.budgetJigsawData)),
        };

        const index = this.chatList.findIndex((chat) => chat.id === chatId);
        if (index !== -1) {
          this.chatList[index] = chatData;
        } else {
          this.chatList.unshift(chatData);
        }

        this.currentChatId = chatId;
      }
    },
    switchToChat(chat) {
      this.currentChatId = chat.id;
      this.currentChatTitle = chat.title;
      this.messages = [...chat.messages];
      this.showWelcome = false;
      this.toggleSidebar();
      if (chat.itinerary) {
        this.itinerary = JSON.parse(JSON.stringify(chat.itinerary));
      }
      if (chat.budget) {
        this.budgetJigsawData = JSON.parse(JSON.stringify(chat.budget));
      }
    },
    /** 创建会话，返回 Promise<sessionId> */
    createSession() {
      if (this.sessionId) return Promise.resolve(this.sessionId);
      // 避免重复并发创建
      if (this._creatingSession) return this._creatingSession;
      uni.showToast({ title: "会话初始化中", icon: "none" });
      this._creatingSession = request("/api/session/", { username: "demo" }, "POST")
        .then((res) => {
          this.sessionId = res.session_id;
          return this.sessionId;
        })
        .catch((err) => {
          console.error("会话创建失败", err);
          uni.showToast({ title: "创建会话失败", icon: "none" });
          throw err;
        })
        .finally(() => {
          this._creatingSession = null;
        });
      return this._creatingSession;
    },

    /** 真正发送消息到后端并处理回复 */
    _sendToBackend(text) {
      if (this.isStreamMode) {
        this._sendToBackendStream(text);
        } else {
        this._sendToBackendSync(text);
      }
    },

    /** 同步发送消息到后端 */
    _sendToBackendSync(text) {
      this.awaitingReply = true;
      request("/api/message/", { session_id: this.sessionId, message: text }, "POST")
        .then((res) => {
          const reply =
            res.response ||
            res.reply ||
            res.data?.content ||
            "[AI暂无回复]";
          this.messages.push({
            type: "ai",
            content: reply,
          time: new Date().toLocaleTimeString(),
          });
          this.saveChatToHistory();
          this.scrollToBottom();
        })
        .catch((err) => {
          console.error(err);
            this.messages.push({
            type: "ai",
            content: "⚠️ 服务器出错，请稍后再试",
            time: new Date().toLocaleTimeString(),
          });
        })
        .finally(() => {
          this.awaitingReply = false;
        });
    },

    /** 流式发送消息到后端 */
    _sendToBackendStream(text) {
      this.awaitingReply = true;
      this.streamingContent = "";
      
      // 添加一个空的AI消息，用于流式更新
            this.messages.push({
              type: "ai",
        content: "",
              time: new Date().toLocaleTimeString(),
        isStreaming: true // 标记为流式消息
            });
      
      this.streamingMessageIndex = this.messages.length - 1;
      this.scrollToBottom();

      // 优先尝试真正的流式请求
      const streamOptions = {
        onChunk: (chunk) => {
          this._handleStreamChunk(chunk);
        },
        onDone: (fullContent) => {
          this._handleStreamDone(fullContent);
        },
        onError: (error) => {
          this._handleStreamError(error);
        }
      };

      // 尝试流式请求，如果失败则降级到模拟流式
      requestStream("/api/talker/state-machine/", { 
        session_id: this.sessionId, 
        message: text,
        stream: true
      }, streamOptions)
        .then((controller) => {
          this.streamController = controller;
        })
                  .catch((err) => {
            console.error("流式请求失败:", err);
            this._handleStreamError(err);
          });
    },

    /** 处理流式数据块 */
    _handleStreamChunk(chunk) {
      console.log('收到流式数据块:', chunk);
      
      if (chunk.type === 'content' && chunk.chunk) {
        this.streamingContent += chunk.chunk;
        
        console.log('更新流式内容:', {
          streamingMessageIndex: this.streamingMessageIndex,
          messagesLength: this.messages.length,
          streamingContent: this.streamingContent,
          chunkContent: chunk.chunk
        });
        
        // 更新正在流式输出的消息内容
        if (this.streamingMessageIndex >= 0 && this.streamingMessageIndex < this.messages.length) {
          // 添加短暂延迟以便观察打字机效果
          setTimeout(() => {
            this.$set(this.messages, this.streamingMessageIndex, {
              ...this.messages[this.streamingMessageIndex],
              content: this.streamingContent
            });
            
            console.log('消息已更新:', this.messages[this.streamingMessageIndex]);
            
            // 自动滚动到底部
            this.$nextTick(() => {
              this.scrollToBottom();
            });
          }, 10); // 10ms延迟
        }
      } else if (chunk.type === 'event') {
        console.log('收到事件:', chunk.event, chunk.data);
      }
    },

    /** 处理流式完成 */
    _handleStreamDone(fullContent) {
      // 标记流式输出完成
      if (this.streamingMessageIndex >= 0 && this.streamingMessageIndex < this.messages.length) {
        this.$set(this.messages, this.streamingMessageIndex, {
          ...this.messages[this.streamingMessageIndex],
          content: fullContent || this.streamingContent,
          isStreaming: false // 取消流式标记
        });
      }
      
      this._resetStreamState();
            this.saveChatToHistory();
            this.scrollToBottom();
    },

    /** 处理流式错误 */
    _handleStreamError(error) {
      console.error("流式处理错误:", error);
      
      // 更新消息为错误状态
      if (this.streamingMessageIndex >= 0 && this.streamingMessageIndex < this.messages.length) {
        this.$set(this.messages, this.streamingMessageIndex, {
          ...this.messages[this.streamingMessageIndex],
          content: "⚠️ 服务器出错，请稍后再试",
          isStreaming: false
        });
        } else {
        // 如果没有正在流式输出的消息，添加一个错误消息
            this.messages.push({
              type: "ai",
          content: "⚠️ 服务器出错，请稍后再试",
              time: new Date().toLocaleTimeString(),
            });
      }
      
      this._resetStreamState();
    },

    /** 重置流式状态 */
    _resetStreamState() {
      this.awaitingReply = false;
      this.streamingMessageIndex = -1;
      this.streamingContent = "";
      this.streamController = null;
    },

    /** 切换流式模式 */
    toggleStreamMode() {
      this.isStreamMode = !this.isStreamMode;
      uni.showToast({
        title: this.isStreamMode ? "已启用流式模式" : "已关闭流式模式",
        icon: "none"
      });
    },

    /** 取消流式生成 */
    cancelStreamGeneration() {
      if (this.streamController && typeof this.streamController.cancel === 'function') {
        this.streamController.cancel();
      }
      
      // 更新UI状态
      if (this.streamingMessageIndex >= 0 && this.streamingMessageIndex < this.messages.length) {
        this.$set(this.messages, this.streamingMessageIndex, {
          ...this.messages[this.streamingMessageIndex],
          content: this.streamingContent || "⚠️ 生成已取消",
          isStreaming: false
        });
      }
      
      this._resetStreamState();
      
      uni.showToast({
        title: "已取消生成",
        icon: "none"
      });
    },
    sendMessage() {
      const text = this.inputMessage.trim();
      if (!text) return;

        this.inputMessage = "";

      if (!this.sessionId) {
        // 首次对话：先创建会话，获取AI问候，然后再发送用户信息
        if (this.initializing) return; // 已在初始化中
        this.initializing = true;
        this.queuedMessage = text;

        // 显示 loading 状态
        this.messages.push({ type: "status", content: "会话初始化中..." });

        this.createSession()
          .then(() => {
            // 移除初始化状态
            this.messages = this.messages.filter(
              (m) => !(m.type === "status" && m.content.includes("会话初始化中"))
            );
            
            // 直接发送用户消息，让状态机处理欢迎语和用户消息
            this._pushUserMessage(this.queuedMessage);
            
            // 根据当前模式选择发送方式
            if (this.isStreamMode) {
              this._sendToBackendStream(this.queuedMessage);
            } else {
              this._sendToBackend(this.queuedMessage);
            }
          })
          .catch((err) => {
            console.error(err);
            this.messages.push({
              type: "ai",
              content: "⚠️ 会话初始化失败，请重试",
              time: new Date().toLocaleTimeString(),
            });
          })
          .finally(() => {
            this.initializing = false;
            this.queuedMessage = "";
          });
        return;
      }

      // 已存在会话，正常流程
      this._pushUserMessage(text);
      
      // 根据当前模式选择发送方式
      if (this.isStreamMode) {
        this._sendToBackendStream(text);
      } else {
        this._sendToBackend(text);
      }
    },
    _pushUserMessage(text) {
      if (this.messages.length === 0) this.currentChatTitle = text;
      this.messages.push({
        type: "user",
        content: text,
        time: new Date().toLocaleTimeString(),
      });
      this.showWelcome = false;
      this.$nextTick(() => {
        this.lastMessageId = "msg-" + (this.messages.length - 1);
      });
    },
    scrollToBottom() {
      this.$nextTick(() => {
        this.lastMessageId = "msg-" + (this.messages.length - 1);
      });
    },
    getSampleItinerary() {
      return [
        {
          date: "4月12日",
          weatherIcon: "☀️",
          temperature: "32/39℃",
          events: [
            {
              time: "08:00",
              image: "/static/images/airport1.jpg",
              location: "成都双流国际机场",
              travel: { duration: "1.5h", method: "乘飞机前往" },
              type: "交通",
              duration: 90,
            },
            {
              time: "09:30",
              image: "/static/images/airport2.jpg",
              location: "昆明长水机场",
              travel: { duration: "2.5h", method: "乘大巴前往" },
              type: "交通",
              duration: 150,
            },
            {
              time: "12:00",
              image: "/static/images/flower.jpg",
              location: "罗平油菜花田入口",
              travel: { duration: "15min", method: "步行" },
              type: "游玩",
              duration: 120,
            },
            {
              time: "12:15 ~ 13:45",
              subtext: "用餐",
              image: "/static/images/food.jpg",
              location: "当地XXX饭店",
              travel: { duration: "30min", method: "步行" },
              type: "吃饭",
              duration: 90,
            },
          ],
        },
        {
          date: "4月13日",
          weatherIcon: "⛅",
          temperature: "28/35℃",
          events: [
            {
              time: "08:30",
              image: "/static/images/flower.jpg",
              location: "罗平油菜花田深处",
              travel: { duration: "20min", method: "步行" },
              type: "游玩",
              duration: 120,
            },
            {
              time: "10:30",
              image: "/static/images/food.jpg",
              location: "花田农家乐",
              travel: { duration: "10min", method: "步行" },
              type: "吃饭",
              duration: 60,
            },
            {
              time: "12:00",
              image: "/static/images/airport2.jpg",
              location: "昆明长水机场",
              travel: { duration: "2h", method: "乘大巴返回" },
              type: "交通",
              duration: 120,
            },
            {
              time: "14:30",
              image: "/static/images/airport1.jpg",
              location: "成都双流国际机场",
              travel: { duration: "2h", method: "乘飞机返回" },
              type: "交通",
              duration: 120,
            },
            {
              time: "17:00",
              image: "/static/images/food.jpg",
              location: "成都火锅店",
              travel: { duration: "30min", method: "步行" },
              type: "吃饭",
              duration: 90,
            },
          ],
        },
        {
          date: "4月14日",
          weatherIcon: "☁️",
          temperature: "25/32℃",
          events: [
            {
              time: "09:00",
              image: "/static/images/flower.jpg",
              location: "成都人民公园",
              travel: { duration: "20min", method: "步行" },
              type: "游玩",
              duration: 120,
            },
            {
              time: "11:30",
              image: "/static/images/food.jpg",
              location: "公园茶馆",
              travel: { duration: "10min", method: "步行" },
              type: "吃饭",
              duration: 60,
            },
            {
              time: "13:00",
              image: "/static/images/flower.jpg",
              location: "宽窄巷子",
              travel: { duration: "30min", method: "步行" },
              type: "游玩",
              duration: 120,
            },
            {
              time: "15:30",
              image: "/static/images/food.jpg",
              location: "成都小吃街",
              travel: { duration: "20min", method: "步行" },
              type: "吃饭",
              duration: 60,
            },
          ],
        },
      ];
    },
    toggleJigsaw() {
      this.showJigsaw = !this.showJigsaw;
    },
    formatTime(time) {
      if (time.includes("~")) {
        const parts = time.split("~");
        return {
          main: parts[0].trim(),
          range: `~<br/>${parts[1].trim()}`,
        };
      }
      return { main: time, range: null };
    },
    cancelGeneration() {
      // 只移除包含"生成中"的状态消息
      this.messages = this.messages.filter(
        (msg) => !(msg.type === "status" && msg.content.includes("生成中"))
      );
      this.isGenerating = false;

      // 添加"已取消生成"状态消息
      this.messages.push({
        type: "status",
        content: "已取消生成",
      });
      this.scrollToBottom();

      // 添加AI询问消息
      setTimeout(() => {
        this.messages.push({
          type: "ai",
          content:
            "已为您取消生成。请问您是否需要修改行程要求？比如调整目的地、预算、天数或者其他需求？",
          time: new Date().toLocaleTimeString(),
        });
        this.saveChatToHistory();
        this.scrollToBottom();
      }, 500);
    },
    getBudgetChartDasharray(idx) {
      // 总周长 = 2 * Math.PI * r (r=50)
      const C = 2 * Math.PI * 50;
      const total = this.budgetJigsawData.chart.reduce(
        (sum, item) => sum + item.value,
        0
      );
      const value = this.budgetJigsawData.chart[idx].value;
      const length = (value / total) * C;
      return `${length} ${C - length}`;
    },
    getBudgetChartOffset(idx) {
      // 总周长 = 2 * Math.PI * r (r=50)
      const C = 2 * Math.PI * 50;
      const total = this.budgetJigsawData.chart.reduce(
        (sum, item) => sum + item.value,
        0
      );
      let offset = 0;
      for (let i = 0; i < idx; i++) {
        offset += (this.budgetJigsawData.chart[i].value / total) * C;
      }
      return -offset;
    },
    syncChartAndTotal(key, newVal) {
      // 更新chart数组
      const chartItem = this.budgetJigsawData.chart.find(
        (item) => item.name === key
      );
      if (chartItem) {
        chartItem.value = newVal;
      }
      // 重新计算总数
      this.budgetJigsawData.total = this.budgetJigsawData.chart.reduce(
        (total, item) => total + item.value,
        0
      );
    },
    onViewDetail() {
      const itineraryStr = encodeURIComponent(JSON.stringify(this.itinerary));
      const budgetStr = encodeURIComponent(
        JSON.stringify(this.budgetJigsawData)
      );
      uni.navigateTo({
        url: `/pages/detail/detail?itinerary=${itineraryStr}&budget=${budgetStr}`,
      });
    },
    onSimpleEdit() {
      this.isSimpleEditMode = true;
    },
    onSaveRoute() {
      this.isSimpleEditMode = false;
      uni.showToast({ title: "已保存路线", icon: "success" });
    },
    onEditEvent(dayIndex, eventIndex, event) {
      if (!this.isSimpleEditMode) return;
      if (
        typeof dayIndex !== "number" ||
        typeof eventIndex !== "number" ||
        !event ||
        !this.itinerary[dayIndex] ||
        !this.itinerary[dayIndex].events ||
        !this.itinerary[dayIndex].events[eventIndex]
      ) {
        return;
      }
      this.editEvent = { dayIndex, eventIndex, event };
      this.showPlaceSelector = true;
      this.activePlaceTab = 0;

      // 动态生成placeTabs和placeCandidates
      if (event.location && event.location.includes("饭店")) {
        this.placeTabs = ["相似主体", "更高性价比", "更少人流"];
        this.placeCandidates = [
          [
            { name: "当地YYY饭店", image: "/static/images/food.jpg" },
            { name: "当地ZZZ饭店", image: "/static/images/food.jpg" },
          ],
          [
            { name: "高性价比饭店A", image: "/static/images/food.jpg" },
            { name: "高性价比饭店B", image: "/static/images/food.jpg" },
          ],
          [
            { name: "人流少饭店A", image: "/static/images/food.jpg" },
            { name: "人流少饭店B", image: "/static/images/food.jpg" },
          ],
        ];
      } else if (event.location && event.location.includes("机场")) {
        this.placeTabs = ["同类机场", "交通便利", "航班多"];
        this.placeCandidates = [
          [
            { name: "成都天府机场", image: "/static/images/airport1.jpg" },
            { name: "重庆江北机场", image: "/static/images/airport2.jpg" },
          ],
          [{ name: "交通便利机场A", image: "/static/images/airport1.jpg" }],
          [{ name: "航班多机场A", image: "/static/images/airport2.jpg" }],
        ];
      } else {
        this.placeTabs = ["推荐"];
        this.placeCandidates = [
          [
            { name: "默认推荐A", image: "/static/images/flower.jpg" },
            { name: "默认推荐B", image: "/static/images/flower.jpg" },
          ],
        ];
      }
    },
    onSelectPlace(place) {
      try {
        const { dayIndex, eventIndex } = this.editEvent;
        if (
          !this.itinerary[dayIndex] ||
          !this.itinerary[dayIndex].events ||
          !this.itinerary[dayIndex].events[eventIndex]
        ) {
          this.showPlaceSelector = false;
          this.editEvent = null;
          return;
        }
        const newEvent = {
          ...this.itinerary[dayIndex].events[eventIndex],
          location: place.name,
          image: place.image,
        };
        this.$set(this.itinerary[dayIndex].events, eventIndex, newEvent);
        this.showPlaceSelector = false;
        this.editEvent = null;
      } catch (e) {
        this.showPlaceSelector = false;
        this.editEvent = null;
        console.error("onSelectPlace error", e);
      }
    },
    onSwitchPlaceTab(idx) {
      this.activePlaceTab = idx;
    },
    onClosePlaceSelector() {
      this.showPlaceSelector = false;
      this.editEvent = null;
    },
    loadMoreMessages() {
      /* 下拉加载历史消息占位 */
    },
    /** 重置对话相关状态标记 */
    _resetFlags() {
      this.messages = [];
      this.currentChatTitle = "";
      this.currentChatId = null;
      this.itinerary = [];
      this.sessionId = null;
      this.initializing = false;
      this.awaitingReply = false;
      this.queuedMessage = "";
      // 重置流式状态
      this._resetStreamState();
      this._creatingSession = null;
    },
  },
};
</script>

<style lang="scss">
.container {
  min-height: 100vh;
  background-color: #f8f4e9;
  position: relative;
}

.custom-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background-color: rgba(79, 112, 99, 0.95);
  backdrop-filter: blur(10px);

  .nav-content {
    height: 52px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    position: relative;

    .left-area {
      position: absolute;
      left: 16px;
      height: 100%;
      display: flex;
      align-items: center;

      .menu-icon {
        width: 24px;
        height: 24px;
        opacity: 0.9;

        image {
          width: 100%;
          height: 100%;
        }
      }
    }

    .center-area {
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100%;

      .title {
        display: flex;
        align-items: center;
        color: #f8f4e9;
        font-size: 18px;
        font-weight: 500;
        opacity: 0.95;

        .logo-icon {
          width: 30px;
          height: 30px;
          margin-right: 3%;
          margin-bottom: -3%;
          vertical-align: middle;
        }
      }
    }

    .right-area {
      position: absolute;
      right: 16px;
      height: 100%;
      width: 24px;
    }
  }
}

.content {
  min-height: 100vh;
  box-sizing: border-box;
  overflow-y: auto;
  padding-bottom: 70px;
}

.banner {
  width: 100%;
  height: 240px;
  position: relative;
  overflow: hidden;
  margin-top: -44px;

  &::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 180px;
    background: linear-gradient(
      to bottom,
      transparent 0%,
      rgba(248, 244, 233, 0.4) 35%,
      rgba(248, 244, 233, 0.9) 75%,
      #f8f4e9 100%
    );
  }

  image {
    width: 100%;
    height: 100%;
  }
}

.welcome-card {
  margin: -100px 16px 16px;
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(60, 89, 107, 0.08);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  position: relative;
  z-index: 1;

  .welcome-title {
    font-size: 17px;
    font-weight: bold;
    margin-bottom: 8px;
    color: #2c4a52;
  }

  .welcome-subtitle {
    font-size: 13px;
    color: #5b7b84;
    margin-bottom: 20px;
    line-height: 1.4;
  }

  .quick-options {
    .option-item {
      background-color: rgba(60, 89, 107, 0.03);
      padding: 12px;
      border-radius: 20px;
      margin-bottom: 14px;
      font-size: 13px;
      color: #2c4a52;
      border: 1px solid rgba(60, 89, 107, 0.08);
      line-height: 1.4;
    }

    .option-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;

      .option-btn {
        background-color: rgba(60, 89, 107, 0.03);
        padding: 10px;
        border-radius: 16px;
        text-align: center;
        font-size: 12px;
        color: #2c4a52;
        border: 1px solid rgba(60, 89, 107, 0.08);
        transition: all 0.3s ease;
        line-height: 1.4;

        &:active {
          background-color: rgba(60, 89, 107, 0.08);
          transform: scale(0.98);
        }
      }
    }
  }
}

.bottom-space {
  height: 74px;
}

.input-hint {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.85) 0%,
    rgba(255, 255, 255, 0.95) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 -1px 20px rgba(60, 89, 107, 0.04);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.8);
  z-index: 99;

  &::after {
    content: "";
    position: absolute;
    bottom: -34px;
    left: 0;
    right: 0;
    height: 34px;
    background-color: #fff;
  }

  .input-box {
    background-color: rgba(60, 89, 107, 0.03);
    border: 1px solid rgba(60, 89, 107, 0.08);
    border-radius: 20px;
    padding: 12px 16px;
    margin-bottom: 0px;
    width: 100%;
    max-width: 600px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.3s ease;
    position: relative;

    &:active {
      background-color: rgba(60, 89, 107, 0.05);
      transform: scale(0.995);
    }

    .message-input {
      flex: 1;
      height: 20px;
      font-size: 13px;
      color: #2c4a52;
      background: transparent;
      border: none;
      outline: none;
      padding: 0;
      margin-right: 8px;

      &::placeholder {
        color: #8a9ea7;
      }
    }

    .send-icon {
      width: 20px;
      height: 20px;
      opacity: 0.7;
    }
  }
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 80%;
  max-width: 300px;
  background-color: #fff;
  z-index: 1000;
  transform: translateX(-100%);
  transition: transform 0.3s ease-out;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);

  &.sidebar-show {
    transform: translateX(0);
  }

  .sidebar-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #fff;
  }

  .user-info {
    background-color: #4f7063;
    padding: 16px;
    padding-top: calc(#{statusBarHeight}px + 16px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #fff;

    .avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      overflow: hidden;
      background-color: rgba(255, 255, 255, 0.2);

      image {
        width: 100%;
        height: 100%;
      }
    }

    .user-name {
      flex: 1;
      margin-left: 12px;
      font-size: 15px;
    }

    .user-actions {
      display: flex;
      gap: 16px;

      .search-icon,
      .settings-icon {
        width: 20px;
        height: 20px;
        opacity: 0.9;

        image {
          width: 100%;
          height: 100%;
        }
      }
    }
  }

  .new-chat {
    padding: 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);

    .new-chat-btn {
      width: 100%;
      height: 36px;
      line-height: 36px;
      text-align: center;
      background-color: rgba(79, 112, 99, 0.1);
      color: #4f7063;
      font-size: 14px;
      border-radius: 18px;
      border: 1px solid rgba(79, 112, 99, 0.2);
    }
  }

  .chat-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px;

    .chat-list-title {
      font-size: 13px;
      color: #999;
      margin-bottom: 12px;
    }

    .chat-item {
      display: flex;
      flex-direction: column;
      padding: 12px;
      border-bottom: 1px solid rgba(0, 0, 0, 0.05);
      transition: background-color 0.3s ease;

      &:active {
        background-color: rgba(0, 0, 0, 0.05);
      }

      .chat-item-title {
        font-size: 14px;
        color: #333;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .chat-item-time {
        font-size: 12px;
        color: #999;
      }
    }
  }
}

.mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 999;
}

.chat-background {
  margin: -100px 16px 16px;
  min-height: 200px;
  height: auto;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(60, 89, 107, 0.08);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  position: relative;
  z-index: 1;
  padding: 20px;
  display: block;

  .chat-container {
    width: 100%;
    display: block;
  }

  .message-list {
    width: 100%;
    padding: 20px 0;
    min-height: 100px;
  }
}

.chat-title {
  text-align: center;
  padding: 16px 0;
  border-bottom: 1px solid rgba(60, 89, 107, 0.1);
  margin-bottom: 10px;

  text {
    font-size: 15px;
    color: #2c4a52;
    font-weight: 500;
  }
}

.message-item {
  margin-bottom: 20px;
  display: flex;

  &.user {
    justify-content: flex-end;

    .message-content {
      background-color: #4f7063;
      color: #fff;
      border-radius: 16px 4px 16px 16px;
      margin-right: 40px;

      .message-time {
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }

  &.ai {
    justify-content: flex-start;

    .message-content {
      background-color: #fff;
      color: #2c4a52;
      border-radius: 4px 16px 16px 16px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      .message-time {
        color: #8a9ea7;
      }
    }
  }

  &.status {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 10px 0;
    font-size: 14px;
    color: #2c4a52;
  }

  .message-content {
    max-width: 80%;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.5;

    .message-time {
      display: block;
      font-size: 11px;
      margin-top: 4px;
    }
  }
}

.suggestion-bar {
  background: #f8f4e9b0;
  border-radius: 12px;
  margin: 0 0 12px 0;
  padding: 12px 12px 8px 12px;
  .suggestion-title {
    font-size: 13px;
    color: #8a9ea7;
    margin-bottom: 8px;
  }
  .suggestion-list {
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    white-space: nowrap;
    .suggestion-btn {
      display: inline-block;
      background: #f5f5f5;
      color: #4f7063;
      border-radius: 16px;
      padding: 6px 16px;
      font-size: 14px;
      margin-right: 10px;
      margin-bottom: 4px;
      border: 1px solid #e0e0e0;
      transition: background 0.2s;
    }
    .suggestion-btn:active {
      background: #e6f7ee;
    }
  }
}

.jigsaw-fab {
  position: fixed;
  right: 20px;
  bottom: 120px;
  width: 50px;
  height: 50px;
  background-color: #4f7063;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.95);
  }

  image {
    width: 28px;
    height: 28px;
    filter: brightness(0) invert(1);
  }
}

.jigsaw-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 85%;
  max-width: 360px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background-color: #4f7063;
  z-index: 1000;
  transform: translateX(100%);
  transition: transform 0.3s ease-out;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);

  &.jigsaw-sidebar-show {
    transform: translateX(0);
  }

  .jigsaw-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding-top: var(--status-bar-height);
    flex: 1;
    min-height: 0;
  }

  .jigsaw-header {
    padding: 20px;
    color: #fff;
    .jigsaw-title {
      font-size: 24px;
      font-weight: bold;
    }
    .jigsaw-subtitle {
      font-size: 14px;
      opacity: 0.8;
      margin-top: 4px;
    }
  }

  .timeline-container {
    flex: 1;
    height: 100%;
    min-height: 0;
    background-color: #f8f4e9;
    padding: 20px;
    box-sizing: border-box;
    overflow-y: auto;
  }

  .timeline {
    padding-left: 20px;
  }

  .timeline-day {
    margin-bottom: 20px;
    .date {
      font-size: 18px;
      font-weight: bold;
      color: #2c4a52;
    }
    .weather {
      font-size: 14px;
      color: #5b7b84;
      margin-left: 10px;
    }
  }

  .event-item {
    display: flex;
    position: relative;
  }

  .event-time {
    width: 80px;
    text-align: right;
    padding-right: 20px;
    flex-shrink: 0;
    color: #2c4a52;
    .time-main {
      font-size: 16px;
      font-weight: bold;
    }
    .time-range {
      font-size: 12px;
      line-height: 1.2;
      display: inline-block;
    }
    .time-sub {
      font-size: 14px;
      display: block;
      margin-top: 4px;
    }
  }

  .event-line-content {
    flex: 1;
    padding-left: 20px;
    border-left: 2px solid #d3c0a5;
    padding-bottom: 20px;
    position: relative;
  }

  .event-dot {
    width: 12px;
    height: 12px;
    background-color: #4f7063;
    border-radius: 50%;
    position: absolute;
    left: -7px;
    top: 5px;
  }

  .event-image-card {
    width: 100%;
    border-radius: 16px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    .event-image {
      width: 100%;
      height: 120px;
      display: block;
    }
    .location-overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
      color: #fff;
      padding: 16px 12px 8px;
      font-size: 14px;
      font-weight: bold;
    }
  }

  .travel-info {
    display: flex;
    align-items: center;
    color: #5b7b84;
    font-size: 13px;
    margin-top: 15px;
    padding-left: 15px;
    position: relative;

    .travel-arrow {
      margin-left: 8px;
    }
  }
}

.status-content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  color: #2c4a52;
  min-height: 40px;
  padding: 8px 16px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

  .status-icon {
    width: 20px;
    height: 20px;
    margin-right: 8px;
  }

  text {
    margin-right: 8px;
  }

  .cancel-btn {
    background: #fff0f0;
    color: #d9534f;
    border: 1px solid #d9534f;
    border-radius: 12px;
    font-size: 13px;
    padding: 2px 12px;
    height: 28px;
    line-height: 24px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .cancel-btn:active {
    background: #ffeaea;
  }
}

.loading-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

.jigsaw-action-btns {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin: 24px 0 0 0;
  .jigsaw-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: #fff;
    border-radius: 12px;
    padding: 12px 18px 8px 18px;
    box-shadow: 0 2px 8px rgba(60, 89, 107, 0.08);
    font-size: 13px;
    color: #2c4a52;
    cursor: pointer;
    .jigsaw-btn-icon {
      width: 28px;
      height: 28px;
      margin-bottom: 6px;
    }
  }
}

.place-selector-modal {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
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
  width: 90%;
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

/* 流式相关样式 */
.stream-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 28px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  cursor: pointer;
  transition: background 0.2s;
  
  text {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
    transition: color 0.2s;
    
    &.active {
      color: #f8f4e9;
      font-weight: 500;
    }
  }
  
  &:active {
    background: rgba(255, 255, 255, 0.2);
  }
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  
  .message-time {
    font-size: 12px;
    color: #999;
  }
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  
  .streaming-dot {
    width: 8px;
    height: 8px;
    background: #4CAF50;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
  }
  
  .streaming-text {
    font-size: 12px;
    color: #4CAF50;
  }
  
  .cancel-stream-btn {
    background: #fff0f0;
    color: #d9534f;
    border: 1px solid #d9534f;
    border-radius: 8px;
    font-size: 11px;
    padding: 2px 8px;
    height: 24px;
    line-height: 20px;
    cursor: pointer;
    transition: background 0.2s;
    
    &:active {
      background: #ffeaea;
    }
  }
}

@keyframes pulse {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
