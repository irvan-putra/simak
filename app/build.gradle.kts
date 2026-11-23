plugins {
    id("com.android.application")
}

val appVersionName = "0.3.4"
val appVersionCode = 8

base {
    archivesName.set("simak-v$appVersionName")
}

android {
    namespace = "com.vanipy.simak"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.vanipy.simak"
        minSdk = 26
        targetSdk = 34
        versionCode = appVersionCode
        versionName = appVersionName
    }

    signingConfigs {
        create("release") {
            val ks = System.getenv("SIMAK_KEYSTORE_FILE")
            if (ks != null) {
                storeFile = file(ks)
                storePassword = System.getenv("SIMAK_STORE_PASSWORD")
                keyAlias = System.getenv("SIMAK_KEY_ALIAS")
                keyPassword = System.getenv("SIMAK_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            if (System.getenv("SIMAK_KEYSTORE_FILE") != null) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}
