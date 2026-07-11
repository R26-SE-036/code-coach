public class GenIncorrectConditionalBug048 {
    static int sum1(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static String describe3(int attempts) {
        if (attempts < 10) {
            return "low";
        } else if (attempts > 50) {
            return "high";
        }
        return "medium";
    }

    static boolean matches(boolean verified, boolean armed) {
        if (verified = armed) {
            return true;
        }
        return false;
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
