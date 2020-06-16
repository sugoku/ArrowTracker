from configparser import ConfigParser

parser = ConfigParser()
parser.read('settings.ini')

class Config():
    SECRET_KEY = parser.get('settings', 'SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = parser.get('sql', 'SQLALCHEMY_DATABASE_URI')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = parser.get('email', 'email')
    MAIL_PASSWORD = parser.get('email', 'password')

    RECAPTCHA_ENABLED = parser.get('recaptcha', 'enable')
    RECAPTCHA_PUBLIC_KEY = parser.get('recaptcha', 'PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = parser.get('recaptcha', 'PRIVATE_KEY')
    # RECAPTCHA_PARAMETERS = {'hl': 'zh', 'render': 'explicit'}
    # RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}

    # Flask-User settings
    USER_APP_NAME = 'ArrowTracker'      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = 'noreply@example.com'

    USER_ENABLE_CONFIRM_EMAIL = False
    USER_ENABLE_CHANGE_USERNAME = False

    # USER_CHANGE_PASSWORD_URL = '/user/change-password'
    # USER_CHANGE_USERNAME_URL = '/user/change-username'
    USER_CONFIRM_EMAIL_URL = '/confirm-email/<token>'
    USER_EDIT_USER_PROFILE_URL = '/dashboard'
    # USER_EMAIL_ACTION_URL = '/user/email/<id>/<action>'
    USER_FORGOT_PASSWORD_URL = '/reset_password'
    # USER_INVITE_USER_URL = '/user/invite'
    USER_LOGIN_URL = '/login'
    USER_LOGOUT_URL = '/logout'
    # USER_MANAGE_EMAILS_URL = '/user/manage-emails'
    USER_REGISTER_URL = '/register'
    USER_RESEND_EMAIL_CONFIRMATION_URL = '/user/resend-email-confirmation'
    USER_RESET_PASSWORD_URL = '/reset_password/<token>'
    # USER_CHANGE_PASSWORD_TEMPLATE = 'change_password.html'
    # USER_CHANGE_USERNAME_TEMPLATE = 'change_username.html'
    USER_EDIT_USER_PROFILE_TEMPLATE = 'dashboard.html'
    USER_FORGOT_PASSWORD_TEMPLATE = 'reset_request.html'
    # USER_INVITE_USER_TEMPLATE = 'invite_user.html'
    USER_LOGIN_TEMPLATE = 'login.html'
    # USER_LOGIN_AUTH0_TEMPLATE = 'login_auth0.html'
    # USER_MANAGE_EMAILS_TEMPLATE = 'manage_emails.html'
    USER_REGISTER_TEMPLATE = 'register.html'
    # USER_RESEND_CONFIRM_EMAIL_TEMPLATE = 'resend_confirm_email.html'
    USER_RESET_PASSWORD_TEMPLATE = 'reset_request.html'
    # USER_CONFIRM_EMAIL_TEMPLATE = 'emails/confirm_email'
    # USER_INVITE_USER_EMAIL_TEMPLATE = 'emails/invite_user'
    # USER_PASSWORD_CHANGED_EMAIL_TEMPLATE = 'emails/password_changed'
    # USER_REGISTERED_EMAIL_TEMPLATE = 'emails/registered'
    # USER_RESET_PASSWORD_EMAIL_TEMPLATE = 'emails/reset_password'
    # USER_USERNAME_CHANGED_EMAIL_TEMPLATE = 'emails/username_changed'
    USER_UNAUTHENTICATED_ENDPOINT = 'user.login'

def GetChangelog():
    with open('changelog.txt') as f:
        log = f.read()
    return log
