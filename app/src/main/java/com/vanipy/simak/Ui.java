package com.vanipy.simak;

import android.content.Context;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.View;
import android.widget.TextView;

/** Small programmatic-UI helpers shared by the screens. */
public final class Ui {

    static final int INK = 0xFF10312B;      // deep teal ink
    static final int INK_SOFT = 0xFF4A6B63;
    static final int ACCENT = 0xFF0E7C66;   // teal accent
    static final int PAPER = 0xFFF7F6F1;
    static final int CARD = 0xFFFFFFFF;
    static final int STAR = 0xFFE8A13D;     // warm gold
    static final int LINE = 0x22000000;

    private Ui() {}

    static int dp(Context ctx, float v) {
        return (int) (v * ctx.getResources().getDisplayMetrics().density + 0.5f);
    }

    static TextView text(Context ctx, float sp, int color, int style) {
        TextView t = new TextView(ctx);
        t.setTextSize(sp);
        t.setTextColor(color);
        t.setTypeface(Typeface.DEFAULT, style);
        return t;
    }

    static GradientDrawable card(Context ctx) {
        return card(ctx, false);
    }

    /** Card background; highlighted cards get a warm tint and a gold edge. */
    static GradientDrawable card(Context ctx, boolean highlighted) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(highlighted ? 0xFFFCF3DF : CARD);
        g.setCornerRadius(dp(ctx, 12));
        g.setStroke(dp(ctx, 1), highlighted ? STAR : LINE);
        return g;
    }

    static void pad(View v, Context ctx, int l, int t, int r, int b) {
        v.setPadding(dp(ctx, l), dp(ctx, t), dp(ctx, r), dp(ctx, b));
    }
}
