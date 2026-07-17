import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import { brand } from './branding'

export type Locale = 'en' | 'ar'

const localeStorageKey = 'baytak-locale'

const arabic: Record<string, string> = {
  'Open navigation': 'فتح القائمة',
  'Close navigation': 'إغلاق القائمة',
  'Collapse navigation': 'طيّ القائمة',
  'Expand navigation': 'توسيع القائمة',
  'Language selector': 'اختيار اللغة',
  'Sign out': 'تسجيل الخروج',
  'Workspace': 'مساحة العمل',
  'Overview': 'نظرة عامة',
  'Donors': 'المتبرعون',
  'Donations': 'التبرعات',
  'Donation types': 'أنواع التبرعات',
  'Custody': 'العُهد',
  'Approvals': 'الموافقات',
  'Reports': 'التقارير',
  'Scheduled reports': 'التقارير المجدولة',
  'Users': 'المستخدمون',
  'Settings': 'الإعدادات',
  'Loading data…': 'جارٍ تحميل البيانات…',
  'Loading your workspace…': 'جارٍ تحميل مساحة العمل…',
  'Close': 'إغلاق',
  'Cancel': 'إلغاء',
  'Edit': 'تعديل',
  'Save changes': 'حفظ التغييرات',
  'Saving…': 'جارٍ الحفظ…',
  'Create': 'إنشاء',
  'Actions': 'الإجراءات',
  'Status': 'الحالة',
  'Active': 'نشط',
  'Inactive': 'غير نشط',
  'active': 'نشط',
  'inactive': 'غير نشط',
  'confirmed': 'مؤكد',
  'cancelled': 'ملغى',
  'refunded': 'مسترد',
  'pending': 'قيد الانتظار',
  'approved': 'موافق عليه',
  'rejected': 'مرفوض',
  'closed': 'مغلق',
  'Staff sign in': 'تسجيل دخول الموظفين',
  'Community-first giving': 'عطاء يضع المجتمع أولاً',
  'Every act of generosity deserves a clear purpose.': 'كل عمل من أعمال العطاء يستحق هدفاً واضحاً.',
  'We connect thoughtful donors with practical community support—food, medical aid, education, and urgent relief—while keeping every contribution accountable.': 'نربط المتبرعين الكرام بالدعم العملي للمجتمع — الغذاء، والمساعدة الطبية، والتعليم، والإغاثة العاجلة — مع ضمان توثيق كل مساهمة.',
  'Get in touch': 'تواصل معنا',
  'See our impact': 'شاهد أثرنا',
  'active programs': 'برامج نشطة',
  'traceable giving': 'عطاء قابل للتتبع',
  'Local': 'محلي',
  'community focus': 'تركيز مجتمعي',
  'What we support': 'ما ندعمه',
  'Practical care where it matters most.': 'رعاية عملية حيث تكون الحاجة أكبر.',
  'Our programmes are shaped by local needs and delivered with dignity.': 'تتشكّل برامجنا وفق الاحتياجات المحلية وتُقدّم بكرامة.',
  'Food & essentials': 'الغذاء والاحتياجات الأساسية',
  'Reliable food parcels and essential supplies for families facing hardship.': 'سلال غذائية موثوقة واحتياجات أساسية للعائلات التي تواجه صعوبات.',
  'Education': 'التعليم',
  'Learning materials and opportunity for children to thrive.': 'مواد تعليمية وفرص تساعد الأطفال على الازدهار.',
  'Medical support': 'الدعم الطبي',
  'Urgent assistance with treatment, medicine, and recovery.': 'مساعدة عاجلة للعلاج والدواء والتعافي.',
  'Let’s make an impact': 'لنصنع أثراً',
  'Have a question or want to support a program?': 'هل لديك سؤال أو ترغب في دعم برنامج؟',
  'Welcome back': 'مرحباً بعودتك',
  'Good work starts with a clear record.': 'العمل الجيد يبدأ بسجل واضح.',
  'Sign in to manage the people, gifts, and funds entrusted to your organisation.': 'سجّل الدخول لإدارة الأشخاص والتبرعات والأموال الموكلة إلى مؤسستك.',
  'Secure sign in': 'تسجيل دخول آمن',
  'Access your workspace': 'الوصول إلى مساحة العمل',
  'Use the administrator account configured for this environment.': 'استخدم حساب المسؤول المُعدّ لهذه البيئة.',
  'Email': 'البريد الإلكتروني',
  'Password': 'كلمة المرور',
  'Signing in…': 'جارٍ تسجيل الدخول…',
  'Sign in': 'تسجيل الدخول',
  'Forgot password?': 'هل نسيت كلمة المرور؟',
  'Account recovery': 'استعادة الحساب',
  'Keep access to the work that matters.': 'حافظ على الوصول إلى العمل المهم.',
  'Use your organisation email to securely restore access to your account.': 'استخدم بريد مؤسستك لاستعادة الوصول إلى حسابك بأمان.',
  'Password reset': 'إعادة تعيين كلمة المرور',
  'Reset your password': 'إعادة تعيين كلمة المرور',
  'We will email a secure, time-limited reset link to your organisation address.': 'سنرسل رابطاً آمناً ومحدود المدة لإعادة التعيين إلى بريد مؤسستك.',
  'Check your email': 'تحقق من بريدك الإلكتروني',
  'Sending…': 'جارٍ الإرسال…',
  'Send reset link': 'إرسال رابط إعادة التعيين',
  'Back to sign in': 'العودة إلى تسجيل الدخول',
  'Choose a new password': 'اختر كلمة مرور جديدة',
  'Set a new password': 'تعيين كلمة مرور جديدة',
  'Confirm new password': 'تأكيد كلمة المرور الجديدة',
  'The two passwords do not match.': 'كلمتا المرور غير متطابقتين.',
  'This password reset link is invalid or incomplete.': 'رابط إعادة تعيين كلمة المرور غير صالح أو غير مكتمل.',
  'Updating…': 'جارٍ التحديث…',
  'Password updated': 'تم تحديث كلمة المرور',
  'Password updated. Please sign in with your new password.': 'تم تحديث كلمة المرور. يرجى تسجيل الدخول بكلمة المرور الجديدة.',
  'If an active account uses that email, a password reset link has been sent.': 'إذا كان هناك حساب نشط يستخدم هذا البريد، فقد تم إرسال رابط إعادة تعيين كلمة المرور.',
  'Operations overview': 'نظرة عامة على العمليات',
  'Good morning.': 'صباح الخير.',
  'Here is what is happening across your charity.': 'إليك ما يحدث في مؤسستك الخيرية.',
  'day': 'يوم',
  'week': 'أسبوع',
  'month': 'شهر',
  'Donations received': 'التبرعات المستلمة',
  'confirmed in period': 'مؤكدة خلال الفترة',
  'Active donors': 'المتبرعون النشطون',
  'gave in this period': 'تبرعوا خلال هذه الفترة',
  'Custody available': 'العُهدة المتاحة',
  'after approved expenses': 'بعد المصروفات المعتمدة',
  'Pending approvals': 'الموافقات المعلقة',
  'awaiting a decision': 'بانتظار قرار',
  'Giving by fund': 'التبرعات حسب الصندوق',
  'Confirmed donations for the selected period.': 'التبرعات المؤكدة للفترة المحددة.',
  'No donations yet': 'لا توجد تبرعات بعد',
  'Donation totals will appear here.': 'ستظهر إجماليات التبرعات هنا.',
  'Recently active donors': 'المتبرعون النشطون مؤخراً',
  'People who gave most recently.': 'الأشخاص الذين تبرعوا مؤخراً.',
  'No activity yet': 'لا يوجد نشاط بعد',
  'New donors will appear here.': 'سيظهر المتبرعون الجدد هنا.',
  'Donation distribution': 'توزيع التبرعات',
  'See the balance of support across active funds.': 'شاهد توازن الدعم بين الصناديق النشطة.',
  'No donation data yet': 'لا توجد بيانات تبرعات بعد',
  'Record a donation to start seeing distribution.': 'سجّل تبرعاً لعرض التوزيع.',
  'Relationships': 'العلاقات',
  'Keep complete, searchable records of the people who support your work.': 'احتفظ بسجلات كاملة وقابلة للبحث للأشخاص الذين يدعمون عملك.',
  'Add donor': 'إضافة متبرع',
  'Search by donor name': 'ابحث باسم المتبرع',
  'Phone': 'الهاتف',
  'Donor ID': 'معرّف المتبرع',
  'Clear filters': 'مسح عوامل التصفية',
  'Donor': 'المتبرع',
  'Giving to date': 'إجمالي التبرعات',
  'Last fund': 'آخر صندوق',
  'Added': 'تاريخ الإضافة',
  'Archive': 'أرشفة',
  'No donors found': 'لم يتم العثور على متبرعين',
  'Adjust the filters or add a donor to begin.': 'عدّل عوامل التصفية أو أضف متبرعاً للبدء.',
  'Edit donor': 'تعديل متبرع',
  'Add a donor': 'إضافة متبرع',
  'First name': 'الاسم الأول',
  'Last name': 'اسم العائلة',
  'Primary phone': 'الهاتف الرئيسي',
  'City': 'المدينة',
  'Address': 'العنوان',
  'Country': 'الدولة',
  'Save donor': 'حفظ المتبرع',
  'Create donor': 'إنشاء متبرع',
  'Fund setup': 'إعداد الصناديق',
  'Define the funds and causes donors can support.': 'حدّد الصناديق والمجالات التي يمكن للمتبرعين دعمها.',
  'Add type': 'إضافة نوع',
  'No description supplied for this fund.': 'لا يوجد وصف لهذا الصندوق.',
  'Deactivate': 'إلغاء التفعيل',
  'No donation types': 'لا توجد أنواع تبرعات',
  'Create a fund before recording a donation.': 'أنشئ صندوقاً قبل تسجيل تبرع.',
  'Edit donation type': 'تعديل نوع التبرع',
  'Add donation type': 'إضافة نوع تبرع',
  'Fund name': 'اسم الصندوق',
  'Description': 'الوصف',
  'Active and available for new donations': 'نشط ومتاح للتبرعات الجديدة',
  'Create type': 'إنشاء نوع',
  'Income records': 'سجلات الإيرادات',
  'Record contributions accurately and keep every receipt traceable.': 'سجّل المساهمات بدقة وحافظ على إمكانية تتبع كل إيصال.',
  'Record donation': 'تسجيل تبرع',
  'All donors': 'كل المتبرعين',
  'All types': 'كل الأنواع',
  'All statuses': 'كل الحالات',
  'Confirmed': 'مؤكد',
  'Cancelled': 'ملغى',
  'Refunded': 'مسترد',
  'Minimum amount': 'الحد الأدنى للمبلغ',
  'Maximum amount': 'الحد الأقصى للمبلغ',
  'From': 'من',
  'To': 'إلى',
  'Date': 'التاريخ',
  'Fund': 'الصندوق',
  'Receipt': 'الإيصال',
  'Amount': 'المبلغ',
  'No donations found': 'لم يتم العثور على تبرعات',
  'Adjust the filters or record a donation.': 'عدّل عوامل التصفية أو سجّل تبرعاً.',
  'Edit donation': 'تعديل تبرع',
  'Choose a donor': 'اختر متبرعاً',
  'Choose a fund': 'اختر صندوقاً',
  'Currency': 'العملة',
  'Received at': 'تاريخ الاستلام',
  'Payment method': 'طريقة الدفع',
  'Record status': 'حالة السجل',
  'Receipt number': 'رقم الإيصال',
  'Save donation': 'حفظ التبرع',
  'Expense funds': 'أموال العُهد',
  'Assign funds, monitor available balance, and review submitted expenses.': 'عيّن الأموال، وراقب الرصيد المتاح، وراجع المصروفات المقدمة.',
  'View the funds assigned to you and their remaining balance.': 'اعرض الأموال المسندة إليك ورصيدها المتبقي.',
  'Assign custody': 'تعيين عُهدة',
  'Assigned amount': 'المبلغ المعيّن',
  'Available': 'المتاح',
  'Recipient': 'المستلم',
  'Assigned by': 'عيّن بواسطة',
  'Assigned': 'تاريخ التعيين',
  'Expenses': 'المصروفات',
  'No assignment description.': 'لا يوجد وصف للعُهدة.',
  'Submit expense': 'تقديم مصروف',
  'No custody assigned': 'لا توجد عُهد مسندة',
  'Assign custody to a user when they need funds for expenses.': 'عيّن عُهدة لمستخدم عندما يحتاج إلى أموال للمصروفات.',
  'An assigned fund will appear here.': 'سيظهر الصندوق المعيّن هنا.',
  'Choose a user': 'اختر مستخدماً',
  'Assigned at': 'تاريخ التعيين',
  'Purpose or usage guidance': 'الغرض أو إرشادات الاستخدام',
  'Save custody': 'حفظ العُهدة',
  'Submit custody expense': 'تقديم مصروف عُهدة',
  'Expense title': 'عنوان المصروف',
  'Expense date': 'تاريخ المصروف',
  'Submit for approval': 'إرسال للموافقة',
  'Financial review': 'المراجعة المالية',
  'Review submitted expenses before they reduce available custody.': 'راجع المصروفات المقدمة قبل أن تخصم من العُهدة المتاحة.',
  'Expense': 'المصروف',
  'Assignment': 'العُهدة',
  'Submitted': 'تاريخ التقديم',
  'Decision': 'القرار',
  'Reject': 'رفض',
  'Approve': 'موافقة',
  'Nothing awaiting approval': 'لا يوجد ما ينتظر الموافقة',
  'New expense submissions will appear here.': 'ستظهر طلبات المصروفات الجديدة هنا.',
  'Access control': 'التحكم في الوصول',
  'Manage team members and their access to financial records.': 'أدر أعضاء الفريق وصلاحيات وصولهم إلى السجلات المالية.',
  'Add user': 'إضافة مستخدم',
  'Team member': 'عضو الفريق',
  'Roles': 'الأدوار',
  'Created': 'تاريخ الإنشاء',
  'Add team member': 'إضافة عضو فريق',
  'Create user': 'إنشاء مستخدم',
  'Your account': 'حسابك',
  'Profile & settings': 'الملف الشخصي والإعدادات',
  'Update your contact details and keep your account secure.': 'حدّث بيانات الاتصال وحافظ على أمان حسابك.',
  'Personal details': 'البيانات الشخصية',
  'How your name appears on operational records.': 'كيف يظهر اسمك في السجلات التشغيلية.',
  'Phone number': 'رقم الهاتف',
  'Security': 'الأمان',
  'Use a unique password with at least 8 characters.': 'استخدم كلمة مرور فريدة من 8 أحرف على الأقل.',
  'Current password': 'كلمة المرور الحالية',
  'New password': 'كلمة المرور الجديدة',
  'Update password': 'تحديث كلمة المرور',
  'Your profile was updated.': 'تم تحديث ملفك الشخصي.',
  'Password updated. Please sign in again to continue.': 'تم تحديث كلمة المرور. يرجى تسجيل الدخول مرة أخرى للمتابعة.',
  'Insights & exports': 'الإحصاءات والتصدير',
  'Generate a CSV export for a specific reporting period.': 'أنشئ ملف CSV لفترة تقارير محددة.',
  'Manual export': 'تصدير يدوي',
  'Build a time-bound report': 'إنشاء تقرير لفترة زمنية',
  'Choose the report contents and a start/end date. The exported CSV includes only records in that reporting window.': 'اختر محتوى التقرير وتاريخ البداية والنهاية. يتضمن ملف CSV السجلات ضمن فترة التقرير فقط.',
  'Report contents': 'محتوى التقرير',
  'Donation ledger': 'سجل التبرعات',
  'Donor summary': 'ملخص المتبرعين',
  'Custody assignments': 'تعيينات العُهد',
  'Start date': 'تاريخ البداية',
  'End date': 'تاريخ النهاية',
  'Choose both dates before generating a report.': 'اختر التاريخين قبل إنشاء التقرير.',
  'Generating…': 'جارٍ الإنشاء…',
  'Generate CSV': 'إنشاء CSV',
  'Generated reports': 'التقارير المنشأة',
  'Files are kept in the local application report volume.': 'تُحفظ الملفات في وحدة تخزين التقارير المحلية للتطبيق.',
  'Download': 'تنزيل',
  'No reports generated': 'لا توجد تقارير منشأة',
  'Your generated files will appear here.': 'ستظهر ملفاتك المنشأة هنا.',
  'Automated delivery': 'تسليم آلي',
  'Create recurring CSV reports and send them through your configured SMTP server.': 'أنشئ تقارير CSV متكررة وأرسلها عبر خادم SMTP المُعدّ.',
  'Schedule report': 'جدولة تقرير',
  'Run now': 'تشغيل الآن',
  'Name': 'الاسم',
  'Report': 'التقرير',
  'Window': 'الفترة',
  'Recipients': 'المستلمون',
  'Next run': 'التشغيل القادم',
  'Disable': 'تعطيل',
  'No scheduled reports': 'لا توجد تقارير مجدولة',
  'Schedule a recurring report for finance or leadership.': 'جدوِل تقريراً متكرراً للمالية أو الإدارة.',
  'Edit scheduled report': 'تعديل التقرير المجدول',
  'Schedule a report': 'جدولة تقرير',
  'Schedule name': 'اسم الجدول',
  'Frequency': 'التكرار',
  'Weekly': 'أسبوعي',
  'Monthly': 'شهري',
  'Yearly': 'سنوي',
  'Reporting window': 'فترة التقرير',
  'Previous 7 days': 'الـ 7 أيام السابقة',
  'Previous 30 days': 'الـ 30 يوماً السابقة',
  'Previous 365 days': 'الـ 365 يوماً السابقة',
  'Email recipients': 'البريد الإلكتروني للمستلمين',
  'Active schedule': 'جدول نشط',
  'Create schedule': 'إنشاء جدول',
  'SMTP delivery uses the': 'إرسال SMTP يستخدم قيم',
  'values in `.env`. Use': 'الموجودة في `.env`. استخدم',
  'to test a schedule immediately.': 'لاختبار الجدول فوراً.',
  'About us': 'من نحن',
  'Our projects': 'مشاريعنا',
  'Contact': 'تواصل معنا',
  'Together, We Restore Hope.': 'معا، نُعيد الأمل.',
  'Every donation creates a better future. Baytak Foundation brings people together around practical, compassionate community support.': 'كل تبرع يصنع مستقبلاً أفضل. تجمع مؤسسة بيتك الناس حول دعم مجتمعي عملي ورحيم.',
  'Donate': 'تبرع',
  'Our Projects': 'مشاريعنا',
  'Become a Volunteer': 'كن متطوعاً',
  'About Us': 'من نحن',
  'Online donation and volunteer sign-up channels are being prepared. Contact us directly to take part.': 'يجري تجهيز قنوات التبرع والتسجيل للتطوع عبر الإنترنت. تواصلوا معنا مباشرةً للمشاركة.',
  'Who we are': 'من نحن',
  'Direct help, delivered with dignity.': 'مساعدة مباشرة تُقدَّم بكرامة.',
  'Baytak Foundation is a community-focused charitable initiative. Its publicly visible work centres on aid distribution, volunteer activities, charity campaigns, and documenting support reaching beneficiaries.': 'مؤسسة بيتك مبادرة خيرية تركز على المجتمع. يرتكز عملها الظاهر للعامة على توزيع المساعدات، والأنشطة التطوعية، والحملات الخيرية، وتوثيق وصول الدعم إلى المستفيدين.',
  'Why we exist': 'لماذا نعمل',
  'To turn generosity into practical support for people and communities facing everyday hardship.': 'لتحويل العطاء إلى دعم عملي للأفراد والمجتمعات التي تواجه صعوبات يومية.',
  'What makes us different': 'ما الذي يميزنا',
  'We put people first, focus on direct action, and aim to show the human impact behind every contribution.': 'نضع الإنسان أولاً، ونركز على العمل المباشر، ونسعى لإظهار الأثر الإنساني خلف كل مساهمة.',
  'Where we work': 'أين نعمل',
  'Current regions and formal programme locations are being verified and will be published here.': 'يجري التحقق من المناطق الحالية ومواقع البرامج الرسمية، وسيتم نشرها هنا.',
  'Mission': 'رسالتنا',
  'Mobilise compassionate support for people who need it most.': 'حشد الدعم الرحيم للأشخاص الأكثر حاجة.',
  'We aim to connect donors, volunteers, and local communities through transparent, practical charitable action.': 'نسعى لربط المتبرعين والمتطوعين والمجتمعات المحلية عبر عمل خيري عملي وشفاف.',
  'Vision': 'رؤيتنا',
  'A future where every community can meet essential needs with hope.': 'مستقبل تستطيع فيه كل المجتمعات تلبية احتياجاتها الأساسية بأمل.',
  'Our long-term ambition is sustained community wellbeing, stronger local participation, and a culture of accountable giving.': 'طموحنا طويل المدى هو رفاه مجتمعي مستدام، ومشاركة محلية أقوى، وثقافة عطاء خاضع للمساءلة.',
  'Core values': 'قيمنا الأساسية',
  'The principles behind every act of support.': 'المبادئ التي تقف خلف كل عمل داعم.',
  'Transparency': 'الشفافية',
  'Clear communication about how support is delivered.': 'تواصل واضح حول كيفية تقديم الدعم.',
  'Compassion': 'الرحمة',
  'People are treated with care, empathy, and respect.': 'يُعامل الناس بعناية وتعاطف واحترام.',
  'Dignity': 'الكرامة',
  'Aid protects the choices and worth of every beneficiary.': 'تحمي المساعدة خيارات وكرامة كل مستفيد.',
  'Accountability': 'المساءلة',
  'We take responsibility for every contribution entrusted to us.': 'نتحمل مسؤولية كل مساهمة اؤتُمِنّا عليها.',
  'Community': 'المجتمع',
  'Local people and volunteers are part of the solution.': 'أفراد المجتمع والمتطوعون جزء من الحل.',
  'Sustainability': 'الاستدامة',
  'We seek support that strengthens communities beyond one moment.': 'نسعى إلى دعم يقوّي المجتمعات لما بعد لحظة واحدة.',
  'Our impact': 'أثرنا',
  'Every figure represents a person, family, and community.': 'كل رقم يمثل شخصاً وعائلةً ومجتمعاً.',
  'Verified impact figures will be published as the foundation’s reporting information becomes available.': 'سيتم نشر أرقام الأثر الموثقة عند توفر معلومات تقارير المؤسسة.',
  'Families helped': 'العائلات المستفيدة',
  'Food packages distributed': 'السلال الغذائية الموزعة',
  'Water projects': 'مشاريع المياه',
  'Volunteers': 'المتطوعون',
  'Regions served': 'المناطق المخدومة',
  'Donations delivered': 'التبرعات التي تم إيصالها',
  'Impact figure to be verified': 'رقم الأثر قيد التحقق',
  'Current campaigns': 'الحملات الحالية',
  'Campaign information is being prepared.': 'يجري إعداد معلومات الحملات.',
  'Verified campaign data pending': 'بيانات الحملة الموثقة قيد الانتظار',
  'Active campaign · details pending': 'حملة نشطة · التفاصيل قيد الإعداد',
  'Emergency Relief': 'الإغاثة العاجلة',
  'Rapid support for people facing urgent hardship.': 'دعم سريع للأشخاص الذين يواجهون ظروفاً صعبة وعاجلة.',
  'Food Security': 'الأمن الغذائي',
  'Helping families access essential food and household supplies.': 'مساعدة العائلات في الوصول إلى الغذاء والاحتياجات المنزلية الأساسية.',
  'Community Care': 'الرعاية المجتمعية',
  'Supporting practical local initiatives with dignity and care.': 'دعم المبادرات المحلية العملية بكرامة وعناية.',
  'Campaign details and donation target to be confirmed.': 'تفاصيل الحملة وهدف التبرعات قيد التأكيد.',
  'Donate to this campaign': 'تبرع لهذه الحملة',
  'Our programs': 'برامجنا',
  'Areas of support we are ready to grow.': 'مجالات الدعم التي نحن مستعدون لتنميتها.',
  'These programme areas reflect the foundation’s visible community-centred work and will be refined as formal programme information is published.': 'تعكس مجالات البرامج هذه العمل المجتمعي الظاهر للمؤسسة، وستُحدّث عند نشر معلومات البرامج الرسمية.',
  'Prepared to respond when a community faces urgent needs.': 'جاهزون للاستجابة عندما يواجه المجتمع احتياجات عاجلة.',
  'Food Aid': 'المساعدات الغذائية',
  'Food parcels and essential supplies for families.': 'سلال غذائية واحتياجات أساسية للعائلات.',
  'Medical Support': 'الدعم الطبي',
  'Help with treatment, medicine, and recovery.': 'مساعدة في العلاج والدواء والتعافي.',
  'Learning resources and opportunities for children.': 'موارد تعليمية وفرص للأطفال.',
  'Orphan Sponsorship': 'كفالة الأيتام',
  'Long-term care and opportunity for children.': 'رعاية طويلة الأمد وفرص للأطفال.',
  'Water Projects': 'مشاريع المياه',
  'Safe water initiatives for communities in need.': 'مبادرات مياه آمنة للمجتمعات المحتاجة.',
  'Ramadan & Eid Campaigns': 'حملات رمضان والعيد',
  'Seasonal giving with meaningful local impact.': 'عطاء موسمي بأثر محلي ملموس.',
  'Success stories': 'قصص النجاح',
  'Stories of change will live here.': 'ستُروى قصص التغيير هنا.',
  'With beneficiary consent and verified information, this area will share the people and communities behind the work.': 'بموافقة المستفيدين ومعلومات موثقة، ستشارك هذه المساحة قصص الأشخاص والمجتمعات خلف هذا العمل.',
  'Before / after': 'قبل / بعد',
  'From immediate need to renewed stability.': 'من الحاجة العاجلة إلى استقرار متجدد.',
  'Impact stories and documented outcomes are not yet available for publication.': 'قصص الأثر والنتائج الموثقة ليست متاحة للنشر بعد.',
  'Before photo placeholder': 'مساحة مخصصة لصورة قبل',
  'After photo placeholder': 'مساحة مخصصة لصورة بعد',
  'Testimonials': 'الشهادات',
  'Voices from the community.': 'أصوات من المجتمع.',
  '“Testimonial content will be added after verified consent and publication approval.”': '«ستُضاف الشهادات بعد التحقق من الموافقة واعتماد النشر.»',
  '— Placeholder for beneficiary, volunteer, or donor story': '— مساحة مخصصة لقصة مستفيد أو متطوع أو متبرع',
  'Gallery & media': 'المعرض والوسائط',
  'Field moments, photos, and video.': 'لحظات ميدانية وصور ومقاطع فيديو.',
  'Gallery image placeholder': 'مساحة مخصصة لصورة في المعرض',
  'Video placeholder': 'مساحة مخصصة لفيديو',
  'Event photo placeholder': 'مساحة مخصصة لصورة فعالية',
  'Volunteer activity placeholder': 'مساحة مخصصة لصورة نشاط تطوعي',
  'How you can help': 'كيف يمكنك المساعدة',
  'Make meaningful action possible.': 'اجعل العمل المؤثر ممكناً.',
  'Support a campaign or programme when donation channels are published.': 'ادعم حملة أو برنامجاً عند نشر قنوات التبرع.',
  'Ask about donating': 'اسأل عن التبرع',
  'Volunteer': 'تطوع',
  'Offer your time, skills, and local knowledge to community initiatives.': 'قدّم وقتك ومهاراتك ومعرفتك المحلية للمبادرات المجتمعية.',
  'Volunteer with us': 'تطوع معنا',
  'Partner with us': 'كن شريكاً معنا',
  'Build practical partnerships that strengthen community support.': 'ابنِ شراكات عملية تعزز الدعم المجتمعي.',
  'Start a partnership': 'ابدأ شراكة',
  'Trust is built through openness.': 'تُبنى الثقة بالانفتاح.',
  'Formal public reports, policies, registration information, and partner lists were not available at the time this page was prepared. This section is reserved for their publication.': 'لم تكن التقارير العامة الرسمية والسياسات ومعلومات التسجيل وقوائم الشركاء متاحة عند إعداد هذه الصفحة. هذه المساحة مخصصة لنشرها.',
  'Annual reports': 'التقارير السنوية',
  'Financial reports': 'التقارير المالية',
  'Donation process': 'آلية التبرع',
  'Frequently asked questions': 'الأسئلة الشائعة',
  'Policies': 'السياسات',
  'Partners': 'الشركاء',
  'Publication pending': 'النشر قيد الإعداد',
  'News & events': 'الأخبار والفعاليات',
  'Latest updates from Baytak.': 'أحدث أخبار بيتك.',
  'Updates will be published here': 'ستُنشر التحديثات هنا',
  'FIELD UPDATE': 'تحديث ميداني',
  'Community activity update': 'تحديث نشاط مجتمعي',
  'Published updates are currently shared on the foundation’s Facebook page.': 'تُنشر التحديثات المتاحة حالياً على صفحة المؤسسة في فيسبوك.',
  'UPCOMING EVENT': 'فعالية قادمة',
  'Event details to be announced': 'سيُعلن عن تفاصيل الفعالية',
  'Dates, location, and registration information will be added here.': 'ستُضاف التواريخ والموقع ومعلومات التسجيل هنا.',
  'Let’s create a better future together.': 'لنصنع مستقبلاً أفضل معاً.',
  'Reach out to ask about donations, volunteering, partnerships, or the foundation’s community work.': 'تواصلوا معنا للاستفسار عن التبرعات أو التطوع أو الشراكات أو العمل المجتمعي للمؤسسة.',
  'WhatsApp contact to be added': 'سيُضاف رقم واتساب للتواصل',
  'Address and service locations to be added': 'سيُضاف العنوان ومواقع الخدمة',
  'Facebook is currently the foundation’s primary public channel': 'فيسبوك هو القناة العامة الرئيسية للمؤسسة حالياً',
  'How can we help?': 'كيف يمكننا مساعدتك؟',
  'Your name': 'اسمك',
  'Tell us how you would like to support Baytak Foundation': 'أخبرنا كيف تود دعم مؤسسة بيتك',
  'Send message': 'إرسال الرسالة',
  'Form delivery is being configured. Please contact the foundation by email in the meantime.': 'يجري إعداد إرسال النموذج. يرجى التواصل مع المؤسسة عبر البريد الإلكتروني في الوقت الحالي.',
  'Back top': 'العودة إلى الأعلى',
  'Built around compassion, dignity, and accountability.': 'مبني على الرحمة والكرامة والمساءلة.',
}

const english = Object.fromEntries(Object.entries(arabic).map(([key, value]) => [value, key]))

function localizedValue(value: string, locale: Locale) {
  return (locale === 'ar' ? arabic[value] : english[value]) ?? value
}

function localizedText(value: string, locale: Locale) {
  const leading = value.match(/^\s*/)?.[0] ?? ''
  const trailing = value.match(/\s*$/)?.[0] ?? ''
  const text = value.trim()
  const direct = localizedValue(text, locale)
  if (direct !== text) return `${leading}${direct}${trailing}`

  if (locale === 'ar') {
    const donors = text.match(/^(\d+) donors$/)
    if (donors) return `${leading}${donors[1]} متبرع${trailing}`
    const donations = text.match(/^(\d+) donations$/)
    if (donations) return `${leading}${donations[1]} تبرع${trailing}`
    const identifier = text.match(/^ID #(\d+)$/)
    if (identifier) return `${leading}المعرّف #${identifier[1]}${trailing}`
  } else {
    const donors = text.match(/^(\d+) متبرع$/)
    if (donors) return `${leading}${donors[1]} donors${trailing}`
    const donations = text.match(/^(\d+) تبرع$/)
    if (donations) return `${leading}${donations[1]} donations${trailing}`
    const identifier = text.match(/^المعرّف #(\d+)$/)
    if (identifier) return `${leading}ID #${identifier[1]}${trailing}`
  }
  return value
}

function translateSubtree(node: Node, locale: Locale) {
  if (node.nodeType === Node.TEXT_NODE) {
    const translated = localizedText(node.nodeValue ?? '', locale)
    if (translated !== node.nodeValue) node.nodeValue = translated
    return
  }
  if (!(node instanceof HTMLElement) || ['SCRIPT', 'STYLE', 'CODE', 'SVG'].includes(node.tagName)) return

  for (const attribute of ['placeholder', 'aria-label', 'title']) {
    const value = node.getAttribute(attribute)
    if (!value) continue
    const translated = localizedText(value, locale)
    if (translated !== value) node.setAttribute(attribute, translated)
  }
  for (const child of node.childNodes) translateSubtree(child, locale)
}

interface LocaleContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
}

const LocaleContext = createContext<LocaleContextValue | null>(null)

function initialLocale(): Locale {
  const saved = window.localStorage.getItem(localeStorageKey)
  if (saved === 'ar' || saved === 'en') return saved
  return brand.defaultLocale
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(initialLocale)

  useEffect(() => {
    window.localStorage.setItem(localeStorageKey, locale)
    document.documentElement.lang = locale
    document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr'
    document.title = locale === 'ar' ? `${brand.appName} | العربية` : brand.appName

    const root = document.getElementById('root')
    if (!root) return
    translateSubtree(root, locale)
    const observer = new MutationObserver((records) => {
      for (const record of records) {
        if (record.type === 'characterData') translateSubtree(record.target, locale)
        for (const node of record.addedNodes) translateSubtree(node, locale)
      }
    })
    observer.observe(root, { childList: true, characterData: true, subtree: true })
    return () => observer.disconnect()
  }, [locale])

  const value = useMemo(() => ({ locale, setLocale }), [locale])
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
}

export function useLocale() {
  const context = useContext(LocaleContext)
  if (!context) throw new Error('useLocale must be used inside LocaleProvider')
  return context
}

export function LanguageSwitcher() {
  const { locale, setLocale } = useLocale()
  return (
    <div className="language-switcher" aria-label="Language selector">
      <button className={locale === 'en' ? 'selected' : ''} type="button" onClick={() => setLocale('en')}>EN</button>
      <button className={locale === 'ar' ? 'selected' : ''} type="button" onClick={() => setLocale('ar')}>العربية</button>
    </div>
  )
}
