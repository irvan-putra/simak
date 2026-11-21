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

    /**
     * Higher = stronger hint, for display ordering only. What counts as a
     * match is alike()'s call and is unchanged: every alike() pair scores
     * above zero. Tiers: exact name first, then the same words in another
     * order, then partial matches ranked by word overlap over both names
     * plus spelling closeness (Levenshtein, normalized by length) - so a
     * near-full-name match always beats one shared common word.
     */
    public static int score(String speaker, String contact) {
        List<String> s = tokens(speaker);
        List<String> c = tokens(contact);
        if (s.isEmpty() || c.isEmpty()) return 0;
        LinkedHashSet<String> shared = new LinkedHashSet<>(s);
        shared.retainAll(c);
        if (s.equals(c)) return 400 + s.size();
        if (shared.size() == s.size() && shared.size() == c.size()) {
            return 300 + s.size();  // same words, reordered
        }
        if (!alike(speaker, contact)) return 0;
        String sj = join(s);
        String cj = join(c);
        double overlap = 2.0 * shared.size() / (s.size() + c.size());
        double spelling = 1.0
                - (double) levenshtein(sj, cj) / Math.max(sj.length(), cj.length());
        return 100 + (int) Math.round(100 * (overlap + spelling));
    }

    /**
     * Display order for hints about one speaker: strongest first, ties
     * alphabetical by the contact name.
     */
    public static int compare(String speaker, String contactA, String contactB) {
        int d = Integer.compare(score(speaker, contactB), score(speaker, contactA));
        if (d != 0) return d;
        return contactA.compareToIgnoreCase(contactB);
    }

    /** Edit distance between two normalized names, for the partial tier. */
    static int levenshtein(String a, String b) {
        int[] prev = new int[b.length() + 1];
        for (int j = 0; j <= b.length(); j++) prev[j] = j;
        for (int i = 1; i <= a.length(); i++) {
            int[] cur = new int[b.length() + 1];
            cur[0] = i;
            for (int j = 1; j <= b.length(); j++) {
                int cost = a.charAt(i - 1) == b.charAt(j - 1) ? 0 : 1;
                cur[j] = Math.min(Math.min(cur[j - 1] + 1, prev[j] + 1), prev[j - 1] + cost);
            }
            prev = cur;
        }
        return prev[b.length()];
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
