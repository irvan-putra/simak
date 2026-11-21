package com.vanipy.simak;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

/** Fires one notification for a session reminder, then goes back to sleep. */
public class ReminderReceiver extends BroadcastReceiver {

    public static final String EXTRA_ID = "id";
    public static final String EXTRA_TITLE = "title";
    public static final String EXTRA_START = "start";
    private static final String CHANNEL = "session-reminders";

    @Override
    public void onReceive(Context ctx, Intent intent) {
        String id = intent.getStringExtra(EXTRA_ID);
        String title = intent.getStringExtra(EXTRA_TITLE);
        String start = intent.getStringExtra(EXTRA_START);
        if (id == null || title == null) return;

        NotificationManager nm = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(new NotificationChannel(
                    CHANNEL, "Session reminders", NotificationManager.IMPORTANCE_HIGH));
        }
        Intent open = new Intent(ctx, MainActivity.class);
        PendingIntent tap = PendingIntent.getActivity(ctx, id.hashCode(), open,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(ctx, CHANNEL)
                : new Notification.Builder(ctx);
        b.setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setContentTitle("Starting at " + (start == null ? "soon" : start))
                .setContentText(title)
                .setStyle(new Notification.BigTextStyle().bigText(title))
                .setContentIntent(tap)
                .setAutoCancel(true);
        nm.notify(id.hashCode(), b.build());

        // One-shot: the stored toggle is consumed so a later boot does not
        // resurrect an alarm for a session that already fired.
        Prefs.setReminder(ctx, id, false);
    }
}
