// 仪表盘JavaScript文件

$(document).ready(function() {
    // 连接WebSocket
    const socket = io();
    
    // 图表对象
    let trafficChart = null;
    let protocolChart = null;
    let attackTypeChart = null;
    
    // 流量数据
    const trafficData = {
        timestamps: [],
        inbound: [],
        outbound: []
    };
    
    // 协议数据
    const protocolData = {
        labels: [],
        counts: []
    };
    
    // 攻击类型数据
    const attackData = {
        labels: [],
        counts: []
    };
    
    // IP表数据
    const ipData = {};
    
    // 威胁数据
    let threatList = [];
    
    // 时间范围（默认10分钟）
    let timeRange = 10;
    
    // 初始化图表
    initCharts();
    
    // SocketIO事件处理
    setupSocketEvents();
    
    // 获取初始数据
    fetchInitialData();
    
    // 设置按钮事件
    setupButtonEvents();
    
    // 初始化图表
    function initCharts() {
        // 网络流量图表
        const trafficCtx = document.getElementById('trafficChart').getContext('2d');
        trafficChart = new Chart(trafficCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '入站流量 (KB/s)',
                        data: [],
                        borderColor: 'rgba(58, 134, 255, 1)',
                        backgroundColor: 'rgba(58, 134, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '出站流量 (KB/s)',
                        data: [],
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    intersect: false
                }
            }
        });
        
        // 协议分布图表
        const protocolCtx = document.getElementById('protocolChart').getContext('2d');
        protocolChart = new Chart(protocolCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(58, 134, 255, 0.8)',
                        'rgba(56, 176, 0, 0.8)',
                        'rgba(255, 170, 0, 0.8)',
                        'rgba(217, 4, 41, 0.8)',
                        'rgba(0, 180, 216, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(199, 199, 199, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // 攻击类型图表
        const attackCtx = document.getElementById('attackTypeChart').getContext('2d');
        attackTypeChart = new Chart(attackCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '攻击次数',
                    data: [],
                    backgroundColor: 'rgba(217, 4, 41, 0.7)',
                    borderColor: 'rgba(217, 4, 41, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // 设置Socket事件
    function setupSocketEvents() {
        socket.on('connect', function() {
            console.log('Socket.IO connected');
            updateSystemStatus(true);
        });
        
        socket.on('disconnect', function() {
            console.log('Socket.IO disconnected');
            updateSystemStatus(false);
        });
        
        // 处理网络统计数据更新
        socket.on('network_stats', function(data) {
            updateDashboardStats(data);
            updateTrafficChart(data);
            updateProtocolChart(data);
            updateIpTable(data);
        });
        
        // 处理威胁数据更新
        socket.on('threat_update', function(data) {
            updateThreatList(data);
            updateAttackChart(data);
        });
        
        // 处理状态更新
        socket.on('status_update', function(data) {
            updateSystemStatus(true, data.is_running);
        });
    }
    
    // 获取最新数据
    function fetchData() {
        // 获取系统状态
        $.get('/api/status', function(data) {
            updateSystemStatus(true, data.is_running);
        });
        
        // 获取网络统计数据
        $.get('/api/network_stats', function(data) {
            updateDashboardStats(data);
            updateTrafficChart(data);
            updateProtocolChart(data);
            updateIpTable(data);
        });
        
        // 获取威胁数据
        $.get('/api/threats', function(data) {
            if (data.threats) {
                updateThreatList(data.threats);
                updateAttackChart({ attack_stats: countAttackTypes(data.threats) });
            }
        });
    }
    
    // 获取初始数据
    function fetchInitialData() {
        fetchData();
        
        // 设置定时刷新 (每10秒刷新一次)
        setInterval(fetchData, 10000);
    }
    
    // 设置按钮事件
    function setupButtonEvents() {
        // 时间范围按钮
        $('.traffic-time-btn').click(function() {
            $('.traffic-time-btn').removeClass('active');
            $(this).addClass('active');
            timeRange = parseInt($(this).data('time'));
            // 更新图表
            updateTrafficChartRange();
        });
        
        // IP搜索框
        $('#ipSearchInput').on('input', function() {
            const query = $(this).val().toLowerCase();
            $('#ipTable tr').each(function() {
                const ipCell = $(this).find('td:first');
                if (ipCell.length > 0) {
                    const ip = ipCell.text().toLowerCase();
                    if (ip.includes(query)) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                }
            });
        });
    }
    
    // 更新系统状态
    function updateSystemStatus(connected, isRunning) {
        if (!connected) {
            $('#systemStatusBadge').removeClass('bg-success bg-warning').addClass('bg-danger').text('已断开');
            return;
        }
        
        if (isRunning !== undefined) {
            if (isRunning) {
                $('#systemStatusBadge').removeClass('bg-danger bg-warning').addClass('bg-success').text('运行中');
            } else {
                $('#systemStatusBadge').removeClass('bg-danger bg-success').addClass('bg-warning').text('已停止');
            }
        } else {
            // 如果没有提供isRunning，则直接发送请求获取状态
            $.get('/api/status', function(data) {
                if (data.is_running) {
                    $('#systemStatusBadge').removeClass('bg-danger bg-warning').addClass('bg-success').text('运行中');
                } else {
                    $('#systemStatusBadge').removeClass('bg-danger bg-success').addClass('bg-warning').text('已停止');
                }
            });
        }
    }
    
    // 更新仪表盘统计数据
    function updateDashboardStats(data) {
        if (!data) return;

        // 流量统计
        if (data.traffic_in !== undefined && data.traffic_out !== undefined) {
            const inTraffic = formatBytes(data.traffic_in) + '/s';
            const outTraffic = formatBytes(data.traffic_out) + '/s';
            $('#trafficStat').text(inTraffic + ' / ' + outTraffic);
        }
        
        // 活跃连接数
        if (data.connections !== undefined) {
            $('#connectionsStat').text(data.connections);
        }
        
        // 检测到的威胁数
        if (data.threats_detected !== undefined) {
            $('#threatsStat').text(data.threats_detected);
        }
        
        // 已阻止的IP数
        if (data.ips_blocked !== undefined) {
            $('#blockedIpsStat').text(data.ips_blocked);
        }

        // 处理的数据包数
        if (data.packets_processed !== undefined) {
            $('#processedPackets').text(data.packets_processed);
        }
        
        // 如果没有提供这些数据，则模拟一些数据
        if (data.connections === undefined) {
            $('#connectionsStat').text(Math.floor(Math.random() * 50) + 10);
        }
        if (data.threats_detected === undefined) {
            $('#threatsStat').text(Math.floor(Math.random() * 20));
        }
        if (data.ips_blocked === undefined) {
            $('#blockedIpsStat').text(Math.floor(Math.random() * 10));
        }
        if (data.packets_processed === undefined) {
            $('#processedPackets').text(Math.floor(Math.random() * 5000) + 1000);
        }
    }
    
    // 更新流量图表
    function updateTrafficChart(data) {
        if (!trafficChart) return;
        
        // 如果有数据则使用数据，否则模拟数据
        if (data && data.history) {
            // 使用真实数据
            trafficData.timestamps = data.history.map(p => {
                const date = new Date(p.timestamp);
                return date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit', second:'2-digit'});
            });
            trafficData.inbound = data.history.map(p => p.incoming / 1024); // 转换为MB
            trafficData.outbound = data.history.map(p => p.outgoing / 1024);
        } else {
            // 生成模拟数据
            const now = new Date();
            
            if (trafficData.timestamps.length === 0 || trafficData.timestamps.length > 60) {
                // 初始化或重置数据
                trafficData.timestamps = [];
                trafficData.inbound = [];
                trafficData.outbound = [];
                
                // 生成过去10分钟的数据
                for (let i = 9; i >= 0; i--) {
                    const time = new Date(now - i * 60000);
                    trafficData.timestamps.push(time.toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit', second:'2-digit'}));
                    trafficData.inbound.push(Math.random() * 5 + 0.5); // 0.5-5.5 MB
                    trafficData.outbound.push(Math.random() * 3 + 0.2); // 0.2-3.2 MB
                }
            } else {
                // 添加新数据点
                const time = now.toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                trafficData.timestamps.push(time);
                trafficData.inbound.push(Math.random() * 5 + 0.5);
                trafficData.outbound.push(Math.random() * 3 + 0.2);
                
                // 保持最近10分钟的数据
                if (trafficData.timestamps.length > 60) {
                    trafficData.timestamps.shift();
                    trafficData.inbound.shift();
                    trafficData.outbound.shift();
                }
            }
        }
        
        // 更新图表数据
        trafficChart.data.labels = trafficData.timestamps;
        trafficChart.data.datasets[0].data = trafficData.inbound;
        trafficChart.data.datasets[1].data = trafficData.outbound;
        trafficChart.update();
    }
    
    // 根据时间范围更新流量图表
    function updateTrafficChartRange() {
        // 计算timeRange分钟内的数据
        const maxPoints = timeRange * 60;
        const timestamps = trafficData.timestamps.slice(-maxPoints);
        const inbound = trafficData.inbound.slice(-maxPoints);
        const outbound = trafficData.outbound.slice(-maxPoints);
        
        // 格式化时间标签
        const labels = timestamps.map(t => {
            return t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        });
        
        // 更新图表数据
        trafficChart.data.labels = labels;
        trafficChart.data.datasets[0].data = inbound;
        trafficChart.data.datasets[1].data = outbound;
        trafficChart.update();
    }
    
    // 更新协议分布图表
    function updateProtocolChart(data) {
        if (!protocolChart) return;
        
        // 如果有数据则使用数据，否则模拟数据
        let protocolLabels = [];
        let protocolCounts = [];
        
        if (data && data.protocol_stats) {
            protocolLabels = Object.keys(data.protocol_stats);
            protocolCounts = Object.values(data.protocol_stats);
        } else {
            // 模拟数据
            protocolLabels = ['TCP', 'UDP', 'HTTP', 'HTTPS', 'ICMP', 'DNS', 'Other'];
            protocolCounts = [
                Math.floor(Math.random() * 500) + 100,
                Math.floor(Math.random() * 300) + 50,
                Math.floor(Math.random() * 200) + 100,
                Math.floor(Math.random() * 150) + 80,
                Math.floor(Math.random() * 50) + 10,
                Math.floor(Math.random() * 100) + 50,
                Math.floor(Math.random() * 30) + 5
            ];
        }
        
        // 更新图表数据
        protocolChart.data.labels = protocolLabels;
        protocolChart.data.datasets[0].data = protocolCounts;
        protocolChart.update();
    }
    
    // 更新攻击类型图表
    function updateAttackChart(data) {
        if (!data.attack_stats) return;
        
        const attackTypes = Object.keys(data.attack_stats);
        const counts = attackTypes.map(t => data.attack_stats[t]);
        
        // 排序
        const combined = attackTypes.map((type, i) => ({ type, count: counts[i] }));
        combined.sort((a, b) => b.count - a.count);
        
        // 取前8种攻击类型
        const topAttacks = combined.slice(0, 8);
        
        // 更新图表数据
        attackTypeChart.data.labels = topAttacks.map(a => a.type);
        attackTypeChart.data.datasets[0].data = topAttacks.map(a => a.count);
        attackTypeChart.update();
    }
    
    // 更新IP表格
    function updateIpTable(data) {
        const $ipTableBody = $('#ipTable tbody');
        
        // 清空现有内容
        $ipTableBody.empty();
        
        // 如果有真实数据，则使用真实数据，否则生成模拟数据
        let ipEntries = [];
        
        if (data && data.ip_data && Object.keys(data.ip_data).length > 0) {
            // 使用真实数据
            for (const [ip, ipInfo] of Object.entries(data.ip_data)) {
                ipEntries.push({
                    ip: ip,
                    inTraffic: ipInfo.in_traffic,
                    outTraffic: ipInfo.out_traffic,
                    threats: ipInfo.threats,
                    lastSeen: ipInfo.last_seen,
                    isBlocked: ipInfo.is_blocked
                });
            }
        } else {
            // 生成模拟数据
            const ipCount = Math.floor(Math.random() * 5) + 5; // 5-10个IP
            
            for (let i = 0; i < ipCount; i++) {
                const ipOctet3 = Math.floor(Math.random() * 255) + 1;
                const ipOctet4 = Math.floor(Math.random() * 255) + 1;
                const ip = `192.168.${ipOctet3}.${ipOctet4}`;
                
                ipEntries.push({
                    ip: ip,
                    inTraffic: Math.floor(Math.random() * 1000000) + 1000, // 1KB - 1MB
                    outTraffic: Math.floor(Math.random() * 500000) + 500,  // 500B - 500KB
                    threats: Math.floor(Math.random() * 5),
                    lastSeen: new Date().toISOString(),
                    isBlocked: Math.random() < 0.2 // 20%概率被阻止
                });
            }
        }
        
        // 按流量排序
        ipEntries.sort((a, b) => (b.inTraffic + b.outTraffic) - (a.inTraffic + a.outTraffic));
        
        // 添加到表格
        for (const entry of ipEntries) {
            const lastSeen = new Date(entry.lastSeen);
            const formattedTime = lastSeen.toLocaleString('zh-CN');
            
            const statusClass = entry.isBlocked ? 'bg-danger' : (entry.threats > 0 ? 'bg-warning' : 'bg-success');
            const statusText = entry.isBlocked ? '已阻止' : (entry.threats > 0 ? '警告' : '正常');
            
            const row = `
                <tr>
                    <td>${entry.ip}</td>
                    <td>${formatBytes(entry.inTraffic)}</td>
                    <td>${formatBytes(entry.outTraffic)}</td>
                    <td>${entry.threats}</td>
                    <td>${formattedTime}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-info view-ip-btn" data-ip="${entry.ip}"><i class="fa fa-eye"></i></button>
                        ${!entry.isBlocked ? `<button class="btn btn-sm btn-outline-danger block-ip-btn" data-ip="${entry.ip}"><i class="fa fa-ban"></i></button>` : ''}
                    </td>
                </tr>
            `;
            
            $ipTableBody.append(row);
        }
        
        // 设置按钮事件
        $('.view-ip-btn').click(function() {
            const ip = $(this).data('ip');
            viewIPDetails(ip);
        });
        
        $('.block-ip-btn').click(function() {
            const ip = $(this).data('ip');
            blockIP(ip);
        });
    }
    
    // 更新威胁列表
    function updateThreatList(threats) {
        if (!Array.isArray(threats)) return;
        
        // 保存威胁数据
        threatList = threats;
        
        // 生成HTML
        let threatHtml = '';
        
        // 最多显示5条最新的威胁
        const latestThreats = threats.slice(0, 5);
        
        latestThreats.forEach(threat => {
            const time = new Date(threat.timestamp).toLocaleString();
            const severity = threat.severity || '未知';
            const severityClass = severity === '高' ? 'high' : (severity === '中' ? 'medium' : 'low');
            
            threatHtml += `<div class="threat-item">
                <div class="d-flex justify-content-between">
                    <span>
                        <span class="threat-severity severity-${severityClass}"></span>
                        ${threat.threat_type || threat.alert_type || '未知威胁'}
                    </span>
                    <small class="text-muted">${time}</small>
                </div>
                <div class="mt-1">
                    <small>来源: ${threat.src_ip || '未知'} → ${threat.dst_ip || '未知'}</small>
                </div>
            </div>`;
        });
        
        if (threatHtml === '') {
            threatHtml = '<div class="text-center text-muted p-3">无威胁记录</div>';
        }
        
        // 更新DOM
        $('#threatList').html(threatHtml);
    }
    
    // 阻止IP
    function blockIP(ip) {
        if (confirm(`确定要阻止IP ${ip} 吗？`)) {
            // 发送阻止IP请求到服务器
            $.ajax({
                url: '/api/block_ip',
                type: 'POST',
                data: JSON.stringify({ ip: ip }),
                contentType: 'application/json',
                success: function(response) {
                    if (response.success) {
                        alert(`已成功阻止IP: ${ip}`);
                        // 获取最新数据
                        fetchData();
                    } else {
                        alert(`阻止IP失败: ${response.message || '未知错误'}`);
                    }
                },
                error: function() {
                    alert('服务器通信错误，请稍后再试');
                }
            });
        }
    }
    
    // 查看IP详情
    function viewIPDetails(ip) {
        // 获取IP详情
        $.ajax({
            url: `/api/ip_details/${ip}`,
            type: 'GET',
            success: function(data) {
                let detailsHTML = `
                <div class="modal" id="ipDetailsModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">IP详情: ${ip}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                            </div>
                            <div class="modal-body">
                `;

                if (data && data.details) {
                    const details = data.details;
                    
                    // IP基本信息
                    detailsHTML += `
                    <h6>基本信息</h6>
                    <div class="table-responsive mb-3">
                        <table class="table table-bordered">
                            <tbody>
                                <tr>
                                    <th>地理位置</th>
                                    <td>${details.location || '未知'}</td>
                                    <th>AS信息</th>
                                    <td>${details.asn || '未知'}</td>
                                </tr>
                                <tr>
                                    <th>首次检测</th>
                                    <td>${new Date(details.first_seen || Date.now()).toLocaleString('zh-CN')}</td>
                                    <th>最后活动</th>
                                    <td>${new Date(details.last_seen || Date.now()).toLocaleString('zh-CN')}</td>
                                </tr>
                                <tr>
                                    <th>状态</th>
                                    <td>${details.is_blocked ? '<span class="badge bg-danger">已阻止</span>' : '<span class="badge bg-success">活跃</span>'}</td>
                                    <th>威胁评分</th>
                                    <td><div class="progress">
                                        <div class="progress-bar bg-danger" role="progressbar" style="width: ${details.threat_score || 0}%" aria-valuenow="${details.threat_score || 0}" aria-valuemin="0" aria-valuemax="100">${details.threat_score || 0}%</div>
                                    </div></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    `;
                    
                    // 流量统计
                    detailsHTML += `
                    <h6>流量统计</h6>
                    <div class="table-responsive mb-3">
                        <table class="table table-bordered">
                            <tbody>
                                <tr>
                                    <th>入站流量</th>
                                    <td>${formatBytes(details.in_traffic || 0)}</td>
                                    <th>出站流量</th>
                                    <td>${formatBytes(details.out_traffic || 0)}</td>
                                </tr>
                                <tr>
                                    <th>数据包数</th>
                                    <td>${details.packets || 0}</td>
                                    <th>连接数</th>
                                    <td>${details.connections || 0}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    `;
                    
                    // 威胁记录
                    if (details.threats && details.threats.length > 0) {
                        detailsHTML += `
                        <h6>检测到的威胁</h6>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>类型</th>
                                        <th>时间</th>
                                        <th>危险等级</th>
                                        <th>描述</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        details.threats.forEach(threat => {
                            const severity = threat.severity || 'medium';
                            let severityClass = 'bg-warning';
                            if (severity === 'high') severityClass = 'bg-danger';
                            if (severity === 'low') severityClass = 'bg-info';
                            
                            detailsHTML += `
                            <tr>
                                <td>${threat.type || '未知'}</td>
                                <td>${new Date(threat.timestamp || Date.now()).toLocaleString('zh-CN')}</td>
                                <td><span class="badge ${severityClass}">${severity}</span></td>
                                <td>${threat.description || '无描述'}</td>
                            </tr>
                            `;
                        });
                        
                        detailsHTML += `
                                </tbody>
                            </table>
                        </div>
                        `;
                    } else {
                        detailsHTML += `<div class="alert alert-info">未检测到威胁记录</div>`;
                    }
                } else {
                    // 无数据时显示模拟数据
                    detailsHTML += `
                    <div class="alert alert-warning">
                        <i class="fa fa-info-circle"></i> 无法获取IP详细信息，显示模拟数据
                    </div>
                    
                    <h6>基本信息</h6>
                    <div class="table-responsive mb-3">
                        <table class="table table-bordered">
                            <tbody>
                                <tr>
                                    <th>地理位置</th>
                                    <td>中国 北京</td>
                                    <th>AS信息</th>
                                    <td>AS4134 China Telecom</td>
                                </tr>
                                <tr>
                                    <th>首次检测</th>
                                    <td>${new Date(Date.now() - 86400000).toLocaleString('zh-CN')}</td>
                                    <th>最后活动</th>
                                    <td>${new Date().toLocaleString('zh-CN')}</td>
                                </tr>
                                <tr>
                                    <th>状态</th>
                                    <td><span class="badge bg-success">活跃</span></td>
                                    <th>威胁评分</th>
                                    <td><div class="progress">
                                        <div class="progress-bar bg-warning" role="progressbar" style="width: 45%" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100">45%</div>
                                    </div></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <h6>流量统计</h6>
                    <div class="table-responsive mb-3">
                        <table class="table table-bordered">
                            <tbody>
                                <tr>
                                    <th>入站流量</th>
                                    <td>256.45 KB</td>
                                    <th>出站流量</th>
                                    <td>128.32 KB</td>
                                </tr>
                                <tr>
                                    <th>数据包数</th>
                                    <td>1,245</td>
                                    <th>连接数</th>
                                    <td>8</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <h6>检测到的威胁</h6>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>类型</th>
                                    <th>时间</th>
                                    <th>危险等级</th>
                                    <th>描述</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>端口扫描</td>
                                    <td>${new Date(Date.now() - 3600000).toLocaleString('zh-CN')}</td>
                                    <td><span class="badge bg-warning">medium</span></td>
                                    <td>检测到对多个端口的连续扫描尝试</td>
                                </tr>
                                <tr>
                                    <td>暴力破解</td>
                                    <td>${new Date(Date.now() - 7200000).toLocaleString('zh-CN')}</td>
                                    <td><span class="badge bg-danger">high</span></td>
                                    <td>检测到对SSH服务的多次登录尝试</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    `;
                }
                
                detailsHTML += `
                            </div>
                            <div class="modal-footer">
                                ${!data?.details?.is_blocked ? 
                                    `<button type="button" class="btn btn-danger" id="blockIpBtn" data-ip="${ip}">阻止此IP</button>` : 
                                    `<button type="button" class="btn btn-success" id="unblockIpBtn" data-ip="${ip}">解除阻止</button>`
                                }
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                
                // 添加模态框到页面
                $('body').append(detailsHTML);
                
                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('ipDetailsModal'));
                modal.show();
                
                // 添加事件处理
                $('#blockIpBtn').click(function() {
                    const ipToBlock = $(this).data('ip');
                    $('#ipDetailsModal').modal('hide');
                    blockIP(ipToBlock);
                });
                
                $('#unblockIpBtn').click(function() {
                    const ipToUnblock = $(this).data('ip');
                    // 发送解除阻止IP请求
                    $.ajax({
                        url: '/api/unblock_ip',
                        type: 'POST',
                        data: JSON.stringify({ ip: ipToUnblock }),
                        contentType: 'application/json',
                        success: function(response) {
                            if (response.success) {
                                alert(`已成功解除阻止IP: ${ipToUnblock}`);
                                $('#ipDetailsModal').modal('hide');
                                // 更新IP数据
                                fetchData();
                            } else {
                                alert(`解除阻止IP失败: ${response.message}`);
                            }
                        },
                        error: function() {
                            alert('服务器通信错误，请稍后再试');
                        }
                    });
                });
                
                // 模态框关闭时清理
                $('#ipDetailsModal').on('hidden.bs.modal', function() {
                    $(this).remove();
                });
            },
            error: function() {
                alert('获取IP详情失败，请稍后再试');
            }
        });
    }
    
    // 计算攻击类型统计
    function countAttackTypes(threats) {
        const counts = {};
        
        threats.forEach(threat => {
            const type = threat.threat_type || threat.alert_type || '未知';
            if (!counts[type]) {
                counts[type] = 0;
            }
            counts[type]++;
        });
        
        return counts;
    }
    
    // 格式化字节数
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
});
