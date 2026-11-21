package com.vanipy.simak;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class NameMatchTest {

    @Test
    public void exactAndCaseInsensitiveMatch() {
        assertTrue(NameMatch.alike("Kresna Satya", "kresna satya"));
        assertTrue(NameMatch.alike("Kresna Satya", "KRESNA SATYA"));
    }

    @Test
    public void partialTwoTokenMatch() {
        assertTrue(NameMatch.alike("Eko Kurniawan Khannedy", "Eko Khannedy"));
    }

    @Test
    public void singleLongTokenMatches() {
        assertTrue(NameMatch.alike("Kresna Satya", "Kresna"));
    }

    @Test
    public void singleShortCommonTokenDoesNotMatch() {
        assertFalse(NameMatch.alike("Zain Fathoni", "Zain"));
        assertFalse(NameMatch.alike("Iman Fattah", "Iman"));
    }

    @Test
    public void unrelatedNamesDoNotMatch() {
        assertFalse(NameMatch.alike("Kresna Satya", "Budi Santoso"));
        assertFalse(NameMatch.alike("Mustafa Zaki Assagaf", "Thomas Edwin Santosa"));
    }

    @Test
    public void punctuationAndExtraTokensAreIgnored() {
        assertTrue(NameMatch.alike("Muqorrobin Marufi Syihab / Robin", "Muqorrobin Syihab"));
        assertTrue(NameMatch.alike("luthfiyyah hanifah amari", "Luthfiyyah H. Amari"));
    }

    @Test
    public void emptyInputNeverMatches() {
        assertFalse(NameMatch.alike("", "Kresna"));
        assertFalse(NameMatch.alike("Kresna", ""));
    }

    @Test
    public void scoreRanksExactThenReorderedThenPartials() {
        int exact = NameMatch.score("Thomas Edwin Santosa", "thomas edwin santosa");
        int reordered = NameMatch.score("Thomas Edwin Santosa", "Santosa Thomas Edwin");
        int containment = NameMatch.score("Bagas Wastu", "Bagas Wastu Junior");
        int twoShared = NameMatch.score("Denny Aditya Pradipta", "Denny Wijaya Pradipta");
        int oneLong = NameMatch.score("Kresna Satya", "Kresna Wijaya");
        assertTrue(exact > reordered);
        assertTrue(reordered > containment);
        assertTrue(containment > 0);
        assertTrue(twoShared > 0);
        assertTrue(oneLong > 0);
        // every pair alike() accepts must score above zero, and no others
        assertTrue(NameMatch.alike("Kresna Satya", "Kresna Wijaya"));
        assertEquals(0, NameMatch.score("Bagas Wastu", "Kresna Satya"));
    }

    @Test
    public void nearFullNameBeatsOneSharedCommonWord() {
        // "Muhammad" alone must not outrank a near-full-name match
        int nearFull = NameMatch.score("Salahuddin Muhammad Iqbal", "Salahuddin Iqbal");
        int commonWord = NameMatch.score("Salahuddin Muhammad Iqbal", "Muhammad Rizqi");
        assertTrue(NameMatch.alike("Salahuddin Muhammad Iqbal", "Muhammad Rizqi"));
        assertTrue(nearFull > commonWord);
    }

    @Test
    public void compareBreaksTiesAlphabetically() {
        // equal-score reordered variants fall back to alphabetical
        assertTrue(NameMatch.compare("Thomas Edwin Santosa", "Santosa Edwin Thomas", "Santosa Thomas Edwin") < 0);
        assertTrue(NameMatch.compare("Thomas Edwin Santosa", "Santosa Thomas Edwin", "Santosa Edwin Thomas") > 0);
        // stronger score wins regardless of alphabetical order
        assertTrue(NameMatch.compare("Bagas Wastu", "Bagas Wastu", "Bagas Wastu Junior") < 0);
    }
}
