package com.vanipy.simak;

import org.junit.Test;

import java.util.HashSet;
import java.util.Set;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/** Guards the generated schedule data: the app is only as good as this table. */
public class ScheduleDataTest {

    @Test
    public void hasBothDays() {
        Set<String> days = new HashSet<>();
        for (ScheduleData.Session s : ScheduleData.SESSIONS) days.add(s.day);
        assertTrue(days.contains("day1"));
        assertTrue(days.contains("day2"));
    }

    @Test
    public void sessionIdsAreUnique() {
        Set<String> ids = new HashSet<>();
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            assertTrue("duplicate id " + s.id, ids.add(s.id));
        }
    }

    @Test
    public void timesAreWellFormedAndOrderedWithinEachDay() {
        String prevKey = "";
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            assertTrue(s.date.matches("\\d{4}-\\d{2}-\\d{2}"));
            assertTrue(s.start.matches("\\d{2}:\\d{2}"));
            assertTrue(s.end.matches("\\d{2}:\\d{2}"));
            assertTrue(s.start.compareTo(s.end) < 0);
            String key = s.day + s.start;
            assertTrue("sessions out of order at " + s.id, key.compareTo(prevKey) >= 0);
            prevKey = key;
        }
    }

    @Test
    public void kresnaIsDay2BrowserEngineTalk() {
        // Regression anchor: a real lookup asked for this speaker's slot.
        boolean found = false;
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            if (s.speaker.contains("Kresna Satya")) {
                found = true;
                assertEquals("day2", s.day);
                assertEquals("2026-11-22", s.date);
                assertEquals("13:55", s.start);
                assertEquals("14:25", s.end);
            }
        }
        assertTrue(found);
    }

    @Test
    public void everySessionHasTitleAndKind() {
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            assertFalse(s.title.isEmpty());
            assertFalse(s.kind.isEmpty());
            assertNotNull(s.speaker);
        }
    }

    @Test
    public void speakersListIsNonEmptyAndTrimmed() {
        String[] speakers = ScheduleData.speakers();
        assertTrue(speakers.length >= 10);
        for (String name : speakers) {
            assertEquals(name, name.trim());
            assertFalse(name.isEmpty());
        }
    }

    @Test
    public void guideHasAllSections() {
        assertEquals(4, ScheduleData.GUIDE.length);
        for (ScheduleData.Section sec : ScheduleData.GUIDE) {
            assertFalse(sec.title.isEmpty());
            assertTrue(sec.bullets.length > 0);
        }
    }

    @Test
    public void speakerPartsStripOrgSuffixes() {
        assertEquals(java.util.Arrays.asList("Zain Fathoni"),
                ScheduleData.speakerParts("Zain Fathoni (BookThatApp)"));
        assertEquals(java.util.Arrays.asList("Kresna Satya"),
                ScheduleData.speakerParts("Kresna Satya"));
    }

    @Test
    public void speakerPartsSplitMultiSpeakerCards() {
        assertEquals(java.util.Arrays.asList("Azzam Muhammadi Rizqun Karima", "Bagas Wastu"),
                ScheduleData.speakerParts("Azzam Muhammadi Rizqun Karima; Bagas Wastu"));
    }

    @Test
    public void everyCardSpeakerPartIsInSpeakersList() {
        // The highlight join depends on cards and speakers() agreeing here.
        Set<String> listed = new HashSet<>(java.util.Arrays.asList(ScheduleData.speakers()));
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            for (String part : ScheduleData.speakerParts(s.speaker)) {
                assertTrue("missing " + part, listed.contains(part));
            }
        }
    }

    @Test
    public void speakerPartsIgnorePunctuationInsideAffiliations() {
        assertEquals(java.util.Arrays.asList("Eko Kurniawan Khannedy"),
                ScheduleData.speakerParts(
                        "Eko Kurniawan Khannedy (Technical Architect at Blibli; founder of Programmer Zaman Now)"));
        assertEquals(java.util.Arrays.asList("Mansur Maturidi Arief"),
                ScheduleData.speakerParts("Mansur Maturidi Arief (KFUPM; AI Verification and Validation Lab)"));
    }

    @Test
    public void speakerPartsKeepEverySpeakerWhenAllCarryAffiliations() {
        assertEquals(java.util.Arrays.asList("Anisa Rahma", "Budi Santoso"),
                ScheduleData.speakerParts("Anisa Rahma (Lumbung); Budi Santoso (Sawit)"));
    }

    @Test
    public void lightningBlockIsSplitIntoPerTalkCardsSharingTheWindow() {
        java.util.List<ScheduleData.Session> lightning = new java.util.ArrayList<>();
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            if ("lightning".equals(s.kind)) lightning.add(s);
        }
        assertTrue("expected several lightning cards", lightning.size() >= 2);
        // the first card keeps the old combined card's id so existing
        // stars, notes and reminders stay attached
        assertEquals("d2-1430-a", lightning.get(0).id);
        for (ScheduleData.Session s : lightning) {
            assertEquals("14:30", s.start);
            assertEquals("15:30", s.end);
            assertFalse("one speaker per lightning card", s.speaker.contains(";"));
        }
    }

    @Test
    public void legacyWholeBlockEntryKeepsTheOldIdAndWindow() {
        ScheduleData.Session legacy = null;
        for (ScheduleData.Session s : ScheduleData.SESSIONS) {
            if (s.id.equals("d2-1430")) legacy = s;
        }
        assertNotNull("the old combined card's id must keep resolving", legacy);
        assertEquals("legacy", legacy.kind);
        assertEquals("14:30", legacy.start);
        assertEquals("15:30", legacy.end);
        assertEquals("", legacy.speaker);
    }
}
