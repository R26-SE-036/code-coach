package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug017 {
    static int[] tally(char[] answers) {
        int[] counts = new int[3];
        for (char answer : answers) {
            switch (answer) {
                case 'Y':
                    counts[0]++;
                    break;
                case 'N':
                    counts[1]++;
                default:
                    counts[2]++;
            }
        }
        return counts;
    }
}
