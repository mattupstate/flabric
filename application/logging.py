
def init(app):
    """
    Initialize logging for the application, (only if its not in debug mode)
    """
    if not app.debug:
        from logging import Formatter
        from logging.handlers import SMTPHandler, TimedRotatingFileHandler
        
        # File handler
        file_formatter = Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        file_handler = TimedRotatingFileHandler(app.config['LOG_FILE_NAME'], when='midnight', backupCount=31)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(app.config['LOG_FILE_LEVEL'])
        app.logger.addHandler(file_handler)
        
        # Email handler
        mail_formatter = Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
''')
        mail_handler = SMTPHandler(app.config['LOG_EMAIL_SERVER'], app.config['LOG_EMAIL_SENDER'],
                                   app.config['ADMIN_EMAILS'].split(','), '[%s] Error' % app.config['HOST_DOMAIN'])
        mail_handler.setFormatter(mail_formatter)
        mail_handler.setLevel(app.config['LOG_EMAIL_LEVEL'])
        app.logger.addHandler(mail_handler)
        