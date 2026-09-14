package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix023 {
    static int riskScore(String answer) {
        int score = 0;
        switch (answer.toLowerCase()) {
            case "never":
                score = 0;
                break;
            case "sometimes":
                score = 1;
                break;
            case "often":
                score = 2;
                break;
            case "always":
                score = 3;
                break;
        }
        return score;
    }
}
