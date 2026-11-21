package com.vanipy.simak;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.LinkedHashSet;
import java.util.Set;

/** Stars, notes and reminder toggles, all on-device in SharedPreferences. */
public final class Prefs {

    private static final String FILE = "simak";
    private static final String KEY_STARS = "stars";
    private static final String KEY_REMINDERS = "reminders";
    private static final String NOTE_PREFIX = "note:";

    private Prefs() {}

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }

    public static Set<String> stars(Context ctx) {
        return new LinkedHashSet<>(prefs(ctx).getStringSet(KEY_STARS, new LinkedHashSet<String>()));
    }

    public static boolean isStarred(Context ctx, String sessionId) {
        return stars(ctx).contains(sessionId);
    }

    public static void setStarred(Context ctx, String sessionId, boolean starred) {
        Set<String> set = stars(ctx);
        if (starred) set.add(sessionId); else set.remove(sessionId);
        prefs(ctx).edit().putStringSet(KEY_STARS, set).apply();
    }

    public static Set<String> reminders(Context ctx) {
        return new LinkedHashSet<>(prefs(ctx).getStringSet(KEY_REMINDERS, new LinkedHashSet<String>()));
    }

    public static boolean hasReminder(Context ctx, String sessionId) {
        return reminders(ctx).contains(sessionId);
    }

    public static void setReminder(Context ctx, String sessionId, boolean on) {
        Set<String> set = reminders(ctx);
        if (on) set.add(sessionId); else set.remove(sessionId);
        prefs(ctx).edit().putStringSet(KEY_REMINDERS, set).apply();
    }

    public static String note(Context ctx, String sessionId) {
        return prefs(ctx).getString(NOTE_PREFIX + sessionId, "");
    }

    public static void setNote(Context ctx, String sessionId, String text) {
        prefs(ctx).edit().putString(NOTE_PREFIX + sessionId, text).apply();
    }
}
