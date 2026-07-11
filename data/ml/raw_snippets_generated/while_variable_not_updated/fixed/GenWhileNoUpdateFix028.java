public class GenWhileNoUpdateFix028 {
    static void countdown(int budget) {
        while (budget > 0) {
            System.out.println("left: " + budget);
            budget--;
        }
    }

    static int largest1(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe3(int attempts) {
        if (attempts < 5) {
            return "low";
        } else if (attempts > 20) {
            return "high";
        }
        return "medium";
    }

    static String describe4(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }
}
