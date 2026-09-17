package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix017 {
    static int[] tally(char[] answers) {
        int[] counts = new int[3];
        for (char answer : answers) {
            switch (answer) {
                case 'Y':
                    counts[0]++;
                    break;
                case 'N':
                    counts[1]++;
                    break;
                default:
                    counts[2]++;
            }
        }
        return counts;
    }
}
