package com.vanipy.simak;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import java.util.Calendar;
import java.util.TimeZone;

/**
 * Session reminders as exact-or-best-effort AlarmManager alarms, ten minutes
 * before a session starts. No polling, no services, no wake locks: the app
 * does nothing in the background except deliver an alarm the user asked for.
 */
public final class Reminders {

    public static final long LEAD_MS = 10 * 60 * 1000L;
    private static final TimeZone TZ = TimeZone.getTimeZone("Asia/Jakarta");

    private Reminders() {}

    /** Start time of the session in epoch millis, Asia/Jakarta wall clock. */
    public static long sessionMillis(ScheduleData.Session s) {
        Calendar cal = Calendar.getInstance(TZ);
        String[] d = s.date.split("-");
        String[] t = s.start.split(":");
        cal.set(Integer.parseInt(d[0]), Integer.parseInt(d[1]) - 1, Integer.parseInt(d[2]),
                Integer.parseInt(t[0]), Integer.parseInt(t[1]), 0);
        cal.set(Calendar.MILLISECOND, 0);
        return cal.getTimeInMillis();
    }

    /**
     * Schedules the reminder. Returns null on success, or a short
     * user-facing reason when the alarm could only be approximate or the
     * session is already past.
     */
    public static String schedule(Context ctx, ScheduleData.Session s) {
        long at = sessionMillis(s) - LEAD_MS;
        if (at <= System.currentTimeMillis()) {
            return "already started";
        }
        AlarmManager am = (AlarmManager) ctx.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pi = intent(ctx, s);
        if (Build.VERSION.SDK_INT >= 31 && !am.canScheduleExactAlarms()) {
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, pi);
            return "approximate: exact alarms are off for this app in system settings";
        }
        am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, pi);
        return null;
    }

    public static void cancel(Context ctx, String sessionId) {
        AlarmManager am = (AlarmManager) ctx.getSystemService(Context.ALARM_SERVICE);
        Intent i = new Intent(ctx, ReminderReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(ctx, sessionId.hashCode(), i,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        am.cancel(pi);
        pi.cancel();
    }

    /** Re-arm every stored reminder still in the future (boot, app update, open). */
    public static void rescheduleAll(Context ctx) {
        for (String id : Prefs.reminders(ctx)) {
            ScheduleData.Session s = find(id);
            if (s == null) continue;
            if (sessionMillis(s) - LEAD_MS > System.currentTimeMillis()) {
                schedule(ctx, s);
            }
        }
    }

    public static ScheduleData.Session find(String sessionId) {
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            if (s.id.equals(sessionId)) return s;
        }
        return null;
    }

    private static PendingIntent intent(Context ctx, ScheduleData.Session s) {
        Intent i = new Intent(ctx, ReminderReceiver.class);
        i.putExtra(ReminderReceiver.EXTRA_ID, s.id);
        i.putExtra(ReminderReceiver.EXTRA_TITLE, s.title);
        i.putExtra(ReminderReceiver.EXTRA_START, s.start);
        return PendingIntent.getBroadcast(ctx, s.id.hashCode(), i,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }
}
