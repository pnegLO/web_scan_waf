if __name__ == '__main__':
    try:
        logger.info("网络入侵检测与防御系统启动中...")
        socketio.run(app, host='0.0.0.0', port=8080, debug=True)
    except Exception as e:
        logger.error(f"系统启动失败: {str(e)}")