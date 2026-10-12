# مدل‌های ترجمهٔ آفلاین (ML Kit) — منبع دانلود، متادیتا و نصب

این سند توضیح می‌دهد ماژول `fastdic_desktop/mlkit_models.py` از کجا مدل می‌گیرد، چطور سالم‌بودنش را
بررسی می‌کند و کجا نصب می‌کند. تحلیل پایه (کلاس `zzu`، فیلدهای متادیتا و ساختار بسته) از بررسی
پروژهٔ اندرویدی [melonityhub/offdic](https://github.com/melonityhub/offdic) برداشته شده است
(`docs/OFFLINE_TRANSLATION_MODELS_FA.md` آن مخزن).

## ۱) چه مدل‌هایی؟

اپ از **ML Kit On-device Translation** (`com.google.mlkit:translate`) استفاده می‌کند؛ این مدل‌ها
**همان مدل‌های حالت آفلاین Google Translate** هستند. هر مدل فقط **انگلیسی ⇄ یک زبان** آموزش دیده است
و هر بسته هر دو جهت را با هم دارد (مثلاً بستهٔ `en_fa` شامل `translate_enfa` و `translate_faen` است)،
پس انتخاب یک زبان مقصد = فقط یک دانلود. فهرست کامل ۵۸ زبان بستهٔ کیفیت بالا (`PKG_HIGH`) در
`fastdic_desktop/data/translate_models_metadata.json` آمده — که عین فایل `res/raw/translate_models_metadata.json`
نسخهٔ ۱۷.۰.x خود SDK است (نسخهٔ قالب `V=5`).

## ۲) منبع دانلود — دقیقاً مثل ML Kit

در کلاس داخلی `com.google.mlkit.nl.translate.internal.zzu` دو قالب نشانی هست:

```
https://dl.google.com/translate/offline/%s/high/%s/%s.zip
https://redirector.gvt1.com/edgedl/translate/offline/%s/high/%s/%s.zip
```

جای‌گذارها: `(v<V>، r<RV>، <pair>)` — برای فارسی:

```
https://dl.google.com/translate/offline/v5/high/r29/en_fa.zip
```

| بخش آدرس | معنی | مقدار برای فارسی |
|---|---|---|
| `v5` | نسخهٔ قالب متادیتا (`"V": 5`) | ۵ |
| `high` | ردهٔ بستهٔ کیفیت بالا (`PKG_HIGH`) | high |
| `r29` | ریویژن مدل (`"RV": 29` برای هر زوج از متادیتا) | ۲۹ |
| `en_fa.zip` | نام زوج زبان (دو کد مرتب‌شدهٔ الفبایی) | `en_fa` |

برنامه اول `dl.google.com` را امتحان می‌کند و در خطا به `redirector.gvt1.com` برمی‌گردد.

## ۳) متادیتا و راستی‌آزمایی (DL_SZ / SZ / RV / HASH)

برای هر زوج، متادیتای SDK این فیلدها را دارد (نمونهٔ فارسی):

| کلید | مقدار | معنی |
|---|---|---|
| `DL_SZ` | ۳۲٬۴۰۵٬۴۲۸ بایت (~۳۰.۹ مگابایت) | حجم فایل ZIP دانلودی — همان عددی که در UI نمایش داده می‌شود |
| `SZ` | ۳۹٬۹۲۸٬۸۷۶ بایت (~۳۸.۱ مگابایت) | حجم بازشدهٔ مدل |
| `RV` | ۲۹ | ریویژن مدل |
| `HASH` | `39603ed8…72a46485c` | **SHA-256 بستهٔ ZIP دانلودی** |

مثل خود ML Kit (کلاس `ModelUtils.zza`)، هش فایل دریافتی با `HASH` مقایسه می‌شود و در صورت مغایرت
بسته نصب نمی‌شود — معادل خطای ۱۰۲ «Hash does not match with expected» در SDK. ساختار داخلی بسته هم
اعتبارسنجی می‌شود: `translation_model.pb`، هفت فایل `.bipe` با امضای `BIPE` و منابع واژگان
(`resources/*`) برای هر دو جهت.

## ۴) محل نصب (کش محلی) و استفادهٔ آفلاین

بسته در مسیری هم‌ساختار با اندروید نصب می‌شود:

```
<models_root>/en_fa/
├── translate_enfa/   ← انگلیسی → فارسی (translation_model.pb + *.bipe + resources/)
└── translate_faen/   ← فارسی → انگلیسی
```

`<models_root>` پیش‌فرض `~/.fastdic_desktop/models/` است و از ⚙ تنظیمات قابل تغییر است. پس از نصب،
همه‌چیز از همین کش محلی خوانده می‌شود؛ در اجراهای بعدی هیچ اینترنتی لازم نیست و فقط اگر زبان تازه‌ای
انتخاب شود دانلود جدید انجام می‌شود. حذف مدل هم در همان پنجره (دکمهٔ «حذف») پوشهٔ زوج را پاک می‌کند.
