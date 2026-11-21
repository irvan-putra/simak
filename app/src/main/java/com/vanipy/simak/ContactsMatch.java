package com.vanipy.simak;

import android.content.Context;
import android.database.Cursor;
import android.provider.ContactsContract;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * On-device check of the speaker list against the phone's contacts. Reads
 * display names only, keeps everything in memory, and uploads nothing.
 */
public final class ContactsMatch {

    public static final class Hit {
        public final String speaker;
        public final String contact;

        Hit(String speaker, String contact) {
            this.speaker = speaker;
            this.contact = contact;
        }
    }

    private ContactsMatch() {}

    /** Speaker-to-contact name similarities. Call only after READ_CONTACTS is granted. */
    public static List<Hit> find(Context ctx) {
        List<String> contacts = new ArrayList<>();
        Cursor c = ctx.getContentResolver().query(
                ContactsContract.Contacts.CONTENT_URI,
                new String[]{ContactsContract.Contacts.DISPLAY_NAME},
                null, null, null);
        if (c != null) {
            try {
                while (c.moveToNext()) {
                    String name = c.getString(0);
                    if (name != null && !name.trim().isEmpty()) contacts.add(name.trim());
                }
            } finally {
                c.close();
            }
        }
        List<Hit> hits = new ArrayList<>();
        for (String speaker : ScheduleData.speakers()) {
            for (String contact : contacts) {
                if (NameMatch.alike(speaker, contact)) {
                    hits.add(new Hit(speaker, contact));
                }
            }
        }
        return hits;
    }

    /**
     * Speaker fields to their contact look-alikes, for highlighting agenda
     * cards with the matched names. Call only after READ_CONTACTS is
     * granted; names stay in memory on the device, never uploaded.
     */
    public static Map<String, List<String>> matchedBySpeaker(Context ctx) {
        Map<String, List<String>> byPart = new LinkedHashMap<>();
        for (Hit hit : find(ctx)) {
            List<String> names = byPart.get(hit.speaker);
            if (names == null) {
                names = new ArrayList<>();
                byPart.put(hit.speaker, names);
            }
            if (!names.contains(hit.contact)) names.add(hit.contact);
        }
        // Agenda cards render the raw speaker field, so join normalized
        // parts back to it: org-suffixed and multi-speaker cards highlight
        // too, with every matched contact name kept.
        Map<String, List<String>> out = new LinkedHashMap<>();
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            if (s.speaker.isEmpty()) continue;
            List<String> names = new ArrayList<>();
            for (String part : ScheduleData.speakerParts(s.speaker)) {
                List<String> hit = byPart.get(part);
                if (hit != null) {
                    for (String n : hit) {
                        if (!names.contains(n)) names.add(n);
                    }
                }
            }
            if (!names.isEmpty()) out.put(s.speaker, names);
        }
        return out;
    }
}
