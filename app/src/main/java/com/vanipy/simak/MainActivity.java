package com.vanipy.simak;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;

/**
 * simak - the IDSW 2026 companion. Two day tabs with the full agenda, a
 * guide tab with the topic walkthrough, stars, per-session notes and
 * reminders. Everything lives on the phone.
 */
public class MainActivity extends Activity {

    private static final int REQ_CONTACTS = 41;
    private static final int REQ_NOTIFICATIONS = 42;

    private LinearLayout content;
    private String day = "day1";
    private String pendingReminderSession;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Reminders.rescheduleAll(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Ui.PAPER);

        TextView head = Ui.text(this, 13, Ui.INK_SOFT, Typeface.NORMAL);
        head.setText("simak - " + ScheduleData.EVENT_NAME + " - " + ScheduleData.VENUE);
        Ui.pad(head, this, 16, 14, 16, 4);
        root.addView(head);

        LinearLayout tabs = new LinearLayout(this);
        tabs.setOrientation(LinearLayout.HORIZONTAL);
        Ui.pad(tabs, this, 12, 6, 12, 6);
        addTab(tabs, "Day 1", "day1");
        addTab(tabs, "Day 2", "day2");
        addTab(tabs, "Guide", "guide");
        root.addView(tabs);

        ScrollView scroll = new ScrollView(this);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        Ui.pad(content, this, 12, 4, 12, 24);
        scroll.addView(content);
        root.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        setContentView(root);
        render();
    }

    private void addTab(LinearLayout tabs, String label, String id) {
        Button b = new Button(this);
        b.setText(label);
        b.setOnClickListener(v -> { day = id; render(); });
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        lp.setMargins(Ui.dp(this, 4), 0, Ui.dp(this, 4), 0);
        tabs.addView(b, lp);
    }

    private void render() {
        content.removeAllViews();
        if ("guide".equals(day)) {
            renderGuide();
            return;
        }
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            if (s.day.equals(day)) content.addView(sessionCard(s));
        }
        TextView foot = Ui.text(this, 12, Ui.INK_SOFT, Typeface.NORMAL);
        foot.setText("Agenda from " + ScheduleData.SOURCE + ", checked "
                + ScheduleData.CHECKED + ". Subject to change.\n" + ScheduleData.EVENT_NOTE);
        Ui.pad(foot, this, 8, 20, 8, 8);
        content.addView(foot);
    }

    private View sessionCard(ScheduleData.Session s) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(Ui.card(this));
        Ui.pad(card, this, 12, 10, 12, 10);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, Ui.dp(this, 4), 0, Ui.dp(this, 4));
        card.setLayoutParams(lp);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        TextView time = Ui.text(this, 13, Ui.ACCENT, Typeface.BOLD);
        time.setText(s.start + " - " + s.end);
        top.addView(time, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView bell = Ui.text(this, 18, Ui.INK_SOFT, Typeface.NORMAL);
        bell.setText(Prefs.hasReminder(this, s.id) ? "🔔" : "🔕");
        Ui.pad(bell, this, 8, 0, 8, 0);
        bell.setOnClickListener(v -> toggleReminder(s, bell));
        top.addView(bell);

        TextView star = Ui.text(this, 20, Prefs.isStarred(this, s.id) ? Ui.STAR : Ui.INK_SOFT, Typeface.NORMAL);
        star.setText(Prefs.isStarred(this, s.id) ? "★" : "☆");
        Ui.pad(star, this, 8, 0, 4, 0);
        star.setOnClickListener(v -> {
            boolean now = !Prefs.isStarred(this, s.id);
            Prefs.setStarred(this, s.id, now);
            star.setText(now ? "★" : "☆");
            star.setTextColor(now ? Ui.STAR : Ui.INK_SOFT);
        });
        top.addView(star);
        card.addView(top);

        TextView title = Ui.text(this, 16, Ui.INK, Typeface.BOLD);
        title.setText(s.title);
        card.addView(title);

        if (!s.speaker.isEmpty()) {
            TextView speaker = Ui.text(this, 13, Ui.INK_SOFT, Typeface.NORMAL);
            speaker.setText(s.speaker);
            card.addView(speaker);
        }

        LinearLayout noteArea = new LinearLayout(this);
        noteArea.setOrientation(LinearLayout.VERTICAL);
        noteArea.setVisibility(View.GONE);
        EditText note = new EditText(this);
        note.setHint("Your note for this session");
        note.setTextSize(14);
        note.setMinLines(2);
        note.setText(Prefs.note(this, s.id));
        note.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence c, int a, int b, int n) {}
            public void onTextChanged(CharSequence c, int a, int b, int n) {}
            public void afterTextChanged(Editable e) { Prefs.setNote(MainActivity.this, s.id, e.toString()); }
        });
        noteArea.addView(note);
        card.addView(noteArea);

        View.OnClickListener expand = v ->
                noteArea.setVisibility(noteArea.getVisibility() == View.GONE ? View.VISIBLE : View.GONE);
        title.setOnClickListener(expand);
        time.setOnClickListener(expand);
        return card;
    }

    private void toggleReminder(ScheduleData.Session s, TextView bell) {
        if (Prefs.hasReminder(this, s.id)) {
            Reminders.cancel(this, s.id);
            Prefs.setReminder(this, s.id, false);
            bell.setText("🔕");
            return;
        }
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            pendingReminderSession = s.id;
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIFICATIONS);
            return;
        }
        enableReminder(s, bell);
    }

    private void enableReminder(ScheduleData.Session s, TextView bell) {
        String warn = Reminders.schedule(this, s);
        if ("already started".equals(warn)) {
            Toast.makeText(this, "That session already started.", Toast.LENGTH_SHORT).show();
            return;
        }
        Prefs.setReminder(this, s.id, true);
        if (bell != null) bell.setText("🔔"); else render();
        Toast.makeText(this,
                warn != null ? warn : "Reminder set for 10 minutes before " + s.start + ".",
                Toast.LENGTH_SHORT).show();
    }

    private void renderGuide() {
        TextView about = Ui.text(this, 14, Ui.INK, Typeface.NORMAL);
        about.setText(ScheduleData.ABOUT);
        Ui.pad(about, this, 4, 8, 4, 12);
        content.addView(about);

        Button people = new Button(this);
        people.setText("Speakers you may know (uses your contacts, on this phone only)");
        people.setOnClickListener(v -> checkContacts());
        content.addView(people);

        for (ScheduleData.Section sec : ScheduleData.GUIDE) {
            TextView h = Ui.text(this, 16, Ui.ACCENT, Typeface.BOLD);
            h.setText(sec.title);
            Ui.pad(h, this, 4, 18, 4, 4);
            content.addView(h);
            for (String b : sec.bullets) {
                TextView t = Ui.text(this, 14, Ui.INK, Typeface.NORMAL);
                t.setText("•  " + b);
                Ui.pad(t, this, 8, 3, 4, 3);
                content.addView(t);
            }
        }

        TextView foot = Ui.text(this, 12, Ui.INK_SOFT, Typeface.NORMAL);
        foot.setText("The agenda is from " + ScheduleData.SOURCE + " (checked "
                + ScheduleData.CHECKED + "). The guide above is our interpretation and "
                + "suggestions, not the organizers' descriptions.");
        Ui.pad(foot, this, 4, 20, 4, 8);
        content.addView(foot);
    }

    private void checkContacts() {
        if (Build.VERSION.SDK_INT >= 23
                && checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.READ_CONTACTS}, REQ_CONTACTS);
            return;
        }
        showContactMatches();
    }

    private void showContactMatches() {
        List<ContactsMatch.Hit> hits = ContactsMatch.find(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setBackground(Ui.card(this));
        Ui.pad(box, this, 12, 10, 12, 10);

        TextView h = Ui.text(this, 15, Ui.ACCENT, Typeface.BOLD);
        h.setText("Speakers who look like your contacts");
        box.addView(h);

        TextView caveat = Ui.text(this, 12, Ui.INK_SOFT, Typeface.NORMAL);
        caveat.setText("Name similarity only - not proof it is the same person. "
                + "Contact names never leave this phone.");
        Ui.pad(caveat, this, 0, 4, 0, 8);
        box.addView(caveat);

        if (hits.isEmpty()) {
            TextView none = Ui.text(this, 14, Ui.INK, Typeface.NORMAL);
            none.setText("No speaker names look like your saved contacts.");
            box.addView(none);
        } else {
            for (ContactsMatch.Hit hit : hits) {
                TextView t = Ui.text(this, 14, Ui.INK, Typeface.NORMAL);
                t.setText("•  " + hit.speaker + "  ≈  " + hit.contact);
                Ui.pad(t, this, 0, 2, 0, 2);
                box.addView(t);
            }
        }
        content.addView(box, 2);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        boolean granted = grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        if (requestCode == REQ_CONTACTS) {
            if (granted) showContactMatches();
            else Toast.makeText(this, "No contacts access - the speakers-you-may-know check stays off.", Toast.LENGTH_LONG).show();
        } else if (requestCode == REQ_NOTIFICATIONS) {
            if (granted && pendingReminderSession != null) {
                ScheduleData.Session s = Reminders.find(pendingReminderSession);
                pendingReminderSession = null;
                if (s != null) enableReminder(s, null);
            } else {
                pendingReminderSession = null;
                Toast.makeText(this, "Notifications are off, so reminders cannot alert you.", Toast.LENGTH_LONG).show();
            }
        }
    }
}
