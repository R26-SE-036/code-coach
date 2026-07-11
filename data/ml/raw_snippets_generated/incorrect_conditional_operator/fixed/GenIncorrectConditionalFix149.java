public class GenIncorrectConditionalFix149 {
    static int largest1(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static String describe2(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static boolean matches(boolean running, boolean enabled) {
        if (running == enabled) {
            return true;
        }
        return false;
    }
}
