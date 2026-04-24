/**
 * E-TukTukGo i18n — Text Replacement Engine v2
 * Works WITHOUT data-i18n attributes.
 * Scans all text nodes and replaces English → target language.
 * setLang('as') or setLang('hi') translates entire page instantly.
 */
(function(){
'use strict';
var LANG_KEY  = 'etg-lang';
var SUPPORTED = ['en','as','hi'];

var T = {
  /* Navigation */
  'Home':{'as':'মূখপাত','hi':'होम'},
  'My Rides':{'as':'মোৰ যাত্ৰাসমূহ','hi':'मेरी सवारियाँ'},
  'Profile':{'as':'প্ৰফাইল','hi':'प्रोफ़ाइल'},
  'Earnings':{'as':'উপাৰ্জন','hi':'कमाई'},
  'Dashboard':{'as':'ড্যাছব\'ৰ্ড','hi':'डैशबोर्ड'},
  'Logout':{'as':'লগ আউট','hi':'लॉग आउट'},
  'Login':{'as':'লগইন','hi':'लॉगिन'},
  'Sign Up Free':{'as':'বিনামূলীয়া সাইন আপ','hi':'मुफ्त साइन अप'},
  'Driver Hub':{'as':'ড্ৰাইভাৰ হাব','hi':'ड्राइवर हब'},
  'E-TukTukGo':{'as':'ই-টুকটুকগো','hi':'ई-टुकटुकगो'},
  /* Auth */
  'Welcome Back':{'as':'স্বাগতম','hi':'वापस स्वागत है'},
  'Sign in to your account':{'as':'একাউণ্টত প্ৰৱেশ কৰক','hi':'अपने खाते में साइन इन करें'},
  'Join E-TukTukGo':{'as':'ই-টুকটুকগোত যোগ দিয়ক','hi':'ई-टुकटुकगो से जुड़ें'},
  'Book electric rides instantly':{'as':'তাৎক্ষণিক বৈদ্যুতিক যাত্ৰা বুক কৰক','hi':'तुरंत सवारी बुक करें'},
  'Continue with Google':{'as':'গুগলেৰে অব্যাহত ৰাখক','hi':'Google से जारी रखें'},
  'or':{'as':'অথবা','hi':'या'},
  'Full Name':{'as':'সম্পূৰ্ণ নাম','hi':'पूरा नाम'},
  'Email':{'as':'ইমেইল','hi':'ईमेल'},
  'Phone Number':{'as':'ফোন নম্বৰ','hi':'फ़ोन नंबर'},
  'Password':{'as':'পাছৱাৰ্ড','hi':'पासवर्ड'},
  'New Password':{'as':'নতুন পাছৱাৰ্ড','hi':'नया पासवर्ड'},
  'Current Password':{'as':'বৰ্তমান পাছৱাৰ্ড','hi':'वर्तमान पासवर्ड'},
  "Don't have an account?":{'as':'একাউণ্ট নাই?','hi':'खाता नहीं है?'},
  'Already have an account?':{'as':'ইতিমধ্যে একাউণ্ট আছে?','hi':'पहले से खाता है?'},
  'Register here':{'as':'এখানে পঞ্জীয়ন কৰক','hi':'यहाँ रजिस्टर करें'},
  'Log in':{'as':'লগইন কৰক','hi':'लॉगिन करें'},
  'Log In':{'as':'লগইন কৰক','hi':'लॉगिन करें'},
  'Create Account':{'as':'একাউণ্ট বনাওক','hi':'खाता बनाएं'},
  'Driver Login':{'as':'ড্ৰাইভাৰ লগইন','hi':'ड्राइवर लॉगिन'},
  'Join as a Driver':{'as':'ড্ৰাইভাৰ হিচাপে যোগ দিয়ক','hi':'ड्राइवर के रूप में जुड़ें'},
  'Create Driver Account':{'as':'ড্ৰাইভাৰ একাউণ্ট বনাওক','hi':'चालक खाता बनाएं'},
  'Update Password':{'as':'পাছৱাৰ্ড আপডেট কৰক','hi':'पासवर्ड अपडेट करें'},
  'Change Password':{'as':'পাছৱাৰ্ড সলনি কৰক','hi':'पासवर्ड बदलें'},
  /* Homepage */
  '100% Electric · Zero Emissions':{'as':'১০০% বৈদ্যুতিক · শূন্য নিৰ্গমন','hi':'100% इलेक्ट्रिक · शून्य उत्सर्जन'},
  'Book your':{'as':'আপোনাৰ','hi':'अपनी'},
  'electric ride':{'as':'বৈদ্যুতিক যাত্ৰা','hi':'इलेक्ट्रिक सवारी'},
  'in seconds.':{'as':'বুক কৰক।','hi':'बुक करें।'},
  'Find Available TukTuks':{'as':'উপলব্ধ টুকটুক বিচাৰক','hi':'उपलब्ध टुकटुक खोजें'},
  'Drivers Online':{'as':'ড্ৰাইভাৰ অনলাইন','hi':'ड्राइवर ऑनलाइन'},
  'Rides Done':{'as':'যাত্ৰা সম্পন্ন','hi':'सवारियाँ पूर्ण'},
  'CO₂ Emitted':{'as':'CO₂ নিৰ্গমন','hi':'CO₂ उत्सर्जित'},
  '🗺️ Live Driver Map':{'as':'🗺️ লাইভ ড্ৰাইভাৰ মেপ','hi':'🗺️ लाइव चालक मानचित्र'},
  'Expand Map':{'as':'মেপ বিস্তাৰ কৰক','hi':'मानचित्र बड़ा करें'},
  'Collapse':{'as':'সংকুচিত কৰক','hi':'छोटा करें'},
  'My Location':{'as':'মোৰ অৱস্থান','hi':'मेरा स्थान'},
  '🛰️ Satellite':{'as':'🛰️ স্যাটেলাইট','hi':'🛰️ उपग्रह'},
  '🗺️ Street':{'as':'🗺️ ৰাজপথ','hi':'🗺️ सड़क'},
  'Available Drivers':{'as':'উপলব্ধ ড্ৰাইভাৰসকল','hi':'उपलब्ध चालक'},
  'Book':{'as':'বুক কৰক','hi':'बुक करें'},
  'Why Choose Us':{'as':'আমাক কিয় বাছক','hi':'हमें क्यों चुनें'},
  'How It Works':{'as':'কেনেকৈ কাম কৰে','hi':'कैसे काम करता है'},
  /* Booking */
  'Book a Ride':{'as':'এটা যাত্ৰা বুক কৰক','hi':'सवारी बुक करें'},
  'Pickup Location':{'as':'পিকআপ স্থান','hi':'पिकअप स्थान'},
  'Drop-off Location':{'as':'গন্তব্য স্থান','hi':'गंतव्य स्थान'},
  'Booking Type':{'as':'বুকিং প্ৰকাৰ','hi':'बुकिंग प्रकार'},
  'Book Now':{'as':'এতিয়া বুক কৰক','hi':'अभी बुक करें'},
  'Advance':{'as':'আগতীয়া','hi':'अग्रिम'},
  'Hourly':{'as':'ঘণ্টাভিত্তিক','hi':'प्रति घंटे'},
  'Hours':{'as':'ঘণ্টা','hi':'घंटे'},
  'Any available driver':{'as':'যিকোনো উপলব্ধ ড্ৰাইভাৰ','hi':'कोई भी उपलब्ध चालक'},
  'Notes for driver':{'as':'ড্ৰাইভাৰৰ বাবে টোকা','hi':'चालक के लिए नोट'},
  'Estimated Fare':{'as':'আনুমানিক ভাড়া','hi':'अनुमानित किराया'},
  'Confirm Booking':{'as':'বুকিং নিশ্চিত কৰক','hi':'बुकिंग पुष्टि करें'},
  'Distance':{'as':'দূৰত্ব','hi':'दूरी'},
  /* Booking detail */
  'Booking Reference':{'as':'বুকিং ৰেফাৰেন্স','hi':'बुकिंग संदर्भ'},
  '🔴 Live Driver Tracking':{'as':'🔴 লাইভ ড্ৰাইভাৰ ট্ৰেকিং','hi':'🔴 लाइव चालक ट्रैकिंग'},
  'Fare':{'as':'ভাড়া','hi':'किराया'},
  'Payment':{'as':'পেমেন্ট','hi':'भुगतान'},
  'Duration':{'as':'সময়কাল','hi':'अवधि'},
  'Booked':{'as':'বুক কৰা হৈছে','hi':'बुक किया गया'},
  'PICKUP':{'as':'পিকআপ','hi':'पिकअप'},
  'DROP-OFF':{'as':'গন্তব্য','hi':'गंतव्य'},
  'Payment Locked':{'as':'পেমেন্ট লক','hi':'भुगतान बंद'},
  '⏳ Waiting for driver to accept...':{'as':'⏳ ড্ৰাইভাৰৰ অপেক্ষা...','hi':'⏳ चालक की प्रतीक्षा...'},
  'Driver Accepted! Pay Now':{'as':'ড্ৰাইভাৰে গ্ৰহণ কৰিছে! এতিয়া পেমেন্ট কৰক','hi':'चालक ने स्वीकार किया! अभी भुगतान करें'},
  'Payment Complete':{'as':'পেমেন্ট সম্পন্ন','hi':'भुगतान पूर्ण'},
  'Ride Status':{'as':'যাত্ৰাৰ স্থিতি','hi':'सवारी की स्थिति'},
  'Booking Placed':{'as':'বুকিং দিয়া হৈছে','hi':'बुकिंग दी गई'},
  'Driver Accepted':{'as':'ড্ৰাইভাৰে গ্ৰহণ কৰিছে','hi':'चालक ने स्वीकार किया'},
  'Ride In Progress':{'as':'যাত্ৰা চলি আছে','hi':'सवारी जारी है'},
  'Ride Completed':{'as':'যাত্ৰা সম্পন্ন','hi':'सवारी पूर्ण'},
  'Cancel Booking':{'as':'বুকিং বাতিল কৰক','hi':'बुकिंग रद्द करें'},
  'Payment Receipt':{'as':'পেমেন্ট ৰচিদ','hi':'भुगतान रसीद'},
  'Call':{'as':'ফোন কৰক','hi':'कॉल करें'},
  '← My Rides':{'as':'← মোৰ যাত্ৰাসমূহ','hi':'← मेरी सवारियाँ'},
  /* Status */
  '⏳ Pending':{'as':'⏳ বিচাৰাধীন','hi':'⏳ लंबित'},
  '✓ Confirmed':{'as':'✓ নিশ্চিত','hi':'✓ पुष्टि'},
  '✓ Done':{'as':'✓ সম্পন্ন','hi':'✓ पूर्ण'},
  '✗ Cancelled':{'as':'✗ বাতিল','hi':'✗ रद्द'},
  '✓ Paid':{'as':'✓ পেমেন্ট হৈছে','hi':'✓ भुगतान हो गया'},
  '🔒 Locked':{'as':'🔒 লক','hi':'🔒 बंद'},
  'Unpaid':{'as':'পেমেন্ট বাকী','hi':'अभुगतान'},
  /* My bookings */
  'No rides yet':{'as':'এতিয়ালৈ কোনো যাত্ৰা নাই','hi':'अभी कोई सवारी नहीं'},
  'Book your first ride!':{'as':'প্ৰথম যাত্ৰা বুক কৰক!','hi':'पहली सवारी बुक करें!'},
  'View':{'as':'চাওক','hi':'देखें'},
  'All':{'as':'সকলো','hi':'सभी'},
  'Active':{'as':'সক্ৰিয়','hi':'सक्रिय'},
  'Completed':{'as':'সম্পন্ন','hi':'पूर्ण'},
  'Cancelled':{'as':'বাতিল','hi':'रद्द'},
  /* Profile */
  'My Profile':{'as':'মোৰ প্ৰফাইল','hi':'मेरी प्रोफ़ाइल'},
  'Edit Profile':{'as':'প্ৰফাইল সম্পাদনা কৰক','hi':'प्रोफ़ाइल संपादित करें'},
  'Wallet':{'as':'ৱালেট','hi':'वॉलेट'},
  'Loyalty Points':{'as':'আনুগত্য পয়েন্ট','hi':'वफ़ादारी अंक'},
  'Total Rides':{'as':'মুঠ যাত্ৰা','hi':'कुल सवारियाँ'},
  'Member Since':{'as':'সদস্যপদ','hi':'सदस्यता से'},
  'Save Changes':{'as':'পৰিৱৰ্তন সংৰক্ষণ কৰক','hi':'परिवर्तन सहेजें'},
  /* Payment */
  'Payment Successful! 🎉':{'as':'পেমেন্ট সফল! 🎉','hi':'भुगतान सफल! 🎉'},
  'Payment Failed':{'as':'পেমেন্ট বিফল','hi':'भुगतान विफल'},
  'Try Again':{'as':'পুনৰ চেষ্টা কৰক','hi':'फिर कोशिश करें'},
  /* Driver dashboard */
  "You're Online 🟢":{'as':'আপুনি অনলাইন আছে 🟢','hi':'आप ऑनलाइन हैं 🟢'},
  "You're Offline":{'as':'আপুনি অফলাইন আছে','hi':'आप ऑफलाइन हैं'},
  'Tap to go offline':{'as':'অফলাইন হ\'বলৈ টেপ কৰক','hi':'ऑफलाइन होने के लिए टैप करें'},
  'Tap to go online':{'as':'অনলাইন হ\'বলৈ টেপ কৰক','hi':'ऑनलाइन होने के लिए टैप करें'},
  'Riders can find and book you':{'as':'যাত্ৰীসকলে আপোনাক বিচাৰি বুক কৰিব পাৰে','hi':'यात्री आपको ढूंढकर बुक कर सकते हैं'},
  'Tap to start accepting rides':{'as':'যাত্ৰা গ্ৰহণ কৰিবলৈ টেপ কৰক','hi':'सवारी स्वीकार करने के लिए टैप करें'},
  'Incoming Ride Requests':{'as':'আহৰণ যাত্ৰাৰ অনুৰোধ','hi':'आने वाले सवारी अनुरोध'},
  'Accept Ride':{'as':'যাত্ৰা গ্ৰহণ কৰক','hi':'सवारी स्वीकार करें'},
  'Skip':{'as':'এৰি দিয়ক','hi':'छोड़ें'},
  'No ride requests right now. Stay online!':{'as':'এই মুহূৰ্তত কোনো অনুৰোধ নাই। অনলাইন থাকক!','hi':'अभी कोई अनुरोध नहीं। ऑनलाइन रहें!'},
  'All-Time Stats':{'as':'সামগ্ৰিক পৰিসংখ্যা','hi':'कुल आँकड़े'},
  "Today's Earnings":{'as':'আজিৰ উপাৰ্জন','hi':'आज की कमाई'},
  "Today's Rides":{'as':'আজিৰ যাত্ৰা','hi':'आज की सवारियाँ'},
  'Rating':{'as':'ৰেটিং','hi':'रेटिंग'},
  'Total Earned':{'as':'মুঠ উপাৰ্জন','hi':'कुल कमाई'},
  'Account Pending Approval':{'as':'একাউণ্ট অনুমোদনৰ অপেক্ষাত','hi':'खाता अनुमोदन लंबित'},
  /* Driver ride detail */
  '🔴 Live Ride Map':{'as':'🔴 লাইভ যাত্ৰা মেপ','hi':'🔴 लाइव सवारी मानचित्र'},
  'Start Ride — Customer Picked Up':{'as':'যাত্ৰা আৰম্ভ কৰক — গ্ৰাহক তুলি লোৱা হৈছে','hi':'सवारी शुरू करें — ग्राहक उठा लिया'},
  'Complete Ride':{'as':'যাত্ৰা সম্পন্ন কৰক','hi':'सवारी पूर्ण करें'},
  'Total Fare':{'as':'মুঠ ভাড়া','hi':'कुल किराया'},
  'Your Earnings (80%)':{'as':'আপোনাৰ উপাৰ্জন (৮০%)','hi':'आपकी कमाई (80%)'},
  'Ride Completed!':{'as':'যাত্ৰা সম্পন্ন!','hi':'सवारी पूर्ण!'},
  '← Back':{'as':'← ঘূৰি যাওক','hi':'← वापस'},
  /* Earnings */
  'Total All-Time Earnings':{'as':'মুঠ সামগ্ৰিক উপাৰ্জন','hi':'कुल सर्वकालिक कमाई'},
  'Withdraw Money':{'as':'টকা উঠাওক','hi':'पैसे निकालें'},
  'Bank / UPI Settings':{'as':'বেংক / UPI ছেটিং','hi':'बैंक / UPI सेटिंग'},
  'Last 7 Days':{'as':'শেষ ৭ দিন','hi':'पिछले 7 दिन'},
  'Completed Rides':{'as':'সম্পন্ন যাত্ৰাসমূহ','hi':'पूर्ण सवारियाँ'},
  'Available Wallet Balance':{'as':'উপলব্ধ ৱালেট বেলেঞ্চ','hi':'उपलब्ध वॉलेट बैलेंस'},
  'Minimum withdrawal: ₹100':{'as':'নূন্যতম উঠাই লোৱা: ₹১০০','hi':'न्यूनतम निकासी: ₹100'},
  'Your UPI ID':{'as':'আপোনাৰ UPI ID','hi':'आपका UPI ID'},
  'Bank Account Number':{'as':'বেংক একাউণ্ট নম্বৰ','hi':'बैंक खाता नंबर'},
  'IFSC Code':{'as':'IFSC ক\'ড','hi':'IFSC कोड'},
  'Save UPI Details':{'as':'UPI বিৱৰণ সংৰক্ষণ কৰক','hi':'UPI विवरण सहेजें'},
  'Save Bank Details':{'as':'বেংক বিৱৰণ সংৰক্ষণ কৰক','hi':'बैंक विवरण सहेजें'},
  'Request Withdrawal':{'as':'উঠাই লোৱাৰ অনুৰোধ কৰক','hi':'निकासी का अनुरोध करें'},
  'Withdrawal History':{'as':'উঠাই লোৱাৰ ইতিহাস','hi':'निकासी इतिहास'},
  /* Driver profile */
  'Complete Your Driver Profile':{'as':'ড্ৰাইভাৰ প্ৰফাইল সম্পূৰ্ণ কৰক','hi':'चालक प्रोफ़ाइल पूर्ण करें'},
  'Complete Profile & Continue':{'as':'প্ৰফাইল সম্পন্ন কৰি অব্যাহত ৰাখক','hi':'प्रोफ़ाइल पूर्ण करें और जारी रखें'},
  'Vehicle Number':{'as':'যানৰ নম্বৰ','hi':'वाहन नंबर'},
  'License Number':{'as':'লাইচেন্স নম্বৰ','hi':'लाइसेंस नंबर'},
  'Driving License Number':{'as':'ড্ৰাইভিং লাইচেন্স নম্বৰ','hi':'ड्राइविंग लाइसेंस नंबर'},
  /* Common */
  'Save':{'as':'সংৰক্ষণ','hi':'सहेजें'},
  'Cancel':{'as':'বাতিল','hi':'रद्द करें'},
  'Submit':{'as':'দাখিল কৰক','hi':'जमा करें'},
  'Confirm':{'as':'নিশ্চিত কৰক','hi':'पुष्टि करें'},
  'Edit':{'as':'সম্পাদনা','hi':'संपादित करें'},
  'Loading...':{'as':'লোড হৈছে...','hi':'लोड हो रहा है...'},
  'Live':{'as':'লাইভ','hi':'लाइव'},
  'Sign out':{'as':'ছাইন আউট','hi':'साइन आउट'},
  '← Back to Earnings':{'as':'← উপাৰ্জনলৈ ঘূৰি যাওক','hi':'← कमाई पर वापस'},
};

/* Build lowercase lookup */
var TL = {};
Object.keys(T).forEach(function(k){ TL[k.toLowerCase().trim()] = T[k]; });

function getLang(){
  var l = localStorage.getItem(LANG_KEY)||'en';
  return SUPPORTED.indexOf(l)>=0 ? l : 'en';
}

function tr(text, lang){
  if(lang==='en') return null;
  var t = text.trim();
  if(!t) return null;
  var e = TL[t.toLowerCase()];
  if(e && e[lang]) return e[lang];
  return null;
}

/* Walk DOM and translate every text node */
function walkDOM(node, lang){
  if(!node) return;
  if(node.nodeType===1){
    var tag=node.tagName.toUpperCase();
    if(tag==='SCRIPT'||tag==='STYLE'||tag==='TEXTAREA'||tag==='CODE'||tag==='PRE') return;
    /* Translate placeholders */
    if((tag==='INPUT'||tag==='TEXTAREA') && node.placeholder){
      var tp=tr(node.placeholder,lang);
      if(tp){ if(!node._op) node._op=node.placeholder; node.placeholder=tp; }
      else if(lang==='en' && node._op){ node.placeholder=node._op; }
    }
    for(var i=0;i<node.childNodes.length;i++) walkDOM(node.childNodes[i],lang);
  } else if(node.nodeType===3){
    var orig = node._orig!==undefined ? node._orig : node.textContent;
    var lead = orig.match(/^\s*/)[0];
    var trail= orig.match(/\s*$/)[0];
    var core = orig.trim();
    if(!core) return;
    var translated = tr(core, lang);
    if(translated){
      if(node._orig===undefined) node._orig=node.textContent;
      node.textContent = lead+translated+trail;
    } else if(lang==='en' && node._orig!==undefined){
      node.textContent=node._orig; delete node._orig;
    }
  }
}

function updateButtons(lang){
  document.querySelectorAll('.lang-btn').forEach(function(b){
    var bl=b.getAttribute('data-lang');
    var active=(bl===lang);
    b.classList.toggle('active',active);
    b.style.background = active ? '#1E8449' : '';
    b.style.color      = active ? '#fff'    : '';
    b.style.borderColor= active ? '#1E8449' : '';
    b.style.fontWeight = active ? '700'     : '600';
  });
}

function applyLang(lang){
  walkDOM(document.body, lang);
  document.documentElement.lang = lang;
  updateButtons(lang);
  localStorage.setItem(LANG_KEY, lang);
}

/* Public */
window.setLang = function(lang){
  if(SUPPORTED.indexOf(lang)<0) return;
  applyLang(lang);
};

window.t = function(key,lang){
  lang=lang||getLang();
  if(lang==='en') return key;
  var e=T[key];
  return (e&&e[lang]) ? e[lang] : key;
};

/* Boot */
function boot(){
  var lang=getLang();
  if(lang!=='en') applyLang(lang);
  else updateButtons('en');
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',boot);
} else { boot(); }

})();
