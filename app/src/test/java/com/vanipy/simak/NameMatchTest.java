package com.vanipy.simak;

import org.junit.Test;

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
}
