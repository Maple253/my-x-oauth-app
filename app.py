import os
from flask import Flask, redirect, url_for, session, request
import tweepy # مكتبة Tweepy للتفاعل مع X API

app = Flask(__name__)
# هذا مفتاح سري يستخدمه Flask لتشفير بيانات الجلسة. غيره بقيمة عشوائية قوية!
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

# مفاتيح API الخاصة بـ X (توفرها كمتغيرات بيئة لأمان أفضل)
CONSUMER_KEY = os.environ.get("X_CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("X_CONSUMER_SECRET")

# التحقق من وجود المفاتيح
if not all([CONSUMER_KEY, CONSUMER_SECRET]):
    print("Error: X_CONSUMER_KEY and X_CONSUMER_SECRET environment variables must be set.")
    # يمكنك توجيه المستخدم لصفحة خطأ أو إيقاف التطبيق
    exit(1) # إيقاف التطبيق مؤقتًا لعدم وجود المفاتيح

# تهيئة كائن OAuthHandler
# هذه هي النقطة التي ستبدأ منها عملية التفويض OAuth 1.0a
oauth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

@app.route('/')
def home():
    return """
    <h1>أهلاً بك في تطبيق X OAuth!</h1>
    <p>هذا تطبيق بسيط لإظهار كيفية عمل تفويض X.</p>
    <p><a href="/start_oauth">ابدأ عملية تفويض X</a></p>
    """

@app.route('/start_oauth')
def start_oauth():
    # الخطوة 1: الحصول على Request Token
    try:
        # تأكد من أن الـ callback_uri يتطابق تمامًا مع ما قمت بتعيينه في X Developer Portal
        # Render سيوفر متغير البيئة HOST لعنوان URL
        callback_uri = f"{request.url_root.rstrip('/')}/callback"
        print(f"Using callback URI: {callback_uri}") # للمساعدة في تصحيح الأخطاء

        redirect_url = oauth.get_authorization_url(signin_with_twitter=True)
        session['request_token'] = oauth.request_token

        # الخطوة 2: إعادة توجيه المستخدم إلى صفحة تفويض X
        return redirect(redirect_url)
    except tweepy.TweepyException as e:
        return f"حدث خطأ أثناء بدء عملية OAuth: {e}<br>الرجاء التأكد من صحة مفاتيح X API وCallback URI.", 500

@app.route('/callback')
def callback():
    # الخطوة 3: معالجة الاستجابة من X بعد موافقة المستخدم
    verifier = request.args.get('oauth_verifier')
    if not verifier:
        return "لم يتم توفير OAuth Verifier.", 400

    request_token = session.get('request_token')
    if not request_token:
        return "لم يتم العثور على Request Token في الجلسة.", 400

    # إعادة تهيئة OAuthHandler باستخدام Request Token المستعاد
    # هذا مهم لأن get_access_token يحتاج إلى Request Token الأصلي.
    oauth_callback_handler = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_callback_handler.request_token = request_token

    try:
        # الخطوة 4: تبادل Request Token و Verifier بـ Access Token و Access Token Secret
        access_token, access_token_secret = oauth_callback_handler.get_access_token(verifier)

        # حفظ Access Token و Access Token Secret في الجلسة أو قاعدة البيانات
        # (في هذا المثال، سنحفظهما في الجلسة فقط، لكن في تطبيق حقيقي يجب حفظهما بشكل آمن)
        session['access_token'] = access_token
        session['access_token_secret'] = access_token_secret

        # الآن يمكنك استخدام access_token و access_token_secret للتفاعل مع X API
        # مثال: تهيئة API object
        api = tweepy.API(oauth_callback_handler)

        # هنا يمكنك استدعاء API لتغيير صورة البروفايل أو غيرها
        # مثال بسيط: جلب معلومات المستخدم
        user = api.verify_credentials()
        return f"""
        <h1>تفويض X تم بنجاح!</h1>
        <p>مرحباً بك، {user.name}!</p>
        <p>لقد حصلنا على Access Token الخاص بك (تم حفظه في الجلسة).</p>
        <p>يمكنك الآن استخدام هذا الرمز للتفاعل مع X API.</p>
        <p><strong>ملاحظة:</strong> في تطبيق حقيقي، يجب حفظ Access Token و Secret بأمان في قاعدة بيانات.</p>
        """

    except tweepy.TweepyException as e:
        return f"حدث خطأ أثناء الحصول على Access Token: {e}<br>الرجاء المحاولة مرة أخرى.", 500

if __name__ == '__main__':
    # تأكد من أن FLASK_SECRET_KEY ليس قيمته الافتراضية "supersecretkey" في بيئة الإنتاج
    # Render سيوفر المنفذ عبر متغير البيئة PORT
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
