public class GenMissingBreakFix170 {
    static int largest1(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }

    static String describe2(int level) {
        if (level < 10) {
            return "low";
        } else if (level > 50) {
            return "high";
        }
        return "medium";
    }

    static String describe3(int points) {
        if (points < 5) {
            return "low";
        } else if (points > 20) {
            return "high";
        }
        return "medium";
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "queued";
                break;
            case 4:
                label = "final";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static int largest4(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }
}
