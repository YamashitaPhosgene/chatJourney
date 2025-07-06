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
                  <template v-if="message.content.includes('生成中') || message.content.includes('行程规划中')">
                    <image
                      class="status-icon loading-spin"
                      src="/static/icons/loading.svg"
                      mode="aspectFit"
                    />
                    <text v-if="message.content.includes('行程规划中')">正在生成行程链，请稍等...</text>
                    <text v-else>生成中，请稍等...</text>
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
                  <!-- 使用Markdown渲染组件显示AI回复 -->
                  <template v-if="message.type === 'ai'">
                    <MarkdownRenderer :content="message.content" />
                  </template>
                  <!-- 用户消息仍使用普通文本 -->
                  <template v-else>
                    <text>{{ message.content }}</text>
                  </template>
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
        <view class="suggestion-bar" v-if="!showWelcome && suggestions.length && !awaitingReply && !initializing && !isGenerating">
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

      <!-- 回到底部按钮 -->
      <view 
        class="back-to-bottom-btn" 
        v-if="!showWelcome && isUserScrolling && messages.length > 5"
        @click="forceScrollToBottom"
      >
        <image src="/static/icons/send.png" mode="aspectFit" class="back-to-bottom-icon"></image>
        <text>回到底部</text>
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
        jigsawType === 'location' ||
        jigsawType === 'budget' ||
        jigsawType === 'itinerary' ||
        jigsawType === 'my_pois'
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
            <template v-else-if="jigsawType === 'my_pois'">我的POI</template>
            <template v-else>预览攻略</template>
          </view>
          
          <!-- 标签页导航 -->
          <view class="jigsaw-tabs">
            <view 
              class="jigsaw-tab"
              :class="{ active: jigsawType === 'location' }"
              @tap="switchJigsawType('location')"
            >
              推荐
            </view>
            <view 
              class="jigsaw-tab"
              :class="{ active: jigsawType === 'my_pois' }"
              @tap="switchJigsawType('my_pois')"
            >
              我的POI
            </view>
            <view 
              class="jigsaw-tab"
              :class="{ active: jigsawType === 'budget' }"
              @tap="switchJigsawType('budget')"
            >
              预算
            </view>
            <view 
              class="jigsaw-tab"
              :class="{ active: jigsawType === 'itinerary' }"
              @tap="switchJigsawType('itinerary')"
            >
              行程
            </view>
          </view>
          
          <!-- 会话状态信息 -->
          <view v-if="sessionInfo && sessionInfo.collected_info && sessionInfo.collected_info.length > 0" class="session-status">
            <view class="status-title" @tap="toggleCollectedInfo">
              <text>已收集信息</text>
              <text class="collapse-icon" :class="{ expanded: showCollectedInfo }">▼</text>
            </view>
            <view v-if="showCollectedInfo" class="status-items">
              <view v-for="info in sessionInfo.collected_info" :key="info" class="status-item">
                {{ info }}
              </view>
            </view>
            <view v-else class="status-summary">
              <text>{{ sessionInfo.collected_info.length }}条信息</text>
              <text class="tap-to-expand"></text>
            </view>
          </view>
        </view>
        <scroll-view
          class="timeline-container"
          scroll-y
          :style="{ height: '100%' }"
        >
          <template v-if="jigsawType === 'location'">
            <!-- Loading状态 -->
            <template v-if="locationJigsawLoading">
              <view
                style="
                  text-align: center;
                  padding: 60px 20px;
                  background: #f8f9fa;
                  border-radius: 16px;
                  margin: 20px 0;
                "
              >
                <view style="font-size: 48px; margin-bottom: 16px">
                  <image
                    src="/static/icons/loading.svg"
                    style="width: 48px; height: 48px; animation: spin 1s linear infinite;"
                  />
                </view>
                <view
                  style="
                    font-size: 16px;
                    color: #2c4a52;
                    font-weight: bold;
                    margin-bottom: 8px;
                  "
                  >正在获取推荐数据...</view
                >
                <view style="font-size: 14px; color: #888; line-height: 1.4">
                  请稍候，我正在为您搜索合适的目的地
                </view>
              </view>
            </template>
            
            <!-- 有推荐数据时显示 -->
            <template v-else-if="locationJigsawData.length > 0">
              <!-- POI推荐卡片 -->
              <view
                v-for="(item, idx) in getCurrentPageData()"
                :key="idx"
                style="margin-bottom: 18px"
              >
                <view
                  @click="selectPoi(item)"
                  :style="{
                    display: 'flex',
                    background: '#fff',
                    borderRadius: '16px',
                    boxShadow: '0 2px 8px rgba(60, 89, 107, 0.08)',
                    padding: '10px 14px',
                    alignItems: 'center',
                    border: selectedPoi && selectedPoi.poi_id === item.poi_id ? '2px solid #4f7063' : '2px solid transparent',
                    cursor: 'pointer'
                  }"
                >
                  <image
                    :src="item.image"
                    @error="handleImageError"
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
                    <view v-if="item.type && item.type.trim()" style="font-size: 12px; color: #666; margin-bottom: 2px"
                      >类型：{{ item.type }}</view
                    >
                    <view v-if="item.address && item.address.trim()" style="font-size: 12px; color: #666; margin-bottom: 2px"
                      >地址：{{ item.address }}</view
                    >
                  </view>
                  
                  <!-- 加入按钮 -->
                  <view 
                    v-if="selectedPoi && selectedPoi.poi_id === item.poi_id"
                    @click.stop="addPOIToSession(item)"
                    style="
                      background: #4f7063;
                      color: white;
                      padding: 8px 16px;
                      border-radius: 8px;
                      font-size: 14px;
                      font-weight: 500;
                      margin-left: 8px;
                      display: flex;
                      align-items: center;
                      box-shadow: 0 2px 4px rgba(79, 112, 99, 0.3);
                    "
                  >
                    加入
                  </view>
                </view>
              </view>
              
              <!-- 分页控件 -->
              <view v-if="getTotalPages() > 1" style="
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 12px;
                padding: 16px 0;
                margin-top: 8px;
              ">
                <!-- 上一页按钮 -->
                <view 
                  @tap="prevPage"
                  :class="['pagination-btn', { disabled: currentPage === 1 }]"
                  style="
                    width: 32px;
                    height: 32px;
                    border-radius: 8px;
                    background: #f0f0f0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    color: #666;
                  "
                >
                  ‹
                </view>
                
                <!-- 页码指示器 -->
                <view style="
                  display: flex;
                  align-items: center;
                  font-size: 14px;
                  color: #666;
                ">
                  {{ currentPage }} / {{ getTotalPages() }}
                </view>
                
                <!-- 下一页按钮 -->
                <view 
                  @tap="nextPage"
                  :class="['pagination-btn', { disabled: currentPage === getTotalPages() }]"
                  style="
                    width: 32px;
                    height: 32px;
                    border-radius: 8px;
                    background: #f0f0f0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    color: #666;
                  "
                >
                  ›
                </view>
              </view>
            </template>
            
            <!-- 没有推荐数据时显示空状态 -->
            <template v-else>
              <view
                style="
                  text-align: center;
                  padding: 60px 20px;
                  background: #f8f9fa;
                  border-radius: 16px;
                  margin: 20px 0;
                "
              >
                <view style="font-size: 48px; margin-bottom: 16px">🗺️</view>
                <view
                  style="
                    font-size: 16px;
                    color: #2c4a52;
                    font-weight: bold;
                    margin-bottom: 8px;
                  "
                  >暂无目的地推荐</view
                >
                <view style="font-size: 14px; color: #888; line-height: 1.4">
                  <template v-if="!sessionId">开始对话后将为您推荐合适的目的地</template>
                  <template v-else>请告诉我您的旅行偏好，我来为您推荐目的地</template>
                </view>
              </view>
            </template>
          </template>
          <template v-else-if="jigsawType === 'my_pois'">
            <!-- 我的POI列表 -->
            <template v-if="myPoisData.length > 0">
              <view
                v-for="(poi, idx) in myPoisData"
                :key="poi.id"
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
                    :src="poi.image"
                    @error="handleImageError"
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
                    >{{ poi.name }}</view>
                    <view style="font-size: 13px; color: #888; margin-bottom: 2px"
                      >评分：{{ poi.score != null && poi.score !== undefined ? poi.score : 4.5 }}分</view>
                    <view v-if="poi.type && poi.type.trim()" style="font-size: 12px; color: #666; margin-bottom: 2px"
                      >类型：{{ poi.type }}</view>
                    <view v-if="poi.address && poi.address.trim()" style="font-size: 12px; color: #666; margin-bottom: 2px"
                      >地址：{{ poi.address }}</view>
                  </view>
                  
                  <!-- 删除按钮 -->
                  <view 
                    @click="removePOIFromSession(poi)"
                    style="
                      background: #dc3545;
                      color: white;
                      padding: 8px 16px;
                      border-radius: 8px;
                      font-size: 14px;
                      font-weight: 500;
                      margin-left: 8px;
                      display: flex;
                      align-items: center;
                      box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
                    "
                  >
                    删除
                  </view>
                </view>
              </view>
              
              <!-- POI统计信息 -->
              <view
                style="
                  background: #f8f9fa;
                  border-radius: 16px;
                  padding: 16px;
                  margin-top: 20px;
                  border: 1px solid #e9ecef;
                "
              >
                <view
                  style="
                    font-weight: bold;
                    font-size: 15px;
                    color: #2c4a52;
                    margin-bottom: 8px;
                  "
                >POI统计</view>
                <view style="font-size: 13px; color: #666; line-height: 1.5">
                  总计：{{ myPoisData.length }}个POI
                </view>
              </view>
            </template>
            
            <!-- 没有POI时显示空状态 -->
            <template v-else>
              <view
                style="
                  text-align: center;
                  padding: 60px 20px;
                  background: #f8f9fa;
                  border-radius: 16px;
                  margin: 20px 0;
                "
              >
                <view style="font-size: 48px; margin-bottom: 16px">📍</view>
                <view
                  style="
                    font-size: 16px;
                    color: #2c4a52;
                    font-weight: bold;
                    margin-bottom: 8px;
                  "
                >暂无已加入的POI</view>
                <view style="font-size: 14px; color: #888; line-height: 1.4">
                  在推荐页面点击"加入"按钮添加POI
                </view>
              </view>
            </template>
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
              <!-- 预算状态标题 -->
              <view
                style="
                  font-weight: bold;
                  font-size: 15px;
                  color: #2c4a52;
                  margin-bottom: 10px;
                "
              >
                <template v-if="budgetJigsawData.budget_type === 'empty'">
                  预算待设置
                </template>
                <template v-else-if="budgetJigsawData.budget_type === 'specific'">
                  预算分配 (总预算: {{ budgetJigsawData.budget_value }}元)
                  <text v-if="budgetJigsawData.total_considered > budgetJigsawData.budget_max" style="color: #ff6b6b; font-size: 12px; margin-left: 8px;">⚠️ 超出预算</text>
                </template>
                <template v-else-if="budgetJigsawData.budget_type === 'range'">
                  预算分配 (范围: {{ budgetJigsawData.budget_min }}-{{ budgetJigsawData.budget_max }}元)
                  <text v-if="budgetJigsawData.total_considered > budgetJigsawData.budget_max" style="color: #ff6b6b; font-size: 12px; margin-left: 8px;">⚠️ 超出预算</text>
                </template>
                <template v-else-if="budgetJigsawData.budget_type === 'unlimited'">
                  预算分配 (不限预算)
                </template>
                <template v-else-if="budgetJigsawData.budget_type === 'limited'">
                  预算分配 (预算有限)
                </template>
                <template v-else>
                  预算分配
                </template>
              </view>
              
              <!-- 预算概览 -->
              <view v-if="budgetJigsawData.total_considered > 0" style="margin-bottom: 15px; padding: 12px; background: #fff; border-radius: 8px;">
                <view style="font-size: 14px; color: #2c4a52; margin-bottom: 8px;">
                  <text style="font-weight: bold;">已考虑预算：</text>
                  <text style="color: #f7a35c;">{{ budgetJigsawData.total_considered }}元</text>
                </view>
                <view v-if="budgetJigsawData.budget_type === 'specific' && budgetJigsawData.remaining_budget > 0" style="font-size: 14px; color: #2c4a52;">
                  <text style="font-weight: bold;">剩余预算：</text>
                  <text style="color: #8fd3c7;">{{ budgetJigsawData.remaining_budget }}元</text>
                </view>
                <view v-if="budgetJigsawData.budget_type === 'range'" style="font-size: 14px; color: #2c4a52;">
                  <text style="font-weight: bold;">预算状态：</text>
                  <text v-if="budgetJigsawData.total_considered <= budgetJigsawData.budget_min" style="color: #8fd3c7;">
                    在预期范围内
                  </text>
                  <text v-else-if="budgetJigsawData.total_considered <= budgetJigsawData.budget_max" style="color: #f7a35c;">
                    超出最低预算，但在可接受范围内
                  </text>
                  <text v-else style="color: #ff6b6b;">
                    超出最高预算
                  </text>
                </view>
              </view>
              
              <!-- 预算分布图 -->
              <view style="margin-bottom: 18px;">
                <view
                  style="
                    font-weight: bold;
                    font-size: 15px;
                    color: #2c4a52;
                    margin-bottom: 10px;
                  "
                >预算分布图</view>
                
                <view style="display: flex; align-items: center;">
                  <!-- 饼图 -->
                  <svg width="120" height="120" viewBox="0 0 120 120" style="margin-right: 20px;">
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
                    <!-- 中心文字 -->
                    <text x="60" y="55" text-anchor="middle" style="font-size: 12px; fill: #2c4a52; font-weight: bold;">
                      {{ budgetJigsawData.budget_type === 'empty' ? '预算' : (budgetJigsawData.budget_type === 'specific' ? '总预算' : '已考虑') }}
                    </text>
                    <text x="60" y="70" text-anchor="middle" style="font-size: 14px; fill: #f7a35c; font-weight: bold;">
                      {{ budgetJigsawData.budget_type === 'empty' ? '未设置' : (budgetJigsawData.budget_type === 'specific' ? budgetJigsawData.budget_value + '元' : budgetJigsawData.total_considered + '元') }}
                    </text>
                  </svg>
                  
                  <!-- 图例 -->
                  <view style="flex: 1;">
                    <view
                      v-for="(item, idx) in budgetJigsawData.chart"
                      :key="idx"
                      style="
                        font-size: 13px;
                        color: #2c4a52;
                        margin-bottom: 6px;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                      "
                    >
                      <view style="display: flex; align-items: center;">
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
                        <text>{{ item.name }}</text>
                      </view>
                      <text style="font-weight: bold;">{{ budgetJigsawData.budget_type === 'empty' ? '' : item.value + '元' }}</text>
                    </view>
                  </view>
                </view>
              </view>
              
              <!-- POI费用详情 -->
              <view v-if="budgetJigsawData.poi_costs && budgetJigsawData.poi_costs.length > 0" style="margin-top: 15px;">
                <view
                  style="
                    font-weight: bold;
                    font-size: 15px;
                    color: #2c4a52;
                    margin-bottom: 10px;
                  "
                >POI费用详情</view>
                <view
                  v-for="poi in budgetJigsawData.poi_costs"
                  :key="poi.name"
                  style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    background: #fff;
                    border-radius: 6px;
                    margin-bottom: 6px;
                  "
                >
                  <view>
                    <view style="font-size: 14px; color: #2c4a52; font-weight: bold;">{{ poi.name }}</view>
                    <view style="font-size: 12px; color: #888;">{{ poi.category }} · {{ poi.type }}</view>
                  </view>
                  <view style="text-align: right;">
                    <view style="font-size: 14px; color: #f7a35c; font-weight: bold;">{{ poi.cost }}元</view>
                    <view style="font-size: 11px; color: #888;">{{ poi.cost_str }}</view>
                  </view>
                </view>
              </view>
              

              
              <!-- 交通预算预留提示 -->
              <view v-if="budgetJigsawData.budget_breakdown && budgetJigsawData.budget_breakdown.交通 === 0" 
                    style="margin-top: 15px; padding: 12px; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <view style="font-size: 14px; color: #0c5460; font-weight: bold; margin-bottom: 4px;">交通费用</view>
                <view style="font-size: 13px; color: #0c5460;">
                  交通费用将在生成行程后根据实际路线计算。
                </view>
              </view>
            </view>
          </template>
          <template v-else-if="jigsawType === 'itinerary'">
            <!-- 行程标签页 -->
            <template v-if="itinerary && itinerary.length > 0">
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
                <view class="jigsaw-btn" @tap="regenerateItinerary">
                  <image
                    src="/static/icons/loading.svg"
                    mode="aspectFit"
                    class="jigsaw-btn-icon"
                  />
                  <text>重新生成</text>
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
            
            <!-- 没有行程数据时显示空状态和生成按钮 -->
            <template v-else>
              <view
                style="
                  text-align: center;
                  padding: 60px 20px;
                  background: #f8f9fa;
                  border-radius: 16px;
                  margin: 20px 0;
                "
              >
                <view style="font-size: 48px; margin-bottom: 16px">📅</view>
                <view
                  style="
                    font-size: 16px;
                    color: #2c4a52;
                    font-weight: bold;
                    margin-bottom: 8px;
                  "
                >暂无行程数据</view>
                <view style="font-size: 14px; color: #888; line-height: 1.4; margin-bottom: 24px;">
                  完成信息收集后，点击下方按钮生成个性化行程
                </view>
                
                <!-- 生成行程按钮 -->
                <view 
                  @tap="generateItinerary"
                  :class="['generate-btn', { 'generate-btn-loading': isGenerating }]"
                  :style="{
                    background: isGenerating ? '#ccc' : '#4f7063',
                    color: 'white',
                    padding: '12px 24px',
                    borderRadius: '12px',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    cursor: isGenerating ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s ease',
                    boxShadow: isGenerating ? 'none' : '0 4px 8px rgba(79, 112, 99, 0.3)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px'
                  }"
                >
                  <image
                    v-if="isGenerating"
                    src="/static/icons/loading.svg"
                    style="width: 18px; height: 18px; animation: spin 1s linear infinite;"
                  />
                  <text>{{ isGenerating ? '正在生成...' : '生成行程' }}</text>
                </view>
                
                <!-- 生成条件提示 -->
                <view 
                  v-if="currentState !== 'COMPLETED' && currentState !== 'CONFIRMATION'"
                  style="
                    font-size: 12px;
                    color: #ff6b6b;
                    margin-top: 12px;
                    padding: 8px 12px;
                    background: rgba(255, 107, 107, 0.1);
                    border-radius: 8px;
                    display: inline-block;
                  "
                >
                  ⚠️ 请先完成与AI的对话，收集完整的旅行信息
                </view>
              </view>
            </template>
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
import MarkdownRenderer from "@/components/MarkdownRenderer.vue";

export default {
  components: {
    MarkdownRenderer
  },
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
      jigsawType: "location", // 'location' | 'budget' | 'itinerary' | 'my_pois'
      locationJigsawData: [], // 目的地推荐数据，通过API获取
      myPoisData: [], // 我的POI数据，通过API获取
      // 分页相关
      currentPage: 1, // 当前页码
      pageSize: 4, // 每页显示数量
      budgetJigsawData: {
        budget_type: "empty",
        budget_value: null,
        budget_min: 0,
        budget_max: 0,
        total_considered: 0,
        remaining_budget: 0,
        budget_breakdown: {
          住宿: 0,
          餐饮: 0,
          景点: 0,
          娱乐: 0,
          购物: 0,
          交通: 0,
        },
        chart: [
          { name: "预算待分配", value: 1000, color: "#e0e0e0" },
        ],
        poi_costs: [],
        poi_count: 0,
        // 兼容原有结构
        住宿: 0,
        餐饮: 0,
        娱乐: 0,
        景点: 0,
        购物: 0,
        交通: 0,
        total: 0,
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
      isUserScrolling: false, // 用户是否在手动滚动
      shouldAutoScroll: true, // 是否应该自动滚动到底部
      lastScrollTime: 0, // 上次滚动时间，用于控制滚动频率
      lastScrollTop: undefined, // 上次滚动位置，用于判断滚动方向
      _creatingSession: null,
      initializing: false,
      queuedMessage: "",
      awaitingReply: false,
      // 流式处理相关
      isStreamMode: true, // 是否启用流式模式
      streamingMessageIndex: -1, // 正在流式输出的消息索引
      streamingContent: "", // 流式输出的累积内容
      streamController: null, // 流式请求控制器
      // 会话状态管理
      sessionInfo: null, // 后端会话信息
      slotsInfo: null, // 槽位信息
      currentState: 'INIT', // 当前状态机状态
      selectedPoi: null, // 当前选中的POI
      shouldUpdatePOIAfterReply: false, // 控制是否在大模型回复后更新POI
      locationJigsawLoading: false, // 目的地推荐数据加载状态
      timelineAbortController: null, // Timeline生成请求的取消控制器
      showCollectedInfo: false, // 控制是否显示已收集信息
    };
  },
  onLoad() {
    const systemInfo = uni.getSystemInfoSync();
    this.statusBarHeight = systemInfo.statusBarHeight;
    this.contentPaddingTop = this.statusBarHeight + this.navContentHeight;
    
    // ===== 读取本地持久化数据 =====
    try {
      const storedChatList = uni.getStorageSync('chatList');
      if (storedChatList && Array.isArray(storedChatList)) {
        this.chatList = storedChatList;
        // 自动选中最后一条会话（如有）
        if (this.chatList.length > 0) {
          const lastChat = this.chatList[0];
          this.switchToChat(lastChat);
        }
      }
      const storedSessionId = uni.getStorageSync('sessionId');
      if (storedSessionId) {
        this.sessionId = storedSessionId;
      }
    } catch (e) {
      console.warn('读取本地聊天历史失败:', e);
    }
    // 如果已有会话ID，获取会话状态
    if (this.sessionId) {
      this.fetchSessionState();
    }
  },
  onPageScroll(e) {
    const scrollTop = e.scrollTop;
    
    // 记录当前滚动位置，用于判断滚动方向
    if (this.lastScrollTop === undefined) {
      this.lastScrollTop = scrollTop;
      return;
    }
    
    const scrollDirection = scrollTop > this.lastScrollTop ? 'down' : 'up';
    const scrollDiff = Math.abs(scrollTop - this.lastScrollTop);
    this.lastScrollTop = scrollTop;
    
    // 只有在用户明显滚动时才处理（避免微小滚动触发）
    if (scrollDiff < 5) return;
    
    // 获取页面高度信息
    const systemInfo = uni.getSystemInfoSync();
    const windowHeight = systemInfo.windowHeight;
    
    // 简化判断：只检查是否接近底部
    uni.createSelectorQuery().selectViewport().scrollOffset((res) => {
      const maxScrollTop = res.scrollHeight - windowHeight;
      const isNearBottom = scrollTop >= maxScrollTop - 100;
      
      if (scrollDirection === 'up' && scrollTop > 100) {
        // 用户向上滚动且不在最顶部，停止自动滚动
        this.isUserScrolling = true;
        this.shouldAutoScroll = false;
      } else if (isNearBottom) {
        // 用户滚动到底部附近，恢复自动滚动
        this.isUserScrolling = false;
        this.shouldAutoScroll = true;
      }
    }).exec();
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
    "budgetJigsawData.景点"(newVal) {
      this.syncChartAndTotal("景点", newVal);
    },
    "budgetJigsawData.购物"(newVal) {
      this.syncChartAndTotal("购物", newVal);
    },
    "budgetJigsawData.交通"(newVal) {
      this.syncChartAndTotal("交通", newVal);
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
        // 用户点击建议时，强制滚动到底部
        this.forceScrollToBottom();
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

        // 持久化到本地
        try {
          uni.setStorageSync('chatList', this.chatList);
        } catch (e) {
          console.warn('保存聊天历史失败:', e);
        }
      }
    },
    switchToChat(chat) {
      this.currentChatId = chat.id;
      this.currentChatTitle = chat.title;
      this.messages = [...chat.messages];
      this.showWelcome = false;
      this.toggleSidebar();
      this.itinerary = JSON.parse(JSON.stringify(chat.itinerary));
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
      this._creatingSession = request("/api/talker/session/", { username: "demo" }, "POST")
        .then((res) => {
          this.sessionId = res.session_id;
          console.log('会话创建成功，sessionId:', this.sessionId);
          // 持久化 sessionId
          try {
            uni.setStorageSync('sessionId', this.sessionId);
          } catch (e) {
            console.warn('保存sessionId失败:', e);
          }
          // 创建会话后立即获取会话状态
          return this.fetchSessionState().then(() => this.sessionId);
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

    /** 获取会话状态 */
    async fetchSessionState() {
      if (!this.sessionId) {
        console.log('fetchSessionState: sessionId为空，跳过获取');
        return;
      }
      
      try {
        console.log('开始获取会话状态，sessionId:', this.sessionId);
        const response = await request(`/api/talker/session/${this.sessionId}/`, {}, "GET");
        
        console.log('获取会话状态成功:', response);
        
        this.sessionInfo = response.session_info;
        this.slotsInfo = response.slots_info;
        this.currentState = response.current_state;
        
        // 根据会话状态更新拼图类型和数据
        // shouldUpdatePOI 参数控制是否在此次更新中刷新POI数据
        await this.updateJigsawFromSessionState(this.shouldUpdatePOIAfterReply);
        
        // 如果当前在我的POI页面，也要加载数据
        if (this.jigsawType === 'my_pois') {
          this.loadMyPoisData();
        }
        
        // 重置POI更新标志
        this.shouldUpdatePOIAfterReply = false;
        
        console.log('会话状态已更新:', {
          sessionInfo: this.sessionInfo,
          slotsInfo: this.slotsInfo,
          currentState: this.currentState
        });
        
      } catch (err) {
        console.error("获取会话状态失败", err);
      }
    },

    /** 根据会话状态更新拼图显示 */
    async updateJigsawFromSessionState(shouldUpdatePOI = false) {
      console.log('更新拼图显示:', {
        currentState: this.currentState,
        slotsInfo: this.slotsInfo,
        sessionInfo: this.sessionInfo,
        shouldUpdatePOI: shouldUpdatePOI
      });
      
      // 根据当前状态决定拼图类型
      if (this.currentState === 'SLOT_FILLING_DESTINATION' || 
          this.currentState === 'SLOT_FILLING_DESTINATION_DEEP') {
        // 目的地询问阶段，显示目的地推荐拼图
        this.jigsawType = 'location';
        // 只有在DESTINATION_DEEP状态且大模型回复完成后才更新POI
        console.log('检查POI更新条件:', {
          shouldUpdatePOI: shouldUpdatePOI,
          currentState: this.currentState,
          isDESTINATION_DEEP: this.currentState === 'SLOT_FILLING_DESTINATION_DEEP',
          bothConditions: shouldUpdatePOI && this.currentState === 'SLOT_FILLING_DESTINATION_DEEP'
        });
        
        if (shouldUpdatePOI && this.currentState === 'SLOT_FILLING_DESTINATION_DEEP') {
          console.log('✅ DESTINATION_DEEP状态 + 大模型回复完成 → 更新POI推荐');
        this.updateLocationJigsawData();
        } else {
          console.log('❌ 不符合POI更新条件，跳过搜索');
        }
      } else if (this.currentState === 'SLOT_FILLING_DESTINATION_CONFIRM') {
        // 目的地确认阶段，显示当前对话的POI
        this.jigsawType = 'location';
        console.log('设置拼图类型为：location (目的地确认阶段) - 不更新POI数据');
      } else if (this.currentState === 'SLOT_FILLING_BUDGET') {
        // 预算询问阶段，显示预算拼图
        this.jigsawType = 'budget';
        await this.updateBudgetJigsawData();
        console.log('设置拼图类型为：budget');
      } else if (this.currentState === 'SLOT_FILLING_DATES') {
        // 日期询问阶段，可以显示预算或行程拼图
        this.jigsawType = 'budget';
        await this.updateBudgetJigsawData();
        console.log('设置拼图类型为：budget (日期询问阶段)');
      } else if (this.currentState === 'CONFIRMATION' || this.currentState === 'COMPLETED') {
        // 确认或完成阶段，显示行程拼图
        this.jigsawType = 'itinerary';
        this.updateItineraryData();
        console.log('设置拼图类型为：itinerary');
      } else {
        // 默认或初始状态，显示目的地拼图
        this.jigsawType = 'location';
        console.log('设置拼图类型为：location (默认) - 不更新POI数据');
      }
    },

    /** 处理图片加载错误 */
    handleImageError(event) {
      console.warn('图片加载失败:', event);
      // 可以在这里设置默认图片
      // event.target.src = '/static/images/flower.jpg';
    },

    /** 更新目的地拼图数据 */
    async updateLocationJigsawData() {
      try {
        console.log('开始获取目的地推荐数据...');
        
        // 设置loading状态
        this.locationJigsawLoading = true;
        
        // 构建请求URL
        let url = '/api/talker/recommendations/destinations/';
        if (this.sessionId) {
          url = `/api/talker/recommendations/destinations/${this.sessionId}/`;
        }
        
        // 构建查询参数
        const params = new URLSearchParams({
          count: '20',  // 获取足够多的POI用于分页
          budget_range: 'medium'
        });
        
        // 如果有用户画像，添加到参数中
        if (this.slotsInfo && this.slotsInfo.profile && this.slotsInfo.profile.value) {
          params.append('user_profile', this.slotsInfo.profile.value);
        }
        
        const response = await request(`${url}?${params.toString()}`, {}, "GET");
        
        if (response.recommendations && response.recommendations.length > 0) {
          // 更新拼图数据
          this.locationJigsawData = response.recommendations;
          // 重置分页到第一页
          this.currentPage = 1;
          console.log('目的地推荐数据更新成功:', response.recommendations);
        } else {
          // 没有推荐数据时清空数组
          this.locationJigsawData = [];
          this.currentPage = 1;
          console.log('未获取到推荐数据，显示空状态');
        }
        
      } catch (error) {
        console.error('获取目的地推荐失败:', error);
        // 清空推荐数据
        this.locationJigsawData = [];
        this.currentPage = 1;
        console.log('推荐接口失败，显示空状态');
      } finally {
        // 无论成功还是失败，都要关闭loading状态
        this.locationJigsawLoading = false;
      }
    },



    /** 分页相关方法 */
    // 获取当前页显示的POI数据
    getCurrentPageData() {
      const startIndex = (this.currentPage - 1) * this.pageSize;
      const endIndex = startIndex + this.pageSize;
      return this.locationJigsawData.slice(startIndex, endIndex);
    },
    
    // 计算总页数
    getTotalPages() {
      return Math.ceil(this.locationJigsawData.length / this.pageSize);
    },
    
    // 上一页
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        // 换页时重置选中状态
        this.selectedPoi = null;
      }
    },
    
    // 下一页
    nextPage() {
      if (this.currentPage < this.getTotalPages()) {
        this.currentPage++;
        // 换页时重置选中状态
        this.selectedPoi = null;
      }
    },
    
    // 跳转到指定页
    goToPage(page) {
      if (page >= 1 && page <= this.getTotalPages()) {
        this.currentPage = page;
      }
    },

    /** POI选择和加入相关方法 */
    // 选择POI
    selectPoi(poi) {
      this.selectedPoi = poi;
      console.log('选中POI:', poi);
    },
    
    // 添加POI到会话
    async addPOIToSession(poi) {
      if (!this.sessionId) {
        uni.showToast({ title: "请先创建会话", icon: "none" });
        return;
      }
      
      // 检查POI是否有索引
      if (poi.poi_index === undefined) {
        uni.showToast({ title: "POI索引无效，请重新获取推荐", icon: "error" });
        return;
      }
      
      try {
        uni.showToast({ title: "正在添加POI...", icon: "loading" });
        
        const response = await request("/api/talker/pois/add/", {
          session_id: this.sessionId,
          poi_index: poi.poi_index
        }, "POST");
        
        // 添加详细的调试信息
        console.log('=== POI添加响应调试信息 ===');
        console.log('完整响应:', JSON.stringify(response, null, 2));
        console.log('response.success:', response.success, typeof response.success);
        console.log('response.exists:', response.exists, typeof response.exists);
        console.log('response.message:', response.message);
        console.log('判断逻辑:');
        console.log('  第一个if (response.success):', !!response.success);
        console.log('  第二个else if (response.exists):', !!response.exists);
        
        if (response.success) {
          console.log('-> 执行成功分支');
          uni.showToast({ title: "POI添加成功", icon: "success" });
          console.log('POI添加成功:', response.message);
          
          // 添加成功后取消选中状态
          this.selectedPoi = null;
          
          // 如果当前在我的POI页面，刷新数据
          if (this.jigsawType === 'my_pois') {
            this.loadMyPoisData();
          }
        } else if (response.exists) {
          // POI已存在的情况
          console.log('-> 执行POI已存在分支');
          uni.showToast({ 
            title: "该POI已存在于会话中", 
            icon: "success",
            duration: 2000
          });
          console.log('POI已存在:', response.message);
          
          // 取消选中状态
          this.selectedPoi = null;
          
          // 如果当前在我的POI页面，刷新数据以显示最新状态
          if (this.jigsawType === 'my_pois') {
            this.loadMyPoisData();
          }
        } else {
          console.log('-> 执行失败分支');
          uni.showToast({ title: response.message || "POI添加失败", icon: "error" });
          console.error('POI添加失败:', response.message);
        }
        console.log('=== POI添加响应调试信息结束 ===');
      } catch (error) {
        console.error('添加POI错误:', error);
        uni.showToast({ title: "添加POI失败", icon: "error" });
      }
    },

    /** 拼图类型切换 */
    async switchJigsawType(type) {
      this.jigsawType = type;
      
      // 根据类型加载相应数据
      if (type === 'location') {
        // 不在标签页切换时触发POI搜索，只显示现有数据
        console.log('切换到推荐标签页 - 显示现有数据，不触发搜索');
      } else if (type === 'my_pois') {
        this.loadMyPoisData();
              } else if (type === 'budget') {
          await this.updateBudgetJigsawData();
        } else if (type === 'itinerary') {
        this.updateItineraryData();
      }
    },

    /** 加载我的POI数据 */
    async loadMyPoisData() {
      if (!this.sessionId) {
        console.log('loadMyPoisData: sessionId为空，跳过加载');
        this.myPoisData = [];
        return;
      }
      
      try {
        const response = await request(`/api/talker/pois/list/?session_id=${this.sessionId}`, {}, "GET");
        
        if (response.success && response.pois) {
          this.myPoisData = response.pois;
          console.log('我的POI数据加载成功:', response.pois);
        } else {
          this.myPoisData = [];
          console.log('未获取到我的POI数据');
        }
        
      } catch (error) {
        console.error('加载我的POI数据失败:', error);
        this.myPoisData = [];
      }
    },

    /** 从会话中删除POI */
    async removePOIFromSession(poi) {
      if (!this.sessionId) {
        uni.showToast({ title: "请先创建会话", icon: "none" });
        return;
      }
      
      try {
        uni.showToast({ title: "正在删除POI...", icon: "loading" });
        
        const response = await request("/api/talker/pois/remove/", {
          session_id: this.sessionId,
          poi_id: poi.id
        }, "POST");
        
        if (response.success) {
          uni.showToast({ title: "POI删除成功", icon: "success" });
          console.log('POI删除成功:', response.message);
          
          // 删除成功后重新加载数据
          this.loadMyPoisData();
        } else {
          uni.showToast({ title: "POI删除失败", icon: "error" });
          console.error('POI删除失败:', response.message);
        }
      } catch (error) {
        console.error('删除POI错误:', error);
        uni.showToast({ title: "删除POI失败", icon: "error" });
      }
    },

    /** 更新预算拼图数据 */
    async updateBudgetJigsawData() {
      // 根据目的地和其他信息更新预算建议
      if (!this.sessionId) {
        console.log('updateBudgetJigsawData: sessionId为空，跳过更新');
        return;
      }
      
      try {
        console.log('开始更新预算拼图数据，sessionId:', this.sessionId);
        
        const response = await request(`/api/talker/budget/analysis/?session_id=${this.sessionId}`, {}, "GET");
        
        if (response.error) {
          console.error('获取预算分析失败:', response.message);
          return;
        }
        
        console.log('预算分析结果:', response);
        
        // 更新预算数据结构
        this.budgetJigsawData = {
          budget_type: response.budget_type,
          budget_value: response.budget_value,
          budget_min: response.budget_min,
          budget_max: response.budget_max,
          total_considered: response.total_considered,
          remaining_budget: response.remaining_budget,
          budget_breakdown: response.budget_breakdown,
          chart: response.chart_data,
          poi_costs: response.poi_costs,
          poi_count: response.poi_count
        };
        
        // 为了兼容现有的输入框，同时设置各类别的值
        if (response.budget_breakdown) {
          this.budgetJigsawData.住宿 = response.budget_breakdown.住宿 || 0;
          this.budgetJigsawData.餐饮 = response.budget_breakdown.餐饮 || 0;
          this.budgetJigsawData.娱乐 = response.budget_breakdown.娱乐 || 0;
          this.budgetJigsawData.景点 = response.budget_breakdown.景点 || 0;
          this.budgetJigsawData.购物 = response.budget_breakdown.购物 || 0;
          this.budgetJigsawData.交通 = response.budget_breakdown.交通 || 0;
        }
        
        // 计算总预算
        this.budgetJigsawData.total = response.total_considered;
        
        console.log('预算拼图数据已更新:', this.budgetJigsawData);
        
      } catch (error) {
        console.error('更新预算拼图数据失败:', error);
      }
    },

    /** 更新行程拼图数据 */
    async updateItineraryData() {
      // 只检查和显示现有的行程数据，不主动生成
      console.log('切换到行程标签页 - 检查现有行程数据');
      
      // 如果已有行程数据，直接显示
      if (this.itinerary && this.itinerary.length > 0) {
        console.log('已有行程数据，直接显示');
        return;
      }
      
      // 若后端会话中已存 timeline_data，直接转换展示
      if (this.sessionInfo && this.sessionInfo.state && this.sessionInfo.state.timeline_data) {
        try {
          this.itinerary = this.convertTimelineToItinerary(this.sessionInfo.state.timeline_data);
          if (this.itinerary.length > 0) {
            console.log('已从会话状态加载行程数据');
            return;
          }
        } catch (e) {
          console.warn('解析timeline_data失败', e);
        }
      }
      
      // 如果没有行程数据，显示空状态和生成按钮
      console.log('暂无行程数据，等待用户手动生成');
    },

    /** 手动生成行程链 */
    async generateItinerary() {
      // 检查是否满足生成条件
      if (this.currentState !== 'COMPLETED' && this.currentState !== 'CONFIRMATION') {
        uni.showToast({
          title: "请先完成信息收集",
          icon: "none"
        });
        return;
      }
      
      if (!this.sessionId) {
        uni.showToast({
          title: "请先创建会话",
          icon: "none"
        });
        return;
      }
      
      console.log('手动生成行程链 - 开始生成Timeline行程链');
      
      try {
        // 显示生成状态
        this.isGenerating = true;
        
        // 添加状态消息
        this.messages.push({
          type: "status",
          content: "行程规划中，正在生成个性化行程链..."
        });
        this.scrollToBottom();
        
        // 设置取消标志
        this.timelineAbortController = { cancelled: false };
        
        // 调用Timeline服务API
        const response = await request(`/api/talker/timeline/${this.sessionId}/`, {}, "GET", {}, { timeout: 300000 });
        
        // 检查是否已被取消
        if (this.timelineAbortController && this.timelineAbortController.cancelled) {
          console.log('Timeline生成已被用户取消');
          return;
        }
        
        if (response.success && response.timeline_data) {
          // 先同步会话 POI 数据，确保图片匹配时可用
          await this.loadMyPoisData();
          // 转换 Timeline 数据格式为前端 itinerary 格式
          this.itinerary = this.convertTimelineToItinerary(response.timeline_data);
          
          // 移除生成状态消息
          this.messages = this.messages.filter(
            (msg) => !(msg.type === "status" && msg.content.includes("行程规划中"))
          );
          
          // 添加完成状态
          this.messages.push({
            type: "status",
            content: "行程链生成完成"
          });
          
          console.log('Timeline行程链生成成功:', this.itinerary);
          
          uni.showToast({
            title: "行程生成成功",
            icon: "success"
          });
        } else {
          throw new Error(response.error || '行程生成失败');
        }
      } catch (error) {
        console.error('Timeline行程生成失败:', error);
        
        // 移除生成状态消息
        this.messages = this.messages.filter(
          (msg) => !(msg.type === "status" && msg.content.includes("行程规划中"))
        );
        
        // 如果是用户取消的请求，不显示错误消息
        if (this.timelineAbortController && this.timelineAbortController.cancelled) {
          console.log('Timeline生成已被用户取消');
          return;
        }
        
        // 显示错误消息
        uni.showToast({
          title: "行程生成失败",
          icon: "error"
        });
        
        this.messages.push({
          type: "ai",
          content: `⚠️ 行程生成失败：${error.message || '未知错误'}`,
          time: new Date().toLocaleTimeString(),
        });
        
      } finally {
        this.isGenerating = false;
        this.timelineAbortController = null;
        this.scrollToBottom();
      }
    },

    /** 将Timeline数据转换为前端itinerary格式 */
    convertTimelineToItinerary(timelineData) {
      console.log('开始转换Timeline数据:', timelineData);
      
      try {
        const itineraryChain = timelineData.itinerary_chain || [];
        const convertedItinerary = [];
        
        itineraryChain.forEach((dayData, dayIndex) => {
          const dayInfo = {
            date: dayData.day || `第${dayIndex + 1}天`,
            weatherIcon: this.getRandomWeatherIcon(),
            temperature: this.getRandomTemperature(),
            events: []
          };
          
          const activities = dayData.activities || [];
          
          activities.forEach((activity, activityIndex) => {
            const event = {
              // 兼容后端返回的 time_period 字段，将其映射为大致时间点
              time: activity.time || this.mapTimePeriodToClock(activity.time_period, activityIndex) || `${8 + activityIndex * 2}:00`,
              image: this.getActivityImage(activity),
              // 兼容后端返回的 place 字段
              location: activity.place || activity.location || activity.activity || '未知地点',
              subtext: activity.description || activity.desc || activity.type || '',
              type: this.getActivityType(activity),
              duration: this.getActivityDuration(activity)
            };
            
            // 添加交通信息（除了最后一个活动）
            if (activityIndex < activities.length - 1) {
              event.travel = {
                duration: this.calculateTravelTime(activity, activities[activityIndex + 1]),
                method: this.getTravelMethod(activity, activities[activityIndex + 1])
              };
            }
            
            dayInfo.events.push(event);
          });
          
          convertedItinerary.push(dayInfo);
        });
        
        console.log('Timeline数据转换完成:', convertedItinerary);
        return convertedItinerary; // 不再返回示例数据
        
      } catch (error) {
        console.error('Timeline数据转换失败:', error);
        return []; // 失败时返回空数组，前端UI会提示用户
      }
    },

    /** 将 time_period 映射为大致时间点 */
    mapTimePeriodToClock(timePeriod, index) {
      const mapping = {
        '清晨': '06:00',
        '上午': '09:00',
        '中午': '12:00',
        '下午': '15:00',
        '傍晚': '18:00',
        '夜晚': '21:00'
      };
      return mapping[timePeriod] || null;
    },

    /** 获取活动图片 */
    getActivityImage(activity) {
      // 1) 优先使用 activity 本身携带的 image 字段
      if (activity && activity.image && typeof activity.image === 'string' && activity.image.trim()) {
        return activity.image;
      }
      // 2) 尝试在已加载的会话 POI 列表中，根据名称匹配获取图片
      const actName = (activity.place || activity.location || activity.activity || '').toLowerCase();
      if (actName && Array.isArray(this.myPoisData) && this.myPoisData.length > 0) {
        const matchedPoi = this.myPoisData.find(poi => {
          const poiName = (poi.name || '').toLowerCase();
          return poiName && (actName.includes(poiName) || poiName.includes(actName));
        });
        if (matchedPoi && matchedPoi.image) {
          return matchedPoi.image;
        }
      }
      // 3) 回退到启发式默认图片
      if (actName.includes('机场') || actName.includes('airport')) {
        return '/static/images/airport1.jpg';
      } else if (actName.includes('饭店') || actName.includes('餐厅') ||
                 actName.includes('美食') || actName.includes('用餐')) {
        return '/static/images/food.jpg';
      } else if (actName.includes('花') || actName.includes('公园') ||
                 actName.includes('景点') || actName.includes('游览')) {
        return '/static/images/flower.jpg';
      }
      return '/static/images/banner.jpg';
    },

    /** 获取活动类型 */
    getActivityType(activity) {
      const activityName = (activity.place || activity.activity || activity.location || '').toLowerCase();
      
      if (activityName.includes('机场') || activityName.includes('交通')) {
        return '交通';
      } else if (activityName.includes('饭店') || activityName.includes('餐厅') || 
                 activityName.includes('用餐') || activityName.includes('美食')) {
        return '吃饭';
      } else if (activityName.includes('酒店') || activityName.includes('住宿')) {
        return '住宿';
      } else {
        return '游玩';
      }
    },

    /** 获取活动时长 */
    getActivityDuration(activity) {
      const type = this.getActivityType(activity);
      
      switch (type) {
        case '交通': return 60;
        case '吃饭': return 90;
        case '住宿': return 480;
        case '游玩': return 120;
        default: return 90;
      }
    },

    /** 计算交通时间 */
    calculateTravelTime(fromActivity, toActivity) {
      // 简单的时间估算逻辑
      const fromType = this.getActivityType(fromActivity);
      const toType = this.getActivityType(toActivity);
      
      if (fromType === '住宿' || toType === '住宿') {
        return '15min';
      } else if (fromType === '交通' || toType === '交通') {
        return '45min';
      } else {
        return '20min';
      }
    },

    /** 获取交通方式 */
    getTravelMethod(fromActivity, toActivity) {
      const fromName = (fromActivity.location || fromActivity.activity || '').toLowerCase();
      const toName = (toActivity.location || toActivity.activity || '').toLowerCase();
      
      if (fromName.includes('机场') || toName.includes('机场')) {
        return '乘大巴前往';
      } else if (fromName.includes('地铁') || toName.includes('地铁')) {
        return '乘地铁前往';
      } else {
        return Math.random() > 0.5 ? '步行' : '打车前往';
      }
    },

    /** 获取随机天气图标 */
    getRandomWeatherIcon() {
      const icons = ['☀️', '⛅', '🌤️', '⛈️'];
      return icons[Math.floor(Math.random() * icons.length)];
    },

    /** 获取随机温度 */
    getRandomTemperature() {
      const low = Math.floor(Math.random() * 10) + 20;
      const high = low + Math.floor(Math.random() * 10) + 5;
      return `${low}/${high}℃`;
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
      request("/api/talker/state-machine/", { session_id: this.sessionId, message: text }, "POST")
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
          
          // 消息完成后延时同步会话状态，并标记需要更新POI
          this.shouldUpdatePOIAfterReply = true;
          setTimeout(() => {
          this.fetchSessionState();
          }, 500);
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
      // 开始流式输出时滚动到底部
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
      if (chunk.type === 'content' && chunk.chunk) {
        this.streamingContent += chunk.chunk;
        
        // 更新正在流式输出的消息内容
        if (this.streamingMessageIndex >= 0 && this.streamingMessageIndex < this.messages.length) {
          // 添加短暂延迟以便观察打字机效果
          setTimeout(() => {
            this.$set(this.messages, this.streamingMessageIndex, {
              ...this.messages[this.streamingMessageIndex],
              content: this.streamingContent
            });
            
            // 降低滚动频率：每10个字符或每500ms滚动一次
            if (this.shouldAutoScroll && !this.isUserScrolling) {
              if (!this.lastScrollTime || Date.now() - this.lastScrollTime > 500) {
                this.lastScrollTime = Date.now();
              this.$nextTick(() => {
                this.scrollToBottom();
              });
              }
            }
          }, 10); // 10ms延迟
        }
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
      
      // 消息完成后延时同步会话状态，确保状态机处理完成，并标记需要更新POI
      this.shouldUpdatePOIAfterReply = true;
      setTimeout(() => {
      this.fetchSessionState();
      }, 500);
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
      // 阻止在loading状态下发送消息
      if (this.awaitingReply || this.initializing) {
        console.log('正在等待回复或初始化中，忽略发送请求');
        return;
      }
      
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
      // 用户发送消息后强制滚动到底部
      this.forceScrollToBottom();
    },
    

    
    /** 智能滚动到底部 */
    scrollToBottom() {
      // 只有在应该自动滚动的情况下才滚动
      if (!this.shouldAutoScroll) {
        return;
      }
      
      // 如果用户正在手动滚动或查看历史消息，不要自动滚动
      if (this.isUserScrolling) {
        return;
      }
      
      this.$nextTick(() => {
        // 使用uni.pageScrollTo滚动整个页面到底部
        uni.pageScrollTo({
          scrollTop: 99999, // 使用足够大的值确保滚动到底部
          duration: 300,
          success: () => {
            // console.log('页面滚动成功');
          }
        });
      });
    },
    
    /** 强制滚动到底部（无论用户是否在查看历史消息） */
    forceScrollToBottom() {
      this.shouldAutoScroll = true;
      this.isUserScrolling = false;
      this.scrollToBottom();
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
      // 移除包含"生成中"或"行程规划中"的状态消息
      this.messages = this.messages.filter(
        (msg) => !(msg.type === "status" && (
          msg.content.includes("生成中") || 
          msg.content.includes("行程规划中")
        ))
      );
      this.isGenerating = false;

      // 添加"已取消生成"状态消息
      this.messages.push({
        type: "status",
        content: "已取消生成",
      });
      this.scrollToBottom();

      // 如果有Timeline生成请求，标记为已取消
      if (this.timelineAbortController) {
        this.timelineAbortController.cancelled = true;
      }

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
      
      if (!this.budgetJigsawData.chart || this.budgetJigsawData.chart.length === 0) {
        return `${C} ${C}`;
      }
      
      const total = this.budgetJigsawData.chart.reduce(
        (sum, item) => sum + (item.value || 0),
        0
      );
      
      if (total === 0) {
        return `${C} ${C}`;
      }
      
      const value = this.budgetJigsawData.chart[idx].value || 0;
      const length = (value / total) * C;
      return `${length} ${C - length}`;
    },
    getBudgetChartOffset(idx) {
      // 总周长 = 2 * Math.PI * r (r=50)
      const C = 2 * Math.PI * 50;
      
      if (!this.budgetJigsawData.chart || this.budgetJigsawData.chart.length === 0) {
        return 0;
      }
      
      const total = this.budgetJigsawData.chart.reduce(
        (sum, item) => sum + (item.value || 0),
        0
      );
      
      if (total === 0) {
        return 0;
      }
      
      let offset = 0;
      for (let i = 0; i < idx; i++) {
        offset += ((this.budgetJigsawData.chart[i].value || 0) / total) * C;
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
      } else {
        // 如果chart中没有找到对应项，且值大于0，则添加
        if (newVal > 0) {
          const colors = {
            "住宿": "#e6c36f",
            "餐饮": "#8fd3c7", 
            "景点": "#f7a35c",
            "娱乐": "#ff9999",
            "购物": "#c7a9dd",
            "交通": "#95d4f4"
          };
          this.budgetJigsawData.chart.push({
            name: key,
            value: newVal,
            color: colors[key] || "#cccccc"
          });
        }
      }
      
      // 更新budget_breakdown
      if (this.budgetJigsawData.budget_breakdown) {
        this.budgetJigsawData.budget_breakdown[key] = newVal;
      }
      
      // 重新计算总数
      this.budgetJigsawData.total = this.budgetJigsawData.chart
        .filter(item => item.name !== '剩余预算' && item.name !== '预算待分配')
        .reduce((total, item) => total + (item.value || 0), 0);
      
      this.budgetJigsawData.total_considered = this.budgetJigsawData.total;
      
      // 如果有具体预算限制，重新计算剩余预算
      if (this.budgetJigsawData.budget_type === 'specific' && this.budgetJigsawData.budget_max > 0) {
        const remaining = Math.max(0, this.budgetJigsawData.budget_max - this.budgetJigsawData.total_considered);
        this.budgetJigsawData.remaining_budget = remaining;
        
        // 更新或添加剩余预算到chart
        const remainingItem = this.budgetJigsawData.chart.find(item => item.name === '剩余预算');
        if (remainingItem) {
          remainingItem.value = remaining;
        } else if (remaining > 0) {
          this.budgetJigsawData.chart.push({
            name: '剩余预算',
            value: remaining,
            color: '#e0e0e0'
          });
        }
      }
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
      // 清理会话状态
      this.sessionInfo = null;
      this.slotsInfo = null;
      this.currentState = 'INIT';
      this.jigsawType = 'location';
      // 重置POI选择状态
      this.selectedPoi = null;
      // 清空POI数据
      this.myPoisData = [];
      // 重置滚动状态
      this.isUserScrolling = false;
      this.shouldAutoScroll = true;
    },
    toggleCollectedInfo() {
      this.showCollectedInfo = !this.showCollectedInfo;
    },
    /** 重新生成行程链（清除现有行程后再次生成） */
    regenerateItinerary() {
      if (this.isGenerating) {
        return;
      }
      uni.showModal({
        title: '重新生成行程',
        content: '该操作将基于已收集的信息重新生成新的行程，是否继续？',
        success: (res) => {
          if (res.confirm) {
            this.itinerary = [];
            this.generateItinerary();
          }
        }
      });
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

    /* Markdown内容适配 */
    .markdown-content {
      font-size: 14px;
      line-height: 1.6;
      
      /* 重写Markdown组件的样式以适配消息气泡 */
      :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
        margin: 8px 0 6px 0;
        font-size: 1.1em;
      }
      
      :deep(h1) {
        font-size: 1.2em;
        border-bottom: 1px solid #e1e8ed;
      }
      
      :deep(h2) {
        font-size: 1.15em;
        border-bottom: 1px solid #f0f0f0;
      }
      
      :deep(p) {
        margin: 6px 0;
      }
      
      :deep(ul), :deep(ol) {
        margin: 6px 0;
        padding-left: 16px;
      }
      
      :deep(li) {
        margin: 2px 0;
      }
      
      :deep(strong) {
        color: inherit;
        font-weight: 600;
      }
      
      :deep(code) {
        background-color: rgba(0, 0, 0, 0.05);
        padding: 1px 3px;
        border-radius: 2px;
        font-size: 0.9em;
      }
      
      :deep(pre) {
        background-color: rgba(0, 0, 0, 0.03);
        border-radius: 4px;
        padding: 8px;
        margin: 8px 0;
        overflow-x: auto;
        font-size: 0.85em;
      }
      
      :deep(blockquote) {
        border-left: 3px solid #ddd;
        margin: 8px 0;
        padding: 4px 8px;
        background-color: rgba(0, 0, 0, 0.02);
        font-style: italic;
      }
      
      /* 旅游攻略特殊样式 */
      :deep(.day-title) {
        background: linear-gradient(135deg, #4f7063 0%, #5b7b84 100%);
        color: white;
        padding: 6px 10px;
        border-radius: 4px;
        margin: 10px 0 8px 0;
        font-size: 0.95em;
        font-weight: bold;
      }
      
      :deep(.poi-item) {
        background-color: rgba(79, 112, 99, 0.05);
        border-left: 3px solid #4f7063;
        padding: 6px 10px;
        margin: 6px 0;
        border-radius: 0 3px 3px 0;
        font-size: 0.9em;
      }
      
      :deep(.time-marker) {
        color: #e74c3c;
        font-weight: 600;
        background-color: rgba(231, 76, 60, 0.1);
        padding: 1px 4px;
        border-radius: 2px;
        font-size: 0.9em;
      }
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

/* 会话状态信息样式 */
.session-status {
  background: #f0f8ff;
  border-radius: 8px;
  padding: 8px 12px;
  margin-top: 8px;
  border-left: 3px solid #4a90e2;
  transition: all 0.2s ease;
}

.status-title {
  font-size: 13px;
  font-weight: bold;
  color: #2c4a52;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.status-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.status-item {
  font-size: 12px;
  color: #4a90e2;
  background: rgba(74, 144, 226, 0.1);
  padding: 3px 6px;
  border-radius: 6px;
  display: inline-block;
  width: fit-content;
  border: 1px solid rgba(74, 144, 226, 0.2);
}

/* 分页控件样式 */
.pagination-btn {
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:not(.disabled):active {
  background: #e0e0e0 !important;
  transform: scale(0.95);
}

.pagination-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* POI选择和加入功能样式 */
.poi-card {
  transition: all 0.3s ease;
  cursor: pointer;
}

.poi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(60, 89, 107, 0.12);
}

.poi-card.selected {
  border: 2px solid #4f7063;
  box-shadow: 0 4px 12px rgba(79, 112, 99, 0.2);
}

.poi-add-btn {
  background: #4f7063;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  margin-left: 8px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(79, 112, 99, 0.3);
  transition: all 0.2s ease;
}

.poi-add-btn:hover {
  background: #3a5449;
  transform: translateY(-1px);
}

.poi-add-btn:active {
  transform: translateY(0);
}

/* 拼图标签页导航样式 */
.jigsaw-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 4px;
  margin-top: 16px;
  backdrop-filter: blur(10px);
}

.jigsaw-tab {
  flex: 1;
  text-align: center;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
  cursor: pointer;
}

.jigsaw-tab.active {
  background: rgba(255, 255, 255, 0.2);
  color: #f8f4e9;
  font-weight: 500;
}

.jigsaw-tab:hover {
  color: #f8f4e9;
}

/* 删除按钮样式 */
.poi-remove-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  margin-left: 8px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
  transition: all 0.2s ease;
}

.poi-remove-btn:hover {
  background: #c82333;
  transform: translateY(-1px);
}

.poi-remove-btn:active {
  transform: translateY(0);
}

/* 回到底部按钮样式 */
.back-to-bottom-btn {
  position: fixed;
  right: 20px;
  bottom: 160px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 25px;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  z-index: 100;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 500;
}

.back-to-bottom-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

.back-to-bottom-btn:active {
  transform: translateY(0);
}

.back-to-bottom-icon {
  width: 16px;
  height: 16px;
  transform: rotate(90deg); /* 将发送图标旋转90度作为向下箭头 */
}

.collapse-icon {
  font-size: 12px;
  margin-left: 4px;
  cursor: pointer;
  transition: transform 0.2s;

  &.expanded {
    transform: rotate(180deg);
  }
}

.status-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #8a9ea7;
  padding: 4px 0;
  cursor: pointer;
}

.tap-to-expand {
  font-size: 12px;
  color: #4CAF50;
}
</style>
