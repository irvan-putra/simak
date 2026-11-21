package com.vanipy.simak;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Re-arms still-future session reminders after a phone restart. */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Reminders.rescheduleAll(ctx);
        }
    }
}
