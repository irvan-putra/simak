package com.vanipy.simak;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;

/**
 * Name similarity between the speaker list and contact names. Pure Java so
 * unit tests run on the JVM; no Android imports.
 *
 * A match is only ever a hint that two names look alike - never proof that
 * the contact is the speaker. The UI says so next to every result.
 */
public final class NameMatch {

    private NameMatch() {}

    /** Lowercase, letters only, split into tokens. */
    public static List<String> tokens(String name) {
        String norm = name.toLowerCase(Locale.ROOT).replaceAll("[^a-z]+", " ").trim();
        List<String> out = new ArrayList<>();
        if (norm.isEmpty()) return out;
        for (String t : norm.split(" +")) {
            if (!t.isEmpty()) out.add(t);
        }
        return out;
    }

    /**
     * True when the two names are alike enough to be worth a human look:
     * one contains the other as text, or they share at least two tokens,
     * or they share one long token (6+ letters, e.g. "kresna").
     */
    public static boolean alike(String speaker, String contact) {
        List<String> s = tokens(speaker);
        List<String> c = tokens(contact);
        if (s.isEmpty() || c.isEmpty()) return false;
        // Whole-name containment only counts when both sides have at least
        // two tokens; a single shared first name like "zain" is not a hint.
        if (s.size() >= 2 && c.size() >= 2) {
            String sj = " " + join(s) + " ";
            String cj = " " + join(c) + " ";
            if (sj.contains(cj) || cj.contains(sj)) return true;
        }
        LinkedHashSet<String> shared = new LinkedHashSet<>(s);
        shared.retainAll(c);
        if (shared.size() >= 2) return true;
        if (shared.size() == 1) {
            String only = shared.iterator().next();
            return only.length() >= 6;
        }
        return false;
    }

    private static String join(List<String> tokens) {
        StringBuilder sb = new StringBuilder();
        for (String t : tokens) {
            if (sb.length() > 0) sb.append(' ');
            sb.append(t);
        }
        return sb.toString();
    }
}
