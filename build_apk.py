import os, sys, shutil, subprocess
from pathlib import Path

BUILD_DIR = Path("./AimlockFF_Project")
OUTPUT_APK = Path("./AimlockFF.apk")

MANIFEST = '<?xml version="1.0" encoding="utf-8"?><manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.aimlockff"><uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/><uses-permission android:name="android.permission.FOREGROUND_SERVICE"/><uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/><uses-permission android:name="android.permission.KILL_BACKGROUND_PROCESSES"/><application android:allowBackup="true" android:label="Aimlock FF" android:icon="@android:drawable/ic_menu_view" android:theme="@android:style/Theme.Material.NoActionBar"><activity android:name=".MainActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity><service android:name=".OverlayService" android:exported="false" android:foregroundServiceType="specialUse"/></application></manifest>'

MAIN_ACTIVITY = '''package com.example.aimlockff
import android.app.*
import android.content.*
import android.graphics.*
import android.net.Uri
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.*
class MainActivity : Activity() {
    override fun onCreate(s: Bundle?) {
        super.onCreate(s)
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(60,80,60,80); setBackgroundColor(Color.parseColor("#0B0F14")) }
        val title = TextView(this).apply { text="AIMLOCK FF"; textSize=26f; setTextColor(Color.parseColor("#FF3B3B")); gravity=Gravity.CENTER; setPadding(0,0,0,50) }
        root.addView(title)
        val swAim = Switch(this).apply { text="Aimlock Mode"; textSize=18f; setTextColor(Color.WHITE) }
        root.addView(swAim)
        val swCross = Switch(this).apply { text="Tâm ảo màu đỏ"; textSize=18f; setTextColor(Color.WHITE) }
        root.addView(swCross)
        val swRam = Switch(this).apply { text="Tăng tốc RAM"; textSize=18f; setTextColor(Color.WHITE) }
        root.addView(swRam)
        val btnOn = Button(this).apply { text="BẬT OVERLAY"; setTextColor(Color.WHITE); setBackgroundColor(Color.parseColor("#FF3B3B")) }
        root.addView(btnOn)
        val btnOff = Button(this).apply { text="TẮT OVERLAY"; setTextColor(Color.WHITE); setBackgroundColor(Color.parseColor("#37474F")) }
        root.addView(btnOff)
        val status = TextView(this).apply { text="Trạng thái: Chưa bật"; setTextColor(Color.parseColor("#8FA3B0")); gravity=Gravity.CENTER }
        root.addView(status)
        setContentView(root)
        btnOn.setOnClickListener {
            if (!Settings.canDrawOverlays(this)) {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
                return@setOnClickListener
            }
            val i = Intent(this, OverlayService::class.java).apply {
                putExtra("aimlock", swAim.isChecked)
                putExtra("crosshair", swCross.isChecked)
                putExtra("ramboost", swRam.isChecked)
            }
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(i) else startService(i)
            status.text = "Trạng thái: Đang bật"
        }
        btnOff.setOnClickListener {
            stopService(Intent(this, OverlayService::class.java))
            status.text = "Trạng thái: Đã tắt"
        }
    }
}
class OverlayService : Service() {
    private lateinit var wm: WindowManager
    private var cross: View? = null
    private var ov: View? = null
    override fun onBind(i: Intent?) = null
    override fun onStartCommand(i: Intent?, f: Int, s: Int): Int {
        startForeground(1, notif())
        val aim = i?.getBooleanExtra("aimlock", false) ?: false
        val cr = i?.getBooleanExtra("crosshair", false) ?: false
        val rb = i?.getBooleanExtra("ramboost", false) ?: false
        wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        if (cr) addCross()
        if (aim) addOv()
        if (rb) try {
            val am = getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
            am.killBackgroundProcesses("com.dts.freefireth")
            am.killBackgroundProcesses("com.dts.freefiremax")
            Runtime.getRuntime().gc(); System.gc()
        } catch (_: Exception) {}
        return START_STICKY
    }
    private fun addCross() {
        if (cross != null) return
        val v = object : View(this) {
            val p = Paint().apply { color=Color.RED; strokeWidth=4f; style=Paint.Style.STROKE; isAntiAlias=true }
            override fun onDraw(c: Canvas) {
                val cx=width/2f; val cy=height/2f; val sz=40f; val g=10f
                c.drawLine(cx,cy-sz,cx,cy-g,p); c.drawLine(cx,cy+g,cx,cy+sz,p)
                c.drawLine(cx-sz,cy,cx-g,cy,p); c.drawLine(cx+g,cy,cx+sz,cy,p)
                c.drawCircle(cx,cy,3f,p)
            }
        }
        val t = if (Build.VERSION.SDK_INT >= 26) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else @Suppress("DEPRECATION") WindowManager.LayoutParams.TYPE_PHONE
        val lp = WindowManager.LayoutParams(200,200,t, WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN, PixelFormat.TRANSLUCENT).apply { gravity=Gravity.CENTER }
        wm.addView(v, lp); cross = v
    }
    private fun addOv() {
        if (ov != null) return
        val v = View(this).apply { setBackgroundColor(Color.TRANSPARENT) }
        val t = if (Build.VERSION.SDK_INT >= 26) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else @Suppress("DEPRECATION") WindowManager.LayoutParams.TYPE_PHONE
        val lp = WindowManager.LayoutParams(WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.MATCH_PARENT, t, WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE, PixelFormat.TRANSLUCENT)
        wm.addView(v, lp); ov = v
    }
    private fun notif(): Notification {
        val ch = "aimlock_channel"
        if (Build.VERSION.SDK_INT >= 26) {
            val nm = getSystemService(NotificationManager::class.java)
            if (nm.getNotificationChannel(ch) == null) nm.createNotificationChannel(NotificationChannel(ch, "Aimlock FF", NotificationManager.IMPORTANCE_LOW))
            return Notification.Builder(this, ch).setContentTitle("Aimlock FF").setContentText("Overlay đang chạy").setSmallIcon(android.R.drawable.ic_menu_view).build()
        } else {
            @Suppress("DEPRECATION") return Notification.Builder(this).setContentTitle("Aimlock FF").setContentText("Overlay đang chạy").setSmallIcon(android.R.drawable.ic_menu_view).build()
        }
    }
    override fun onDestroy() {
        super.onDestroy()
        cross?.let { runCatching { wm.removeView(it) } }; ov?.let { runCatching { wm.removeView(it) } }
        cross=null; ov=null
    }
}
'''

BUILD_GRADLE = '''plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}
android {
    namespace 'com.example.aimlockff'
    compileSdk 34
    defaultConfig {
        applicationId "com.example.aimlockff"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = '17' }
}
dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
}
'''

ROOT_GRADLE = '''plugins {
    id 'com.android.application' version '8.2.0' apply false
    id 'org.jetbrains.kotlin.android' version '1.9.20' apply false
}
'''

SETTINGS = '''pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories { google(); mavenCentral() } }
rootProject.name = "AimlockFF"
include ':app'
'''

PROPS = 'org.gradle.jvmargs=-Xmx2048m\nandroid.useAndroidX=true\nkotlin.code.style=official\n'

def w(p, c):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(c, encoding="utf-8")

def setup():
    if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    w(BUILD_DIR / "settings.gradle", SETTINGS)
    w(BUILD_DIR / "build.gradle", ROOT_GRADLE)
    w(BUILD_DIR / "gradle.properties", PROPS)
    w(BUILD_DIR / "app" / "build.gradle", BUILD_GRADLE)
    w(BUILD_DIR / "app" / "src" / "main" / "AndroidManifest.xml", MANIFEST)
    w(BUILD_DIR / "app" / "src" / "main" / "java" / "com" / "example" / "aimlockff" / "MainActivity.kt", MAIN_ACTIVITY)

def build():
    env = os.environ.copy()
    sdk = env.get("ANDROID_HOME") or env.get("ANDROID_SDK_ROOT")
    if sdk: w(BUILD_DIR / "local.properties", f"sdk.dir={sdk}\n")
    g = shutil.which("gradle") or shutil.which("gradle.bat")
    if not g: print("No gradle"); sys.exit(1)
    r = subprocess.run([g, "assembleDebug", "--no-daemon", "-q"], cwd=BUILD_DIR, env=env)
    if r.returncode != 0: sys.exit(1)
    apk = BUILD_DIR / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    if apk.exists(): shutil.copy(apk, OUTPUT_APK); print(str(OUTPUT_APK.resolve()))
    else: sys.exit(1)

if __name__ == "__main__":
    setup()
    build()
