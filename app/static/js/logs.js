// 日志页面JavaScript文件

$(document).ready(function() {
    // 连接WebSocket
    const socket = io();
    
    let logs = [];
    let filteredLogs = [];
    let currentPage = 1;
    let logsPerPage = 20;
    let currentFilter = 'all';
    let currentSort = 'newest';
    
    // 初始化
    init();
    
    function init() {
        // 加载日志数据
        loadLogs();
        
        // 设置按钮事件
        setupEventHandlers();
        
        // 设置WebSocket监听
        setupSocketEvents();
        
        // 添加系统事件
        addSystemEvent('信息', '日志页面已加载');
    }
    
    // 加载日志数据
    function loadLogs() {
        $.get('/api/logs', function(data) {
            logs = data.logs || [];
            applyFilterAndSort();
            renderLogs();
            
            $('#totalLogs').text(logs.length);
        }).fail(function() {
            $('#logTable').html('<tr><td colspan="6" class="text-center text-danger">加载日志失败</td></tr>');
        });
    }
    
    // 应用过滤和排序
    function applyFilterAndSort() {
        // 先过滤
        if (currentFilter === 'all') {
            filteredLogs = [...logs];
        } else {
            filteredLogs = logs.filter(log => log.severity === currentFilter);
        }
        
        // 再排序
        if (currentSort === 'newest') {
            filteredLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        } else {
            filteredLogs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        }
        
        // 重置页码
        currentPage = 1;
        updatePagination();
    }
    
    // 渲染日志表格
    function renderLogs() {
        const start = (currentPage - 1) * logsPerPage;
        const end = start + logsPerPage;
        const pageData = filteredLogs.slice(start, end);
        
        if (pageData.length === 0) {
            $('#logTable').html('<tr><td colspan="6" class="text-center">没有找到匹配的日志记录</td></tr>');
            return;
        }
        
        let html = '';
        pageData.forEach(log => {
            const time = moment(log.timestamp).format('YYYY-MM-DD HH:mm:ss');
            const severityClass = log.severity === '高' ? 'danger' : (log.severity === '中' ? 'warning' : 'info');
            
            html += `<tr>
                <td>${time}</td>
                <td>${log.alert_type || log.threat_type || '未知'}</td>
                <td><span class="badge bg-${severityClass}">${log.severity || '未知'}</span></td>
                <td>${log.src_ip || '未知'}</td>
                <td>${log.dst_ip || '未知'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary view-log" data-id="${log.alert_id || ''}">
                        查看
                    </button>
                </td>
            </tr>`;
        });
        
        $('#logTable').html(html);
        $('#logCount').text(pageData.length);
        
        // 绑定查看按钮事件
        $('.view-log').click(function() {
            const logId = $(this).data('id');
            const log = logs.find(l => l.alert_id === logId);
            if (log) {
                showLogDetails(log);
            }
        });
    }
    
    // 更新分页控件状态
    function updatePagination() {
        const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
        $('#currentPage').text(currentPage);
        
        $('#prevBtn').prop('disabled', currentPage <= 1);
        $('#nextBtn').prop('disabled', currentPage >= totalPages);
    }
    
    // 显示日志详情
    function showLogDetails(log) {
        const time = moment(log.timestamp).format('YYYY-MM-DD HH:mm:ss');
        
        let detailsHtml = `<div class="log-detail-header">
            <h6>时间：${time}</h6>
            <h6>类型：${log.alert_type || log.threat_type || '未知'}</h6>
            <h6>严重程度：${log.severity || '未知'}</h6>
        </div>
        <hr>
        <div class="row">
            <div class="col-md-6">
                <p><strong>源IP：</strong> ${log.src_ip || '未知'}</p>
                <p><strong>目标IP：</strong> ${log.dst_ip || '未知'}</p>
                <p><strong>协议：</strong> ${log.protocol || '未知'}</p>
                <p><strong>端口：</strong> ${log.port || '未知'}</p>
            </div>
            <div class="col-md-6">
                <p><strong>操作：</strong> ${log.action_taken || '无'}</p>
                <p><strong>告警ID：</strong> ${log.alert_id || '无'}</p>
            </div>
        </div>`;
        
        if (log.details) {
            detailsHtml += `<hr><div><strong>详细信息：</strong><pre>${log.details}</pre></div>`;
        }
        
        $('#logDetails').html(detailsHtml);
        $('#blockIPBtn').data('ip', log.src_ip);
        
        const logModal = new bootstrap.Modal(document.getElementById('logModal'));
        logModal.show();
    }
    
    // 添加系统事件
    function addSystemEvent(type, message) {
        const time = moment().format('HH:mm:ss');
        const typeClass = type.toLowerCase();
        
        const eventHtml = `<div class="event-item">
            <div class="event-time">${time}</div>
            <div class="event-type ${typeClass}">${type}</div>
            <div class="event-message">${message}</div>
        </div>`;
        
        $('#systemEvents').prepend(eventHtml);
        
        // 限制显示的事件数量
        const maxEvents = 100;
        if ($('#systemEvents .event-item').length > maxEvents) {
            $('#systemEvents .event-item').slice(maxEvents).remove();
        }
    }
    
    // 设置事件处理函数
    function setupEventHandlers() {
        // 阻止IP按钮点击事件
        $('#blockIPBtn').click(function() {
            const ip = $(this).data('ip');
            if (ip && ip !== '未知') {
                $.post('/api/block_ip', { ip: ip }, function(response) {
                    if (response.success) {
                        addSystemEvent('成功', `已阻止IP: ${ip}`);
                    } else {
                        addSystemEvent('错误', `阻止IP失败: ${response.message || '未知错误'}`);
                    }
                }).fail(function() {
                    addSystemEvent('错误', '操作失败，请重试');
                });
                
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('logModal'));
                if (modal) {
                    modal.hide();
                }
            } else {
                addSystemEvent('警告', '无效的IP地址');
            }
        });
        
        // 过滤按钮点击事件
        $('.filter-btn').click(function() {
            $('.filter-btn').removeClass('active');
            $(this).addClass('active');
            currentFilter = $(this).data('filter');
            applyFilterAndSort();
            renderLogs();
        });
        
        // 排序按钮点击事件
        $('.sort-btn').click(function() {
            $('.sort-btn').removeClass('active');
            $(this).addClass('active');
            currentSort = $(this).data('sort');
            applyFilterAndSort();
            renderLogs();
        });
        
        // 分页按钮点击事件
        $('#prevBtn').click(function() {
            if (currentPage > 1) {
                currentPage--;
                renderLogs();
                updatePagination();
            }
        });
        
        $('#nextBtn').click(function() {
            const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                renderLogs();
                updatePagination();
            }
        });
        
        // 搜索按钮点击事件
        $('#searchBtn').click(function() {
            searchLogs();
        });
        
        // 回车键触发搜索
        $('#searchInput').keypress(function(e) {
            if (e.which === 13) {
                searchLogs();
            }
        });
        
        // 刷新按钮点击事件
        $('#refreshBtn').click(function() {
            loadLogs();
            addSystemEvent('信息', '已刷新日志数据');
        });
        
        // 清除事件按钮点击事件
        $('#clearEvents').click(function() {
            $('#systemEvents').empty();
            addSystemEvent('信息', '已清除所有系统事件');
        });
    }
    
    // 搜索日志
    function searchLogs() {
        const searchText = $('#searchInput').val().toLowerCase();
        if (searchText) {
            filteredLogs = logs.filter(log => 
                JSON.stringify(log).toLowerCase().includes(searchText)
            );
        } else {
            applyFilterAndSort();
        }
        currentPage = 1;
        renderLogs();
        updatePagination();
    }
    
    // 设置WebSocket事件
    function setupSocketEvents() {
        socket.on('connect', function() {
            addSystemEvent('信息', '已连接到服务器');
        });
        
        socket.on('disconnect', function() {
            addSystemEvent('警告', '与服务器的连接已断开');
        });
        
        socket.on('new_alert', function(data) {
            // 添加到日志数组
            logs.unshift(data);
            
            // 如果当前是最新排序且没有过滤或者符合当前过滤条件，则更新显示
            if (currentSort === 'newest' && (currentFilter === 'all' || data.severity === currentFilter)) {
                applyFilterAndSort();
                renderLogs();
            }
            
            // 更新总数
            $('#totalLogs').text(logs.length);
            
            // 添加系统事件通知
            const severityMap = {
                '高': '高危',
                '中': '中危',
                '低': '低危'
            };
            
            const severity = severityMap[data.severity] || data.severity || '未知';
            addSystemEvent('告警', `${severity} - ${data.alert_type || data.threat_type || '未知'} 来自 ${data.src_ip || '未知'}`);
        });
    }
}); 