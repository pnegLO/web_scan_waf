// 设置页面JavaScript文件

$(document).ready(function() {
    // 连接WebSocket
    const socket = io();
    
    // 初始化
    init();
    
    function init() {
        // 加载设置数据
        loadSettings();
        
        // 设置事件处理函数
        setupEventHandlers();
        
        // 设置范围滑块的值显示
        updateRangeValues();
    }
    
    // 加载设置数据
    function loadSettings() {
        $.get('/api/settings', function(data) {
            if (data && data.settings) {
                applySettings(data.settings);
            }
        }).fail(function() {
            showToast('错误', '加载设置失败');
        });
    }
    
    // 应用设置到表单
    function applySettings(settings) {
        // 常规设置
        if (settings.general) {
            $('#systemName').val(settings.general.systemName || '网络入侵检测与防御系统');
            $('#networkInterface').val(settings.general.networkInterface || 'all');
            $('#logRetention').val(settings.general.logRetention || 30);
            $('#autoStart').prop('checked', settings.general.autoStart !== false);
            $('#darkMode').prop('checked', !!settings.general.darkMode);
        }
        
        // 检测设置
        if (settings.detection) {
            $('#detectionMode').val(settings.detection.mode || 'active');
            $('#packetSampleRate').val(settings.detection.packetSampleRate || 100);
            $('#packetSampleRateValue').text(settings.detection.packetSampleRate + '%' || '100%');
            $('#deepPacketInspection').prop('checked', settings.detection.deepPacketInspection !== false);
            $('#anomalyDetection').prop('checked', settings.detection.anomalyDetection !== false);
            
            // 威胁检测类型
            $('#detectSqlInjection').prop('checked', settings.detection.detectSqlInjection !== false);
            $('#detectXss').prop('checked', settings.detection.detectXss !== false);
            $('#detectDos').prop('checked', settings.detection.detectDos !== false);
            $('#detectPortScan').prop('checked', settings.detection.detectPortScan !== false);
        }
        
        // 防御设置
        if (settings.prevention) {
            $('#preventionMode').val(settings.prevention.mode || 'auto');
            $('#ipBlockDuration').val(settings.prevention.ipBlockDuration || 60);
            $('#blockThreshold').val(settings.prevention.blockThreshold || 3);
            
            $(`input[name="trafficAction"][value="${settings.prevention.trafficAction || 'block'}"]`).prop('checked', true);
        }
        
        // 告警设置
        if (settings.alert) {
            $('#webNotifications').prop('checked', settings.alert.webNotifications !== false);
            $('#emailAlerts').prop('checked', !!settings.alert.emailAlerts);
            $('#emailRecipients').val(settings.alert.emailRecipients || '');
            $('#minAlertSeverity').val(settings.alert.minAlertSeverity || 'medium');
        }
        
        // 网络设置
        if (settings.network) {
            $('#managementPort').val(settings.network.managementPort || 5000);
            $('#monitoredNetworks').val(settings.network.monitoredNetworks || '192.168.1.0/24\n10.0.0.0/8');
            $('#enableSsl').prop('checked', !!settings.network.enableSsl);
            $('#requireAuth').prop('checked', settings.network.requireAuth !== false);
        }
    }
    
    // 设置事件处理函数
    function setupEventHandlers() {
        // 表单提交事件
        $('#generalSettingsForm').submit(function(e) {
            e.preventDefault();
            saveSettings('general', getGeneralSettings());
        });
        
        $('#detectionSettingsForm').submit(function(e) {
            e.preventDefault();
            saveSettings('detection', getDetectionSettings());
        });
        
        $('#preventionSettingsForm').submit(function(e) {
            e.preventDefault();
            saveSettings('prevention', getPreventionSettings());
        });
        
        $('#alertSettingsForm').submit(function(e) {
            e.preventDefault();
            saveSettings('alert', getAlertSettings());
        });
        
        $('#networkSettingsForm').submit(function(e) {
            e.preventDefault();
            saveSettings('network', getNetworkSettings());
        });
        
        // 滑块值更新
        $('#packetSampleRate').on('input', function() {
            $('#packetSampleRateValue').text($(this).val() + '%');
        });
        
        // 备份操作
        $('#createBackupBtn').click(function() {
            createBackup();
        });
        
        $('#restoreBackupBtn').click(function() {
            const file = $('#backupFile')[0].files[0];
            if (file) {
                showConfirmDialog(
                    '确定要恢复备份吗？当前的设置和数据将被替换。',
                    function() {
                        restoreBackup(file);
                    }
                );
            } else {
                showToast('警告', '请先选择备份文件');
            }
        });
        
        // 重置系统
        $('#resetSystemBtn').click(function() {
            showConfirmDialog(
                '警告：这将重置系统到初始状态，所有配置和数据将被清除。此操作不可撤销！',
                resetSystem,
                true
            );
        });
    }
    
    // 获取各表单的设置值
    function getGeneralSettings() {
        return {
            systemName: $('#systemName').val(),
            networkInterface: $('#networkInterface').val(),
            logRetention: parseInt($('#logRetention').val()),
            autoStart: $('#autoStart').is(':checked'),
            darkMode: $('#darkMode').is(':checked')
        };
    }
    
    function getDetectionSettings() {
        return {
            mode: $('#detectionMode').val(),
            packetSampleRate: parseInt($('#packetSampleRate').val()),
            deepPacketInspection: $('#deepPacketInspection').is(':checked'),
            anomalyDetection: $('#anomalyDetection').is(':checked'),
            detectSqlInjection: $('#detectSqlInjection').is(':checked'),
            detectXss: $('#detectXss').is(':checked'),
            detectDos: $('#detectDos').is(':checked'),
            detectPortScan: $('#detectPortScan').is(':checked')
        };
    }
    
    function getPreventionSettings() {
        return {
            mode: $('#preventionMode').val(),
            ipBlockDuration: parseInt($('#ipBlockDuration').val()),
            blockThreshold: parseInt($('#blockThreshold').val()),
            trafficAction: $('input[name="trafficAction"]:checked').val()
        };
    }
    
    function getAlertSettings() {
        return {
            webNotifications: $('#webNotifications').is(':checked'),
            emailAlerts: $('#emailAlerts').is(':checked'),
            emailRecipients: $('#emailRecipients').val(),
            minAlertSeverity: $('#minAlertSeverity').val()
        };
    }
    
    function getNetworkSettings() {
        return {
            managementPort: parseInt($('#managementPort').val()),
            monitoredNetworks: $('#monitoredNetworks').val(),
            enableSsl: $('#enableSsl').is(':checked'),
            requireAuth: $('#requireAuth').is(':checked')
        };
    }
    
    // 保存设置
    function saveSettings(section, data) {
        $.ajax({
            url: '/api/settings',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                section: section,
                settings: data
            }),
            success: function(response) {
                if (response.success) {
                    showToast('成功', '设置已保存');
                    
                    // 系统可能需要重启
                    if (section === 'network' && response.requireRestart) {
                        showToast('信息', '修改网络设置需要重启系统才能生效');
                    }
                } else {
                    showToast('错误', response.message || '保存设置失败');
                }
            },
            error: function() {
                showToast('错误', '无法连接到服务器');
            }
        });
    }
    
    // 更新范围滑块的值显示
    function updateRangeValues() {
        // 数据包采样率
        $('#packetSampleRate').on('input', function() {
            $('#packetSampleRateValue').text($(this).val() + '%');
        });
    }
    
    // 创建备份
    function createBackup() {
        $('#backupProgress').removeClass('d-none');
        $('#backupProgress .progress-bar').css('width', '0%').attr('aria-valuenow', 0);
        
        // 模拟进度增长
        let progress = 0;
        const progressInterval = setInterval(function() {
            progress += 5;
            $('#backupProgress .progress-bar').css('width', progress + '%').attr('aria-valuenow', progress);
            
            if (progress >= 100) {
                clearInterval(progressInterval);
                
                setTimeout(function() {
                    $('#backupProgress').addClass('d-none');
                    
                    // 创建下载链接
                    const date = new Date().toISOString().split('T')[0];
                    const filename = `ids_backup_${date}.zip`;
                    
                    // 在实际应用中，这里应该是真实的备份文件URL
                    showToast('成功', `备份已创建: ${filename}`);
                    
                    // 模拟下载链接 - 实际应用中应替换为真实下载URL
                    const downloadLink = $('<a>')
                        .attr('href', '#')
                        .attr('download', filename)
                        .text('下载备份文件')
                        .addClass('btn btn-sm btn-success mt-2');
                    
                    downloadLink.on('click', function(e) {
                        e.preventDefault();
                        showToast('信息', '这是一个模拟下载。在实际应用中，这将下载真实的备份文件。');
                    });
                    
                    $('#createBackupBtn').after(downloadLink);
                }, 500);
            }
        }, 100);
    }
    
    // 恢复备份
    function restoreBackup(file) {
        // 创建表单数据
        const formData = new FormData();
        formData.append('backupFile', file);
        
        // 发送请求
        $.ajax({
            url: '/api/restore',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                if (response.success) {
                    showToast('成功', '系统已成功恢复');
                    setTimeout(function() {
                        window.location.reload();
                    }, 2000);
                } else {
                    showToast('错误', response.message || '恢复失败');
                }
            },
            error: function() {
                showToast('错误', '无法连接到服务器');
            }
        });
    }
    
    // 重置系统
    function resetSystem() {
        $.post('/api/reset', function(response) {
            if (response.success) {
                showToast('成功', '系统已重置');
                setTimeout(function() {
                    window.location.reload();
                }, 2000);
            } else {
                showToast('错误', response.message || '重置失败');
            }
        }).fail(function() {
            showToast('错误', '无法连接到服务器');
        });
    }
    
    // 显示确认对话框
    function showConfirmDialog(message, confirmCallback, isDangerous = false) {
        $('#confirmMessage').text(message);
        
        if (isDangerous) {
            $('#confirmActionBtn').addClass('btn-danger').removeClass('btn-primary');
        } else {
            $('#confirmActionBtn').addClass('btn-primary').removeClass('btn-danger');
        }
        
        $('#confirmActionBtn').off('click').on('click', function() {
            $('#confirmModal').modal('hide');
            if (typeof confirmCallback === 'function') {
                confirmCallback();
            }
        });
        
        $('#confirmModal').modal('show');
    }
    
    // 显示通知消息
    function showToast(type, message) {
        // 检查是否已存在toast容器
        if ($('#toastContainer').length === 0) {
            $('body').append(`
                <div id="toastContainer" style="position: fixed; top: 20px; right: 20px; z-index: 1050;"></div>
            `);
        }
        
        // 设置样式
        const bgClass = type === '错误' ? 'bg-danger' : (type === '警告' ? 'bg-warning' : 'bg-success');
        const textClass = type === '警告' ? 'text-dark' : 'text-white';
        
        // 创建toast
        const toastId = 'toast-' + Date.now();
        const toast = $(`
            <div id="${toastId}" class="toast ${bgClass} ${textClass}" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="5000">
                <div class="toast-header">
                    <strong class="me-auto">${type}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `);
        
        // 添加并显示toast
        $('#toastContainer').append(toast);
        const toastElement = new bootstrap.Toast(document.getElementById(toastId));
        toastElement.show();
        
        // 自动移除
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    // WebSocket事件
    socket.on('connect', function() {
        console.log('已连接到服务器');
    });
    
    socket.on('disconnect', function() {
        console.log('与服务器连接已断开');
    });
    
    socket.on('settings_updated', function(data) {
        showToast('信息', '设置已被更新');
        applySettings(data.settings);
    });
}); 